"""Public pages: home, browse, product detail, about, contact, FAQ."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Category, ContactMessage, Product, Review
from utils import current_user, valid_email

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    featured = (Product.query.filter_by(status="approved")
                .order_by(Product.created_at.desc()).limit(8).all())
    categories = Category.query.order_by(Category.name).all()
    return render_template("index.html", featured=featured, categories=categories)


@main_bp.route("/products")
def products():
    """Browse approved products with search, filters and pagination."""
    page = request.args.get("page", 1, type=int)
    q = (request.args.get("q") or "").strip()
    category_id = request.args.get("category", type=int)
    location = (request.args.get("location") or "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", "newest")

    # Only approved products are ever exposed to the public.
    query = Product.query.filter_by(status="approved")

    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.name.ilike(like),
                                    Product.description.ilike(like),
                                    Product.location.ilike(like)))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if location:
        query = query.filter(Product.location.ilike(f"%{location}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.order_by(Category.name).all()
    return render_template("products.html", pagination=pagination,
                           products=pagination.items, categories=categories,
                           filters=request.args)


@main_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, status="approved").first_or_404()
    related = (Product.query.filter_by(category_id=product.category_id, status="approved")
               .filter(Product.id != product.id).limit(4).all())
    return render_template("product_detail.html", product=product, related=related)


@main_bp.route("/products/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    """Customers can leave a rating + comment on an approved product."""
    user = current_user()
    if not user or user.role != "customer":
        flash("Only signed-in customers can review products.", "warning")
        return redirect(url_for("main.product_detail", product_id=product_id))

    Product.query.filter_by(id=product_id, status="approved").first_or_404()
    rating = request.form.get("rating", type=int)
    comment = (request.form.get("comment") or "").strip()[:1000]
    if not rating or not 1 <= rating <= 5:
        flash("Please choose a rating between 1 and 5.", "danger")
    else:
        db.session.add(Review(product_id=product_id, user_id=user.id,
                              rating=rating, comment=comment))
        db.session.commit()
        flash("Thank you for your review!", "success")
    return redirect(url_for("main.product_detail", product_id=product_id))


@main_bp.route("/api/search-suggestions")
def search_suggestions():
    """JSON endpoint used by the navbar search box for live suggestions."""
    term = (request.args.get("q") or "").strip()
    if len(term) < 2:
        return {"results": []}
    rows = (Product.query.filter_by(status="approved")
            .filter(Product.name.ilike(f"%{term}%")).limit(6).all())
    return {"results": [{"id": p.id, "name": p.name} for p in rows]}


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/faq")
def faq():
    return render_template("faq.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not message:
            flash("Name and message are required.", "danger")
        elif not valid_email(email):
            flash("Please enter a valid email address.", "danger")
        else:
            db.session.add(ContactMessage(name=name[:120], email=email[:160],
                                          subject=subject[:160], message=message[:2000]))
            db.session.commit()
            flash("Message sent. We will get back to you shortly.", "success")
            return redirect(url_for("main.contact"))
    return render_template("contact.html")
