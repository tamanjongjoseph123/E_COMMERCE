import requests
import json
import os
import logging
from datetime import datetime
from django.conf import settings
from .models import Payment, Order

# Set up logging
logger = logging.getLogger(__name__)


class FapshiPaymentService:
    """
    Service class for integrating with Fapshi payment gateway API
    """
    
    def __init__(self):
        self.api_key = os.environ.get('FAPSHI_API_KEY', 'your-api-key')
        self.api_user = os.environ.get('FAPSHI_API_USER', 'your-api-user')
        self.base_url = os.environ.get('FAPSHI_BASE_URL', 'https://sandbox.fapshi.com')
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key,
            'apiuser': self.api_user
        }
        
        # Debug: Log initialization
        logger.info(f"FapshiPaymentService initialized:")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  API User: {self.api_user}")
        logger.info(f"  API Key set: {'Yes' if self.api_key != 'your-api-key' else 'No'}")
    
    def initiate_direct_pay(self, amount, phone, name, email, user_id, external_id=None, message=None):
        """
        Initiate a direct payment request to user's mobile device
        """
        url = f"{self.base_url}/direct-pay"
        
        payload = {
            "amount": int(amount),
            "phone": phone,
            "medium": "mobile money",
            "name": name,
            "email": email,
            "userId": str(user_id),
            "externalId": external_id or f"order_{user_id}_{datetime.now().timestamp()}",
            "message": message or f"Payment for order {external_id}"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "message": "Failed to initiate payment"
            }
    
    def initiate_payment_link(self, amount, email, user_id, external_id=None, redirect_url=None, message=None, phone=None):
        """
        Generate a payment link for user to complete payment
        """
        # Check minimum amount requirement (100 XAF)
        min_amount = 100
        if amount < min_amount:
            logger.error(f"Amount {amount} is below minimum required amount of {min_amount} XAF")
            return {
                "error": f"Amount {amount} is below minimum {min_amount} XAF",
                "message": f"Transaction amount cannot be less than {min_amount} XAF"
            }
        
        url = f"{self.base_url}/initiate-pay"
        
        payload = {
            "amount": int(amount),
            "email": email,
            "userId": str(user_id),
            "externalId": external_id or f"order_{user_id}_{datetime.now().timestamp()}",
            "message": message or f"Payment for order {external_id}"
        }
        
        # Add phone number if provided
        if phone:
            payload["phone"] = phone
        
        if redirect_url:
            payload["redirectUrl"] = redirect_url
        
        # Debug: Log payment link request
        logger.info(f"Initiating payment link request:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Payload: {json.dumps(payload, indent=2)}")
        logger.info(f"  Headers: {self.headers}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"HTTP Error: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                return {
                    "error": f"HTTP {response.status_code}",
                    "message": f"HTTP error occurred: {response.status_code}"
                }
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return {
                "error": str(e),
                "message": "Failed to generate payment link"
            }
    
    def check_payment_status(self, trans_id):
        """
        Check the status of a payment transaction
        """
        url = f"{self.base_url}/payment-status/{trans_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Handle both single transaction and array responses
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
            else:
                return {"error": "Invalid response format"}
                
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "message": "Failed to check payment status"
            }
    
    def expire_payment(self, trans_id):
        """
        Expire a payment transaction
        """
        url = f"{self.base_url}/expire-pay"
        
        payload = {"transId": trans_id}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "message": "Failed to expire payment"
            }
    
    def get_service_balance(self):
        """
        Get the current balance of the service account
        """
        url = f"{self.base_url}/balance"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "message": "Failed to get service balance"
            }
    
    def create_payment_for_order(self, order, payment_type='initiate_pay', phone=None):
        """
        Create a payment record for an order and initiate payment
        """
        logger.info(f"Creating payment for order {order.id}")
        logger.info(f"Order total amount: {order.total_amount}")
        logger.info(f"Payment type: {payment_type}")
        
        user = order.buyer
        external_id = f"order_{order.id}"
        
        logger.info(f"User details: {user.email}, ID: {user.id}")
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            payment_type=payment_type,
            amount=order.total_amount,
            email=user.email,
            external_id=external_id,
            status='pending'
        )
        
        logger.info(f"Payment record created with ID: {payment.id}")
        
        # Only support payment links
        result = self.initiate_payment_link(
            amount=order.total_amount,
            email=user.email,
            user_id=user.id,
            external_id=external_id,
            redirect_url=os.environ.get('PAYMENT_REDIRECT_URL', ''),
            message=f"Payment for Order #{order.id}"
        )
        
        logger.info(f"Payment link initiation result: {result}")
        
        # Update payment record with response
        if 'error' not in result:
            logger.info("Payment link generated successfully")
            payment.trans_id = result.get('transId')
            payment.status = 'created'
            payment.message = result.get('message', '')
            
            if 'link' in result:
                payment.payment_link = result['link']
                logger.info(f"Payment link set: {payment.payment_link}")
            
            if 'dateInitiated' in result:
                payment.date_initiated = datetime.fromisoformat(result['dateInitiated'].replace('Z', '+00:00'))
                logger.info(f"Payment date initiated: {payment.date_initiated}")
            
            payment.save()
            logger.info(f"Payment record updated successfully")
            
            return {
                "success": True,
                "payment_id": payment.id,
                "trans_id": payment.trans_id,
                "payment_link": payment.payment_link,
                "message": result.get('message', 'Payment initiated successfully')
            }
        else:
            logger.error(f"Payment link generation failed: {result}")
            payment.status = 'failed'
            payment.message = result.get('message', 'Payment initiation failed')
            payment.save()
            
            return {
                "success": False,
                "message": result.get('message', 'Payment initiation failed'),
                "error": result.get('error')
            }
    
    def update_payment_status(self, trans_id):
        """
        Update payment status based on transaction ID
        """
        try:
            payment = Payment.objects.get(trans_id=trans_id)
        except Payment.DoesNotExist:
            return {"success": False, "message": "Payment not found"}
        
        result = self.check_payment_status(trans_id)
        
        if 'error' not in result:
            old_status = payment.status
            payment.status = result.get('status', 'unknown').lower()
            
            if 'dateConfirmed' in result:
                payment.date_confirmed = datetime.fromisoformat(result['dateConfirmed'].replace('Z', '+00:00'))
            
            payment.save()
            
            # Update order payment status
            order = payment.order
            if payment.status == 'successful':
                order.payment_status = 'paid'
                # Only update order status to processing if it was pending
                if order.status == 'pending':
                    order.status = 'processing'
            elif payment.status in ['failed', 'expired']:
                order.payment_status = 'failed'
            
            order.save()
            
            return {
                "success": True,
                "old_status": old_status,
                "new_status": payment.status,
                "message": f"Payment status updated to {payment.status}"
            }
        else:
            return {
                "success": False,
                "message": result.get('message', 'Failed to update payment status'),
                "error": result.get('error')
            }
