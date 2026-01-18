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
    path('seller/orders/', views.seller_orders, name='seller-orders'),
    path('seller/orders/<int:order_id>/status/', views.update_order_status, name='update-order-status'),
    
    # Buyer endpoints
    path('products/all/', views.list_all_products, name='list-all-products'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/summary/', views.CartViewSet.as_view({'get': 'cart_summary'}), name='cart-summary'),
    path('orders/', views.my_orders, name='my-orders'),
    path('orders/<int:order_id>/delivered/', views.mark_order_delivered, name='mark-order-delivered'),
    
    # Profile endpoints (Buyer and Seller)
    path('profile/', views.profile, name='profile'),
    path('seller/<int:user_id>/profile/', views.seller_profile, name='seller-profile'),
    path('auth/change-password/', views.change_password, name='change-password'),
    
    # Report endpoints
    path('reports/', views.create_report, name='create-report'),
    path('reports/my/', views.my_reports, name='my-reports'),
    path('admin/reports/', views.manage_reports, name='manage-reports'),
    path('admin/reports/<int:report_id>/', views.manage_reports, name='manage-report-detail'),
    
    # Router URLs
    path('', include(router.urls)),
]

