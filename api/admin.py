from django.contrib import admin
from .models import (
    User, Seller, Category, Product, Cart, CartItem,
    Order, OrderItem, Wallet, Transaction
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'name']
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('name', 'profile_picture', 'phone_number', 'address')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'approval_status', 'created_at']
    list_filter = ['approval_status', 'created_at']
    search_fields = ['user__email', 'user__name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'stock', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'seller', 'quantity', 'subtotal']


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['seller', 'balance', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'amount', 'transaction_type', 'created_at']
    list_filter = ['transaction_type', 'created_at']
