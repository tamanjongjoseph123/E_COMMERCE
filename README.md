# E-Commerce API

A comprehensive Django REST Framework API for an e-commerce platform supporting web and mobile applications.

## Features

- **JWT Authentication** with access and refresh tokens
- **Role-based Access Control** (Admin, Buyer, Seller)
- **Seller Approval System** with ID card verification
- **Product Management** with categories
- **Shopping Cart** functionality
- **Order Processing** with automatic wallet updates
- **Wallet System** for sellers to track earnings
- **Search Functionality** for products
- **Admin Dashboard** for managing users, categories, and seller approvals

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create a superuser (admin):**
```bash
python manage.py createsuperuser
```

4. **Run the development server:**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## Project Structure

```
e_commerce/
├── api/                    # Main API application
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views and viewsets
│   ├── urls.py            # URL routing
│   └── admin.py           # Django admin configuration
├── e_commerce/            # Project settings
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
├── requirements.txt        # Python dependencies
├── API_DOCUMENTATION.md   # Complete API documentation
└── README.md              # This file
```

## User Roles

### Admin
- Approve/reject seller accounts
- Create and manage product categories
- View all seller wallets
- Manage all users in the system

### Seller
- Register with ID card upload (requires admin approval)
- Create, update, and delete products
- View wallet balance and transaction history
- Products are automatically assigned to seller

### Buyer
- Register and login immediately (no approval needed)
- Browse products by category
- Search products
- Add items to cart
- Checkout and place orders
- View order history

## API Endpoints

### Authentication Endpoints (All Users)

- `POST /api/auth/register/` - Register new user (buyer or seller)
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/refresh/` - Refresh access token

---

## Admin Endpoints

**Base URL:** `/api/admin/`  
**Authentication:** Admin role required

### Seller Management
- `GET /api/admin/sellers/` - List all sellers (with optional `?status=pending` filter)
- `POST /api/admin/sellers/{id}/approve/` - Approve seller account
- `POST /api/admin/sellers/{id}/reject/` - Reject seller account

### Category Management
- `GET /api/admin/categories/` - List all categories
- `POST /api/admin/categories/` - Create new category
- `PUT /api/admin/categories/{id}/` - Update category
- `PATCH /api/admin/categories/{id}/` - Partially update category
- `DELETE /api/admin/categories/{id}/` - Delete category
- `GET /api/admin/categories/{id}/products/` - Get products in a category

### User Management
- `GET /api/admin/users/` - List all users (with optional `?role=buyer` filter)
- `DELETE /api/admin/users/{id}/deactivate/` - Deactivate user
- `POST /api/admin/users/{id}/activate/` - Activate user

### Wallet Management
- `GET /api/admin/wallets/` - View all seller wallets and total balance

---

## Seller Endpoints

**Base URL:** `/api/seller/`  
**Authentication:** Seller role required (account must be approved)

### Product Management
- `GET /api/seller/products/` - List my products
- `POST /api/seller/products/` - Create new product
- `GET /api/seller/products/{id}/` - Get product details
- `PUT /api/seller/products/{id}/` - Update product
- `PATCH /api/seller/products/{id}/` - Partially update product
- `DELETE /api/seller/products/{id}/` - Delete product

### Category Access
- `GET /api/seller/categories/` - Get available categories for product creation

### Wallet
- `GET /api/seller/wallet/` - View my wallet balance and transaction history

### Profile
- `GET /api/profile/` - View my profile
- `PUT /api/profile/` - Update my profile (full update)
- `PATCH /api/profile/` - Update my profile (partial update)

---

## Buyer Endpoints

**Base URL:** `/api/`  
**Authentication:** Buyer role required

### Product Browsing
- `GET /api/products/` - List all active products
- `GET /api/products/{id}/` - Get product details
- `GET /api/products/search/?q=query` - Search products
- `GET /api/products/{id}/seller_details/` - Get seller details and other products

### Category Browsing
- `GET /api/admin/categories/` - List all categories (public)
- `GET /api/admin/categories/{id}/products/` - Get products in a category (public)

### Shopping Cart
- `GET /api/cart/summary/` - Get cart summary with all items
- `GET /api/cart/items/` - List cart items
- `POST /api/cart/items/` - Add item to cart
- `PATCH /api/cart/items/{id}/update_quantity/` - Update item quantity
- `DELETE /api/cart/items/{id}/` - Remove item from cart

### Orders
- `POST /api/cart/checkout/` - Checkout and place order
- `GET /api/orders/` - View my order history

### Profile
- `GET /api/profile/` - View my profile
- `PUT /api/profile/` - Update my profile (full update)
- `PATCH /api/profile/` - Update my profile (partial update)

---

## Key Models

- **User**: Custom user model with roles
- **Seller**: Seller profile with approval status and ID card
- **Category**: Product categories created by admin
- **Product**: Products created by sellers
- **Cart/CartItem**: Shopping cart functionality
- **Order/OrderItem**: Order management
- **Wallet**: Seller wallet for tracking earnings
- **Transaction**: Transaction history for sellers

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API endpoint documentation including:
- Detailed request/response formats
- Authentication requirements
- Error handling
- Example workflows

## Media Files

Uploaded files (product images, ID cards) are stored in the `media/` directory. Make sure to configure your web server to serve media files in production.

## Environment Setup

For production, update `settings.py`:
- Set `DEBUG = False`
- Configure `ALLOWED_HOSTS`
- Set up proper database (PostgreSQL recommended)
- Configure static and media file serving
- Set secure `SECRET_KEY`

## Testing

After setup, you can test the API using:
- Postman
- curl
- Any HTTP client
- Frontend application

## Support

For API integration questions, refer to the [API_DOCUMENTATION.md](API_DOCUMENTATION.md) file.
