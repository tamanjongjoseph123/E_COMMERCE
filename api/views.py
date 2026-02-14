from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Sum
from django.db import transaction as db_transaction
from decimal import Decimal
import logging
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    User, Seller, Category, Product, Cart, CartItem,
    Order, OrderItem, Wallet, Transaction, Report, Payment, WithdrawalRequest
)
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, SellerSerializer,
    CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderItemSerializer, SellerOrderSerializer, WalletSerializer, TransactionSerializer, 
    ProfileSerializer, ReportSerializer, PaymentSerializer, PaymentInitiateSerializer,
    WithdrawalRequestSerializer
)
from .payment_service import FapshiPaymentService
from .debug_views import debug_payment_transaction, check_pending_payments

# Set up logging
logger = logging.getLogger(__name__)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_admin or request.user.is_superuser)


class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_seller


class IsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_buyer


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': 'Registration successful. Please wait for admin approval if you are a seller.',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_200_OK)
    return Response({
        'success': False,
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({
            'success': False,
            'message': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'success': True,
            'message': 'Token refreshed successfully',
            'data': {
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Invalid refresh token',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# Admin Views
class SellerApprovalViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsAdmin]
    
    def create(self, request, *args, **kwargs):
        return Response({
            'success': False,
            'message': 'Sellers can only be created through user registration'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = Seller.objects.all()
        if status_filter:
            queryset = queryset.filter(approval_status=status_filter)
        return queryset.select_related('user')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        seller = self.get_object()
        seller.approval_status = 'approved'
        seller.save()
        return Response({
            'success': True,
            'message': 'Seller approved successfully',
            'data': self.get_serializer(seller).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        seller = self.get_object()
        seller.approval_status = 'rejected'
        seller.save()
        return Response({
            'success': True,
            'message': 'Seller rejected',
            'data': self.get_serializer(seller).data
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        # For public access, only show active categories
        # Admins can see all categories
        if self.request.user.is_authenticated and (self.request.user.is_admin or self.request.user.is_superuser):
            return Category.objects.all()
        return Category.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, is_active=True)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        category = self.get_object()
        products = Product.objects.filter(category=category, is_active=True)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': f'Products in {category.name}',
            'data': serializer.data
        })


class UserManagementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        role_filter = self.request.query_params.get('role', None)
        queryset = User.objects.all()
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['delete'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({
            'success': True,
            'message': 'User deactivated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({
            'success': True,
            'message': 'User activated successfully'
        })


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_wallets(request):
    wallets = Wallet.objects.all().select_related('seller')
    serializer = WalletSerializer(wallets, many=True, context={'request': request})
    total_balance = wallets.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
    
    return Response({
        'success': True,
        'message': 'All seller wallets',
        'data': {
            'wallets': serializer.data,
            'total_balance': float(total_balance)
        }
    })


# Seller Views
class SellerProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsSeller]
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user, is_active=True)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_wallet(request):
    try:
        wallet = Wallet.objects.get(seller=request.user)
        serializer = WalletSerializer(wallet, context={'request': request})
        return Response({
            'success': True,
            'message': 'Wallet retrieved successfully',
            'data': serializer.data
        })
    except Wallet.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Wallet not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_categories(request):
    """Fetch all available categories for sellers to use when creating products"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    serializer = CategorySerializer(categories, many=True)
    return Response({
        'success': True,
        'message': 'Available categories retrieved successfully',
        'data': serializer.data
    })


# Buyer Views
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('seller', 'category')
        
        # Filter by seller if provided
        seller_id = self.request.query_params.get('seller_id', None)
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        
        # Filter by category if provided
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Ordering
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_ordering = ['price', '-price', 'created_at', '-created_at', 'name', '-name']
            if ordering in allowed_ordering:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({
                'success': False,
                'message': 'Search query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response({
            'success': True,
            'message': f'Search results for "{query}"',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def seller_details(self, request, pk=None):
        product = self.get_object()
        seller = product.seller
        seller_products = Product.objects.filter(seller=seller, is_active=True).exclude(id=product.id)[:5]
        
        return Response({
            'success': True,
            'message': 'Seller details retrieved',
            'data': {
                'seller': UserSerializer(seller).data,
                'other_products': ProductSerializer(seller_products, many=True, context={'request': request}).data
            }
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def list_all_products(request):
    """
    List all available products from sellers.
    Supports filtering by seller, category, price range, and ordering.
    """
    queryset = Product.objects.filter(is_active=True).select_related('seller', 'category')
    
    # Get query parameters
    seller_id = request.query_params.get('seller_id', None)
    category_id = request.query_params.get('category_id', None)
    min_price = request.query_params.get('min_price', None)
    max_price = request.query_params.get('max_price', None)
    ordering = request.query_params.get('ordering', '-created_at')
    search_query = request.query_params.get('q', None)
    
    # Apply filters
    if seller_id:
        queryset = queryset.filter(seller_id=seller_id)
    
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Apply ordering
    allowed_ordering = ['price', '-price', 'created_at', '-created_at', 'name', '-name']
    if ordering in allowed_ordering:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')
    
    # Get total count before pagination
    total_count = queryset.count()
    
    # Pagination
    page_size = int(request.query_params.get('page_size', 20))
    page = int(request.query_params.get('page', 1))
    
    start = (page - 1) * page_size
    end = start + page_size
    
    products = queryset[start:end]
    
    serializer = ProductSerializer(products, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'message': 'All available products retrieved successfully',
        'data': {
            'products': serializer.data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0
        }
    })


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsBuyer]
    
    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        product = Product.objects.get(id=product_id)
        
        if product.stock < quantity:
            return Response({
                'success': False,
                'message': f'Insufficient stock. Available: {product.stock}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                return Response({
                    'success': False,
                    'message': f'Insufficient stock. Available: {product.stock}'
                }, status=status.HTTP_400_BAD_REQUEST)
            cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response({
            'success': True,
            'message': 'Item added to cart',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        cart_item = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if quantity > cart_item.product.stock:
            return Response({
                'success': False,
                'message': f'Insufficient stock. Available: {cart_item.product.stock}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response({
            'success': True,
            'message': 'Cart item updated',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def cart_summary(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response({
            'success': True,
            'message': 'Cart retrieved successfully',
            'data': serializer.data
        })


@api_view(['POST'])
@permission_classes([IsBuyer])
def bulk_cart_operations(request):
    """Handle multiple cart operations in one call"""
    try:
        operations = request.data.get('operations', [])
        results = []
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        for operation in operations:
            op_type = operation.get('type')  # 'add', 'update', 'remove'
            product_id = operation.get('product_id')
            quantity = operation.get('quantity', 1)
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                
                if op_type == 'add':
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        product=product,
                        defaults={'quantity': quantity}
                    )
                    
                    if not created:
                        new_quantity = cart_item.quantity + quantity
                        if new_quantity > product.stock:
                            results.append({
                                'type': op_type,
                                'product_id': product_id,
                                'success': False,
                                'message': f'Insufficient stock. Available: {product.stock}'
                            })
                            continue
                        
                        cart_item.quantity = new_quantity
                        cart_item.save()
                    
                    results.append({
                        'type': op_type,
                        'product_id': product_id,
                        'success': True,
                        'message': 'Item added to cart',
                        'quantity': cart_item.quantity if not created else quantity
                    })
                
                elif op_type == 'update':
                    cart_item = CartItem.objects.get(cart=cart, product=product)
                    
                    if quantity > product.stock:
                        results.append({
                            'type': op_type,
                            'product_id': product_id,
                            'success': False,
                            'message': f'Insufficient stock. Available: {product.stock}'
                        })
                        continue
                    
                    cart_item.quantity = quantity
                    cart_item.save()
                    
                    results.append({
                        'type': op_type,
                        'product_id': product_id,
                        'success': True,
                        'message': 'Cart item updated',
                        'quantity': quantity
                    })
                
                elif op_type == 'remove':
                    CartItem.objects.filter(cart=cart, product=product).delete()
                    results.append({
                        'type': op_type,
                        'product_id': product_id,
                        'success': True,
                        'message': 'Item removed from cart'
                    })
                
                else:
                    results.append({
                        'type': op_type,
                        'product_id': product_id,
                        'success': False,
                        'message': 'Invalid operation type'
                    })
            
            except Product.DoesNotExist:
                results.append({
                    'type': op_type,
                    'product_id': product_id,
                    'success': False,
                    'message': 'Product not found'
                })
            except CartItem.DoesNotExist:
                results.append({
                    'type': op_type,
                    'product_id': product_id,
                    'success': False,
                    'message': 'Cart item not found'
                })
        
        return Response({
            'success': True,
            'message': 'Bulk cart operations completed',
            'data': {
                'results': results,
                'cart_summary': CartSerializer(cart, context={'request': request}).data
            }
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Bulk cart operations failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsBuyer])
def optimized_checkout(request):
    """Optimized checkout - creates pending order immediately, then initiates payment"""
    logger.info(f"Optimized checkout initiated by user {request.user.email}")
    
    try:
        cart_items_data = request.data.get('cart_items', [])
        delivery_data = request.data.get('delivery_info', {})
        
        if not cart_items_data:
            return Response({'success': False, 'message': 'No items provided for checkout'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required delivery fields
        required_fields = ['delivery_address', 'delivery_phone']
        for field in required_fields:
            if not delivery_data.get(field):
                return Response({'success': False, 'message': f'{field.replace("_", " ").title()} is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate items and calculate total
        total_amount = 0
        validated_items = []
        for item_data in cart_items_data:
            product = Product.objects.get(id=item_data['product_id'], is_active=True)
            quantity = int(item_data['quantity'])
            
            if product.stock < quantity:
                return Response({'success': False, 'message': f'Insufficient stock for {product.name}. Available: {product.stock}'}, status=status.HTTP_400_BAD_REQUEST)
            
            subtotal = product.price * quantity
            total_amount += subtotal
            validated_items.append({
                'product': product, 
                'quantity': quantity, 
                'price': product.price, 
                'subtotal': subtotal
            })
        
        # Check minimum amount
        min_amount = 100
        if total_amount < min_amount:
            return Response({'success': False, 'message': f'Order amount is below minimum required for payment. Minimum amount is {min_amount} XAF.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create pending order immediately with all data
        with db_transaction.atomic():
            order = Order.objects.create(
                buyer=request.user,
                total_amount=total_amount,
                status='pending_payment',  # New status for orders awaiting payment
                payment_status='pending',
                delivery_address=delivery_data.get('delivery_address'),
                delivery_phone=delivery_data.get('delivery_phone'),
                delivery_city=delivery_data.get('delivery_city', ''),
                delivery_state=delivery_data.get('delivery_state', ''),
                delivery_postal_code=delivery_data.get('delivery_postal_code', ''),
                delivery_notes=delivery_data.get('delivery_notes', '')
            )
            
            # Create OrderItems immediately
            for item in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    seller=item['product'].seller,
                    quantity=item['quantity'],
                    price=item['price'],
                    subtotal=item['subtotal']
                )
                logger.info(f"Created OrderItem for product {item['product'].name}, quantity {item['quantity']}")
            
            logger.info(f"Created pending order {order.id} with {order.items.count()} items")
        
        # Initiate payment linked to order
        payment_service = FapshiPaymentService.get_payment_service()
        result = payment_service.initiate_payment_link(
            amount=int(total_amount),
            email=request.user.email,
            user_id=str(request.user.id),
            external_id=str(order.id),  # Use order ID as external_id
            message=f'Payment for order {order.id}',
            phone=delivery_data.get('delivery_phone')
        )
        
        if result.get('link'):
            # Create payment record linked to order
            payment = Payment.objects.create(
                trans_id=result.get('transId'),
                status='created',
                amount=total_amount,
                email=request.user.email,
                payment_link=result.get('link'),
                external_id=str(order.id),
                message=result.get('message'),
                date_initiated=result.get('dateInitiated'),
                order=order  # Link payment to order immediately
            )
            
            return Response({
                'success': True,
                'message': 'Order created and payment initiated successfully',
                'data': {
                    'order_id': order.id,  # Real order ID now
                    'checkout_id': str(order.id),
                    'total_amount': str(total_amount),
                    'payment_link': result.get('link'),
                    'trans_id': result.get('transId'),
                    'items_count': len(validated_items),
                    'status': 'pending_payment'
                }
            }, status=status.HTTP_201_CREATED)
        else:
            # If payment fails, delete the pending order
            order.delete()
            return Response({
                'success': False,
                'message': result.get('message', 'Payment initiation failed'),
                'error': result.get('error', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Optimized checkout failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Checkout failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsBuyer])
def checkout(request):
    """Process checkout - initiate payment first, create order after payment"""
    logger.info(f"Checkout initiated by user {request.user.email}")
    
    try:
        # Get user's cart
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            return Response({
                'success': False,
                'message': 'Your cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate delivery information
        delivery_data = request.data.get('delivery_info', {})
        logger.info(f"Received delivery data: {delivery_data}")
        logger.info(f"Full request data: {request.data}")
        
        # Fallback: check if delivery info is sent directly in request body
        if not delivery_data:
            # Check if delivery fields are directly in request data
            direct_fields = ['delivery_address', 'delivery_phone', 'delivery_city', 'delivery_state', 'delivery_postal_code', 'delivery_notes']
            if any(field in request.data for field in direct_fields):
                delivery_data = {field: request.data.get(field) for field in direct_fields if field in request.data}
                logger.info(f"Using direct delivery data: {delivery_data}")
        
        required_fields = ['delivery_address', 'delivery_phone']
        
        for field in required_fields:
            if not delivery_data.get(field):
                logger.error(f"Missing field: {field}")
                return Response({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required',
                    'debug': {
                        'received_data': delivery_data,
                        'missing_field': field,
                        'full_request_data': request.data
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total amount
        total_amount = cart.total_amount
        
        # Check minimum amount requirement (100 XAF)
        min_amount = 100
        if total_amount < min_amount:
            logger.error(f"Cart total {total_amount} is below minimum {min_amount} XAF")
            return Response({
                'success': False,
                'message': f'Order amount is below minimum required for payment. Minimum amount is {min_amount} XAF.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store checkout data in session for later use after payment
        checkout_data = {
            'delivery_info': delivery_data,
            'total_amount': str(total_amount),
            'cart_items': []
        }
        
        # Store cart items data in session
        for cart_item in cart_items:
            checkout_data['cart_items'].append({
                'product_id': cart_item.product.id,
                'seller_id': cart_item.product.seller.id,
                'quantity': cart_item.quantity,
                'price': str(cart_item.product.price),
                'subtotal': str(cart_item.subtotal)
            })
        
        # Generate a unique checkout ID
        import uuid
        checkout_id = str(uuid.uuid4())
        request.session[f'checkout_{checkout_id}'] = checkout_data
        
        # Create a temporary payment record without order
        payment_service = FapshiPaymentService.get_payment_service()
        
        # Initiate payment
        result = payment_service.initiate_payment_link(
            amount=int(total_amount),
            email=request.user.email,
            user_id=str(request.user.id),
            external_id=checkout_id,
            message=f'Payment for checkout {checkout_id}',
            phone=delivery_data.get('delivery_phone')
        )
        
        if result.get('link'):  # Check if payment link was generated
            logger.info(f"Payment initiated for checkout {checkout_id}")
            
            # Create payment record
            payment = Payment.objects.create(
                trans_id=result.get('transId'),
                payment_type='initiate_pay',
                status='pending',
                amount=total_amount,
                email=request.user.email,
                payment_link=result.get('link'),
                external_id=checkout_id,
                message=result.get('message'),
                date_initiated=result.get('dateInitiated')
            )
            
            return Response({
                'success': True,
                'message': 'Payment initiated successfully',
                'data': {
                    'order_id': f'pending_{checkout_id}',  # Temporary ID for frontend compatibility
                    'checkout_id': checkout_id,
                    'total_amount': str(total_amount),
                    'payment_link': result.get('link'),
                    'trans_id': result.get('transId'),
                    'payment_id': payment.id,
                    'next_step': 'Complete payment using the provided link',
                    'note': 'Order will be created after successful payment'
                }
            }, status=status.HTTP_201_CREATED)
        else:
            # Clean up session data
            if f'checkout_{checkout_id}' in request.session:
                del request.session[f'checkout_{checkout_id}']
            
            logger.error(f"Payment initiation failed for checkout {checkout_id}: {result}")
            return Response({
                'success': False,
                'message': result.get('message', 'Payment initiation failed'),
                'error': result.get('error'),
                'debug_info': result
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Cart.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cart not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Checkout failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Checkout failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_webhook(request):
    """Test endpoint to simulate webhook payment success"""
    try:
        # Get the most recent pending payment
        payment = Payment.objects.filter(status='pending').first()
        
        if not payment:
            return Response({
                'success': False,
                'message': 'No pending payments found. Please complete a checkout first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"Testing webhook for payment {payment.id}")
        
        # Create order directly (same logic that works in shell)
        user = User.objects.get(email=payment.email)
        checkout_id = payment.external_id
        
        with db_transaction.atomic():
            order = Order.objects.create(
                buyer=user,
                total_amount=payment.amount,
                status='pending',
                payment_status='paid',
                delivery_address='Test order from webhook',
                delivery_phone='Test phone',
                delivery_city='',
                delivery_state='',
                delivery_postal_code='',
                delivery_notes=f'Test order from payment {payment.id}. Checkout ID: {checkout_id}'
            )
            
            # Link payment to order
            payment.order = order
            payment.status = 'paid'  # Set to 'paid' to match orders filter
            from django.utils import timezone
            payment.date_confirmed = timezone.now()
            payment.save()
            
            # Create OrderItems from cart if available
            try:
                cart = Cart.objects.get(user=user)
                cart_items = cart.items.all()
                
                # Create OrderItems from cart items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        seller=cart_item.product.seller,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        subtotal=cart_item.subtotal
                    )
                    logger.info(f"TEST: Created OrderItem for product {cart_item.product.name}, quantity {cart_item.quantity}")
                
                # Clear cart items
                cart.items.all().delete()
                logger.info(f"TEST: Cart cleared for user {user.email}")
                
            except Cart.DoesNotExist:
                logger.warning(f"TEST: No cart found for user {user.email}")
            
            logger.info(f"TEST: Order {order.id} created successfully from payment {payment.id}")
            logger.info(f"TEST: Created {order.items.count()} order items for order {order.id}")
            
            # Update seller wallets for successful payment
            payment_service = FapshiPaymentService.get_payment_service()
            payment_service._update_seller_wallets(order)
            logger.info(f"TEST: Updated seller wallets for order {order.id}")
        
        return Response({
            'success': True,
            'message': 'Test webhook processed successfully',
            'order_id': order.id,
            'payment_id': payment.id,
            'order_details': {
                'id': order.id,
                'total_amount': str(order.total_amount),
                'status': order.status,
                'payment_status': order.payment_status
            }
        })
    
    except Exception as e:
        logger.error(f"Test webhook failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': 'Test webhook failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_payment_service(request):
    """Debug endpoint to test payment service configuration"""
    try:
        payment_service = FapshiPaymentService.get_payment_service()
        
        debug_info = {
            'service_initialized': True,
            'service_type': payment_service.service_type,
            'base_url': payment_service.base_url,
            'api_key_set': bool(payment_service.api_key),
            'api_user_set': bool(payment_service.api_user),
            'headers_set': bool(payment_service.headers),
            'environment_variables': {
                'FAPSHI_PAYMENT_API_KEY': bool(os.environ.get('FAPSHI_PAYMENT_API_KEY')),
                'FAPSHI_PAYMENT_API_USER': bool(os.environ.get('FAPSHI_PAYMENT_API_USER')),
                'FAPSHI_PAYOUT_API_KEY': bool(os.environ.get('FAPSHI_PAYOUT_API_KEY')),
                'FAPSHI_PAYOUT_API_USER': bool(os.environ.get('FAPSHI_PAYOUT_API_USER')),
                'FAPSHI_BASE_URL': os.environ.get('FAPSHI_BASE_URL'),
                'PAYMENT_REDIRECT_URL': os.environ.get('PAYMENT_REDIRECT_URL'),
            }
        }
        
        logger.info(f"Payment service debug info: {debug_info}")
        
        return Response({
            'success': True,
            'message': 'Payment service debug information',
            'data': debug_info
        })
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Debug endpoint failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsBuyer])
def initiate_payment(request, order_id):
    """Initiate payment for an order"""
    logger.info(f"Payment initiation requested for order {order_id} by user {request.user.email}")
    
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        logger.info(f"Order found: {order.id}, total amount: {order.total_amount}")
        
        # Check if payment already exists
        if hasattr(order, 'payment'):
            logger.warning(f"Payment already exists for order {order_id}")
            payment = order.payment
            return Response({
                'success': False,
                'message': 'Payment already initiated for this order',
                'data': {
                    'payment_id': payment.id,
                    'payment_status': payment.status,
                    'payment_link': payment.payment_link,
                    'trans_id': payment.trans_id,
                    'suggestion': 'Use the retry endpoint if payment failed or expired'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if order is in correct status
        if order.payment_status != 'pending':
            logger.error(f"Order {order_id} has invalid payment status: {order.payment_status}")
            return Response({
                'success': False,
                'message': f'Cannot initiate payment. Order payment status: {order.payment_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check minimum amount requirement (100 XAF)
        min_amount = 100
        if order.total_amount < min_amount:
            logger.error(f"Order {order_id} amount {order.total_amount} is below minimum {min_amount} XAF")
            return Response({
                'success': False,
                'message': f'Order amount is below minimum required for payment. Minimum amount is {min_amount} XAF.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate payment data
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Payment data validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Invalid payment data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_data = serializer.validated_data
        logger.info(f"Payment data validated: {payment_data}")
        
        payment_service = FapshiPaymentService.get_payment_service()
        
        # Create payment and initiate transaction
        result = payment_service.create_payment_for_order(
            order=order,
            payment_type=payment_data['payment_type']
        )
        
        logger.info(f"Payment creation result: {result}")
        
        if result['success']:
            payment_serializer = PaymentSerializer(order.payment, context={'request': request})
            logger.info(f"Payment initiated successfully for order {order_id}")
            return Response({
                'success': True,
                'message': 'Payment initiated successfully',
                'data': {
                    'payment': payment_serializer.data,
                    'payment_link': result.get('payment_link'),
                    'trans_id': result.get('trans_id')
                }
            })
        else:
            logger.error(f"Payment initiation failed for order {order_id}: {result}")
            return Response({
                'success': False,
                'message': result.get('message', 'Payment initiation failed'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for user {request.user.email}")
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Unexpected error in payment initiation: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return Response({
            'success': False,
            'message': 'Payment initiation failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsSeller])
def mark_order_delivered(request, order_id):
    """Mark an order as delivered (seller only)"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Check if this seller has items in this order
        has_items = order.items.filter(seller=request.user).exists()
        if not has_items:
            return Response({
                'success': False,
                'message': 'You can only mark orders that contain your products as delivered'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if order is in the correct status
        if order.status not in ['pending', 'processing', 'shipped']:
            return Response({
                'success': False,
                'message': f'Cannot mark order as delivered. Current status: {order.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order status and delivery time
        from django.utils import timezone
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        
        serializer = OrderSerializer(order, context={'request': request})
        return Response({
            'success': True,
            'message': 'Order marked as delivered successfully',
            'data': serializer.data
        })
        
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsSeller])
def update_order_status(request, order_id):
    """Update order status for seller's items only"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Check if this seller has items in this order
        seller_items = order.items.filter(seller=request.user)
        if not seller_items.exists():
            return Response({
                'success': False,
                'message': 'You can only update status for orders that contain your products'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get new status from request
        new_status = request.data.get('status')
        if not new_status:
            return Response({
                'success': False,
                'message': 'Status field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered']
        if new_status not in valid_statuses:
            return Response({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update only the seller's items status
        from django.utils import timezone
        update_data = {'status': new_status}
        if new_status == 'delivered':
            update_data['delivered_at'] = timezone.now()
        
        # Allow sellers to update their own items (remove the delivered protection)
        updated_count = seller_items.update(**update_data)
        logger.info(f'SELLER ITEM UPDATE: User {request.user.email} updated {updated_count} items to {new_status} in order {order.id}')
        
        # Intelligently update overall order status based on ALL item statuses
        all_items = order.items.all()
        all_items_count = all_items.count()
        
        # Count items by status
        status_counts = {}
        for status_choice in ['pending', 'processing', 'shipped', 'delivered']:
            status_counts[status_choice] = all_items.filter(status=status_choice).count()
        
        # Get current order status before update
        old_order_status = order.status
        
        # Determine overall order status based on item statuses
        new_order_status = None
        if status_counts['delivered'] == all_items_count:
            # All items delivered
            new_order_status = 'delivered'
        elif status_counts['pending'] == 0 and (status_counts['shipped'] > 0 or status_counts['processing'] > 0):
            # NO pending items, but some are shipped or processing
            if status_counts['delivered'] == 0 and status_counts['shipped'] > 0:
                # All items are shipped (no delivered, no pending)
                new_order_status = 'shipped'
            elif status_counts['delivered'] > 0 and status_counts['shipped'] > 0:
                # Mix of shipped and delivered (no pending)
                new_order_status = 'shipped'
            elif status_counts['processing'] > 0 and status_counts['delivered'] == 0 and status_counts['shipped'] == 0:
                # All items are processing (no pending, no shipped, no delivered)
                new_order_status = 'processing'
        elif status_counts['pending'] > 0:
            # There are pending items - order cannot be shipped or delivered
            # Force order status to processing if there are pending items
            if order.status in ['shipped', 'delivered']:
                # Downgrade from shipped/delivered because there are pending items
                new_order_status = 'processing' if status_counts['processing'] > 0 else 'pending'
            else:
                new_order_status = 'processing' if status_counts['processing'] > 0 else 'pending'
        else:
            # All items are pending
            if order.status not in ['shipped', 'delivered']:  # Don't downgrade from shipped/delivered
                new_order_status = 'pending'
        
        # Only update order status if it actually needs to change
        if new_order_status and new_order_status != old_order_status:
            logger.info(f'ORDER STATUS UPDATE: Order {order.id} - {old_order_status} -> {new_order_status}')
            logger.info(f'ORDER STATUS REASON: Item counts - {status_counts}')
            order.status = new_order_status
            if new_order_status == 'delivered':
                order.delivered_at = timezone.now()
            order.save()
            logger.info(f'ORDER STATUS UPDATED: Order {order.id} now has status {order.status}')
        else:
            logger.info(f'ORDER STATUS UNCHANGED: Order {order.id} remains {order.status} (no change needed)')
        
        # Return updated seller items
        updated_items = order.items.filter(seller=request.user)
        serializer = OrderItemSerializer(updated_items, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'message': f'Your items status updated to {new_status} successfully',
            'data': {
                'items': serializer.data,
                'updated_count': updated_count,
                'order_status': order.status,
                'order_progress': {
                    'total_items': all_items_count,
                    'pending': status_counts['pending'],
                    'processing': status_counts['processing'],
                    'shipped': status_counts['shipped'],
                    'delivered': status_counts['delivered'],
                    'delivered_text': f'{status_counts["delivered"]}/{all_items_count} items delivered'
                }
            }
        })
        
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_orders(request):
    """View all orders that contain seller's products"""
    # Get all order items that belong to this seller with optimized queries
    seller_order_items = OrderItem.objects.filter(
        seller=request.user
    ).select_related(
        'order__buyer'
    ).prefetch_related(
        'order__items'
    ).order_by('-order__created_at')
    
    # Group by order to avoid duplicates
    order_ids = seller_order_items.values_list('order_id', flat=True).distinct()
    
    # Add pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    orders = Order.objects.filter(
        id__in=order_ids,
        payment_status='paid'  # Only show paid orders for sellers
    ).select_related(
        'buyer'
    ).prefetch_related(
        'items__product'
    ).order_by('-created_at')
    
    # Manual pagination
    total_count = orders.count()
    start = (page - 1) * per_page
    end = start + per_page
    orders_page = orders[start:end]
    
    serializer = SellerOrderSerializer(orders_page, many=True, context={'request': request})
    return Response({
        'success': True,
        'message': 'Seller orders retrieved successfully',
        'data': {
            'orders': serializer.data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        }
    })


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_order_items(request, order_id):
    """Get specific order items that belong to this seller for a given order"""
    try:
        # Get the order and verify it contains items from this seller
        order = Order.objects.get(id=order_id)
        
        # Get only the order items that belong to this seller
        seller_items = OrderItem.objects.filter(
            order=order,
            seller=request.user
        ).select_related('product')
        
        if not seller_items.exists():
            return Response({
                'success': False,
                'message': 'No items found for this seller in this order'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the order items
        serializer = OrderItemSerializer(seller_items, many=True, context={'request': request})
        
        # Calculate seller's total amount (only their items)
        seller_total = seller_items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
        
        # Get order details for context
        order_data = {
            'id': order.id,
            'buyer_name': order.buyer.name,
            'buyer_email': order.buyer.email,
            'status': order.status,
            'payment_status': order.payment_status,
            'total_amount': str(seller_total),  # Only seller's items total
            'full_order_total': str(order.total_amount),  # Full order total for reference
            'delivery_address': order.delivery_address,
            'delivery_city': order.delivery_city,
            'delivery_state': order.delivery_state,
            'delivery_phone': order.delivery_phone,
            'created_at': order.created_at,
            'updated_at': order.updated_at
        }
        
        return Response({
            'success': True,
            'message': 'Seller order items retrieved successfully',
            'data': {
                'order': order_data,
                'items': serializer.data,
                'items_count': seller_items.count(),
                'seller_total': str(sum(item.subtotal for item in seller_items))
            }
        })
        
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching seller order items: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while fetching order items'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsBuyer])
def my_orders(request):
    """Get buyer's orders with order items included"""
    orders = Order.objects.filter(
        buyer=request.user,
        payment_status='paid'  # Only show paid orders in buyer dashboard
    ).prefetch_related('items__product', 'items__seller').order_by('-created_at')
    
    # Include order items in response
    orders_data = []
    for order in orders:
        order_items = []
        for item in order.items.all():
            order_items.append({
                'id': item.id,
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'description': item.product.description,
                    'price': str(item.product.price),
                    'image_url': item.product.image.url if item.product.image else None
                },
                'seller': {
                    'id': item.seller.id,
                    'name': item.seller.name,
                    'email': item.seller.email
                },
                'quantity': item.quantity,
                'price': str(item.price),
                'subtotal': str(item.subtotal),
                'status': item.status,
                'delivered_at': item.delivered_at.isoformat() if item.delivered_at else None
            })
        
        orders_data.append({
            'id': order.id,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status,
            'delivery_address': order.delivery_address,
            'delivery_phone': order.delivery_phone,
            'delivery_city': order.delivery_city,
            'delivery_state': order.delivery_state,
            'delivery_postal_code': order.delivery_postal_code,
            'delivery_notes': order.delivery_notes,
            'items': order_items,
            'items_count': order.items.count(),
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat()
        })
    
    return Response({
        'success': True,
        'message': 'Orders retrieved successfully',
        'data': orders_data
    })


# Profile Views (Buyer and Seller)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get or update user profile"""
    user = request.user
    
    if request.method == 'GET':
        serializer = ProfileSerializer(user, context={'request': request})
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': serializer.data
        })
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProfileSerializer(user, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'message': 'Profile update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def seller_profile(request, user_id):
    """Get public seller profile information"""
    try:
        seller = User.objects.get(id=user_id, role='seller')
        serializer = ProfileSerializer(seller, context={'request': request})
        return Response({
            'success': True,
            'message': 'Seller profile retrieved successfully',
            'data': serializer.data
        })
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Seller not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not old_password or not new_password or not confirm_password:
        return Response({
            'success': False,
            'message': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(old_password):
        return Response({
            'success': False,
            'message': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({
            'success': False,
            'message': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    """Webhook endpoint for Fapshi payment status updates"""
    try:
        # Get transaction data from webhook
        webhook_data = request.data
        
        if not isinstance(webhook_data, list):
            webhook_data = [webhook_data]
        
        payment_service = FapshiPaymentService.get_payment_service()
        results = []
        
        for transaction_data in webhook_data:
            trans_id = transaction_data.get('transId')
            if not trans_id:
                logger.warning(f"No transId in webhook data: {transaction_data}")
                continue
            
            logger.info(f"Processing webhook for transaction: {trans_id}")
            
            # Update payment status
            result = payment_service.update_payment_status(trans_id)
            results.append(result)
            
            # If payment is successful, create order and process completion
            if result.get('success') and result.get('new_status') == 'successful':
                try:
                    payment = Payment.objects.get(trans_id=trans_id)
                    checkout_id = payment.external_id
                    
                    if not checkout_id:
                        logger.error(f"Payment {payment.id} has no checkout_id")
                        continue
                    
                    # Get user from payment email
                    try:
                        user = User.objects.get(email=payment.email)
                        
                        # Check if payment already has an order (should exist with new flow)
                        if payment.order:
                            order = payment.order
                            logger.info(f"Found existing order {order.id} for payment {payment.id}")
                            
                            # Update order status from pending_payment to processing
                            if order.status == 'pending_payment':
                                order.status = 'processing'
                                order.payment_status = 'paid'
                                order.save()
                                logger.info(f"Updated order {order.id} status to processing")
                            else:
                                logger.info(f"Order {order.id} already has status {order.status}")
                            
                            # Update payment status
                            payment.status = 'paid'
                            if 'dateConfirmed' in result:
                                payment.date_confirmed = datetime.fromisoformat(result['dateConfirmed'].replace('Z', '+00:00'))
                            payment.save()
                            
                            logger.info(f"Payment {payment.id} marked as paid for order {order.id}")
                        
                        else:
                            # Fallback for old orders without order link
                            logger.warning(f"Payment {payment.id} has no order - creating new order (legacy flow)")
                            checkout_id = payment.external_id
                            
                            with db_transaction.atomic():
                                order = Order.objects.create(
                                    buyer=user,
                                    total_amount=payment.amount,
                                    status='processing',
                                    payment_status='paid',
                                    delivery_address='Payment completed - Contact support for delivery details',
                                    delivery_phone='Payment completed',
                                    delivery_city='',
                                    delivery_state='',
                                    delivery_postal_code='',
                                    delivery_notes=f'Order created from payment {payment.id}. Checkout ID: {checkout_id}'
                                )
                                
                                # Link payment to order
                                payment.order = order
                                payment.status = 'paid'
                                if 'dateConfirmed' in result:
                                    payment.date_confirmed = datetime.fromisoformat(result['dateConfirmed'].replace('Z', '+00:00'))
                                payment.save()
                                
                                # Try to create OrderItems from cart (legacy flow)
                                try:
                                    cart = Cart.objects.get(user=user)
                                    cart_items = cart.items.all()
                                    
                                    for cart_item in cart_items:
                                        OrderItem.objects.create(
                                            order=order,
                                            product=cart_item.product,
                                            seller=cart_item.product.seller,
                                            quantity=cart_item.quantity,
                                            price=cart_item.product.price,
                                            subtotal=cart_item.subtotal
                                        )
                                        logger.info(f"Created OrderItem for product {cart_item.product.name}, quantity {cart_item.quantity}")
                                    
                                    cart.items.all().delete()
                                    logger.info(f"Cart cleared for user {user.email}")
                                except Cart.DoesNotExist:
                                    logger.warning(f"No cart found for user {user.email}")
                                
                                logger.info(f"Created fallback order {order.id} for payment {payment.id}")
                    
                    except User.DoesNotExist:
                        logger.error(f"User with email {payment.email} not found for payment {payment.id}")
                        continue
                
                except Payment.DoesNotExist:
                    logger.error(f"Payment {trans_id} not found")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing payment: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
        
        return Response({
            'success': True,
            'message': 'Webhook processed successfully',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': 'Webhook processing failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsBuyer])
def check_payment_status(request, order_id):
    """Check payment status for an order"""
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        
        if not hasattr(order, 'payment'):
            return Response({
                'success': False,
                'message': 'No payment found for this order'
            }, status=status.HTTP_404_NOT_FOUND)
        
        payment = order.payment
        payment_service = FapshiPaymentService.get_payment_service()
        
        # Update payment status from Fapshi
        if payment.trans_id:
            result = payment_service.update_payment_status(payment.trans_id)
            payment.refresh_from_db()
        
        payment_serializer = PaymentSerializer(payment, context={'request': request})
        return Response({
            'success': True,
            'message': 'Payment status retrieved successfully',
            'data': payment_serializer.data
        })
    
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to check payment status',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsBuyer])
def retry_payment(request, order_id):
    """Retry payment for a failed order"""
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        
        if not hasattr(order, 'payment'):
            return Response({
                'success': False,
                'message': 'No payment found for this order'
            }, status=status.HTTP_404_NOT_FOUND)
        
        payment = order.payment
        
        # Check if payment can be retried
        if payment.status not in ['failed', 'expired']:
            return Response({
                'success': False,
                'message': f'Cannot retry payment. Current status: {payment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate payment data
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid payment data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_data = serializer.validated_data
        payment_service = FapshiPaymentService.get_payment_service()
        
        # Reset payment status
        payment.status = 'pending'
        payment.trans_id = None
        payment.payment_link = None
        payment.date_initiated = None
        payment.date_confirmed = None
        payment.save()
        
        # Retry payment
        result = payment_service.create_payment_for_order(
            order=order,
            payment_type=payment_data['payment_type']
        )
        
        if result['success']:
            payment_serializer = PaymentSerializer(order.payment, context={'request': request})
            return Response({
                'success': True,
                'message': 'Payment retry initiated successfully',
                'data': {
                    'payment': payment_serializer.data,
                    'payment_link': result.get('payment_link'),
                    'trans_id': result.get('trans_id')
                }
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Payment retry failed'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Payment retry failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_payments(request):
    """Get all payments for the current user"""
    try:
        if request.user.is_buyer:
            payments = Payment.objects.filter(order__buyer=request.user).order_by('-created_at')
        elif request.user.is_seller:
            # Get payments for orders containing seller's products
            payments = Payment.objects.filter(
                order__items__seller=request.user
            ).distinct().order_by('-created_at')
        else:
            payments = Payment.objects.none()
        
        serializer = PaymentSerializer(payments, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': 'Payments retrieved successfully',
            'data': serializer.data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to retrieve payments',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_payments(request):
    """Get all payments (admin only)"""
    try:
        payments = Payment.objects.all().order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': 'All payments retrieved successfully',
            'data': serializer.data
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to retrieve payments',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request):
    """Create a new report against a seller"""
    serializer = ReportSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(reporter=request.user)
        return Response({
            'success': True,
            'message': 'Report submitted successfully. Admin will review it.',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Failed to submit report',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_reports(request):
    """View all reports submitted by the current user"""
    reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
    serializer = ReportSerializer(reports, many=True, context={'request': request})
    return Response({
        'success': True,
        'message': 'Your reports retrieved successfully',
        'data': serializer.data
    })


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAdmin])
def manage_reports(request, report_id=None):
    """Admin endpoint to manage reports"""
    if report_id:
        # Handle specific report
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Report not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = ReportSerializer(report, context={'request': request})
            return Response({
                'success': True,
                'message': 'Report retrieved successfully',
                'data': serializer.data
            })
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = ReportSerializer(report, data=request.data, partial=request.method == 'PATCH', context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Report updated successfully',
                    'data': serializer.data
                })
            return Response({
                'success': False,
                'message': 'Failed to update report',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        # Handle list of reports
        if request.method == 'GET':
            status_filter = request.query_params.get('status', None)
            reports = Report.objects.all()
            
            if status_filter:
                reports = reports.filter(status=status_filter)
            
            serializer = ReportSerializer(reports, many=True, context={'request': request})
            return Response({
                'success': True,
                'message': 'Reports retrieved successfully',
                'data': serializer.data
            })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_payment_status_manual(request):
    """Manually check payment status and create order if successful"""
    try:
        trans_id = request.data.get('trans_id')
        
        if not trans_id:
            return Response({
                'success': False,
                'message': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payment
        payment = Payment.objects.get(trans_id=trans_id)
        
        # Check if payment already has an order
        if payment.order:
            return Response({
                'success': True,
                'message': 'Order already exists for this payment',
                'order_id': payment.order.id,
                'payment_status': payment.status
            })
        
        # Check payment status with Fapshi
        payment_service = FapshiPaymentService.get_payment_service()
        
        # Use check_payment_status instead of update_payment_status to avoid model issues
        status_result = payment_service.check_payment_status(trans_id)
        
        if 'error' not in status_result and status_result.get('status', '').upper() == 'SUCCESSFUL':
            # Create order (same logic as webhook)
            user = User.objects.get(email=payment.email)
            checkout_id = payment.external_id
            
            with db_transaction.atomic():
                order = Order.objects.create(
                    buyer=user,
                    total_amount=payment.amount,
                    status='pending',
                    payment_status='paid',
                    delivery_address='Payment completed - Contact support for delivery details',
                    delivery_phone='Payment completed',
                    delivery_city='',
                    delivery_state='',
                    delivery_postal_code='',
                    delivery_notes=f'Order created from payment {payment.id}. Checkout ID: {checkout_id}'
                )
                
                # Link payment to order
                payment.order = order
                payment.status = 'paid'
                from django.utils import timezone
                payment.date_confirmed = timezone.now()
                payment.save()
                
                # Clear user's cart after successful payment
                try:
                    cart = Cart.objects.get(user=user)
                    cart_items = cart.items.all()
                    
                    # Create OrderItems from cart items
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            seller=cart_item.product.seller,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price,
                            subtotal=cart_item.subtotal
                        )
                        logger.info(f"MANUAL CHECK: Created OrderItem for product {cart_item.product.name}, quantity {cart_item.quantity}")
                    
                    # Clear cart items
                    cart.items.all().delete()
                    logger.info(f"MANUAL CHECK: Cart cleared for user {user.email} after successful payment")
                    
                except Cart.DoesNotExist:
                    logger.warning(f"MANUAL CHECK: No cart found for user {user.email} to clear")
                
                logger.info(f"MANUAL CHECK: Order {order.id} created successfully from payment {payment.id}")
                logger.info(f"MANUAL CHECK: Created {order.items.count()} order items for order {order.id}")
                
                # Update seller wallets for successful payment
                payment_service._update_seller_wallets(order)
                logger.info(f"MANUAL CHECK: Updated seller wallets for order {order.id}")
            
            return Response({
                'success': True,
                'message': 'Payment status checked and order created',
                'order_id': order.id,
                'payment_status': 'paid'
            })
        else:
            return Response({
                'success': False,
                'message': 'Payment not yet successful',
                'current_status': status_result.get('status', 'unknown'),
                'result': status_result
            })
    
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Manual payment status check failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Manual payment status check failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Withdrawal Views
@api_view(['POST'])
@permission_classes([IsSeller])
def create_withdrawal_request(request):
    """Create a new withdrawal request"""
    try:
        amount = Decimal(request.data.get('amount'))
        
        if amount <= 0:
            return Response({
                'success': False,
                'message': 'Amount must be greater than 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get seller's wallet
        try:
            wallet = Wallet.objects.get(seller=request.user)
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check sufficient balance
        if amount > wallet.balance:
            return Response({
                'success': False,
                'message': f'Insufficient balance. Available: ${wallet.balance}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for pending withdrawal requests
        pending_requests = WithdrawalRequest.objects.filter(
            seller=request.user,
            status='pending'
        ).exists()
        
        if pending_requests:
            return Response({
                'success': False,
                'message': 'You already have a pending withdrawal request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get seller's phone number for display
        seller_phone = request.user.phone_number
        
        # Create withdrawal request
        withdrawal_request = WithdrawalRequest.objects.create(
            seller=request.user,
            amount=amount,
            status='pending'
        )
        
        serializer = WithdrawalRequestSerializer(withdrawal_request, context={'request': request})
        
        return Response({
            'success': True,
            'message': f'Withdrawal request created successfully. You will receive the money at: {seller_phone or "No phone number in profile"}. If you want to change it, please update your profile.',
            'data': {
                **serializer.data,
                'payout_phone': seller_phone,
                'phone_message': f'Money will be sent to: {seller_phone or "No phone number in profile"}. Update your profile to change the phone number.'
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Create withdrawal request failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create withdrawal request',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_withdrawal_history(request):
    """Get seller's withdrawal request history"""
    try:
        withdrawal_requests = WithdrawalRequest.objects.filter(
            seller=request.user
        ).order_by('-created_at')
        
        serializer = WithdrawalRequestSerializer(withdrawal_requests, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Withdrawal history retrieved successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Get withdrawal history failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve withdrawal history',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin Withdrawal Management Views
class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = WithdrawalRequest.objects.all().select_related('seller', 'processed_by')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate statistics
        total_pending = queryset.filter(status='pending').count()
        total_approved = queryset.filter(status='approved').count()
        total_rejected = queryset.filter(status='rejected').count()
        total_processed = queryset.filter(status='processed').count()
        
        return Response({
            'success': True,
            'message': 'Withdrawal requests retrieved successfully',
            'data': {
                'withdrawal_requests': serializer.data,
                'statistics': {
                    'total_pending': total_pending,
                    'total_approved': total_approved,
                    'total_rejected': total_rejected,
                    'total_processed': total_processed
                }
            }
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a withdrawal request and process the withdrawal via Fapshi payout"""
        try:
            withdrawal_request = self.get_object()
            
            if withdrawal_request.status != 'pending':
                return Response({
                    'success': False,
                    'message': f'Cannot approve withdrawal request with status: {withdrawal_request.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get seller's wallet
            wallet = Wallet.objects.get(seller=withdrawal_request.seller)
            
            # Check if still has sufficient balance
            if withdrawal_request.amount > wallet.balance:
                return Response({
                    'success': False,
                    'message': f'Insufficient balance. Available: ${wallet.balance}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process withdrawal using Fapshi payout service
            payment_service = FapshiPaymentService.get_payout_service()
            payout_result = payment_service.process_withdrawal_payout(withdrawal_request)
            
            if payout_result.get('success'):
                # Update withdrawal request with admin info
                withdrawal_request.processed_by = request.user
                withdrawal_request.save()
                
                serializer = self.get_serializer(withdrawal_request)
                
                return Response({
                    'success': True,
                    'message': 'Withdrawal request approved and processed successfully via Fapshi',
                    'data': {
                        **serializer.data,
                        'payout_trans_id': payout_result.get('trans_id'),
                        'payout_date_initiated': payout_result.get('date_initiated'),
                        'payout_phone_used': payout_result.get('payout_phone')
                    }
                })
            else:
                # Payout failed, don't approve the request
                return Response({
                    'success': False,
                    'message': f'Withdrawal approval failed: {payout_result.get("message")}',
                    'error': payout_result.get('error'),
                    'withdrawal_id': payout_result.get('withdrawal_id')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Wallet.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Seller wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Approve withdrawal request failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to approve withdrawal request',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a withdrawal request"""
        withdrawal_request = self.get_object()
        
        if withdrawal_request.status != 'pending':
            return Response({
                'success': False,
                'message': f'Cannot reject withdrawal request with status: {withdrawal_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '')
        
        withdrawal_request.status = 'rejected'
        withdrawal_request.admin_notes = admin_notes
        withdrawal_request.processed_by = request.user
        withdrawal_request.processed_at = timezone.now()
        withdrawal_request.save()
        
        serializer = self.get_serializer(withdrawal_request)
        
        return Response({
            'success': True,
            'message': 'Withdrawal request rejected successfully',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_processed(self, request, pk=None):
        """Mark an approved withdrawal request as processed (for manual processing)"""
        withdrawal_request = self.get_object()
        
        if withdrawal_request.status != 'approved':
            return Response({
                'success': False,
                'message': f'Cannot mark as processed. Current status: {withdrawal_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '')
        
        with db_transaction.atomic():
            # Get seller's wallet
            wallet = Wallet.objects.get(seller=withdrawal_request.seller)
            
            # Check if still has sufficient balance
            if withdrawal_request.amount > wallet.balance:
                return Response({
                    'success': False,
                    'message': f'Insufficient balance. Available: ${wallet.balance}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Deduct from wallet
            wallet.balance -= withdrawal_request.amount
            wallet.save()
            
            # Create transaction record
            Transaction.objects.create(
                wallet=wallet,
                amount=withdrawal_request.amount,
                transaction_type='withdrawal',
                description=f'Withdrawal processed - Request #{withdrawal_request.id}'
            )
            
            # Update withdrawal request
            withdrawal_request.status = 'processed'
            withdrawal_request.admin_notes = admin_notes
            withdrawal_request.processed_by = request.user
            withdrawal_request.processed_at = timezone.now()
            withdrawal_request.save()
        
        serializer = self.get_serializer(withdrawal_request)
        
        return Response({
            'success': True,
            'message': 'Withdrawal request marked as processed successfully',
            'data': serializer.data
        })
