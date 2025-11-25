#!/usr/bin/env python3
"""
Urban Platter - Restaurant Management System
===========================================

A comprehensive restaurant management system built with Flask, SQLAlchemy, and Bootstrap.
Supports user authentication, menu management, order processing, table reservations, 
and payment integration.

Restaurant: Urban Platter
Author: AI Assistant
Date: September 2025
Tech Stack: Python Flask, SQLAlchemy, SQLite, Bootstrap 5
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import stripe
import csv
import io
import base64
from functools import wraps
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'urban-platter-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////tmp/urban_platter.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create static folder if it doesn't exist
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Stripe configuration (use environment variables)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")

# Valid categories for menu items
VALID_CATEGORIES = {'Starters', 'Main Course', 'Desserts', 'Drinks'}

# Restaurant configuration
RESTAURANT_NAME = "Urban Platter"
CURRENCY_SYMBOL = "₹"

# Database Models
class User(UserMixin, db.Model):
    """User model for authentication and role management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='Customer')  # Admin, Staff, Customer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    reservations = db.relationship('Reservation', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='customer', lazy=True)

class MenuItem(db.Model):
    """Menu items with categories and pricing"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Starters, Main Course, Desserts, Drinks
    image_url = db.Column(db.String(200))
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)
    reviews = db.relationship('Review', backref='menu_item', lazy=True)

class Order(db.Model):
    """Customer orders with status tracking"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Preparing, Ready, Served, Completed
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Failed
    special_instructions = db.Column(db.Text)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False)

class OrderItem(db.Model):
    """Individual items within an order"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order

class Reservation(db.Model):
    """Table reservations with validation"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Cancelled
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    """Payment records with Stripe integration"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # Cash, Card, Online
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    stripe_payment_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Completed')

class Review(db.Model):
    """Customer reviews for menu items"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# Helper functions
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def role_required(role):
    """Decorator to require specific roles for routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_or_staff_required(func):
    """Decorator for routes that require admin or staff access"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['Admin', 'Staff']:
            flash('Access denied. Admin or Staff privileges required.', 'error')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

def validate_category(category):
    """Validate menu item category"""
    return category in VALID_CATEGORIES

def format_currency(amount):
    """Format amount with Indian Rupee symbol"""
    return f"{CURRENCY_SYMBOL}{amount:.2f}"

# Template context processor to make variables available in all templates
@app.context_processor
def inject_globals():
    return {
        'RESTAURANT_NAME': RESTAURANT_NAME,
        'CURRENCY_SYMBOL': CURRENCY_SYMBOL,
        'format_currency': format_currency
    }

# Routes - Authentication
@app.route('/')
def index():
    """Homepage with featured menu items"""
    featured_items = MenuItem.query.filter_by(available=True).limit(6).all()
    return render_template('index.html', featured_items=featured_items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome to {RESTAURANT_NAME}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'Customer')
        
        # Validate role
        if role not in ['Admin', 'Staff', 'Customer']:
            role = 'Customer'
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Registration successful! Welcome to {RESTAURANT_NAME}. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash(f'Thank you for visiting {RESTAURANT_NAME}. You have been logged out.', 'info')
    return redirect(url_for('index'))

