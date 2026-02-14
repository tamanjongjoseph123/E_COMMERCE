from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    User, Seller, Category, Product, Cart, CartItem, 
    Order, OrderItem, Wallet, Transaction, Report, Payment, WithdrawalRequest
)


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'full_name', 'role', 'profile_picture', 'profile_picture_url', 'phone_number', 'address', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    seller_approval_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'full_name', 'role', 'profile_picture', 'profile_picture_url', 'phone_number', 'address', 'store_description', 'date_joined', 'last_login', 'seller_approval_status']
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_seller_approval_status(self, obj):
        if obj.role == 'seller':
            try:
                return obj.seller_profile.approval_status
            except Seller.DoesNotExist:
                return 'not_found'
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=['buyer', 'seller'], required=True)
    id_card = serializers.ImageField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'full_name', 'password', 'password2', 'role', 'id_card']
        extra_kwargs = {
            'name': {'required': True},
            'full_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if attrs['role'] == 'seller' and not attrs.get('id_card'):
            raise serializers.ValidationError({"id_card": "ID card is required for seller registration."})
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        password2 = validated_data.pop('password2')
        role = validated_data.pop('role')
        id_card = validated_data.pop('id_card', None)
        
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            name=validated_data['name'],
            full_name=validated_data['full_name'],
            role=role,
            password=password
        )
        
        if role == 'seller' and id_card:
            Seller.objects.create(
                user=user,
                id_card=id_card,
                approval_status='pending'
            )
            Wallet.objects.create(seller=user, balance=0.00)
        
        if role == 'buyer':
            Cart.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            
            # Check if seller is approved
            if user.role == 'seller':
                try:
                    seller_profile = user.seller_profile
                    if seller_profile.approval_status != 'approved':
                        raise serializers.ValidationError(
                            f"Your seller account is {seller_profile.approval_status}. Please wait for admin approval."
                        )
                except Seller.DoesNotExist:
                    raise serializers.ValidationError("Seller profile not found.")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include email and password.")
        
        return attrs


class SellerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    id_card_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Seller
        fields = ['id', 'user', 'id_card', 'id_card_url', 'approval_status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'id_card', 'created_at', 'updated_at']
    
    def get_id_card_url(self, obj):
        if obj.id_card:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.id_card.url)
            return obj.id_card.url
        return None


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'image_url', 'is_active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    seller_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='seller'), source='seller', write_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_id', 'category', 'category_id', 
            'name', 'description', 'price', 'stock', 'image', 'image_url',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source='product', write_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal', 'created_at']
        read_only_fields = ['id', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_amount', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_image', 'seller_name', 'quantity', 'price', 'subtotal', 'status', 'delivered_at']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    items_count = serializers.SerializerMethodField()
    payment_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer_name', 'buyer_email', 'items_count', 'total_amount', 'status', 'payment_status',
            'delivery_address', 'delivery_city', 'delivery_state', 
            'delivery_postal_code', 'delivery_phone', 'delivery_notes',
            'delivered_at', 'created_at', 'updated_at', 'payment_id'
        ]
        read_only_fields = ['id', 'delivered_at', 'created_at', 'updated_at', 'payment_id']
    
    def get_payment_id(self, obj):
        try:
            return obj.payment.id if hasattr(obj, 'payment') and obj.payment else None
        except Payment.DoesNotExist:
            return None
    
    def get_items_count(self, obj):
        # Use the prefetched items if available, otherwise count efficiently
        if hasattr(obj, '_prefetched_objects_cache') and 'items' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['items'])
        return obj.items.count()


