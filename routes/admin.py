"""Administrator area: statistics, user management, product review, orders."""
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from extensions import db
from models import (ContactMessage, Customer, Farmer, Notification, Order,
                    OrderItem, Product, User)
from utils import notify, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    today = date.today()
    stats = {
        "farmers": User.query.filter_by(role="farmer").count(),
        "customers": User.query.filter_by(role="customer").count(),
        "products": Product.query.count(),
        "pending": Product.query.filter_by(status="pending").count(),
        "approved": Product.query.filter_by(status="approved").count(),
        "rejected": Product.query.filter_by(status="rejected").count(),
        "orders_today": Order.query.filter(func.date(Order.created_at) == today).count(),
        "orders": Order.query.count(),
        "sales": float(db.session.query(func.coalesce(func.sum(Order.total), 0)).scalar()),
    }

    # Revenue + order count for the last 7 days (fed to the charts).
    labels, revenue, order_counts = [], [], []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        labels.append(day.strftime("%d %b"))
        day_orders = Order.query.filter(func.date(Order.created_at) == day).all()
        revenue.append(round(sum(float(o.total) for o in day_orders), 2))
        order_counts.append(len(day_orders))

    recent_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
    chart = {"labels": labels, "revenue": revenue, "orders": order_counts,
             "product_status": [stats["approved"], stats["pending"], stats["rejected"]],
             "users": [stats["farmers"], stats["customers"]]}

    return render_template("admin/dashboard.html", stats=stats, chart=chart,
                           recent_products=recent_products, recent_orders=recent_orders)


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------
@admin_bp.route("/users")
@admin_bp.route("/users/<role>")
@role_required("admin")
def users(role=None):
    query = User.query
    if role in ("customer", "farmer", "admin"):
        query = query.filter_by(role=role)
    rows = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=rows, role=role)


@admin_bp.route("/farmers")
@role_required("admin")
def farmers():
    return redirect(url_for("admin.users", role="farmer"))


@admin_bp.route("/customers")
@role_required("admin")
def customers():
    return redirect(url_for("admin.users", role="customer"))


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@role_required("admin")
def toggle_suspend(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Administrator accounts cannot be suspended.", "danger")
    else:
        user.status = "suspended" if user.status == "active" else "active"
        db.session.commit()
        flash(f"{user.full_name} is now {user.status}.", "success")
    return redirect(request.referrer or url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Administrator accounts cannot be deleted.", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
    return redirect(request.referrer or url_for("admin.users"))


# --------------------------------------------------------------------------
# Product review workflow
# --------------------------------------------------------------------------
@admin_bp.route("/products")
@admin_bp.route("/products/<status>")
@role_required("admin")
def products(status=None):
    query = Product.query
    if status in ("pending", "approved", "rejected"):
        query = query.filter_by(status=status)
    rows = query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=rows, status=status)


@admin_bp.route("/products/<int:product_id>/approve", methods=["POST"])
@role_required("admin")
def approve_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.status = "approved"
    product.rejection_reason = None
    notify(product.farmer.user_id, f"Your product '{product.name}' was approved.",
           url_for("farmer.products", status="approved"))
    db.session.commit()
    flash(f"'{product.name}' approved and published.", "success")
    return redirect(request.referrer or url_for("admin.products", status="pending"))


@admin_bp.route("/products/<int:product_id>/reject", methods=["POST"])
@role_required("admin")
def reject_product(product_id):
    product = Product.query.get_or_404(product_id)
    reason = (request.form.get("reason") or "").strip()[:255] or "No reason provided."
    product.status = "rejected"
    product.rejection_reason = reason
    notify(product.farmer.user_id,
           f"Your product '{product.name}' was rejected: {reason}",
           url_for("farmer.products", status="rejected"))
    db.session.commit()
    flash(f"'{product.name}' rejected.", "success")
    return redirect(request.referrer or url_for("admin.products", status="pending"))


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@role_required("admin")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(request.referrer or url_for("admin.products"))


# --------------------------------------------------------------------------
# Orders / reports / settings
# --------------------------------------------------------------------------
@admin_bp.route("/orders")
@role_required("admin")
def orders():
    rows = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=rows)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@role_required("admin")
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status in ("pending", "confirmed", "shipped", "delivered", "cancelled"):
        order.status = new_status
        notify(order.user_id, f"Order #{order.id} is now {new_status}.",
               url_for("customer.orders"))
        db.session.commit()
        flash(f"Order #{order.id} marked as {new_status}.", "success")
    return redirect(url_for("admin.orders"))


@admin_bp.route("/reports")
@role_required("admin")
def reports():
    top_products = (db.session.query(Product, func.sum(OrderItem.quantity).label("sold"))
                    .join(OrderItem, OrderItem.product_id == Product.id)
                    .group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc())
                    .limit(10).all())
    top_farmers = (db.session.query(Farmer,
                                    func.sum(OrderItem.price * OrderItem.quantity).label("earned"))
                   .join(OrderItem, OrderItem.farmer_id == Farmer.id)
                   .group_by(Farmer.id)
                   .order_by(func.sum(OrderItem.price * OrderItem.quantity).desc())
                   .limit(10).all())
    total_sales = float(db.session.query(func.coalesce(func.sum(Order.total), 0)).scalar())
    return render_template("admin/reports.html", top_products=top_products,
                           top_farmers=top_farmers, total_sales=total_sales)


@admin_bp.route("/settings")
@role_required("admin")
def settings():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(30).all()
    return render_template("admin/settings.html", messages=messages)
