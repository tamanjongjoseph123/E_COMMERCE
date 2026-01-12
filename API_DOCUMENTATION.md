# E-Commerce API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [Admin Endpoints](#admin-endpoints)
3. [Seller Endpoints](#seller-endpoints)
4. [Buyer Endpoints](#buyer-endpoints)
5. [Public Endpoints](#public-endpoints)

---

## Authentication Endpoints

### 1. Register User
**Endpoint:** `POST /api/auth/register/`  
**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123",
  "password2": "securepassword123",
  "role": "buyer" | "seller",
  "id_card": "<file>" // Required only for seller role
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Registration successful. Please wait for admin approval if you are a seller.",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "buyer",
      "date_joined": "2024-01-01T00:00:00Z"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Registration failed",
  "errors": {
    "email": ["This field is required."],
    "password": ["Password fields didn't match."]
  }
}
```

---

### 2. Login
**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "buyer",
      "date_joined": "2024-01-01T00:00:00Z"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Login failed",
  "errors": {
    "non_field_errors": ["Invalid email or password."]
  }
}
```

**Note:** Sellers with pending/rejected status cannot login.

---

### 3. Refresh Token
**Endpoint:** `POST /api/auth/refresh/`  
**Authentication:** Required

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## Admin Endpoints

All admin endpoints require admin role authentication.

### 4. List Pending Sellers
**Endpoint:** `GET /api/admin/sellers/?status=pending`  
**Authentication:** Admin required

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `approved`, `rejected`)

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "email": "seller@example.com",
        "name": "Jane Seller",
        "role": "seller",
        "date_joined": "2024-01-01T00:00:00Z"
      },
      "id_card": "/media/id_cards/id_card.jpg",
      "id_card_url": "http://localhost:8000/media/id_cards/id_card.jpg",
      "approval_status": "pending",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 5. Approve Seller
**Endpoint:** `POST /api/admin/sellers/{id}/approve/`  
**Authentication:** Admin required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Seller approved successfully",
  "data": {
    "id": 1,
    "user": {...},
    "approval_status": "approved",
    ...
  }
}
```

---

### 6. Reject Seller
**Endpoint:** `POST /api/admin/sellers/{id}/reject/`  
**Authentication:** Admin required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Seller rejected",
  "data": {
    "id": 1,
    "user": {...},
    "approval_status": "rejected",
    ...
  }
}
```

---

### 7. Create Category
**Endpoint:** `POST /api/admin/categories/`  
**Authentication:** Admin required

**Request Body:**
```json
{
  "name": "Electronics",
  "description": "Electronic devices and accessories"
}
```

**Response (Success - 201):**
```json
{
  "id": 1,
  "name": "Electronics",
  "description": "Electronic devices and accessories",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": 1
}
```

---

### 8. List Categories
**Endpoint:** `GET /api/admin/categories/`  
**Authentication:** Not required (public)

**Response (Success - 200):**
```json
[
  {
    "id": 1,
    "name": "Electronics",
    "description": "Electronic devices and accessories",
    "created_at": "2024-01-01T00:00:00Z",
    "created_by": 1
  }
]
```

---

### 9. Update Category
**Endpoint:** `PUT /api/admin/categories/{id}/` or `PATCH /api/admin/categories/{id}/`  
**Authentication:** Admin required

**Request Body:**
```json
{
  "name": "Updated Electronics",
  "description": "Updated description"
}
```

---

### 10. Delete Category
**Endpoint:** `DELETE /api/admin/categories/{id}/`  
**Authentication:** Admin required

**Response (Success - 204):** No content

---

### 11. Get Category Products
**Endpoint:** `GET /api/admin/categories/{id}/products/`  
**Authentication:** Not required (public)

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Products in Electronics",
  "data": [
    {
      "id": 1,
      "seller": {...},
      "category": {...},
      "name": "Laptop",
      "description": "High-performance laptop",
      "price": "999.99",
      "stock": 10,
      "image_url": "http://localhost:8000/media/products/laptop.jpg",
      "created_at": "2024-01-01T00:00:00Z",
      "is_active": true
    }
  ]
}
```

---

### 12. List All Users
**Endpoint:** `GET /api/admin/users/?role=buyer`  
**Authentication:** Admin required

**Query Parameters:**
- `role` (optional): Filter by role (`admin`, `buyer`, `seller`)

**Response (Success - 200):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "buyer",
    "date_joined": "2024-01-01T00:00:00Z"
  }
]
```

