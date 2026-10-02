#  FarmConnect

A web-based farmer-to-customer marketplace that connects farmers directly with customers, allowing agricultural products to be listed, discovered, and purchased through an online platform.

FarmConnect was developed as a full-stack web application with a focus on backend development, database management, authentication, product management, and cloud deployment.

##  Project Overview

FarmConnect aims to provide a digital marketplace where farmers can showcase their agricultural products while customers can browse available products and place orders.

The platform includes an administrative approval workflow to help manage users, products, and marketplace activity.

### Problem

Farmers may have difficulty reaching customers directly and efficiently promoting their products.

FarmConnect addresses this by providing an online platform where:

- Farmers can list agricultural products.
- Customers can browse available products.
- Customers can place orders.
- Administrators can manage marketplace activity.
- Products can be reviewed and approved before becoming publicly available.

##  Key Features

###  Farmer Features

- Farmer registration and authentication
- Farmer profile management
- Product creation and management
- Product categorization
- Product information management
- Order management

###  Customer Features

- Customer registration and authentication
- Browse agricultural products
- View product details
- Browse products by category
- Place orders
- View order information

###  Administration

- Administrative authentication
- User management
- Product approval workflow
- Category management
- Marketplace monitoring
- Notification management

##  System Architecture

FarmConnect follows a traditional full-stack web application architecture.

```text
                    ┌─────────────────────┐
                    │       User          │
                    │ Farmer / Customer   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Web Interface    │
                    │   HTML / CSS / JS   │
                    │      Jinja2         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Flask App      │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐
          │     MySQL       │   │   AWS Services  │
          │    Database     │   │ RDS / Elastic   │
          │                 │   │   Beanstalk     │
          └─────────────────┘   └─────────────────┘
 Technology Stack
Backend
Python
Flask
Jinja2
Frontend
HTML5
CSS3
JavaScript
Database
MySQL
AWS RDS
Cloud / Deployment
AWS Elastic Beanstalk
AWS RDS
Development Tools
Git
GitHub
Visual Studio Code
 Database Models

The application uses a relational database to manage users, products, orders, and other marketplace data.

Key models include:

User
Farmer
Customer
Category
Product
Order
OrderItem
Notification
Basic Relationship Structure
User
 ├── Farmer
 │     └── Product
 │            └── Category
 │
 └── Customer
        └── Order
              └── OrderItem
                    └── Product
 Authentication & Security

The application includes authentication and access-control mechanisms for different types of users.

The system distinguishes between different roles, including:

Farmers
Customers
Administrators

Sensitive configuration values such as database credentials and secret keys are stored using environment variables rather than being committed directly to the repository.

Environment Variables

Sensitive configuration should be stored in a local .env file.

A template is provided through:

.env.example

Never commit the actual .env file to GitHub.

📂 Project Structure

A simplified version of the project structure is:

FarmConnect/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── admin/
│   ├── farmer/
│   ├── customer/
│   └── ...
│
├── models/
│
├── routes/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

The exact structure may vary depending on the current version of the project.

 Getting Started
Prerequisites

Before running FarmConnect locally, make sure you have:

Python 3
pip
MySQL
Git
1. Clone the Repository
git clone https://github.com/AddoRichmond-rgb/FarmConnect.git
2. Navigate to the Project
cd FarmConnect
3. Create a Virtual Environment

Windows:

python -m venv venv

Activate it:

venv\Scripts\activate

Linux/macOS:

python3 -m venv venv
source venv/bin/activate
4. Install Dependencies
pip install -r requirements.txt
5. Configure Environment Variables

Create a .env file based on the provided example:

cp .env.example .env

On Windows, you can also create the file manually.

Add your own:

Database credentials
Flask secret key
AWS configuration where required
6. Configure the Database

Create a MySQL database and configure the corresponding connection details in your .env file.

Example:

MYSQL_HOST=your_host
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=your_database

Do not use these example values in a production environment.

7. Run the Application
python app.py

The application should then be available locally through the address shown by Flask.

 Cloud Deployment

FarmConnect was also developed with cloud deployment in mind.

The project has been deployed using:

AWS Elastic Beanstalk for application hosting
AWS RDS for the MySQL database

The database was configured using an AWS RDS instance, while the Flask application was deployed through Elastic Beanstalk.
 Testing

Testing during development included:

User registration and authentication
Farmer product creation
Product browsing
Product approval
Category management
Order creation
Database operations
Application deployment
Role-based functionality
 Challenges & Lessons Learned

During development, I gained practical experience with:

Building a Flask-based web application
Designing relational database structures
Connecting Flask applications to MySQL
Implementing authentication and user roles
Managing CRUD operations
Working with Jinja2 templates
Deploying applications to AWS
Connecting an application to AWS RDS
Managing environment variables
Using Git and GitHub for version control
Debugging application and database issues
 Future Improvements

Potential future improvements include:

Real-time farmer/customer messaging
Google authentication
Online payment integration
Improved product search and filtering
Product reviews and ratings
Improved notification system
Mobile application
Advanced administrator analytics
Improved security monitoring
Automated testing
CI/CD deployment pipeline
 Security Notice

This repository is intended for educational and portfolio purposes.

Sensitive information such as:

Passwords
API keys
AWS credentials
Database credentials
Secret keys

should never be committed to the repository.

Use environment variables and keep the .env file private.

 Author

Richmond Addo

BSc Cybersecurity Student
University of Mines and Technology (UMaT), Ghana

Areas of Interest
Cybersecurity
Web Application Security
Network Security
Cloud Security
Python
Ethical Hacking
Security Automation

If you find this project useful, feel free to explore the repository and review the implementation.
