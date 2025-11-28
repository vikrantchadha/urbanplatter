# 🍽️ Urban Platter - Restaurant Management System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

> **Experience authentic Indian cuisine crafted with love, served with passion.**
> From traditional recipes to modern presentations, every dish tells a story.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Database](#database)
- [Role-Based Access Control](#role-based-access-control)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

Urban Platter is a comprehensive **Restaurant Management System** built with Flask, SQLAlchemy, and Bootstrap. It provides a complete solution for managing a modern restaurant with authentication, menu management, online ordering, table reservations, and payment integration.

The system supports three user roles:
- **Admin** - Full control over system, analytics, and management
- **Staff** - Order processing and table management
- **Customer** - Browsing menu, placing orders, and making reservations

**Live Demo:** [urbanplatter.online](https://www.urbanplatter.online/)

## ✨ Features

### 🔐 Authentication & Security
- User registration and login with secure password hashing
- Role-based access control (RBAC) - Admin, Staff, Customer
- Session management with Flask-Login
- Secure password encryption using Werkzeug

### 🍲 Menu Management
- **60+ menu items** across 4 categories:
  - Starters (Paneer Tikka, Chicken 65, etc.)
  - Main Course (Butter Chicken, Biryani, etc.)
  - Desserts (Gulab Jamun, Ras Malai, etc.)
  - Drinks (Masala Chai, Fresh Lime Soda, etc.)
- Dynamic pricing in Indian Rupees (₹)
- Item availability toggle
- Image URLs for visual menu display

### 🛒 Order Management
- Shopping cart with add/remove functionality
- Order creation and real-time tracking
- Order status workflow: Pending → Preparing → Ready → Served → Completed
- Special instructions for customization
- Order history for customers
- Order queue management for staff

### 💳 Payment System
- payment methods:
  - **Cash on Delivery (COD)** - Default payment option
 
### 📅 Table Reservations
- Online table booking system
- Date and time selection
- Party size validation
- Reservation status management (Pending, Confirmed, Cancelled)
- Conflict detection to prevent double bookings
- Special requests support

### 📊 Admin Dashboard
- Real-time analytics and KPIs:
  - Total orders and revenue
  - Customer count
  - Pending orders queue
- Sales reports with CSV export
- Most ordered items tracking
- Recent orders monitoring
- Menu item management
- User and staff management

### 👤 Customer Dashboard
- Order history with status tracking
- Upcoming reservations
- Account management
- Order details and receipts

### 👨‍🍳 Staff Dashboard
- Order queue management
- Order status updates
- Reservation confirmations
- Real-time notifications

## 🛠 Tech Stack

### Backend
- **Framework:** Flask 3.0.0
- **Database ORM:** SQLAlchemy 3.1.1 via Flask-SQLAlchemy
- **Authentication:** Flask-Login 0.6.3
- **Security:** Werkzeug 3.0.1
- **Database:** SQLite (development) / PostgreSQL (production)
- **Payment:** Stripe 7.8.0
- **Server:** Gunicorn 21.2.0 (production)
- **Config Management:** python-dotenv 1.0.0

### Frontend
- **Template Engine:** Jinja2
- **CSS Framework:** Bootstrap 5
- **Styling:** Custom CSS
- **JavaScript:** Vanilla JS, AJAX for dynamic updates

### Deployment
- **Cloud Platform:** AWS Elastic Beanstalk
- **CI/CD:** AWS CodePipeline
- **Version Control:** GitHub
- **Database:** RDS (for production)

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (venv)

### Step 1: Clone the Repository
```bash
git clone https://github.com/vikrantchadha/urbanplatter.git
cd urbanplatter
```

### Step 2: Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### Create .env File
Create a `.env` file in the project root directory:

```env
# Secret key for session management
SECRET_KEY=your-secret-key-here

# Database URL
DATABASE_URL=sqlite:///urban_platter.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/urbanplatter

# Stripe API Key (for payment processing)
STRIPE_SECRET_KEY=sk_test_your_stripe_key

# Debug mode (Never True in production!)
DEBUG=False

# Flask environment
FLASK_ENV=production
```

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🚀 Running the Application

### Development Mode
```bash
# Method 1: Using Python directly
python urban_platter_app.py

# Method 2: Using Flask CLI
flask run

# Application will be available at http://localhost:5000
```

### Initialize Database
```bash
python -c "from urban_platter_app import app, db; app.app_context().push(); db.create_all()"
```

### Demo Credentials

**Admin User:**
- Email: `admin@urbanplatter.com`
- Password: `admin123`

**Staff User:**
- Email: `staff@urbanplatter.com`
- Password: `staff123`

**Create Customer Account:**
- Register via signup page with your email

## 🌐 Deployment

### AWS Elastic Beanstalk

1. **Install AWS CLI:**
```bash
pip install awsebcli
```

2. **Initialize EB Application:**
```bash
eb init -p python-3.10 urbanplatter --region ap-south-1
```

3. **Create Environment:**
```bash
eb create urbanplatter-env
```

4. **Set Environment Variables:**
```bash
eb setenv SECRET_KEY=your-secret-key
eb setenv DATABASE_URL=your-database-url
eb setenv STRIPE_SECRET_KEY=your-stripe-key
```

5. **Deploy:**
```bash
eb deploy
```

### Using Docker

```bash
# Build image
docker build -t urbanplatter .

# Run container
docker run -p 5000:5000 -e SECRET_KEY=your-key urbanplatter
```

## 📁 Project Structure

```
urbanplatter/
├── urban_platter_app.py          # Main Flask application
├── application.py                 # Elastic Beanstalk entry point
├── requirements.txt               # Python dependencies
├── Procfile                       # Deployment configuration
├── README.md                      # This file
├── templates/                     # HTML templates
│   ├── base.html                 # Base layout
│   ├── index.html                # Homepage
│   ├── menu.html                 # Menu display
│   ├── auth/                     # Authentication templates
│   │   ├── login.html
│   │   └── register.html
│   ├── customer/                 # Customer dashboard
│   ├── staff/                    # Staff dashboard
│   ├── admin/                    # Admin dashboard
│   ├── orders.html               # Order management
│   ├── reservations.html         # Reservation system
│   ├── payment.html              # Payment page
│   └── policy pages/             # Terms, Privacy, Shipping
├── static/                       # Static files
│   ├── css/                      # Bootstrap & custom styles
│   ├── js/                       # JavaScript files
│   ├── images/                   # Logo and menu items
│   └── uploads/                  # User-uploaded files
└── instance/                     # Instance-specific files
```

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | User registration |
| POST | `/login` | User login |
| GET | `/logout` | User logout |

### Menu
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/menu` | View full menu |
| GET | `/api/menu_items` | Get menu items (JSON) |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/order` | Place new order |
| GET | `/orders` | View orders |
| GET | `/order-confirmation/<id>` | Order confirmation page |
| POST | `/orders/<id>/status` | Update order status (Staff/Admin) |

### Reservations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reservations` | Reservation form |
| POST | `/reservations` | Make reservation |
| POST | `/reservations/<id>/status` | Update reservation status (Staff/Admin) |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/dashboard` | Admin analytics |
| GET | `/staff/dashboard` | Staff orders queue |
| GET | `/customer/dashboard` | Customer order history |

## 💾 Database

### Database Models

**User Table:**
```python
id, username, email, password_hash, role, created_at
```

**MenuItem Table:**
```python
id, name, description, price, category, image_url, available, created_at
```

**Order Table:**
```python
id, customer_id, total_amount, status, order_date, payment_status, 
special_instructions, delivery_address, contact_number
```

**OrderItem Table:**
```python
id, order_id, menu_item_id, quantity, price
```

**Reservation Table:**
```python
id, customer_id, date, time, party_size, status, special_requests, created_at
```

**Payment Table:**
```python
id, order_id, amount, payment_method, payment_date, stripe_payment_id, status
```

## 👥 Role-Based Access Control

### Admin Role
- Access to admin dashboard
- View analytics and reports
- Manage menu items (add, edit, delete)
- Manage users and staff
- Generate sales reports
- View all orders and reservations

### Staff Role
- Access to staff dashboard
- View order queue
- Update order status
- Manage table reservations
- Cannot access admin features

### Customer Role
- Browse menu
- Place orders
- Make reservations
- View order history
- Access only own orders and reservations

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact & Support

**Project Author:** Vikrant Chadha

**Repository:** [github.com/vikrantchadha/urbanplatter](https://github.com/vikrantchadha/urbanplatter)

**Website:** [urbanplatter.online](https://www.urbanplatter.online/)

**Issues & Feature Requests:** [GitHub Issues](https://github.com/vikrantchadha/urbanplatter/issues)

---

<div align="center">

**Made with ❤️ for food lovers**

© 2025 Urban Platter. All rights reserved.

</div>
