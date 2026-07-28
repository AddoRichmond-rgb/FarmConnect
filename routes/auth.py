"""Registration, login, logout and password management."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from extensions import db
from models import Customer, Farmer, User
from utils import current_user, login_required, notify_admins, valid_email

auth_bp = Blueprint("auth", __name__)


def _dashboard_for(user):
    return url_for(f"{user.role}.dashboard")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Self-service registration for customers and farmers (never admins)."""
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        role = request.form.get("role")

        errors = []
        if len(full_name) < 3:
            errors.append("Full name must be at least 3 characters.")
        if not valid_email(email):
            errors.append("Enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if role not in ("customer", "farmer"):
            errors.append("Choose an account type.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        user = User(full_name=full_name[:120], email=email, phone=phone[:30], role=role)
        user.set_password(password)                     # Werkzeug password hashing
        db.session.add(user)
        db.session.flush()                              # get user.id before commit

        if role == "farmer":
            db.session.add(Farmer(user_id=user.id,
                                  farm_name=(request.form.get("farm_name") or "").strip()[:140],
                                  farm_location=(request.form.get("farm_location") or "").strip()[:140]))
            notify_admins(f"New farmer registered: {full_name}", url_for("admin.farmers"))
        else:
            db.session.add(Customer(user_id=user.id,
                                    address=(request.form.get("address") or "").strip()[:255]))
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)
        if user.status == "suspended":
            flash("This account has been suspended. Contact support.", "danger")
            return render_template("login.html", email=email)

        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        session.permanent = True
        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
        return redirect(_dashboard_for(user))

    return render_template("login.html", email="")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    user = current_user()
    current = request.form.get("current_password") or ""
    new = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not user.check_password(current):
        flash("Your current password is incorrect.", "danger")
    elif len(new) < 8:
        flash("New password must be at least 8 characters.", "danger")
    elif new != confirm:
        flash("New passwords do not match.", "danger")
    else:
        user.set_password(new)
        db.session.commit()
        flash("Password updated successfully.", "success")
    return redirect(url_for(f"{user.role}.profile"))
