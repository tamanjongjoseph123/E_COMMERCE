from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'admin/sellers', views.SellerApprovalViewSet, basename='seller-approval')
router.register(r'admin/categories', views.CategoryViewSet, basename='category')
router.register(r'admin/users', views.UserManagementViewSet, basename='user-management')
router.register(r'admin/withdrawals', views.WithdrawalRequestViewSet, basename='withdrawal-request')
router.register(r'seller/products', views.SellerProductViewSet, basename='seller-product')
router.register(r'products', views.ProductViewSet, basename='product')

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
    path('seller/orders/<int:order_id>/items/', views.seller_order_items, name='seller-order-items'),
    path('seller/orders/<int:order_id>/status/', views.update_order_status, name='update-order-status'),
    path('seller/withdrawals/request/', views.create_withdrawal_request, name='create-withdrawal-request'),
    path('seller/withdrawals/history/', views.seller_withdrawal_history, name='seller-withdrawal-history'),
    
    # Buyer endpoints
    path('products/all/', views.list_all_products, name='list-all-products'),
    path('cart/bulk-operations/', views.bulk_cart_operations, name='bulk-cart-operations'),
    path('cart/optimized-checkout/', views.optimized_checkout, name='optimized-checkout'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/summary/', views.CartViewSet.as_view({'get': 'cart_summary'}), name='cart-summary'),
    path('orders/', views.my_orders, name='my-orders'),
    path('buyer/orders/', views.my_orders, name='buyer-orders'),  # Add buyer-specific URL
    path('orders/<int:order_id>/delivered/', views.mark_order_delivered, name='mark-order-delivered'),
    path('payments/check-pending/', views.check_pending_payments, name='check-pending-payments'),
    
    # Payment endpoints
    path('debug/payment/', views.debug_payment_service, name='debug-payment-service'),
    path('debug/transaction/', views.debug_payment_transaction, name='debug-payment-transaction'),
    path('test/webhook/', views.test_webhook, name='test-webhook'),
    path('payments/check-status/', views.check_payment_status_manual, name='check-payment-status-manual'),
    path('orders/<int:order_id>/pay/', views.initiate_payment, name='initiate-payment'),
    path('orders/<int:order_id>/payment/status/', views.check_payment_status, name='check-payment-status'),
    path('orders/<int:order_id>/payment/retry/', views.retry_payment, name='retry-payment'),
    path('payments/webhook/', views.payment_webhook, name='payment-webhook'),
    path('payments/my/', views.my_payments, name='my-payments'),
    path('admin/payments/', views.admin_payments, name='admin-payments'),
    
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