class SellerOrderSerializer(serializers.ModelSerializer):
    """Custom serializer for seller orders that shows only seller's item totals and progress"""
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    items_count = serializers.SerializerMethodField()
    payment_id = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()  # Seller's total only
    full_order_total = serializers.ReadOnlyField(source='total_amount')  # Full order total
    status = serializers.SerializerMethodField()  # Seller's item status only
    seller_progress = serializers.SerializerMethodField()  # Seller's item progress only
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer_name', 'buyer_email', 'items_count', 'total_amount', 'full_order_total', 
            'status', 'payment_status', 'delivery_address', 'delivery_city', 'delivery_state', 
            'delivery_postal_code', 'delivery_phone', 'delivery_notes',
            'delivered_at', 'created_at', 'updated_at', 'payment_id', 'seller_progress'
        ]
        read_only_fields = ['id', 'delivered_at', 'created_at', 'updated_at', 'payment_id']
    
    def get_payment_id(self, obj):
        try:
            return obj.payment.id if hasattr(obj, 'payment') and obj.payment else None
        except Payment.DoesNotExist:
            return None
    
    def get_status(self, obj):
        """Get the status of this seller's items in the order"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_seller:
            if hasattr(obj, '_prefetched_objects_cache') and 'items' in obj._prefetched_objects_cache:
                seller_items = [item for item in obj._prefetched_objects_cache['items'] if item.seller == request.user]
                if seller_items:
                    # Return the status of the seller's items (they should all have the same status)
                    return seller_items[0].status
            else:
                seller_item = obj.items.filter(seller=request.user).first()
                if seller_item:
                    return seller_item.status
        return obj.status  # Fallback to overall order status
    
    def get_items_count(self, obj):
        # Count only this seller's items
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_seller:
            if hasattr(obj, '_prefetched_objects_cache') and 'items' in obj._prefetched_objects_cache:
                seller_items = [item for item in obj._prefetched_objects_cache['items'] if item.seller == request.user]
                return len(seller_items)
            else:
                return obj.items.filter(seller=request.user).count()
        return obj.items.count()
    
    def get_total_amount(self, obj):
        # Calculate only this seller's items total (this replaces seller_total_amount)
        from decimal import Decimal
        from django.db.models import Sum
        
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_seller:
            if hasattr(obj, '_prefetched_objects_cache') and 'items' in obj._prefetched_objects_cache:
                seller_items = [item for item in obj._prefetched_objects_cache['items'] if item.seller == request.user]
                if seller_items:
                    return sum(Decimal(str(item.subtotal)) for item in seller_items if item.subtotal)
                else:
                    return Decimal('0.00')
            else:
                seller_total = obj.items.filter(seller=request.user).aggregate(total=Sum('subtotal'))['total']
                return Decimal(str(seller_total)) if seller_total is not None else Decimal('0.00')
        return Decimal(str(obj.total_amount)) if obj.total_amount is not None else Decimal('0.00')
    
    def get_seller_progress(self, obj):
        """Get the status of this seller's items in the order"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_seller:
            if hasattr(obj, '_prefetched_objects_cache') and 'items' in obj._prefetched_objects_cache:
                seller_items = [item for item in obj._prefetched_objects_cache['items'] if item.seller == request.user]
                if seller_items:
                    # Return the status of the seller's items (they should all have the same status)
                    return seller_items[0].status
            else:
                seller_item = obj.items.filter(seller=request.user).first()
                if seller_item:
                    return seller_item.status
        return obj.status  # Fallback to overall order status


class TransactionSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'order_item', 'amount', 'transaction_type', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'seller', 'balance', 'transactions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order_id', 'trans_id', 'payment_type', 'status', 'amount',
            'phone', 'email', 'payment_link', 'external_id', 'message',
            'date_initiated', 'date_confirmed', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'trans_id', 'payment_link', 'date_initiated', 
            'date_confirmed', 'created_at', 'updated_at'
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(choices=['initiate_pay'], default='initiate_pay')
    
    def validate(self, attrs):
        # No validation needed since we only support payment links
        return attrs


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)
    payout_phone = serializers.CharField(read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'seller', 'amount', 'status', 'admin_notes', 
            'processed_at', 'processed_by', 'created_at', 'updated_at', 'payout_phone'
        ]
        read_only_fields = ['id', 'seller', 'processed_at', 'processed_by', 'created_at', 'updated_at', 'payout_phone']
    
    def validate_amount(self, value):
        """Validate that the withdrawal amount doesn't exceed wallet balance"""
        seller = self.context['request'].user
        try:
            wallet = Wallet.objects.get(seller=seller)
            if value > wallet.balance:
                raise serializers.ValidationError(
                    f"Insufficient balance. Available: ${wallet.balance}"
                )
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found.")
        return value


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    seller_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='seller'), source='seller', write_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'seller', 'seller_id', 
            'report_type', 'description', 'status', 'admin_notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Prevent users from reporting themselves (only during creation or when seller is updated)
        # Get the reporter from the context (set in the view)
        if 'seller' in attrs:
            reporter = self.context.get('request').user
            if reporter == attrs['seller']:
                raise serializers.ValidationError("You cannot report yourself.")
        return attrs

