from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    User, Seller, Category, Product, Cart, CartItem, 
    Order, OrderItem, Wallet, Transaction
)


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'profile_picture', 'profile_picture_url', 'phone_number', 'address', 'date_joined']
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
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'profile_picture', 'profile_picture_url', 'phone_number', 'address', 'date_joined', 'last_login']
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=['buyer', 'seller'], required=True)
    id_card = serializers.ImageField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password2', 'role', 'id_card']
        extra_kwargs = {
            'name': {'required': True},
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
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_id_card_url(self, obj):
        if obj.id_card:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.id_card.url)
            return obj.id_card.url
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']


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
    product = ProductSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'seller', 'quantity', 'price', 'subtotal']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'buyer', 'items', 'total_amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


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