# Routes - Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """Role-based dashboard"""
    if current_user.role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'Staff':
        return redirect(url_for('staff_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))

@app.route('/admin/dashboard')
@role_required('Admin')
def admin_dashboard():
    """Admin dashboard with analytics"""
    # Get analytics data
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    total_customers = User.query.filter_by(role='Customer').count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    # Most ordered items
    most_ordered = db.session.query(
        MenuItem.name,
        db.func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem).group_by(MenuItem.id).order_by(
        db.func.sum(OrderItem.quantity).desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         total_customers=total_customers,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         most_ordered=most_ordered)

@app.route('/staff/dashboard')
@role_required('Staff')
def staff_dashboard():
    """Staff dashboard for order management"""
    pending_orders = Order.query.filter_by(status='Pending').all()
    preparing_orders = Order.query.filter_by(status='Preparing').all()
    ready_orders = Order.query.filter_by(status='Ready').all()
    
    return render_template('staff/dashboard.html',
                         pending_orders=pending_orders,
                         preparing_orders=preparing_orders,
                         ready_orders=ready_orders)

@app.route('/customer/dashboard')
@role_required('Customer')
def customer_dashboard():
    """Customer dashboard with order history"""
    recent_orders = Order.query.filter_by(customer_id=current_user.id).order_by(
        Order.order_date.desc()
    ).limit(5).all()
    
    upcoming_reservations = Reservation.query.filter_by(
        customer_id=current_user.id
    ).filter(Reservation.date >= datetime.now().date()).all()
    
    return render_template('customer/dashboard.html',
                         recent_orders=recent_orders,
                         upcoming_reservations=upcoming_reservations)

# Routes - Menu Management
@app.route('/menu')
def menu():
    """Public menu display"""
    category = request.args.get('category', 'all')
    
    if category == 'all':
        menu_items = MenuItem.query.filter_by(available=True).all()
    else:
        menu_items = MenuItem.query.filter_by(category=category, available=True).all()
    
    categories = list(VALID_CATEGORIES)
    
    return render_template('menu.html', menu_items=menu_items, categories=categories, current_category=category)

@app.route('/admin/menu')
@admin_or_staff_required
def admin_menu():
    """Admin menu management"""
    menu_items = MenuItem.query.all()
    return render_template('admin/menu.html', menu_items=menu_items)

@app.route('/admin/menu/add', methods=['GET', 'POST'])
@admin_or_staff_required
def add_menu_item():
    """Add new menu item"""
    if request.method == 'POST':
        category = request.form.get('category')
        
        # Validate category
        if not validate_category(category):
            flash('Invalid category selected.', 'error')
            return redirect(url_for('admin_menu'))
        
        # Handle checkbox properly
        available = request.form.get('available') in ['on', 'true', '1']
        
        try:
            price = float(request.form.get('price', 0))
            if price < 0:
                flash('Price cannot be negative.', 'error')
                return redirect(url_for('add_menu_item'))
        except ValueError:
            flash('Invalid price format.', 'error')
            return redirect(url_for('add_menu_item'))
        
        item = MenuItem(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=price,
            category=category,
            image_url=request.form.get('image_url', ''),
            available=available
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Menu item added successfully!', 'success')
        return redirect(url_for('admin_menu'))
    
    categories = list(VALID_CATEGORIES)
    return render_template('admin/add_menu_item.html', categories=categories)

@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_or_staff_required
def edit_menu_item(item_id):
    """Edit menu item"""
    item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        category = request.form.get('category')
        
        # Validate category
        if not validate_category(category):
            flash('Invalid category selected.', 'error')
            return redirect(url_for('admin_menu'))
        
        try:
            price = float(request.form.get('price', 0))
            if price < 0:
                flash('Price cannot be negative.', 'error')
                return redirect(url_for('edit_menu_item', item_id=item_id))
        except ValueError:
            flash('Invalid price format.', 'error')
            return redirect(url_for('edit_menu_item', item_id=item_id))
        
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.price = price
        item.category = category
        item.image_url = request.form.get('image_url', '')
        item.available = request.form.get('available') in ['on', 'true', '1']
        
        db.session.commit()
        
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('admin_menu'))
    
    categories = list(VALID_CATEGORIES)
    return render_template('admin/edit_menu_item.html', item=item, categories=categories)

@app.route('/admin/menu/delete/<int:item_id>')
@admin_or_staff_required
def delete_menu_item(item_id):
    """Delete menu item"""
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    flash('Menu item deleted successfully!', 'success')
    return redirect(url_for('admin_menu'))

# Routes - Order Management
@app.route('/order', methods=['POST'])
@login_required
def place_order():
    """Place a new order"""
    cart_items = request.json.get('cart_items', [])
    special_instructions = request.json.get('special_instructions', '')
    
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total
    total_amount = 0
    order = Order(
        customer_id=current_user.id,
        total_amount=0,  # Will be updated
        special_instructions=special_instructions
    )
    
    db.session.add(order)
    db.session.flush()  # Get the order ID
    
    # Add order items
    for item in cart_items:
        menu_item = MenuItem.query.get(item['menu_item_id'])
        if menu_item and menu_item.available:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=item['quantity'],
                price=menu_item.price
            )
            total_amount += menu_item.price * item['quantity']
            db.session.add(order_item)
    
    order.total_amount = total_amount
    db.session.commit()
    
    return jsonify({'order_id': order.id, 'total_amount': total_amount})

@app.route('/orders')
@login_required
def view_orders():
    """View orders (role-based)"""
    if current_user.role in ['Admin', 'Staff']:
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.filter_by(customer_id=current_user.id).order_by(
            Order.order_date.desc()
        ).all()
    
    return render_template('orders.html', orders=orders)

@app.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_or_staff_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.json.get('status')
    
    valid_statuses = ['Pending', 'Preparing', 'Ready', 'Served', 'Completed']
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid status'}), 400

# Routes - Reservations
@app.route('/reservations')
def reservations():
    """Reservation form"""
    return render_template('reservations.html')

@app.route('/reservations', methods=['POST'])
@login_required
def make_reservation():
    """Make a table reservation"""
    date_str = request.form.get('date')
    time_str = request.form.get('time')
    party_size = int(request.form.get('party_size'))
    special_requests = request.form.get('special_requests', '')
    
    reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    reservation_time = datetime.strptime(time_str, '%H:%M').time()
    
    # Check for conflicts (simple validation)
    existing = Reservation.query.filter_by(
        date=reservation_date,
        time=reservation_time
    ).filter(Reservation.status != 'Cancelled').first()
    
    if existing:
        flash('Time slot not available. Please choose another time.', 'error')
        return redirect(url_for('reservations'))
    
    reservation = Reservation(
        customer_id=current_user.id,
        date=reservation_date,
        time=reservation_time,
        party_size=party_size,
        special_requests=special_requests
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    flash(f'Reservation at {RESTAURANT_NAME} requested successfully! We will confirm shortly.', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/admin/reservations')
@admin_or_staff_required
def admin_reservations():
    """Admin reservation management"""
    reservations = Reservation.query.order_by(Reservation.date.desc()).all()
    return render_template('admin/reservations.html', reservations=reservations)

@app.route('/reservations/<int:reservation_id>/status', methods=['POST'])
@admin_or_staff_required
def update_reservation_status(reservation_id):
    """Update reservation status"""
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.json.get('status')
    
    valid_statuses = ['Pending', 'Confirmed', 'Cancelled']
    if new_status in valid_statuses:
        reservation.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid status'}), 400

# Routes - Payments
@app.route('/payment/<int:order_id>')
@login_required
def payment_page(order_id):
    """Payment processing page"""
    order = Order.query.get_or_404(order_id)
    
    # Check if user owns this order
    if current_user.role == 'Customer' and order.customer_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('payment.html', order=order)

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment (Stripe integration)"""
    order_id = request.json.get('order_id')
    payment_method = request.json.get('payment_method')
    stripe_token = request.json.get('stripe_token')
    
    order = Order.query.get_or_404(order_id)
    
    try:
        if payment_method == 'Online' and stripe_token and stripe.api_key != "sk_test_placeholder":
            # Process Stripe payment
            charge = stripe.Charge.create(
                amount=int(order.total_amount * 100),  # Amount in paisa (INR cents)
                currency='inr',  # Indian Rupees
                source=stripe_token,
                description=f'{RESTAURANT_NAME} Order #{order.id}'
            )
            
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                payment_method='Online',
                stripe_payment_id=charge.id
            )
        else:
            # Cash or card payment
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                payment_method=payment_method
            )
        
        order.payment_status = 'Paid'
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({'success': True, 'payment_id': payment.id})
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Payment processing failed'}), 400

# Routes - Reports
@app.route('/admin/reports')
@role_required('Admin')
def reports():
    """Admin reports page"""
    return render_template('admin/reports.html')

@app.route('/admin/reports/sales')
@role_required('Admin')
def sales_report():
    """Generate sales report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'json')
    
    query = Order.query.filter(Order.payment_status == 'Paid')
    
    if start_date:
        query = query.filter(Order.order_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Order.order_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    orders = query.all()
    
    if format_type == 'csv':
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Order ID', 'Customer', 'Date', f'Amount ({CURRENCY_SYMBOL})', 'Status'])
        
        for order in orders:
            writer.writerow([
                order.id,
                order.customer.username,
                order.order_date.strftime('%Y-%m-%d %H:%M'),
                f'{CURRENCY_SYMBOL}{order.total_amount:.2f}',
                order.status
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={RESTAURANT_NAME.lower().replace(" ", "_")}_sales_report.csv'}
        )
    
    # JSON response
    report_data = []
    for order in orders:
        report_data.append({
            'id': order.id,
            'customer': order.customer.username,
            'date': order.order_date.isoformat(),
            'amount': order.total_amount,
            'status': order.status
        })
    
    return jsonify(report_data)

# API Routes for AJAX
@app.route('/api/menu_items')
def api_menu_items():
    """API endpoint for menu items"""
    category = request.args.get('category')
    
    query = MenuItem.query.filter_by(available=True)
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    items = query.all()
    
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'price': item.price,
        'category': item.category,
        'image_url': item.image_url
    } for item in items])

@app.route('/api/orders/<int:order_id>')
@login_required
def api_order_status(order_id):
    """API endpoint for order status"""
    order = Order.query.get_or_404(order_id)
    
    # Check permissions
    if current_user.role == 'Customer' and order.customer_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'total_amount': order.total_amount,
        'order_date': order.order_date.isoformat(),
        'items': [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.order_items]
    })

