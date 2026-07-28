"""Customer area: cart, checkout, orders, wishlist, profile."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import CartItem, Notification, Order, OrderItem, Product, Wishlist
from utils import current_user, notify, role_required, valid_email

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


def _cart_items(user_id):
    return CartItem.query.filter_by(user_id=user_id).all()


@customer_bp.route("/dashboard")
@role_required("customer")
def dashboard():
    user = current_user()
    orders = (Order.query.filter_by(user_id=user.id)
              .order_by(Order.created_at.desc()).limit(5).all())
    stats = {
        "orders": Order.query.filter_by(user_id=user.id).count(),
        "cart": CartItem.query.filter_by(user_id=user.id).count(),
        "wishlist": Wishlist.query.filter_by(user_id=user.id).count(),
        "spent": sum(float(o.total) for o in Order.query.filter_by(user_id=user.id).all()),
    }
    notifications = (Notification.query.filter_by(user_id=user.id)
                     .order_by(Notification.created_at.desc()).limit(6).all())
    return render_template("customer/dashboard.html", orders=orders, stats=stats,
                           notifications=notifications)


@customer_bp.route("/cart")
@role_required("customer")
def cart():
    items = _cart_items(current_user().id)
    total = sum(i.subtotal for i in items)
    return render_template("customer/cart.html", items=items, total=total)


@customer_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@role_required("customer")
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id, status="approved").first_or_404()
    qty = max(1, request.form.get("quantity", 1, type=int))
    user_id = current_user().id

    item = CartItem.query.filter_by(user_id=user_id, product_id=product.id).first()
    if item:
        item.quantity = min(item.quantity + qty, product.quantity or qty)
    else:
        db.session.add(CartItem(user_id=user_id, product_id=product.id, quantity=qty))
    db.session.commit()
    flash(f"{product.name} added to your cart.", "success")
    return redirect(request.referrer or url_for("customer.cart"))


@customer_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@role_required("customer")
def update_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user().id).first_or_404()
    qty = request.form.get("quantity", type=int)
    if qty is None or qty < 1:
        db.session.delete(item)
    else:
        item.quantity = min(qty, item.product.quantity or qty)
    db.session.commit()
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@role_required("customer")
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user().id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/checkout", methods=["GET", "POST"])
@role_required("customer")
def checkout():
    user = current_user()
    items = _cart_items(user.id)
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.products"))
    total = sum(i.subtotal for i in items)

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip()
        address = (request.form.get("address") or "").strip()
        payment = request.form.get("payment_method", "cash")

        errors = []
        if len(full_name) < 3:
            errors.append("Enter your full name.")
        if len(phone) < 7:
            errors.append("Enter a valid phone number.")
        if not valid_email(email):
            errors.append("Enter a valid email address.")
        if len(address) < 6:
            errors.append("Enter a delivery address.")
        if payment not in ("cash", "momo", "card"):
            errors.append("Choose a payment method.")
        for i in items:
            if i.quantity > i.product.quantity:
                errors.append(f"Only {i.product.quantity} {i.product.unit} of "
                              f"{i.product.name} left in stock.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customer/checkout.html", items=items,
                                   total=total, user=user, form=request.form)

        order = Order(user_id=user.id, full_name=full_name[:120], phone=phone[:30],
                      email=email[:160], address=address[:255],
                      payment_method=payment, total=total, status="confirmed")
        db.session.add(order)
        db.session.flush()

        for i in items:
            db.session.add(OrderItem(order_id=order.id, product_id=i.product_id,
                                     farmer_id=i.product.farmer_id,
                                     quantity=i.quantity, price=i.product.price))
            i.product.quantity -= i.quantity            # reduce available stock
            # notify the farmer who owns this product
            notify(i.product.farmer.user_id,
                   f"New order #{order.id}: {i.quantity} x {i.product.name}",
                   url_for("farmer.orders"))
            db.session.delete(i)

        notify(user.id, f"Order #{order.id} confirmed. Total GHS {total:.2f}",
               url_for("customer.orders"))
        db.session.commit()
        flash(f"Order #{order.id} placed successfully!", "success")
        return redirect(url_for("customer.orders"))

    return render_template("customer/checkout.html", items=items, total=total,
                           user=user, form={})


@customer_bp.route("/orders")
@role_required("customer")
def orders():
    rows = (Order.query.filter_by(user_id=current_user().id)
            .order_by(Order.created_at.desc()).all())
    return render_template("customer/orders.html", orders=rows)


@customer_bp.route("/wishlist")
@role_required("customer")
def wishlist():
    rows = Wishlist.query.filter_by(user_id=current_user().id).all()
    return render_template("customer/wishlist.html", rows=rows)


@customer_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@role_required("customer")
def toggle_wishlist(product_id):
    user_id = current_user().id
    row = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
    if row:
        db.session.delete(row)
        flash("Removed from favourites.", "success")
    else:
        Product.query.filter_by(id=product_id, status="approved").first_or_404()
        db.session.add(Wishlist(user_id=user_id, product_id=product_id))
        flash("Added to favourites.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("customer.wishlist"))


@customer_bp.route("/profile", methods=["GET", "POST"])
@role_required("customer")
def profile():
    user = current_user()
    if request.method == "POST":
        user.full_name = (request.form.get("full_name") or user.full_name).strip()[:120]
        user.phone = (request.form.get("phone") or "").strip()[:30]
        if user.customer:
            user.customer.address = (request.form.get("address") or "").strip()[:255]
            user.customer.city = (request.form.get("city") or "").strip()[:90]
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("customer.profile"))
    return render_template("customer/profile.html", user=user)
