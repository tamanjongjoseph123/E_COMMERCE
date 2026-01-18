from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Sum
from django.db import transaction as db_transaction
from decimal import Decimal

from .models import (
    User, Seller, Category, Product, Cart, CartItem,
    Order, OrderItem, Wallet, Transaction, Report
)
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, SellerSerializer,
    CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, WalletSerializer, TransactionSerializer, ProfileSerializer,
    ReportSerializer
)


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
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    
    if not cart_items.exists():
        return Response({
            'success': False,
            'message': 'Cart is empty'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            return Response({
                'success': False,
                'message': f'Insufficient stock for {item.product.name}. Available: {item.product.stock}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with db_transaction.atomic():
            # Get delivery information from request
            delivery_data = request.data
            required_fields = ['delivery_address']
            
            # Validate required delivery fields
            for field in required_fields:
                if not delivery_data.get(field):
                    return Response({
                        'success': False,
                        'message': f'{field.replace("_", " ").title()} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create order with delivery information
            order = Order.objects.create(
                buyer=request.user,
                total_amount=cart.total_amount,
                status='pending',
                delivery_address=delivery_data.get('delivery_address'),
                delivery_city=delivery_data.get('delivery_city', ''),
                delivery_state=delivery_data.get('delivery_state', ''),
                delivery_postal_code=delivery_data.get('delivery_postal_code', ''),
                delivery_phone=delivery_data.get('delivery_phone', ''),
                delivery_notes=delivery_data.get('delivery_notes', '')
            )
            
            # Create order items and update wallets
            for cart_item in cart_items:
                # Create order item
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    seller=cart_item.product.seller,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    subtotal=cart_item.subtotal
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()
                
                # Update seller wallet
                wallet, _ = Wallet.objects.get_or_create(seller=cart_item.product.seller)
                wallet.balance += cart_item.subtotal
                wallet.save()
                
                # Create transaction
                Transaction.objects.create(
                    wallet=wallet,
                    order_item=order_item,
                    amount=cart_item.subtotal,
                    transaction_type='sale',
                    description=f'Sale of {cart_item.product.name}'
                )
            
            # Clear cart
            cart_items.delete()
            
            order_serializer = OrderSerializer(order, context={'request': request})
            return Response({
                'success': True,
                'message': 'Order placed successfully',
                'data': order_serializer.data
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Checkout failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


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
    """Update order status (seller only)"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Check if this seller has items in this order
        has_items = order.items.filter(seller=request.user).exists()
        if not has_items:
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
        
        # Update order status
        order.status = new_status
        if new_status == 'delivered':
            from django.utils import timezone
            order.delivered_at = timezone.now()
        order.save()
        
        serializer = OrderSerializer(order, context={'request': request})
        return Response({
            'success': True,
            'message': f'Order status updated to {new_status} successfully',
            'data': serializer.data
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
    # Get all order items that belong to this seller
    seller_order_items = OrderItem.objects.filter(seller=request.user).select_related('order').order_by('-order__created_at')
    
    # Group by order to avoid duplicates
    order_ids = seller_order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
    
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response({
        'success': True,
        'message': 'Seller orders retrieved successfully',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsBuyer])
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response({
        'success': True,
        'message': 'Orders retrieved successfully',
        'data': serializer.data
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