# Initialize database
def init_db():
    """Initialize database with Urban Platter menu data"""
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@urbanplatter.com').first():
        admin = User(
            username='admin',
            email='admin@urbanplatter.com',
            password_hash=generate_password_hash('admin123'),
            role='Admin'
        )
        db.session.add(admin)
    
    # Create staff user if not exists
    if not User.query.filter_by(email='staff@urbanplatter.com').first():
        staff = User(
            username='staff',
            email='staff@urbanplatter.com',
            password_hash=generate_password_hash('staff123'),
            role='Staff'
        )
        db.session.add(staff)
    
    # Clear existing menu items to avoid duplicates
#     MenuItem.query.delete()
    
    # Urban Platter menu with 60 items - All prices in Indian Rupees (₹)
    urban_platter_menu = [
# #     {'category': 'Starters',
 'description': 'Marinated paneer cubes grilled to perfection with aromatic '
                'spices',
 'image_url': '/static/images/menu/starters/paneer-tikka.jpg',
 'name': 'Paneer Tikka',
 'price': 195},
    {'category': 'Starters',
 'description': 'Crispy rolls filled with fresh seasonal vegetables and herbs',
 'image_url': '/static/images/menu/starters/spring-roll.jpg',
 'name': 'Vegetable Spring Rolls',
 'price': 150},
    {'category': 'Starters',
 'description': 'Spicy, deep-fried chicken bites with curry leaves and chilies',
 'image_url': '/static/images/menu/starters/chicken-65.webp',
 'name': 'Chicken 65',
 'price': 210},
    {'category': 'Starters',
 'description': 'Spiced potato patties, shallow-fried and served with chutneys',
 'image_url': '/static/images/menu/starters/aloo-tikki.jpg',
 'name': 'Aloo Tikki',
 'price': 120},
    {'category': 'Starters',
 'description': 'Nutritious spinach and green pea patties with mint flavor',
 'image_url': '/static/images/menu/starters/hara-bhara-kabab.webp',
 'name': 'Hara Bhara Kabab',
 'price': 175},
    {'category': 'Starters',
 'description': 'Batter-fried fish with authentic Punjabi spices and herbs',
 'image_url': '/static/images/menu/starters/Amritsari-fish-fry.webp',
 'name': 'Fish Amritsari',
 'price': 230},
    {'category': 'Starters',
 'description': 'Paneer slices dipped in spiced gram flour batter and fried',
 'image_url': '/static/images/menu/starters/Paneer-Pakora.jpg',
 'name': 'Paneer Pakora',
 'price': 180},
    {'category': 'Starters',
 'description': 'Roasted peanuts tossed with spices, onions, and tomatoes',
 'image_url': '/static/images/menu/starters/Masala Peanuts.webp',
 'name': 'Masala Peanuts',
 'price': 100},
    {'category': 'Starters',
 'description': 'Chicken marinated in yogurt and spices, cooked in clay oven',
 'image_url': '/static/images/menu/starters/Tandoori-Chicken-Recipe.webp',
 'name': 'Tandoori Chicken',
 'price': 250},
    {'category': 'Starters',
 'description': 'Fried mixed vegetable balls in spicy Indo-Chinese sauce',
 'image_url': '/static/images/menu/starters/Veg Manchurian.jpg',
 'name': 'Veg Manchurian',
 'price': 160},
    {'category': 'Starters',
 'description': 'Crispy fried balls stuffed with melted cheese and herbs',
 'image_url': '/static/images/menu/starters/Cheese Balls.webp',
 'name': 'Cheese Balls',
 'price': 190},
    {'category': 'Starters',
 'description': 'Golden pastry triangles filled with spiced minced chicken',
 'image_url': '/static/images/menu/starters/ChickenSamosa.webp',
 'name': 'Chicken Samosa',
 'price': 140},
    {'category': 'Starters',
 'description': 'Crisp wafers topped with potatoes, yogurt, and tangy chutneys',
 'image_url': '/static/images/menu/starters/papdi-chaat.jpg',
 'name': 'Papdi Chaat',
 'price': 130},
    {'category': 'Starters',
 'description': 'Mixed vegetable patties, breaded and shallow fried until '
                'golden',
 'image_url': '/static/images/menu/starters/Veg Cutlets.jfif',
 'name': 'Veg Cutlets',
 'price': 150},
    {'category': 'Starters',
 'description': 'Minced mutton skewers with spices, grilled in tandoor',
 'image_url': '/static/images/menu/starters/Mutton-Seekh-Kebab.jpg',
 'name': 'Mutton Seekh Kabab',
 'price': 280},
    {'category': 'Main Course',
 'description': 'Classic chicken curry in rich, creamy tomato-based sauce',
 'image_url': '/static/images/menu/main-course/butter chicken.png',
 'name': 'Butter Chicken',
 'price': 320},
    {'category': 'Main Course',
 'description': 'Cottage cheese in velvety tomato and cashew nut gravy',
 'image_url': '/static/images/menu/main-course/Paneer-butter-masala.jpeg',
 'name': 'Paneer Butter Masala',
 'price': 280},
    {'category': 'Main Course',
 'description': 'Slow-cooked black lentils and kidney beans in creamy sauce',
 'image_url': '/static/images/menu/main-course/dal-makhani-feature.jpg',
 'name': 'Dal Makhani',
 'price': 240},
    {'category': 'Main Course',
 'description': 'Aromatic basmati rice layered with spiced chicken and saffron',
 'image_url': '/static/images/menu/main-course/hyderabadi-biryani-recipe-chicken.webp',
 'name': 'Hyderabadi Biryani',
 'price': 350},
    {'category': 'Main Course',
 'description': 'Spicy chickpeas curry served with fluffy deep-fried bread',
 'image_url': '/static/images/menu/main-course/Chole Bhature.jfif',
 'name': 'Chole Bhature',
 'price': 220},
    {'category': 'Main Course',
 'description': 'Fresh fish cooked in tangy coconut milk and traditional '
                'spices',
 'image_url': '/static/images/menu/main-course/Fish Curry.webp',
 'name': 'Fish Curry',
 'price': 300},
    {'category': 'Main Course',
 'description': 'Cottage cheese cubes in creamy, nutritious spinach gravy',
 'image_url': '/static/images/menu/main-course/Palak-Paneer.jpg',
 'name': 'Palak Paneer',
 'price': 260},
    {'category': 'Main Course',
 'description': 'Tender lamb curry with aromatic Kashmiri spices and herbs',
 'image_url': '/static/images/menu/main-course/Mutton-Rogan-Josh.jpg',
 'name': 'Mutton Rogan Josh',
 'price': 400},
    {'category': 'Main Course',
 'description': 'Fragrant basmati rice cooked with mixed vegetables and spices',
 'image_url': '/static/images/menu/main-course/veg-pulao.jpg',
 'name': 'Veg Pulao',
 'price': 230},
    {'category': 'Main Course',
 'description': 'Mild and creamy chicken curry enriched with nuts and cream',
 'image_url': '/static/images/menu/main-course/chicken-korma.jpg',
 'name': 'Chicken Korma',
 'price': 310},
    {'category': 'Main Course',
 'description': 'Red kidney beans simmered in rich, spiced onion-tomato gravy',
 'image_url': '/static/images/menu/main-course/rajma-recipe.webp',
 'name': 'Rajma Masala',
 'price': 210},
    {'category': 'Main Course',
 'description': 'Soft, leavened flatbread cooked to perfection in clay oven',
 'image_url': '/static/images/menu/main-course/naan.jpg',
 'name': 'Naan',
 'price': 50},
    {'category': 'Main Course',
 'description': 'Classic naan bread generously brushed with melted butter',
 'image_url': '/static/images/menu/main-course/butter naan.webp',
 'name': 'Butter Naan',
 'price': 70},
    {'category': 'Main Course',
 'description': 'Whole wheat flatbread with smoky flavor from tandoor oven',
 'image_url': '/static/images/menu/main-course/Tandoori Roti.webp',
 'name': 'Tandoori Roti',
 'price': 60},
    {'category': 'Main Course',
 'description': 'Seasonal vegetables cooked in aromatic, flavorful gravy',
 'image_url': '/static/images/menu/main-course/Mixed Vegetable Curry.jpg',
 'name': 'Mixed Vegetable Curry',
 'price': 270},
    {'category': 'Desserts',
 'description': 'Soft, spongy milk balls soaked in cardamom-flavored sugar '
                'syrup',
 'image_url': '/static/images/menu/desserts/Gulab Jamun.jfif',
 'name': 'Gulab Jamun',
 'price': 120},
    {'category': 'Desserts',
 'description': 'Delicate cottage cheese discs in sweetened, thickened milk',
 'image_url': '/static/images/menu/desserts/Ras Malai.jpg',
 'name': 'Ras Malai',
 'price': 140},
    {'category': 'Desserts',
 'description': 'Traditional rice pudding made with milk, sugar, and dry '
                'fruits',
 'image_url': '/static/images/menu/desserts/Kheer.png',
 'name': 'Kheer',
 'price': 110},
    {'category': 'Desserts',
 'description': 'Crispy, deep-fried spirals soaked in saffron sugar syrup',
 'image_url': '/static/images/menu/desserts/jalebi.webp',
 'name': 'Jalebi',
 'price': 100},
    {'category': 'Desserts',
 'description': 'Rich, fudgy chocolate brownie with walnuts and vanilla ice '
                'cream',
 'image_url': '/static/images/menu/desserts/Chocolate Brownie.jpg',
 'name': 'Chocolate Brownie',
 'price': 150},
    {'category': 'Desserts',
 'description': 'Grated carrots slow-cooked in milk, sugar, and aromatic '
                'cardamom',
 'image_url': '/static/images/menu/desserts/carrot-halwa.jpg',
 'name': 'Carrot Halwa',
 'price': 130},
    {'category': 'Desserts',
 'description': 'Premium ice cream - choice of vanilla, chocolate, or '
                'strawberry',
 'image_url': '/static/images/menu/desserts/Ice Cream Scoop.jfif',
 'name': 'Ice Cream Scoop',
 'price': 90},
    {'category': 'Desserts',
 'description': 'Refreshing sweet yogurt drink blended with fresh mango pulp',
 'image_url': '/static/images/menu/desserts/mango-lassi.jpg',
 'name': 'Mango Lassi',
 'price': 100},
    {'category': 'Desserts',
 'description': 'Traditional sweet made from thickened, sweetened milk with '
                'nuts',
 'image_url': '/static/images/menu/desserts/Rabri.jfif',
 'name': 'Rabri',
 'price': 125},
    {'category': 'Desserts',
 'description': 'Semi-soft, melt-in-mouth sweet made from fresh milk solids',
 'image_url': '/static/images/menu/desserts/MilkPeda-.webp',
 'name': 'Peda',
 'price': 110},
    {'category': 'Desserts',
 'description': 'Golden sweet balls made from fine gram flour pearls and ghee',
 'image_url': '/static/images/menu/desserts/Motichoor-Ladoo.webp',
 'name': 'Motichoor Ladoo',
 'price': 115},
    {'category': 'Desserts',
 'description': 'Rich, luxurious dessert made with ground almonds and milk',
 'image_url': '/static/images/menu/desserts/badam-halwa.jpg',
 'name': 'Badam Halwa',
 'price': 135},
    {'category': 'Desserts',
 'description': 'Traditional Indian ice cream with cardamom and pistachio '
                'flavors',
 'image_url': '/static/images/menu/desserts/Kufli.jpg',
 'name': 'Kulfi',
 'price': 140},
    {'category': 'Desserts',
 'description': 'Creamy ground rice pudding flavored with cardamom and rose',
 'image_url': '/static/images/menu/desserts/phirni.jpg',
 'name': 'Phirni',
 'price': 120},
    {'category': 'Desserts',
 'description': 'Delicate Bengali sweet made from fresh cottage cheese and '
                'sugar',
 'image_url': '/static/images/menu/desserts/Sandesh.jpg',
 'name': 'Sandesh',
 'price': 115},
    {'category': 'Drinks',
 'description': 'Authentic spiced Indian tea with milk, cardamom, and ginger',
 'image_url': '/static/images/menu/drinks/masala-chai.jpeg',
 'name': 'Masala Chai',
 'price': 60},
    {'category': 'Drinks',
 'description': 'South Indian style drip coffee with chicory and fresh milk',
 'image_url': '/static/images/menu/drinks/filter-coffee.jpg',
 'name': 'Filter Coffee',
 'price': 70},
    {'category': 'Drinks',
 'description': 'Refreshing soda water with fresh lime juice and mint leaves',
 'image_url': '/static/images/menu/drinks/Fresh Lime Soda.jfif',
 'name': 'Fresh Lime Soda',
 'price': 80},
    {'category': 'Drinks',
 'description': 'Traditional yogurt-based drink, available sweet or salted',
 'image_url': '/static/images/menu/drinks/lassi.jpg',
 'name': 'Lassi',
 'price': 85},
    {'category': 'Drinks',
 'description': 'Creamy sweet yogurt smoothie with cardamom and rose water',
 'image_url': '/static/images/menu/drinks/Sweet-lassi.jpg',
 'name': 'Sweet Lassi',
 'price': 90},
    {'category': 'Drinks',
 'description': 'Chilled coffee blended with milk, ice cream, and chocolate',
 'image_url': '/static/images/menu/drinks/cold-coffee.jpg',
 'name': 'Cold Coffee',
 'price': 95},
    {'category': 'Drinks',
 'description': 'Classic Indian lemonade with fresh lime, mint, and rock salt',
 'image_url': '/static/images/menu/drinks/Nimbu-Paani.jpg',
 'name': 'Nimbu Pani',
 'price': 75},
    {'category': 'Drinks',
 'description': 'Fresh, natural tender coconut water straight from the shell',
 'image_url': '/static/images/menu/drinks/coconut water.webp',
 'name': 'Coconut Water',
 'price': 65},
    {'category': 'Drinks',
 'description': 'Refreshing chilled tea flavored with lemon or peach essence',
 'image_url': '/static/images/menu/drinks/Iced Tea.webp',
 'name': 'Iced Tea',
 'price': 90},
    {'category': 'Drinks',
 'description': 'Freshly squeezed seasonal mango juice, thick and flavorful',
 'image_url': '/static/images/menu/drinks/Mango Juice.webp',
 'name': 'Mango Juice',
 'price': 100},
    {'category': 'Drinks',
 'description': 'Healthy and refreshing green tea with natural antioxidants',
 'image_url': '/static/images/menu/drinks/Green-Tea.jpg',
 'name': 'Green Tea',
 'price': 55},
    {'category': 'Drinks',
 'description': 'Aromatic tea infused with cardamom pods and milk',
 'image_url': '/static/images/menu/drinks/elaichi_chai.webp',
 'name': 'Elaichi Tea',
 'price': 60},
    {'category': 'Drinks',
 'description': 'Chilled Coca-Cola served with ice and lemon slice',
 'image_url': '/static/images/menu/drinks/coca-cola.webp',
 'name': 'Cold Drink (Coke)',
 'price': 50},
    {'category': 'Drinks',
 'description': 'Premium bottled mineral water, chilled and refreshing',
 'image_url': '/static/images/menu/drinks/Mineral Water.webp',
 'name': 'Mineral Water',
 'price': 40},
    {'category': 'Drinks',
 'description': 'Strong, aromatic black coffee served hot without milk',
 'image_url': '/static/images/menu/drinks/Black Coffee.webp',
 'name': 'Black Coffee',
 'price': 70},
]
    
    for item_data in urban_platter_menu:
        item = MenuItem(
            name=item_data['name'],
            description=item_data['description'],
            price=item_data['price'],
            category=item_data['category'],
            image_url=item_data['image_url'],
            available=True
        )
        db.session.add(item)
    
    db.session.commit()
    print("✅ Urban Platter database initialized successfully!")
    print(f"🍽️  {len(urban_platter_menu)} menu items added")
    print(f"🔑 Admin: admin@urbanplatter.com / admin123")
    print(f"👨‍🍳 Staff: staff@urbanplatter.com / staff123")
    print(f"💰 All prices in {CURRENCY_SYMBOL}")

# ==========================================
# Policy Pages Routes
# ==========================================

@app.route('/terms-and-conditions')
def terms_and_conditions():
    """Terms and Conditions page"""
    return render_template('terms-and-conditions.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy-policy.html')

@app.route('/shipping-policy')
def shipping_policy():
    """Shipping and Delivery Policy page"""
    return render_template('shipping-policy.html')

@app.route('/contact-us')
def contact_us():
    """Contact Us page"""
    return render_template('contact-us.html')

@app.route('/cancellation-refunds')
def cancellation_refunds():
    """Cancellation and Refunds Policy page"""
    return render_template('cancellation-refunds.html')


# Initialize database when module is imported
with app.app_context():
    db.create_all()  # Create empty tables on startup
if __name__ == '__main__':
    with app.app_context():
        # init_db()  # Commented - run separately to populate database              # print("📱 Access at: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