---

### 13. Deactivate User
**Endpoint:** `DELETE /api/admin/users/{id}/deactivate/`  
**Authentication:** Admin required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "User deactivated successfully"
}
```

---

### 14. Activate User
**Endpoint:** `POST /api/admin/users/{id}/activate/`  
**Authentication:** Admin required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "User activated successfully"
}
```

---

### 15. View All Seller Wallets
**Endpoint:** `GET /api/admin/wallets/`  
**Authentication:** Admin required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "All seller wallets",
  "data": {
    "wallets": [
      {
        "id": 1,
        "seller": {
          "id": 2,
          "email": "seller@example.com",
          "name": "Jane Seller",
          "role": "seller"
        },
        "balance": "1500.00",
        "transactions": [...],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total_balance": 1500.00
  }
}
```

---

## Seller Endpoints

All seller endpoints require seller role authentication.

### 16. List My Products
**Endpoint:** `GET /api/seller/products/`  
**Authentication:** Seller required

**Response (Success - 200):**
```json
[
  {
    "id": 1,
    "seller": {...},
    "category": {...},
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": "999.99",
    "stock": 10,
    "image_url": "http://localhost:8000/media/products/laptop.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
]
```

---

### 17. Create Product
**Endpoint:** `POST /api/seller/products/`  
**Authentication:** Seller required

**Request Body (multipart/form-data):**
```
category_id: 1
name: "Laptop"
description: "High-performance laptop"
price: 999.99
stock: 10
image: <file>
```

**Response (Success - 201):**
```json
{
  "id": 1,
  "seller": {...},
  "category": {...},
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": "999.99",
  "stock": 10,
  "image_url": "http://localhost:8000/media/products/laptop.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "is_active": true
}
```

---

### 18. Update Product
**Endpoint:** `PUT /api/seller/products/{id}/` or `PATCH /api/seller/products/{id}/`  
**Authentication:** Seller required

**Request Body:**
```json
{
  "name": "Updated Laptop",
  "price": "899.99",
  "stock": 15
}
```

---

### 19. Delete Product
**Endpoint:** `DELETE /api/seller/products/{id}/`  
**Authentication:** Seller required

**Response (Success - 204):** No content

---

### 20. View My Wallet
**Endpoint:** `GET /api/seller/wallet/`  
**Authentication:** Seller required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Wallet retrieved successfully",
  "data": {
    "id": 1,
    "seller": {
      "id": 2,
      "email": "seller@example.com",
      "name": "Jane Seller",
      "role": "seller"
    },
    "balance": "1500.00",
    "transactions": [
      {
        "id": 1,
        "order_item": {
          "id": 1,
          "product": {...},
          "seller": {...},
          "quantity": 2,
          "price": "999.99",
          "subtotal": "1999.98"
        },
        "amount": "1999.98",
        "transaction_type": "sale",
        "description": "Sale of Laptop",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 21. Get Available Categories (Seller)
**Endpoint:** `GET /api/seller/categories/`  
**Authentication:** Seller required

**Description:** Fetch all available categories that sellers can use when creating products.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Available categories retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Electronics",
      "description": "Electronic devices and accessories",
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    },
    {
      "id": 2,
      "name": "Clothing",
      "description": "Apparel and fashion items",
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    }
  ]
}
```

---

### 22. View My Profile
**Endpoint:** `GET /api/profile/`  
**Authentication:** Buyer or Seller required

**Description:** Get current user's profile information.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "buyer",
    "profile_picture": "/media/profile_pictures/profile.jpg",
    "profile_picture_url": "http://localhost:8000/media/profile_pictures/profile.jpg",
    "phone_number": "+1234567890",
    "address": "123 Main St, City, Country",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

---

### 23. Update My Profile
**Endpoint:** `PUT /api/profile/` or `PATCH /api/profile/`  
**Authentication:** Buyer or Seller required

**Description:** Update current user's profile information. Use PUT for full update or PATCH for partial update.

**Request Body (multipart/form-data for PUT or PATCH):**
```
name: "John Updated"
phone_number: "+1234567890"
address: "123 Main St, City, Country"
profile_picture: <file>
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Updated",
    "role": "buyer",
    "profile_picture": "/media/profile_pictures/profile.jpg",
    "profile_picture_url": "http://localhost:8000/media/profile_pictures/profile.jpg",
    "phone_number": "+1234567890",
    "address": "123 Main St, City, Country",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Profile update failed",
  "errors": {
    "phone_number": ["Invalid phone number format."]
  }
}
```

**Note:** 
- Email and role cannot be updated through this endpoint
- Profile picture is optional
- Use `multipart/form-data` content type when uploading profile picture

---

## Buyer Endpoints

All buyer endpoints require buyer role authentication.

### 24. List All Products from Sellers
**Endpoint:** `GET /api/products/all/`  
**Authentication:** Not required (public)

**Description:** List all available products from all sellers with filtering and pagination support.

**Query Parameters:**
- `seller_id` (optional): Filter products by seller ID
- `category_id` (optional): Filter products by category ID
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `q` (optional): Search query (searches in name and description)
- `ordering` (optional): Order results by `price`, `-price`, `created_at`, `-created_at`, `name`, `-name` (default: `-created_at`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Example Requests:**
- `GET /api/products/all/` - Get all products
- `GET /api/products/all/?category_id=1` - Get products in category 1
- `GET /api/products/all/?seller_id=2` - Get products from seller 2
- `GET /api/products/all/?min_price=100&max_price=500` - Get products between $100 and $500
- `GET /api/products/all/?q=laptop` - Search for "laptop"
- `GET /api/products/all/?ordering=price&page=1&page_size=10` - Get cheapest products, page 1, 10 per page

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "All available products retrieved successfully",
  "data": {
    "products": [
      {
        "id": 1,
        "seller": {
          "id": 2,
          "email": "seller@example.com",
          "name": "Jane Seller",
          "role": "seller"
        },
        "category": {
          "id": 1,
          "name": "Electronics",
          "description": "Electronic devices"
        },
        "name": "Laptop",
        "description": "High-performance laptop",
        "price": "999.99",
        "stock": 10,
        "image_url": "http://localhost:8000/media/products/laptop.jpg",
        "created_at": "2024-01-01T00:00:00Z",
        "is_active": true
      }
    ],
    "total_count": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

---

### 25. List All Products (Alternative)
**Endpoint:** `GET /api/products/`  
**Authentication:** Not required (public)

**Description:** Alternative endpoint to list products. Supports filtering via query parameters.

**Query Parameters:**
- `seller_id` (optional): Filter by seller ID
- `category_id` (optional): Filter by category ID
- `min_price` (optional): Minimum price
- `max_price` (optional): Maximum price
- `ordering` (optional): Order by field (price, -price, created_at, -created_at, name, -name)

**Response (Success - 200):**
```json
[
  {
    "id": 1,
    "seller": {...},
    "category": {...},
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": "999.99",
    "stock": 10,
    "image_url": "http://localhost:8000/media/products/laptop.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
]
```

---

### 25. Get Product Details
**Endpoint:** `GET /api/products/{id}/`  
**Authentication:** Not required (public)

**Response (Success - 200):**
```json
{
  "id": 1,
  "seller": {
    "id": 2,
    "email": "seller@example.com",
    "name": "Jane Seller",
    "role": "seller"
  },
  "category": {...},
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": "999.99",
  "stock": 10,
  "image_url": "http://localhost:8000/media/products/laptop.jpg",
  "created_at": "2024-01-01T00:00:00Z",
  "is_active": true
}
```

---

### 26. Search Products
**Endpoint:** `GET /api/products/search/?q=laptop`  
**Authentication:** Not required (public)

**Query Parameters:**
- `q` (required): Search query

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Search results for \"laptop\"",
  "data": [
    {
      "id": 1,
      "name": "Laptop",
      "description": "High-performance laptop",
      "price": "999.99",
      ...
    }
  ]
}
```

---

### 27. Get Seller Details from Product
**Endpoint:** `GET /api/products/{id}/seller_details/`  
**Authentication:** Not required (public)

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Seller details retrieved",
  "data": {
    "seller": {
      "id": 2,
      "email": "seller@example.com",
      "name": "Jane Seller",
      "role": "seller"
    },
    "other_products": [
      {
        "id": 2,
        "name": "Mouse",
        "price": "29.99",
        ...
      }
    ]
  }
}
```

---

### 28. Add Item to Cart
**Endpoint:** `POST /api/cart/items/`  
**Authentication:** Buyer required

**Request Body:**
```json
{
  "product_id": 1,
  "quantity": 2
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Item added to cart",
  "data": {
    "id": 1,
    "product": {
      "id": 1,
      "name": "Laptop",
      "price": "999.99",
      ...
    },
    "quantity": 2,
    "subtotal": "1999.98",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Insufficient stock. Available: 5"
}
```

---

### 29. List Cart Items
**Endpoint:** `GET /api/cart/items/`  
**Authentication:** Buyer required

**Response (Success - 200):**
```json
[
  {
    "id": 1,
    "product": {...},
    "quantity": 2,
    "subtotal": "1999.98",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### 30. Update Cart Item Quantity
**Endpoint:** `PATCH /api/cart/items/{id}/update_quantity/`  
**Authentication:** Buyer required

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Cart item updated",
  "data": {
    "id": 1,
    "product": {...},
    "quantity": 3,
    "subtotal": "2999.97",
    ...
  }
}
```

---

### 31. Remove Cart Item
**Endpoint:** `DELETE /api/cart/items/{id}/`  
**Authentication:** Buyer required

**Response (Success - 204):** No content

---

### 32. Get Cart Summary
**Endpoint:** `GET /api/cart/summary/`  
**Authentication:** Buyer required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Cart retrieved successfully",
  "data": {
    "id": 1,
    "items": [
      {
        "id": 1,
        "product": {...},
        "quantity": 2,
        "subtotal": "1999.98"
      }
    ],
    "total_amount": "1999.98",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 33. Checkout
**Endpoint:** `POST /api/cart/checkout/`  
**Authentication:** Buyer required

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Order placed successfully",
  "data": {
    "id": 1,
    "buyer": {
      "id": 1,
      "email": "buyer@example.com",
      "name": "John Doe",
      "role": "buyer"
    },
    "items": [
      {
        "id": 1,
        "product": {...},
        "seller": {...},
        "quantity": 2,
        "price": "999.99",
        "subtotal": "1999.98"
      }
    ],
    "total_amount": "1999.98",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Cart is empty"
}
```

**Note:** On successful checkout:
- Order is created with status "completed"
- Product stock is reduced
- Seller wallets are updated with the sale amount
- Transactions are created for each seller
- Cart is cleared

---

### 34. My Orders
**Endpoint:** `GET /api/orders/`  
**Authentication:** Buyer required

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Orders retrieved successfully",
  "data": [
    {
      "id": 1,
      "buyer": {...},
      "items": [
        {
          "id": 1,
          "product": {...},
          "seller": {...},
          "quantity": 2,
          "price": "999.99",
          "subtotal": "1999.98"
        }
      ],
      "total_amount": "1999.98",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Public Endpoints

These endpoints don't require authentication:

- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get product details
- `GET /api/products/search/?q=query` - Search products
- `GET /api/products/{id}/seller_details/` - Get seller details
- `GET /api/admin/categories/` - List categories
- `GET /api/admin/categories/{id}/products/` - Get category products

---

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "success": false,
  "message": "Error message",
  "errors": {
    "field_name": ["Error detail"]
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (for DELETE)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Notes

1. **File Uploads:** Use `multipart/form-data` for endpoints that accept file uploads (register as seller, create product).

2. **JWT Tokens:** Access tokens expire after 1 hour. Use the refresh token endpoint to get a new access token.

3. **Seller Approval:** Sellers cannot login until their account is approved by an admin.

4. **Wallet System:** When a buyer checks out:
   - Each seller receives payment for their products
   - Multiple sellers' products in one order are split automatically
   - Transactions are recorded for each seller

5. **Stock Management:** Product stock is automatically reduced when an order is placed.

6. **Pagination:** List endpoints support pagination with `?page=1` query parameter (20 items per page by default).

---

## Example Workflow

### Seller Registration and Product Listing:
1. Register as seller: `POST /api/auth/register/` (with ID card)
2. Admin approves: `POST /api/admin/sellers/{id}/approve/`
3. Login: `POST /api/auth/login/`
4. Create category (admin): `POST /api/admin/categories/`
5. Create product: `POST /api/seller/products/`
6. View wallet: `GET /api/seller/wallet/`

### Buyer Shopping:
1. Register as buyer: `POST /api/auth/register/`
2. Login: `POST /api/auth/login/`
3. Browse categories: `GET /api/admin/categories/`
4. View category products: `GET /api/admin/categories/{id}/products/`
5. Search products: `GET /api/products/search/?q=laptop`
6. Add to cart: `POST /api/cart/items/`
7. View cart: `GET /api/cart/summary/`
8. Checkout: `POST /api/cart/checkout/`
9. View orders: `GET /api/orders/`

