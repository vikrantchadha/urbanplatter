# Add these routes to your existing urban_platter_app.py

from flask import session
from razorpay_integration import razorpay_integration
import json
from datetime import datetime

# Shopping cart session management
def get_cart_items():
    """Get cart items from session"""
    cart_items = []
    subtotal = 0

    if 'cart' in session:
        for item_data in session['cart'].values():
            cart_items.append(item_data)
            subtotal += item_data['price'] * item_data['quantity']

    return cart_items, subtotal

def add_to_cart_session(menu_item, quantity=1, special_instructions=''):
    """Add item to cart session"""
    if 'cart' not in session:
        session['cart'] = {}

    item_key = str(menu_item.id)
    if item_key in session['cart']:
        session['cart'][item_key]['quantity'] += quantity
    else:
        session['cart'][item_key] = {
            'id': menu_item.id,
            'name': menu_item.name,
            'description': menu_item.description,
            'price': float(menu_item.price),
            'quantity': quantity,
            'image_url': menu_item.image_url,
            'special_instructions': special_instructions
        }

    session.modified = True
    return True

# Payment System Routes

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        special_instructions = data.get('special_instructions', '')

        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return jsonify({'success': False, 'message': 'Item not found'})

        add_to_cart_session(menu_item, quantity, special_instructions)

        cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

        return jsonify({
            'success': True,
            'message': 'Item added to cart',
            'cart_count': cart_count
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    try:
        data = request.get_json()
        item_id = str(data.get('item_id'))
        quantity = int(data.get('quantity'))

        if 'cart' in session and item_id in session['cart']:
            if quantity > 0:
                session['cart'][item_id]['quantity'] = quantity
                new_total = session['cart'][item_id]['price'] * quantity

                # Calculate new subtotal
                subtotal = sum(item['price'] * item['quantity'] for item in session['cart'].values())

                session.modified = True
                return jsonify({
                    'success': True, 
                    'new_total': new_total,
                    'subtotal': subtotal
                })
            else:
                del session['cart'][item_id]
                session.modified = True
                return jsonify({'success': True})

        return jsonify({'success': False, 'message': 'Item not found in cart'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        data = request.get_json()
        item_id = str(data.get('item_id'))

        if 'cart' in session and item_id in session['cart']:
            del session['cart'][item_id]
            session.modified = True
            return jsonify({'success': True})

        return jsonify({'success': False, 'message': 'Item not found in cart'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/cart')
def view_cart():
    cart_items, subtotal = get_cart_items()
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/save-instructions', methods=['POST'])
def save_instructions():
    try:
        data = request.get_json()
        session['special_instructions'] = data.get('special_instructions', '')
        session.modified = True
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/checkout')
def checkout():
    cart_items, subtotal = get_cart_items()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('menu'))

    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        if 'cart' not in session or not session['cart']:
            return jsonify({'success': False, 'message': 'Cart is empty'})

        data = request.get_json()
        cart_items, subtotal = get_cart_items()

        # Calculate totals
        tax_amount = subtotal * 0.08
        delivery_fee = 25.00 if data.get('delivery_type') == 'delivery' else 0.00
        total_amount = subtotal + tax_amount + delivery_fee

        # Create order data
        order_data = {
            'id': len(orders) + 1,  # Simple ID generation
            'customer_name': f"{data.get('first_name')} {data.get('last_name')}",
            'customer_email': data.get('email'),
            'customer_phone': data.get('phone'),
            'delivery_type': data.get('delivery_type'),
            'delivery_address': data.get('address') if data.get('delivery_type') == 'delivery' else None,
            'city': data.get('city') if data.get('delivery_type') == 'delivery' else None,
            'state': data.get('state') if data.get('delivery_type') == 'delivery' else None,
            'pincode': data.get('pincode') if data.get('delivery_type') == 'delivery' else None,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'delivery_fee': delivery_fee,
            'total_amount': total_amount,
            'payment_method': data.get('payment_method'),
            'status': 'Confirmed',
            'payment_status': 'Paid' if data.get('payment_method') != 'cod' else 'Pending',
            'special_instructions': session.get('special_instructions', ''),
            'estimated_time': 30 if data.get('delivery_type') == 'pickup' else 45,
            'order_items': cart_items,
            'created_at': datetime.now().isoformat()
        }

        # Store order (in a real app, this would go to database)
        orders.append(order_data)

        # Clear cart
        session.pop('cart', None)
        session.pop('special_instructions', None)
        session.modified = True

        return jsonify({
            'success': True,
            'order_id': order_data['id'],
            'message': 'Order placed successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    # Find order by ID (in a real app, this would be a database query)
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('index'))

    return render_template('order-confirmation.html', order=order)

@app.route('/download-receipt/<int:order_id>')
def download_receipt(order_id):
    # Find order by ID
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break

    if not order:
        return "Order not found", 404

    # Generate PDF receipt (simplified version)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from io import BytesIO

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Add content to PDF
    p.drawString(100, 750, f"Urban Platter - Order Receipt")
    p.drawString(100, 720, f"Order #: {order['id']}")
    p.drawString(100, 700, f"Customer: {order['customer_name']}")
    p.drawString(100, 680, f"Date: {order['created_at']}")
    p.drawString(100, 660, f"Total: {format_currency(order['total_amount'])}")

    p.showPage()
    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'receipt_order_{order_id}.pdf',
        mimetype='application/pdf'
    )

# Initialize orders list (in a real app, this would be in database)
orders = []

# Update menu route to include add to cart functionality
@app.route('/menu')
def menu():
    categories = MenuCategory.query.filter_by(is_active=True).order_by(MenuCategory.display_order).all()
    menu_items = MenuItem.query.filter_by(is_available=True).all()

    # Get cart count for navbar
    cart_count = sum(item['quantity'] for item in session.get('cart', {}).values())

    return render_template('menu.html', 
                         categories=categories, 
                         menu_items=menu_items,
                         cart_count=cart_count)

# Razorpay Payment Routes

@app.route('/get-razorpay-key', methods=['GET'])
def get_razorpay_key():
    """Get Razorpay key for frontend integration"""
    try:
        if razorpay_integration:
            return jsonify({
                'success': True,
                'key_id': razorpay_integration.get_key_id()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Razorpay integration not configured'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    """Create a Razorpay order for payment"""
    try:
        if not razorpay_integration:
            return jsonify({
                'success': False,
                'message': 'Razorpay integration not configured'
            })
        
        data = request.get_json()
        amount = data.get('amount')  # Amount in rupees
        
        if not amount:
            return jsonify({'success': False, 'message': 'Amount is required'})
        
        # Convert amount to paise (Razorpay uses smallest currency unit)
        amount_in_paise = int(float(amount) * 100)
        
        # Generate receipt ID
        receipt_id = f"order_{len(orders) + 1}_{int(datetime.now().timestamp())}"
        
        # Create order
        result = razorpay_integration.create_order(
            amount=amount_in_paise,
            currency='INR',
            receipt=receipt_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'order_id': result['order']['id'],
                'amount': result['order']['amount'],
                'currency': result['order']['currency']
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to create order')
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/verify-razorpay-payment', methods=['POST'])
def verify_razorpay_payment():
    """Verify Razorpay payment signature"""
    try:
        if not razorpay_integration:
            return jsonify({
                'success': False,
                'message': 'Razorpay integration not configured'
            })
        
        data = request.get_json()
        order_id = data.get('razorpay_order_id')
        payment_id = data.get('razorpay_payment_id')
        signature = data.get('razorpay_signature')
        
        if not all([order_id, payment_id, signature]):
            return jsonify({
                'success': False,
                'message': 'Missing payment verification parameters'
            })
        
        # Verify payment signature
        is_valid = razorpay_integration.verify_payment_signature(
            order_id=order_id,
            payment_id=payment_id,
            signature=signature
        )
        
        if is_valid:
            # Payment verified successfully
            # Here you can update order status, send confirmation email, etc.
            return jsonify({
                'success': True,
                'message': 'Payment verified successfully',
                'payment_id': payment_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Payment verification failed'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay webhook notifications"""
    try:
        # Get webhook data
        webhook_data = request.get_json()
        
        # Log webhook event
        event = webhook_data.get('event')
        payload = webhook_data.get('payload')
        
        # Handle different webhook events
        if event == 'payment.captured':
            # Payment was captured successfully
            payment_id = payload.get('payment', {}).get('entity', {}).get('id')
            order_id = payload.get('payment', {}).get('entity', {}).get('order_id')
            
            # Update order status in database
            # This is where you would update your order records
            
            return jsonify({'success': True, 'message': 'Payment captured'})
        
        elif event == 'payment.failed':
            # Payment failed
            payment_id = payload.get('payment', {}).get('entity', {}).get('id')
            
            # Update order status to failed
            # This is where you would update your order records
            
            return jsonify({'success': True, 'message': 'Payment failed recorded'})
        
        else:
            # Unknown event
            return jsonify({'success': True, 'message': f'Received event: {event}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
