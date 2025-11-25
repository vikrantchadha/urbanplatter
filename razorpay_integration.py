import razorpay
import os
from flask import jsonify
import logging

# Configure logging
logger = logging.getLogger(__name__)

class RazorpayIntegration:
    def __init__(self):
        # Get API keys from environment variables
        self.key_id = os.environ.get('RAZORPAY_KEY_ID')
        self.key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
        
        if not self.key_id or not self.key_secret:
            logger.error("Razorpay API keys not found in environment variables")
            raise ValueError("Razorpay API keys must be set in environment variables")
        
        # Initialize Razorpay client
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        logger.info("Razorpay client initialized successfully")
    
    def create_order(self, amount, currency='INR', receipt=None):
        """
        Create a Razorpay order
        
        Args:
            amount (int): Amount in smallest currency unit (paise for INR)
            currency (str): Currency code (default: INR)
            receipt (str): Receipt ID for reference
        
        Returns:
            dict: Order details from Razorpay
        """
        try:
            order_data = {
                'amount': amount,  # Amount in paise
                'currency': currency,
                'payment_capture': 1  # Auto capture payment
            }
            
            if receipt:
                order_data['receipt'] = receipt
            
            order = self.client.order.create(data=order_data)
            logger.info(f"Order created successfully: {order['id']}")
            return {
                'success': True,
                'order': order
            }
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """
        Verify payment signature for security
        
        Args:
            order_id (str): Razorpay order ID
            payment_id (str): Razorpay payment ID
            signature (str): Payment signature to verify
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"Payment signature verified successfully for order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            return False
    
    def fetch_payment_details(self, payment_id):
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id (str): Razorpay payment ID
        
        Returns:
            dict: Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                'success': True,
                'payment': payment
            }
        except Exception as e:
            logger.error(f"Error fetching payment details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_key_id(self):
        """
        Get the Razorpay Key ID for client-side integration
        
        Returns:
            str: Razorpay Key ID
        """
        return self.key_id

# Initialize Razorpay integration
try:
    razorpay_integration = RazorpayIntegration()
except Exception as e:
    logger.warning(f"Razorpay integration not initialized: {str(e)}")
    razorpay_integration = None
