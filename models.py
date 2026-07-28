"""SQLAlchemy models — the "M" of the MVC-like structure.

Relationships:
    users 1--1 farmers / customers / admins   (role profile tables)
    farmers 1--* products *--1 categories
    products 1--* product_images
    users(customer) 1--* cart, orders, reviews, wishlist
    orders 1--* order_items *--1 products
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    """Base account row. `role` drives all authorisation checks."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("customer", "farmer", "admin"), nullable=False, index=True)
    status = db.Column(db.Enum("active", "suspended"), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship("Farmer", backref="user", uselist=False, cascade="all, delete-orphan")
    customer = db.relationship("Customer", backref="user", uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")

    # --- password helpers (Werkzeug PBKDF2 hashing) ---------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Farmer(db.Model):
    """Extra profile fields that only farmers have."""
    __tablename__ = "farmers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        unique=True, nullable=False)
    farm_name = db.Column(db.String(140))
    farm_location = db.Column(db.String(140), index=True)
    bio = db.Column(db.Text)

    products = db.relationship("Product", backref="farmer", cascade="all, delete-orphan")


class Customer(db.Model):
    """Extra profile fields that only customers have."""
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        unique=True, nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(90))


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    products = db.relationship("Product", backref="category")


class Product(db.Model):
    """A farm product. Never visible to customers until status == 'approved'."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmers.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.Enum("kg", "bag", "crate", "litre", "piece"), nullable=False, default="kg")
    image = db.Column(db.String(255))                    # primary image filename
    location = db.Column(db.String(140), index=True)
    status = db.Column(db.Enum("pending", "approved", "rejected"),
                       nullable=False, default="pending", index=True)
    rejection_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    images = db.relationship("ProductImage", backref="product", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="product", cascade="all, delete-orphan")

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)


class ProductImage(db.Model):
    """Additional gallery images for a product."""
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)


class CartItem(db.Model):
    __tablename__ = "cart"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"),
                           nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product")

    @property
    def subtotal(self):
        return float(self.product.price) * self.quantity


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.Enum("cash", "momo", "card"), nullable=False, default="cash")
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum("pending", "confirmed", "shipped", "delivered", "cancelled"),
                       nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    customer = db.relationship("User")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmers.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)   # price snapshot at purchase time

    product = db.relationship("Product")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")


class Wishlist(db.Model):
    __tablename__ = "wishlist"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_wish_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"),
                           nullable=False)
    product = db.relationship("Product")


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    subject = db.Column(db.String(160))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
