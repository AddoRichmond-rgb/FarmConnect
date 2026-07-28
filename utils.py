"""Shared helpers: auth decorators, upload validation, notifications."""
import os
import re
import uuid
from functools import wraps

from flask import abort, current_app, flash, redirect, session, url_for
from werkzeug.utils import secure_filename

from extensions import db
from models import Notification, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


# --------------------------------------------------------------------------
# Session / authorisation
# --------------------------------------------------------------------------
def current_user():
    """Return the logged-in User row, or None."""
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Role-based access control decorator, e.g. @role_required('admin')."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if user.status == "suspended":
                session.clear()
                flash("Your account has been suspended.", "danger")
                return redirect(url_for("auth.login"))
            if user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def allowed_file(filename: str) -> bool:
    return ("." in filename
            and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"])


def save_image(file_storage):
    """Validate and store an uploaded image. Returns the stored filename or None."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    safe = secure_filename(name)
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, safe))
    return safe


# --------------------------------------------------------------------------
# Notifications
# --------------------------------------------------------------------------
def notify(user_id: int, message: str, link: str | None = None) -> None:
    """Create an in-app notification (structure is email-ready)."""
    db.session.add(Notification(user_id=user_id, message=message, link=link))


def notify_admins(message: str, link: str | None = None) -> None:
    for admin in User.query.filter_by(role="admin").all():
        notify(admin.id, message, link)
