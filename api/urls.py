from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin/sellers', views.SellerApprovalViewSet, basename='seller-approval')
router.register(r'admin/categories', views.CategoryViewSet, basename='category')
router.register(r'admin/users', views.UserManagementViewSet, basename='user-management')
router.register(r'seller/products', views.SellerProductViewSet, basename='seller-product')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'cart/items', views.CartViewSet, basename='cart-item')

urlpatterns = [
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/refresh/', views.refresh_token, name='refresh-token'),
    
    # Admin endpoints
    path('admin/wallets/', views.admin_wallets, name='admin-wallets'),
    
    # Seller endpoints
    path('seller/wallet/', views.seller_wallet, name='seller-wallet'),
    path('seller/categories/', views.seller_categories, name='seller-categories'),
    
    # Buyer endpoints
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/summary/', views.CartViewSet.as_view({'get': 'cart_summary'}), name='cart-summary'),
    path('orders/', views.my_orders, name='my-orders'),
    
    # Profile endpoints (Buyer and Seller)
    path('profile/', views.profile, name='profile'),
    
    # Router URLs
    path('', include(router.urls)),
]

