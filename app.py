"""FarmConnect — application factory and entry point.

Run locally:
    1. Create the database:  mysql -u root -p < database/schema.sql
    2. Copy .env.example to .env and fill in your MySQL credentials
    3. pip install -r requirements.txt
    4. python app.py           ->  http://127.0.0.1:5000
"""
from datetime import datetime

from flask import Flask, render_template, session

from config import Config
from extensions import csrf, db
from models import CartItem, Category, Notification, User
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.farmer import farmer_bp
from routes.main import main_bp

DEFAULT_CATEGORIES = [
    "Vegetables", "Fruits", "Grains", "Tubers", "Livestock", "Poultry",
    "Fish", "Dairy", "Herbs", "Seeds", "Fertilisers", "Farm Equipment", "Others",
]


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    csrf.init_app(app)          # CSRF token required on every POST form

    # Blueprints (the "C" of MVC)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    # ---- Template globals available in every page ----------------------
    @app.context_processor
    def inject_globals():
        user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
        cart_count = 0
        unread = 0
        if user:
            unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
            if user.role == "customer":
                cart_count = CartItem.query.filter_by(user_id=user.id).count()
        return {
            "current_user": user,
            "cart_count": cart_count,
            "unread_count": unread,
            "nav_categories": Category.query.order_by(Category.name).all(),
            "now": datetime.utcnow(),
        }

    # ---- Error pages ----------------------------------------------------
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return render_template("500.html"), 500

    # ---- CLI helper: create tables, seed categories and a default admin -
    @app.cli.command("init-db")
    def init_db():
        """Usage:  flask --app app init-db"""
        seed(app)

    return app


def seed(app):
    """Create tables, insert the category list and a default admin account."""
    with app.app_context():
        db.create_all()
        for name in DEFAULT_CATEGORIES:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, slug=name.lower().replace(" ", "-")))
        if not User.query.filter_by(role="admin").first():
            admin = User(full_name="Site Administrator", email="admin@farmconnect.com",
                         role="admin")
            admin.set_password("Admin@12345")     # change this after first login
            db.session.add(admin)
            print("Default admin created -> admin@farmconnect.com / Admin@12345")
        db.session.commit()
        print("Database ready.")


app = create_app()

if __name__ == "__main__":
    seed(app)                       # safe to run repeatedly
    app.run(debug=True)
