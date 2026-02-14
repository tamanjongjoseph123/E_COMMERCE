import requests
import json
import os
import logging
from datetime import datetime
from django.conf import settings
from .models import Payment, Order, WithdrawalRequest, Wallet, Transaction

# Set up logging
logger = logging.getLogger(__name__)


class FapshiPaymentService:
    """
    Service class for integrating with Fapshi payment gateway API
    Supports separate credentials for payments (incoming) and payouts (withdrawals)
    """
    
    def __init__(self, service_type='payment'):
        """
        Initialize the service with specific credentials based on service type
        
        Args:
            service_type (str): 'payment' for receiving payments, 'payout' for sending withdrawals
        """
        self.service_type = service_type
        
        if service_type == 'payment':
            # Credentials for receiving payments from customers
            self.api_key = getattr(settings, 'FAPSHI_PAYMENT_API_KEY', None)
            self.api_user = getattr(settings, 'FAPSHI_PAYMENT_API_USER', None)
        elif service_type == 'payout':
            # Credentials for sending payments to sellers (withdrawals)
            self.api_key = getattr(settings, 'FAPSHI_PAYOUT_API_KEY', None)
            self.api_user = getattr(settings, 'FAPSHI_PAYOUT_API_USER', None)
        else:
            raise ValueError("service_type must be either 'payment' or 'payout'")
        
        self.base_url = os.environ.get('FAPSHI_BASE_URL', 'https://live.fapshi.com')
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key,
            'apiuser': self.api_user
        }
        
        # Debug: Log initialization
        logger.info(f"FapshiPaymentService initialized for {service_type}:")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  API Key set: {'Yes' if self.api_key else 'No'}")
        logger.info(f"  API User set: {'Yes' if self.api_user else 'No'}")
    
    @classmethod
    def get_payment_service(cls):
        """Get service instance for receiving payments"""
        return cls(service_type='payment')
    
    @classmethod
    def get_payout_service(cls):
        """Get service instance for sending payouts/withdrawals"""
        return cls(service_type='payout')
    
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
            
            # Update order payment status if order exists
            try:
                order = payment.order
                if order is not None:
                    if payment.status == 'successful':
                        order.payment_status = 'paid'
                        # Only update order status to processing if it was pending
                        if order.status == 'pending':
                            order.status = 'processing'
                        
                        # Update seller wallets for successful payments
                        self._update_seller_wallets(order)
                        
                    elif payment.status in ['failed', 'expired']:
                        order.payment_status = 'failed'
                    
                    order.save()
                else:
                    logger.info(f"No order exists for payment {payment.id} yet")
            except Order.DoesNotExist:
                # No order exists yet, which is normal for new payments
                logger.info(f"No order exists for payment {payment.id} yet")
            
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
    
    def initiate_payout(self, amount, phone, name, email, user_id, external_id=None, message=None):
        """
        Initiate a payout to a user's mobile money account
        """
        url = f"{self.base_url}/payout"
        
        payload = {
            "amount": int(amount),
            "phone": phone,
            "medium": "mobile money",
            "name": name,
            "email": email,
            "userId": str(user_id),
            "externalId": external_id or f"withdrawal_{user_id}_{datetime.now().timestamp()}",
            "message": message or f"Withdrawal payment for {external_id}"
        }
        
        # Debug: Log payout request
        logger.info(f"Initiating payout request:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Payload: {json.dumps(payload, indent=2)}")
        logger.info(f"  Headers: {self.headers}")
        logger.info(f"  Phone number being sent: '{phone}'")
        logger.info(f"  Phone number length: {len(phone)}")
        logger.info(f"  Phone number starts with 2376/2377: {phone.startswith(('2376', '2377'))}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            logger.info(f"Payout response status code: {response.status_code}")
            logger.info(f"Payout response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"Payout HTTP Error: {response.status_code}")
                logger.error(f"Payout response body: {response.text}")
                return {
                    "error": f"HTTP {response.status_code}",
                    "message": f"Payout HTTP error occurred: {response.status_code}",
                    "response_body": response.text
                }
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Payout response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payout request exception occurred: {str(e)}")
            logger.error(f"Payout exception type: {type(e).__name__}")
            return {
                "error": str(e),
                "message": "Failed to initiate payout"
            }
    
    def process_withdrawal_payout(self, withdrawal_request):
        """
        Process a withdrawal request using Fapshi payout API
        """
        logger.info(f"Processing payout for withdrawal request {withdrawal_request.id}")
        logger.info(f"Withdrawal amount: {withdrawal_request.amount}")
        logger.info(f"Seller: {withdrawal_request.seller.email}")
        
        seller = withdrawal_request.seller
        
        # Get seller's phone number from profile
        phone = seller.phone_number
        
        if not phone:
            logger.error(f"No phone number found for seller {seller.email}")
            return {
                "success": False,
                "message": "No phone number found in seller profile. Please update profile.",
                "withdrawal_id": withdrawal_request.id
            }
        
        # Validate and format phone number for Fapshi
        formatted_phone = self.format_phone_number_for_fapshi(phone)
        if not formatted_phone:
            logger.error(f"Invalid phone number format: {phone}")
            return {
                "success": False,
                "message": f"Invalid phone number format: {phone}. Must be a valid Cameroon MTN or Orange number (e.g., 2376xxxxxxx or 2377xxxxxxx)",
                "withdrawal_id": withdrawal_request.id
            }
        
        logger.info(f"Original phone: {phone}, Formatted phone: {formatted_phone}")
        
        # Create external ID for tracking
        external_id = f"withdrawal_{withdrawal_request.id}"
        
        # Initiate payout
        result = self.initiate_payout(
            amount=withdrawal_request.amount,
            phone=formatted_phone,
            name=seller.full_name or seller.name,
            email=seller.email,
            user_id=seller.id,
            external_id=external_id,
            message=f"Withdrawal payment for request #{withdrawal_request.id}"
        )
        
        logger.info(f"Payout initiation result: {result}")
        
        if 'error' not in result:
            # Payout initiated successfully
            logger.info("Payout initiated successfully")
            
            # Update withdrawal request with payout details
            withdrawal_request.admin_notes = f"Payout initiated via Fapshi to {formatted_phone}. Trans ID: {result.get('transId')}"
            withdrawal_request.status = 'processed'
            withdrawal_request.processed_at = datetime.now()
            withdrawal_request.save()
            
            # Create transaction record
            wallet = Wallet.objects.get(seller=seller)
            Transaction.objects.create(
                wallet=wallet,
                amount=withdrawal_request.amount,
                transaction_type='withdrawal',
                description=f'Withdrawal processed via Fapshi to {formatted_phone} - Request #{withdrawal_request.id}'
            )
            
            # Deduct from wallet
            wallet.balance -= withdrawal_request.amount
            wallet.save()
            
            return {
                "success": True,
                "message": f"Withdrawal processed successfully via Fapshi to {formatted_phone}",
                "trans_id": result.get('transId'),
                "date_initiated": result.get('dateInitiated'),
                "withdrawal_id": withdrawal_request.id,
                "payout_phone": formatted_phone
            }
        else:
            # Payout failed
            logger.error(f"Payout initiation failed: {result}")
            withdrawal_request.admin_notes = f"Payout failed to {formatted_phone}: {result.get('message', 'Unknown error')}"
            withdrawal_request.save()
            
            return {
                "success": False,
                "message": result.get('message', 'Failed to process payout'),
                "error": result.get('error'),
                "withdrawal_id": withdrawal_request.id,
                "payout_phone": formatted_phone
            }
    
    def format_phone_number_for_fapshi(self, phone):
        """
        Format phone number for Fapshi API
        Fapshi expects Cameroon numbers in format: 6xxxxxxx or 7xxxxxxx (9 digits only)
        Valid prefixes:
        - MTN: 650, 651, 652, 653, 654, 655, 656, 657, 658, 659
        - Orange: 690, 691, 692, 693, 694, 695, 696, 697, 698, 699
        """
        if not phone:
            return None
        
        logger.info(f"Original phone input: '{phone}'")
        
        # Remove all non-digit characters
        phone_digits = ''.join(filter(str.isdigit, str(phone)))
        logger.info(f"After removing non-digits: '{phone_digits}'")
        
        # Define valid MTN and Orange prefixes
        mtn_prefixes = ['650', '651', '652', '653', '654', '655', '656', '657', '658', '659']
        orange_prefixes = ['690', '691', '692', '693', '694', '695', '696', '697', '698', '699']
        
        # Remove country code if present (237)
        if phone_digits.startswith('237') and len(phone_digits) == 12:
            phone_digits = phone_digits[3:]  # Remove 237
            logger.info(f"Removed country code, now: '{phone_digits}'")
        
        # Check if we have exactly 9 digits
        if len(phone_digits) == 9:
            prefix = phone_digits[:3]
            if prefix in mtn_prefixes or prefix in orange_prefixes:
                formatted = phone_digits  # Just return the 9 digits
                logger.info(f"Valid {('MTN' if prefix in mtn_prefixes else 'Orange')} prefix: {prefix}")
                logger.info(f"Final formatted phone: {formatted}")
                return formatted
            else:
                logger.error(f"Invalid prefix: {prefix}. Valid MTN: {mtn_prefixes}, Valid Orange: {orange_prefixes}")
                return None
        else:
            logger.error(f"Phone number must be exactly 9 digits after removing country code. Got: {len(phone_digits)} digits")
            return None
    
    def _update_seller_wallets(self, order):
        """
        Update seller wallets when an order is successfully paid
        """
        from django.db import transaction as db_transaction
        
        logger.info(f"Updating seller wallets for order {order.id}")
        
        try:
            with db_transaction.atomic():
                for order_item in order.items.all():
                    seller = order_item.seller
                    amount = order_item.subtotal
                    
                    logger.info(f"Processing wallet update for seller {seller.email}, amount: {amount}")
                    
                    # Get or create wallet for seller
                    wallet, created = Wallet.objects.get_or_create(
                        seller=seller,
                        defaults={'balance': 0}
                    )
                    
                    if created:
                        logger.info(f"Created new wallet for seller {seller.email}")
                    
                    # Update wallet balance
                    old_balance = wallet.balance
                    wallet.balance += amount
                    wallet.save()
                    
                    # Create transaction record
                    Transaction.objects.create(
                        wallet=wallet,
                        order_item=order_item,
                        amount=amount,
                        transaction_type='sale',
                        description=f'Sale from order #{order.id} - {order_item.product.name}'
                    )
                    
                    logger.info(f"Updated wallet for seller {seller.email}: {old_balance} -> {wallet.balance}")
                    
        except Exception as e:
            logger.error(f"Error updating seller wallets for order {order.id}: {str(e)}")
            raise
