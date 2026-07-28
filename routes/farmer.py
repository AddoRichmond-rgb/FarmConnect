"""Farmer area: product CRUD, approval tracking, orders, profile."""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)

from extensions import db
from models import Category, Notification, Order, OrderItem, Product, ProductImage
from utils import current_user, notify_admins, role_required, save_image

farmer_bp = Blueprint("farmer", __name__, url_prefix="/farmer")


def _me():
    """Return the Farmer profile of the logged-in user."""
    user = current_user()
    if not user.farmer:
        abort(403)
    return user.farmer


def _owned(product_id):
    """Fetch a product, ensuring it belongs to the logged-in farmer."""
    product = Product.query.get_or_404(product_id)
    if product.farmer_id != _me().id:
        abort(403)
    return product


@farmer_bp.route("/dashboard")
@role_required("farmer")
def dashboard():
    me = _me()
    products = Product.query.filter_by(farmer_id=me.id)
    stats = {
        "total": products.count(),
        "pending": products.filter_by(status="pending").count(),
        "approved": products.filter_by(status="approved").count(),
        "rejected": products.filter_by(status="rejected").count(),
    }
    order_items = (OrderItem.query.filter_by(farmer_id=me.id)
                   .join(Order).order_by(Order.created_at.desc()).limit(5).all())
    stats["revenue"] = sum(float(i.price) * i.quantity
                           for i in OrderItem.query.filter_by(farmer_id=me.id).all())
    notifications = (Notification.query.filter_by(user_id=current_user().id)
                     .order_by(Notification.created_at.desc()).limit(6).all())
    return render_template("farmer/dashboard.html", stats=stats,
                           order_items=order_items, notifications=notifications)


@farmer_bp.route("/products")
@farmer_bp.route("/products/<status>")
@role_required("farmer")
def products(status=None):
    query = Product.query.filter_by(farmer_id=_me().id)
    if status in ("pending", "approved", "rejected"):
        query = query.filter_by(status=status)
    rows = query.order_by(Product.created_at.desc()).all()
    return render_template("farmer/products.html", products=rows, status=status)


@farmer_bp.route("/products/add", methods=["GET", "POST"])
@role_required("farmer")
def add_product():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        price = request.form.get("price", type=float)
        quantity = request.form.get("quantity", type=int)
        category_id = request.form.get("category_id", type=int)

        errors = []
        if len(name) < 3:
            errors.append("Product name is too short.")
        if price is None or price <= 0:
            errors.append("Enter a valid price.")
        if quantity is None or quantity < 0:
            errors.append("Enter a valid quantity.")
        if not category_id:
            errors.append("Choose a category.")

        image = save_image(request.files.get("image"))
        if request.files.get("image") and request.files["image"].filename and not image:
            errors.append("Image must be a PNG, JPG, JPEG, WEBP or GIF file.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("farmer/product_form.html", categories=categories,
                                   product=None, form=request.form)

        product = Product(
            farmer_id=_me().id, category_id=category_id, name=name[:160],
            description=(request.form.get("description") or "").strip()[:2000],
            price=price, quantity=quantity,
            unit=request.form.get("unit", "kg"), image=image,
            location=(request.form.get("location") or _me().farm_location or "")[:140],
            status="pending",          # every product waits for admin review
        )
        db.session.add(product)
        db.session.flush()

        # optional extra gallery images
        for extra in request.files.getlist("gallery"):
            fn = save_image(extra)
            if fn:
                db.session.add(ProductImage(product_id=product.id, filename=fn))

        notify_admins(f"New product awaiting approval: {product.name}",
                      url_for("admin.products", status="pending"))
        db.session.commit()
        flash("Product submitted. An administrator will review it shortly.", "success")
        return redirect(url_for("farmer.products", status="pending"))

    return render_template("farmer/product_form.html", categories=categories,
                           product=None, form={})


@farmer_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@role_required("farmer")
def edit_product(product_id):
    product = _owned(product_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        product.name = (request.form.get("name") or product.name).strip()[:160]
        product.description = (request.form.get("description") or "").strip()[:2000]
        product.price = request.form.get("price", type=float) or product.price
        product.quantity = request.form.get("quantity", type=int) or 0
        product.unit = request.form.get("unit", product.unit)
        product.category_id = request.form.get("category_id", type=int) or product.category_id
        product.location = (request.form.get("location") or product.location or "")[:140]

        new_image = save_image(request.files.get("image"))
        if new_image:
            product.image = new_image
        for extra in request.files.getlist("gallery"):
            fn = save_image(extra)
            if fn:
                db.session.add(ProductImage(product_id=product.id, filename=fn))

        # Any edit sends the product back through review.
        product.status = "pending"
        product.rejection_reason = None
        notify_admins(f"Edited product awaiting approval: {product.name}",
                      url_for("admin.products", status="pending"))
        db.session.commit()
        flash("Product updated and re-submitted for approval.", "success")
        return redirect(url_for("farmer.products"))

    return render_template("farmer/product_form.html", categories=categories,
                           product=product, form={})


@farmer_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@role_required("farmer")
def delete_product(product_id):
    product = _owned(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("farmer.products"))


@farmer_bp.route("/orders")
@role_required("farmer")
def orders():
    items = (OrderItem.query.filter_by(farmer_id=_me().id)
             .join(Order).order_by(Order.created_at.desc()).all())
    return render_template("farmer/orders.html", items=items)


@farmer_bp.route("/profile", methods=["GET", "POST"])
@role_required("farmer")
def profile():
    user = current_user()
    if request.method == "POST":
        user.full_name = (request.form.get("full_name") or user.full_name).strip()[:120]
        user.phone = (request.form.get("phone") or "").strip()[:30]
        user.farmer.farm_name = (request.form.get("farm_name") or "").strip()[:140]
        user.farmer.farm_location = (request.form.get("farm_location") or "").strip()[:140]
        user.farmer.bio = (request.form.get("bio") or "").strip()[:1000]
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("farmer.profile"))
    return render_template("farmer/profile.html", user=user)
