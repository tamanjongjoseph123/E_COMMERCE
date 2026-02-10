from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
import logging

from .models import Payment
from .payment_service import FapshiPaymentService

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def debug_payment_transaction(request):
    """Debug a specific payment transaction"""
    try:
        trans_id = request.data.get('trans_id')
        
        if not trans_id:
            return Response({
                'success': False,
                'message': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_service = FapshiPaymentService()
        
        # Check payment status with detailed logging
        logger.info(f"Debugging transaction: {trans_id}")
        
        status_result = payment_service.check_payment_status(trans_id)
        logger.info(f"Payment status result: {status_result}")
        
        # Also check our local payment record
        try:
            local_payment = Payment.objects.get(trans_id=trans_id)
            logger.info(f"Local payment: ID={local_payment.id}, status={local_payment.status}, amount={local_payment.amount}")
        except Payment.DoesNotExist:
            logger.error("Payment not found in local database")
        
        return Response({
            'success': True,
            'message': 'Payment transaction debug information',
            'data': {
                'trans_id': trans_id,
                'fapshi_status': status_result,
                'local_payment': {
                    'id': local_payment.id if 'local_payment' in locals() else None,
                    'status': local_payment.status if 'local_payment' in locals() else None,
                    'amount': str(local_payment.amount) if 'local_payment' in locals() else None,
                    'email': local_payment.email if 'local_payment' in locals() else None,
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Payment transaction debug failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Payment transaction debug failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_pending_payments(request):
    """Check pending payments and create orders for successful ones"""
    try:
        from rest_framework.permissions import IsAuthenticated
        from django.db import transaction as db_transaction
        from django.utils import timezone
        from .models import Order, Cart, CartItem
        
        # Check any pending payments and update their status
        pending_payments = Payment.objects.filter(
            email=request.user.email,
            status='pending'
        )
        
        payment_service = FapshiPaymentService()
        orders_created = []
        
        for payment in pending_payments:
            try:
                # Check payment status with Fapshi
                status_result = payment_service.check_payment_status(payment.trans_id)
                
                if 'error' not in status_result and status_result.get('status', '').upper() == 'SUCCESSFUL':
                    # Create order for successful payment
                    with db_transaction.atomic():
                        order = Order.objects.create(
                            buyer=request.user,
                            total_amount=payment.amount,
                            status='pending',
                            payment_status='paid',
                            delivery_address='Payment completed - Contact support for delivery details',
                            delivery_phone='Payment completed',
                            delivery_city='',
                            delivery_state='',
                            delivery_postal_code='',
                            delivery_notes=f'Order created from payment {payment.id}. Auto-checked'
                        )
                        
                        # Link payment to order
                        payment.order = order
                        payment.status = 'paid'
                        payment.date_confirmed = timezone.now()
                        payment.save()
                        
                        # Clear user's cart
                        try:
                            cart = Cart.objects.get(user=request.user)
                            cart.items.all().delete()
                            logger.info(f"Cart cleared for user {request.user.email} after auto payment check")
                        except Cart.DoesNotExist:
                            pass
                        
                        orders_created.append({
                            'order_id': order.id,
                            'payment_id': payment.id,
                            'amount': str(payment.amount),
                            'trans_id': payment.trans_id
                        })
                        
                        logger.info(f"AUTO-CHECK: Order {order.id} created from payment {payment.id}")
            
            except Exception as e:
                logger.error(f"Auto payment check failed for {payment.trans_id}: {str(e)}")
                continue
        
        return Response({
            'success': True,
            'message': 'Pending payments checked',
            'data': {
                'pending_payments_checked': len(pending_payments),
                'orders_created': len(orders_created),
                'orders': orders_created
            }
        })
        
    except Exception as e:
        logger.error(f"Check pending payments failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to check pending payments',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
