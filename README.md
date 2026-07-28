# FarmConnect — Farmer-to-Customer Marketplace

A full-stack Flask + MySQL marketplace that connects farmers directly with
customers. Farmers upload products; **nothing is visible to customers until an
administrator approves it**.

Built with HTML5, CSS3, vanilla JavaScript, Python (Flask) and MySQL — no
frontend frameworks.

---

## 1. Requirements

* Python 3.10+
* MySQL 5.7+ / MariaDB 10.4+
* pip

## 2. Setup

```bash
# 1. unzip and enter the project
cd farmconnect

# 2. create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. create the database
mysql -u root -p < database/schema.sql

# 5. configure credentials
cp .env.example .env              # then edit .env with your MySQL details

# 6. run
python app.py
```

Open <http://127.0.0.1:5000>.

On first run the app creates any missing tables, seeds the 13 product
categories and creates a default administrator:

```
email:    admin@farmconnect.com
password: Admin@12345      <-- change this immediately after logging in
```

## 3. Project structure

```
farmconnect/
├── app.py                 # application factory, blueprints, error handlers, seeding
├── config.py              # environment-driven configuration
├── extensions.py          # db + csrf instances
├── models.py              # SQLAlchemy models (Model layer)
├── utils.py               # auth decorators, upload validation, notifications
├── requirements.txt
├── .env.example
├── database/
│   └── schema.sql         # full MySQL schema with keys, indexes, seed categories
├── routes/                # Controllers (Flask blueprints)
│   ├── main.py            # home, browse, product detail, about, FAQ, contact
│   ├── auth.py            # register, login, logout, change password
│   ├── farmer.py          # product CRUD, approval tracking, orders, profile
│   ├── customer.py        # cart, checkout, orders, wishlist, profile
│   └── admin.py           # stats, users, product review, orders, reports
├── templates/             # Views (Jinja2)
│   ├── base.html          # shared layout
│   ├── partials/          # navbar, footer, sidebar, product card
│   ├── farmer/ customer/ admin/
│   └── 403.html 404.html 500.html
└── static/
    ├── css/style.css      # complete design system, responsive + animations
    ├── js/main.js         # nav, validation, suggestions, accordion, reveal
    ├── js/charts.js       # admin dashboard charts (Chart.js)
    ├── images/            # hero background
    └── uploads/           # product images uploaded by farmers
```

## 4. Roles

| Role | Can do |
|------|--------|
| **Customer** | Register, browse approved products, search & filter, view details, cart (add / update / remove), checkout, order history & status, wishlist, reviews, profile, change password |
| **Farmer** | Register, upload products with images, edit, delete, track pending/approved/rejected status with rejection reasons, view orders for their products, profile |
| **Admin** | Dashboard with stat cards & charts, manage all users, suspend/delete accounts, review queue, approve/reject/delete products, manage orders and statuses, reports, contact messages |

## 5. Approval workflow

```
Farmer uploads product  ->  status = pending  ->  Admin reviews
                                                   |
                              approved -> visible to customers
                              rejected -> hidden + reason sent to farmer
```

Editing an approved product returns it to `pending` for re-review.

## 6. Checkout

Collects full name, phone, email, delivery address and payment method
(cash on delivery, Mobile Money simulated, card simulated). On success the app
creates the order, reduces stock, notifies each farmer involved and confirms to
the customer.

## 7. Security

* Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`)
* CSRF protection on every POST form (Flask-WTF `CSRFProtect`)
* SQL injection protection via SQLAlchemy parameterised queries
* Server-side validation on every form, plus client-side validation for UX
* File upload validation: extension allow-list, randomised filenames, 5 MB limit
* Role-based authorisation decorators (`@role_required('admin')`)
* Ownership checks so a farmer can only edit their own products
* Suspended accounts blocked at login and on every request
* HttpOnly, SameSite session cookies

## 8. Deployment notes

Set `SECRET_KEY` to a long random value, set `FLASK_DEBUG=0`, serve behind
Gunicorn + Nginx (`gunicorn "app:app"`), and enable HTTPS so
`SESSION_COOKIE_SECURE` can be turned on.
