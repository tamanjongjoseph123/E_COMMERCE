# E-Commerce API Documentation



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
  "name": "John",
  "full_name": "John Doe",
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
      "name": "John",
      "full_name": "John Doe",
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
      "name": "John",
      "full_name": "John Doe",
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
        "name": "Jane",
        "full_name": "Jane Seller",
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
  "description": "Electronic devices and accessories",
  "image": "<file>"
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Electronics",
    "description": "Electronic devices and accessories",
    "image": "/media/categories/electronics.jpg",
    "image_url": "http://localhost:8000/media/categories/electronics.jpg",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "created_by": 1
  }
}
```

---

### 8. List Categories
**Endpoint:** `GET /api/admin/categories/`  
**Authentication:** Not required (public)

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Electronics",
      "description": "Electronic devices and accessories",
      "image": "/media/categories/electronics.jpg",
      "image_url": "http://localhost:8000/media/categories/electronics.jpg",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    }
  ]
}
```

---

### 9. Update Category
**Endpoint:** `PUT /api/admin/categories/{id}/` or `PATCH /api/admin/categories/{id}/`  
**Authentication:** Admin required

**Request Body:**
```json
{
  "name": "Updated Electronics",
  "description": "Updated description",
  "image": "<file>"
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
      "price": "59999.99",
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
    "name": "John",
    "full_name": "John Doe",
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
          "name": "Jane",
          "full_name": "Jane Seller",
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
    "price": "59999.99",
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
  "price": "59999.99",
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

### 20. View My Orders (Seller)
**Endpoint:** `GET /api/seller/orders/`  
**Authentication:** Seller required

**Description:** View all orders that contain the seller's products. Shows complete order information including buyer details and delivery information.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Seller orders retrieved successfully",
  "data": [
    {
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
          "price": "59999.99",
          "subtotal": "119999.98"
        }
      ],
      "total_amount": "119999.98",
      "status": "pending",
      "delivery_address": "123 Main St, Apt 4B",
      "delivery_city": "New York",
      "delivery_state": "NY",
      "delivery_postal_code": "10001",
      "delivery_phone": "+1234567890",
      "delivery_notes": "Please call before delivering",
      "delivered_at": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Note:** 
- Only shows orders that contain products from the authenticated seller
- Orders are grouped to avoid duplicates when multiple items from same seller
- Complete delivery information is provided for fulfillment
- Can be used with the mark order delivered endpoint

---

### 21. View My Wallet
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
      "name": "Jane",
      "full_name": "Jane Seller",
      "role": "seller"
    },
    "balance": "900000.00 CFA",
    "transactions": [
      {
        "id": 1,
        "order_item": {
          "id": 1,
          "product": {...},
          "seller": {...},
          "quantity": 2,
          "price": "59999.99",
          "subtotal": "59999.99"
        },
        "amount": "119999.98",
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

### 22. Get Available Categories (Seller)
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
      "image": "/media/categories/electronics.jpg",
      "image_url": "http://localhost:8000/media/categories/electronics.jpg",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    },
    {
      "id": 2,
      "name": "Clothing",
      "description": "Apparel and fashion items",
      "image": "/media/categories/clothing.jpg",
      "image_url": "http://localhost:8000/media/categories/clothing.jpg",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    }
  ]
}
```

---

### 23. Update Order Status (Seller Only)
**Endpoint:** `PATCH /api/seller/orders/{order_id}/status/`  
**Authentication:** Seller required

**Description:** Update the status of items belonging to the authenticated seller within an order. Each seller can only update the status of their own items in an order, not the entire order. When all items in an order are marked as delivered, the overall order status will be automatically updated to "delivered".

**Request Body:**
```json
{
  "status": "pending" | "processing" | "shipped" | "delivered"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Your items status updated to processing successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "product_name": "Laptop",
        "product_image": "/media/products/laptop.jpg",
        "seller_name": "Jane Seller",
        "quantity": 1,
        "price": "59999.99",
        "subtotal": "59999.99",
        "status": "processing",
        "delivered_at": null
      }
    ],
    "updated_count": 1,
    "order_status": "shipped",
    "order_progress": {
      "total_items": 2,
      "pending": 0,
      "processing": 1,
      "shipped": 0,
      "delivered": 1,
      "delivered_text": "1/2 items delivered"
    }
  }
}
```

**Response (Error - 403):**
```json
{
  "success": false,
  "message": "You can only update status for orders that contain your products"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Invalid status. Must be one of: pending, processing, shipped, delivered"
}
```

**Important Notes:**
- Each seller can only update the status of their own items within an order
- The endpoint only affects the seller's items, not other sellers' items in the same order
- **Order status is intelligently calculated based on ALL item statuses:**
  - All items delivered → Order status = "delivered"
  - Some items shipped/delivered → Order status = "shipped"
  - Some items processing (none shipped/delivered) → Order status = "processing"
  - All items pending → Order status = "pending"
- Order status never downgrades from higher states (delivered → shipped → processing → pending)
- The response includes detailed progress tracking for all items in the order
- Individual item statuses are tracked separately from the overall order status
- The `order_progress` object provides complete visibility into each status category

---

### 24. View My Profile
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
    "name": "John",
    "full_name": "John Doe",
    "role": "buyer",
    "profile_picture": "/media/profile_pictures/profile.jpg",
    "profile_picture_url": "http://localhost:8000/media/profile_pictures/profile.jpg",
    "phone_number": "+1234567890",
    "address": "123 Main St, City, Country",
    "store_description": "Welcome to my store! We sell high-quality products.",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

---

### 24. Update My Profile
**Endpoint:** `PUT /api/profile/` or `PATCH /api/profile/`  
**Authentication:** Buyer or Seller required

**Description:** Update current user's profile information. Use PUT for full update or PATCH for partial update.

**Request Body (multipart/form-data for PUT or PATCH):**
```
name: "John"
full_name: "John Updated Doe"
phone_number: "+1234567890"
address: "123 Main St, City, Country"
store_description: "Welcome to my updated store! We sell high-quality electronics and gadgets."
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
    "name": "John",
    "full_name": "John Updated Doe",
    "role": "buyer",
    "profile_picture": "/media/profile_pictures/profile.jpg",
    "profile_picture_url": "http://localhost:8000/media/profile_pictures/profile.jpg",
    "phone_number": "+1234567890",
    "address": "123 Main St, City, Country",
    "store_description": "Welcome to my updated store! We sell high-quality electronics and gadgets.",
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

### 25. View Seller Profile (Public)
**Endpoint:** `GET /api/seller/{user_id}/profile/`  
**Authentication:** Not required (public)

**Description:** View any seller's public profile information including store description. This endpoint allows buyers and visitors to see seller details.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Seller profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "seller@example.com",
    "name": "Jane",
    "full_name": "Jane Seller",
    "role": "seller",
    "store_description": "Welcome to my store! We sell high-quality electronics and gadgets.",
    "profile_picture_url": "http://localhost:8000/media/profile_pictures/seller.jpg",
    "phone_number": "+1234567890",
    "address": "123 Store St, Shop City, Country",
    "seller_approval_status": "approved"
  }
}
```

---

### 26. Change Password
**Endpoint:** `POST /api/auth/change-password/`  
**Authentication:** Required (JWT token)

**Description:** Change account password for any authenticated user (buyer, seller, or admin).

**Request Body:**
```json
{
  "old_password": "currentpassword123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Current password is incorrect"
}
```

---

### 27. Report Seller
**Endpoint:** `POST /api/reports/`  
**Authentication:** Required (JWT token)

**Description:** Report a seller for various issues. Any authenticated user can report a seller.

**Request Body:**
```json
{
  "seller_id": 8,
  "report_type": "fraud",
  "description": "The seller is selling fake products and not delivering orders."
}
```

**Report Type Options:**
- `fraud` - Fraudulent activity
- `fake_product` - Counterfeit or fake products
- `poor_service` - Bad customer service
- `harassment` - Harassment or abuse
- `spam` - Spam or inappropriate content
- `other` - Other issues

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Report submitted successfully. Admin will review it.",
  "data": {
    "id": 1,
    "reporter": {
      "id": 2,
      "name": "John",
      "full_name": "John Buyer",
      "email": "buyer@example.com"
    },
    "seller": {
      "id": 8,
      "name": "Jane",
      "full_name": "Jane Seller",
      "email": "seller@example.com"
    },
    "report_type": "fraud",
    "description": "The seller is selling fake products and not delivering orders.",
    "status": "pending",
    "admin_notes": null,
    "created_at": "2024-01-18T12:30:00Z",
    "updated_at": "2024-01-18T12:30:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Failed to submit report",
  "errors": {
    "seller_id": ["Seller with this ID does not exist."],
    "reporter": ["You cannot report yourself."]
  }
}
```

---

### 28. View My Reports
**Endpoint:** `GET /api/reports/my/`  
**Authentication:** Required (JWT token)

**Description:** View all reports submitted by the current user and see admin responses.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Your reports retrieved successfully",
  "data": [
    {
      "id": 1,
      "reporter": {
        "id": 2,
        "name": "John",
        "full_name": "John Buyer",
        "email": "buyer@example.com"
      },
      "seller": {
        "id": 8,
        "name": "Jane",
        "full_name": "Jane Seller",
        "email": "seller@example.com"
      },
      "report_type": "fraud",
      "description": "The seller is selling fake products and not delivering orders.",
      "status": "under_review",
      "admin_notes": "Investigating seller's account and recent transactions. Found multiple complaints about delivery issues.",
      "created_at": "2024-01-18T12:30:00Z",
      "updated_at": "2024-01-18T13:15:00Z"
    },
    {
      "id": 2,
      "reporter": {
        "id": 2,
        "name": "John",
        "full_name": "John Buyer",
        "email": "buyer@example.com"
      },
      "seller": {
        "id": 12,
        "name": "Mike",
        "full_name": "Mike Seller",
        "email": "mike@example.com"
      },
      "report_type": "poor_service",
      "description": "Seller was rude and didn't respond to messages.",
      "status": "resolved",
      "admin_notes": "Issue resolved. Seller has been warned and account reviewed.",
      "created_at": "2024-01-17T10:20:00Z",
      "updated_at": "2024-01-18T09:45:00Z"
    }
  ]
}
```

---

### 29. View All Reports (Admin)
**Endpoint:** `GET /api/admin/reports/`  
**Authentication:** Admin required

**Description:** Admin can view all submitted reports with optional filtering by status.

**Query Parameters:**
- `status` (optional): Filter by report status
  - `pending` - Reports awaiting review
  - `under_review` - Reports being investigated
  - `resolved` - Reports that have been resolved
  - `dismissed` - Reports that were dismissed

**Example:** `GET /api/admin/reports/?status=pending`

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Reports retrieved successfully",
  "data": [
    {
      "id": 1,
      "reporter": {
        "id": 2,
        "name": "John",
        "full_name": "John Buyer",
        "email": "buyer@example.com"
      },
      "seller": {
        "id": 8,
        "name": "Jane",
        "full_name": "Jane Seller",
        "email": "seller@example.com"
      },
      "report_type": "fraud",
      "description": "The seller is selling fake products and not delivering orders.",
      "status": "pending",
      "admin_notes": null,
      "created_at": "2024-01-18T12:30:00Z",
      "updated_at": "2024-01-18T12:30:00Z"
    }
  ]
}
```

---

### 30. View Specific Report (Admin)
**Endpoint:** `GET /api/admin/reports/{report_id}/`  
**Authentication:** Admin required

**Description:** Admin can view detailed information about a specific report.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Report retrieved successfully",
  "data": {
    "id": 1,
    "reporter": {
      "id": 2,
      "name": "John",
      "full_name": "John Buyer",
      "email": "buyer@example.com"
    },
    "seller": {
      "id": 8,
      "name": "Jane",
      "full_name": "Jane Seller",
      "email": "seller@example.com"
    },
    "report_type": "fraud",
    "description": "The seller is selling fake products and not delivering orders.",
    "status": "pending",
    "admin_notes": null,
    "created_at": "2024-01-18T12:30:00Z",
    "updated_at": "2024-01-18T12:30:00Z"
  }
}
```

---

### 31. Update Report (Admin)
**Endpoint:** `PUT /api/admin/reports/{report_id}/` or `PATCH /api/admin/reports/{report_id}/`  
**Authentication:** Admin required

**Description:** Admin can update report status and add admin notes. Use PUT for full update or PATCH for partial update.

**Request Body:**
```json
{
  "status": "under_review",
  "admin_notes": "Investigating the seller's account and recent transactions. Found multiple complaints about delivery issues."
}
```

**Status Options:**
- `pending` - Reports awaiting review
- `under_review` - Reports being investigated
- `resolved` - Reports that have been resolved
- `dismissed` - Reports that were dismissed

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Report updated successfully",
  "data": {
    "id": 1,
    "reporter": {
      "id": 2,
      "name": "John",
      "full_name": "John Buyer",
      "email": "buyer@example.com"
    },
    "seller": {
      "id": 8,
      "name": "Jane",
      "full_name": "Jane Seller",
      "email": "seller@example.com"
    },
    "report_type": "fraud",
    "description": "The seller is selling fake products and not delivering orders.",
    "status": "under_review",
    "admin_notes": "Investigating the seller's account and recent transactions. Found multiple complaints about delivery issues.",
    "created_at": "2024-01-18T12:30:00Z",
    "updated_at": "2024-01-18T13:15:00Z"
  }
}
```

---

## Buyer Endpoints

All buyer endpoints require buyer role authentication.

### 32. List All Products from Sellers
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
          "name": "Jane",
          "full_name": "Jane Seller",
          "role": "seller"
        },
        "category": {
          "id": 1,
          "name": "Electronics",
          "description": "Electronic devices"
        },
        "name": "Laptop",
        "description": "High-performance laptop",
        "price": "59999.99",
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
    "price": "59999.99",
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
    "name": "Jane",
    "full_name": "Jane Seller",
    "role": "seller"
  },
  "category": {...},
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": "59999.99",
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
      "price": "59999.99",
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
      "name": "Jane",
      "full_name": "Jane Seller",
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
      "price": "59999.99",
      ...
    },
    "quantity": 2,
    "subtotal": "59999.99",
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
    "subtotal": "59999.99",
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
        "subtotal": "59999.99"
      }
    ],
    "total_amount": "119999.98",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 33. Checkout
**Endpoint:** `POST /api/cart/checkout/`  
**Authentication:** Buyer required

**Description:** Place an order with delivery information. Cart items are converted to an order and sellers are notified.

**Request Body:**
```json
{
  "delivery_address": "123 Main St, Apt 4B",
  "delivery_city": "New York",
  "delivery_state": "NY",
  "delivery_postal_code": "10001",
  "delivery_phone": "+1234567890",
  "delivery_notes": "Please call before delivering"
}
```

**Required Fields:**
- `delivery_address` - Street address for delivery

**Optional Fields:**
- `delivery_city` - City name
- `delivery_state` - State/Province
- `delivery_postal_code` - ZIP/Postal code
- `delivery_phone` - Contact phone number
- `delivery_notes` - Special delivery instructions

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
        "price": "59999.99",
        "subtotal": "119999.98"
      }
    ],
    "total_amount": "119999.98",
    "status": "pending",
    "delivery_address": "123 Main St, Apt 4B",
    "delivery_city": "New York",
    "delivery_state": "NY",
    "delivery_postal_code": "10001",
    "delivery_phone": "+1234567890",
    "delivery_notes": "Please call before delivering",
    "delivered_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Delivery Address is required"
}
```

**Note:** On successful checkout:
- Order is created with status "pending"
- Delivery information is saved for seller reference
- Product stock is reduced
- Seller wallets are updated with the sale amount
- Transactions are created for each seller
- Cart is cleared

---

### 34. Mark Order as Delivered
**Endpoint:** `PATCH /api/orders/{order_id}/delivered/`  
**Authentication:** Seller required

**Description:** Mark an order as delivered. Only sellers who have products in the order can mark it as delivered.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Order marked as delivered successfully",
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
        "price": "59999.99",
        "subtotal": "119999.98"
      }
    ],
    "total_amount": "119999.98",
    "status": "delivered",
    "delivery_address": "123 Main St, Apt 4B",
    "delivery_city": "New York",
    "delivery_state": "NY",
    "delivery_postal_code": "10001",
    "delivery_phone": "+1234567890",
    "delivery_notes": "Please call before delivering",
    "delivered_at": "2024-01-18T14:30:00Z",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-18T14:30:00Z"
  }
}
```

**Response (Error - 403):**
```json
{
  "success": false,
  "message": "You can only mark orders that contain your products as delivered"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Cannot mark order as delivered. Current status: delivered"
}
```

**Order Status Flow:**
- `pending` → `processing` → `shipped` → `delivered` → `cancelled`

---

### 35. My Orders (Enhanced)
**Endpoint:** `GET /api/orders/`  
**Authentication:** Buyer required

**Description:** View buyer's orders with complete order items, product details, and seller information. Now includes full order items that were previously missing.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Orders retrieved successfully",
  "data": [
    {
      "id": 1,
      "total_amount": "119999.98",
      "status": "delivered",
      "payment_status": "paid",
      "delivery_address": "123 Main St, Apt 4B",
      "delivery_phone": "+1234567890",
      "delivery_city": "New York",
      "delivery_state": "NY",
      "delivery_postal_code": "10001",
      "delivery_notes": "Please call before delivering",
      "items_count": 2,
      "items": [
        {
          "id": 1,
          "product": {
            "id": 1,
            "name": "Laptop",
            "description": "High-performance laptop with 16GB RAM",
            "price": "59999.99",
            "image_url": "http://localhost:8000/media/products/laptop.jpg"
          },
          "seller": {
            "id": 2,
            "name": "Jane Seller",
            "email": "jane@example.com"
          },
          "quantity": 2,
          "price": "59999.99",
          "subtotal": "119999.98"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-18T14:30:00Z"
    }
  ]
}
```

**Features:**
- ✅ **Order Items Included**: Each order now contains complete item details
- ✅ **Product Details**: Full product information with images
- ✅ **Seller Information**: Seller details for each item
- ✅ **Item Count**: Total number of items in order
- ✅ **Delivery Information**: Complete delivery details
- ✅ **Status Tracking**: Order and payment status

**Previous Issues Fixed:**
- ❌ **Before**: Orders showed empty `items: []` array
- ✅ **Now**: Orders include complete item details with product and seller information

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

## Withdrawal Management Endpoints

### 32. Create Withdrawal Request (Seller)
**Endpoint:** `POST /api/seller/withdrawals/request/`  
**Authentication:** Seller required

**Description:** Create a new withdrawal request to withdraw funds from the seller's wallet. The request will be pending until approved by an admin. Shows the phone number from the seller's profile where the money will be sent.

**Request Body:**
```json
{
  "amount": "500.00"
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Withdrawal request created successfully. You will receive the money at: +237123456789. If you want to change it, please update your profile.",
  "data": {
    "id": 1,
    "seller": {
      "id": 2,
      "email": "seller@example.com",
      "name": "Jane",
      "full_name": "Jane Seller",
      "role": "seller"
    },
    "amount": "500.00",
    "status": "pending",
    "admin_notes": null,
    "processed_at": null,
    "processed_by": null,
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "payout_phone": "+237123456789",
    "phone_message": "Money will be sent to: +237123456789. Update your profile to change the phone number."
  }
}
```

**Response (Success - 201) - No Phone Number:**
```json
{
  "success": true,
  "message": "Withdrawal request created successfully. You will receive the money at: No phone number in profile. If you want to change it, please update your profile.",
  "data": {
    "id": 1,
    "seller": {...},
    "amount": "500.00",
    "status": "pending",
    "payout_phone": null,
    "phone_message": "Money will be sent to: No phone number in profile. Update your profile to change the phone number."
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Insufficient balance. Available: $300.00"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "You already have a pending withdrawal request"
}
```

**Validation Rules:**
- Amount must be greater than 0
- Seller must have sufficient wallet balance
- Cannot create multiple pending requests
- Amount cannot exceed current wallet balance
- Phone number is taken from seller's profile
- If no phone number exists, seller is notified to update profile

**Phone Number Information:**
- The system displays the phone number from the seller's profile
- Sellers can update their phone number via the profile update endpoint
- No phone number means the payout will fail until profile is updated
- Admin can see the phone number in withdrawal details

---

### 33. View Withdrawal History (Seller)
**Endpoint:** `GET /api/seller/withdrawals/history/`  
**Authentication:** Seller required

**Description:** View all withdrawal requests made by the current seller, including their status and processing details.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Withdrawal history retrieved successfully",
  "data": [
    {
      "id": 1,
      "seller": {
        "id": 2,
        "email": "seller@example.com",
        "name": "Jane",
        "full_name": "Jane Seller",
        "role": "seller"
      },
      "amount": "500.00",
      "status": "processed",
      "admin_notes": "Approved and processed successfully",
      "processed_at": "2024-01-20T14:30:00Z",
      "processed_by": {
        "id": 1,
        "email": "admin@example.com",
        "name": "Admin",
        "full_name": "Admin User",
        "role": "admin"
      },
      "created_at": "2024-01-20T10:30:00Z",
      "updated_at": "2024-01-20T14:30:00Z"
    },
    {
      "id": 2,
      "seller": {
        "id": 2,
        "email": "seller@example.com",
        "name": "Jane",
        "full_name": "Jane Seller",
        "role": "seller"
      },
      "amount": "200.00",
      "status": "rejected",
      "admin_notes": "Insufficient documentation provided",
      "processed_at": "2024-01-19T16:45:00Z",
      "processed_by": {
        "id": 1,
        "email": "admin@example.com",
        "name": "Admin",
        "full_name": "Admin User",
        "role": "admin"
      },
      "created_at": "2024-01-19T09:15:00Z",
      "updated_at": "2024-01-19T16:45:00Z"
    }
  ]
}
```

**Withdrawal Status Values:**
- `pending` - Waiting for admin approval
- `approved` - Approved but not yet processed
- `rejected` - Rejected by admin
- `processed` - Withdrawal completed and funds deducted

---

### 34. View All Withdrawal Requests (Admin)
**Endpoint:** `GET /api/admin/withdrawals/`  
**Authentication:** Admin required

**Description:** View all withdrawal requests from all sellers with optional filtering by status. Includes statistics for dashboard purposes.

**Query Parameters:**
- `status` (optional): Filter by withdrawal status
  - `pending` - Requests awaiting approval
  - `approved` - Approved requests
  - `rejected` - Rejected requests
  - `processed` - Completed withdrawals

**Example:** `GET /api/admin/withdrawals/?status=pending`

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Withdrawal requests retrieved successfully",
  "data": {
    "withdrawal_requests": [
      {
        "id": 3,
        "seller": {
          "id": 3,
          "email": "seller2@example.com",
          "name": "Mike",
          "full_name": "Mike Seller",
          "role": "seller"
        },
        "amount": "1000.00",
        "status": "pending",
        "admin_notes": null,
        "processed_at": null,
        "processed_by": null,
        "created_at": "2024-01-20T11:00:00Z",
        "updated_at": "2024-01-20T11:00:00Z"
      }
    ],
    "statistics": {
      "total_pending": 3,
      "total_approved": 5,
      "total_rejected": 2,
      "total_processed": 15
    }
  }
}
```

**Statistics Breakdown:**
- `total_pending` - Number of requests awaiting approval
- `total_approved` - Number of approved requests (may include unprocessed)
- `total_rejected` - Number of rejected requests
- `total_processed` - Number of completed withdrawals

---

### 35. Approve Withdrawal Request (Admin)
**Endpoint:** `POST /api/admin/withdrawals/{id}/approve/`  
**Authentication:** Admin required

**Description:** Approve a pending withdrawal request and automatically process it via Fapshi payout API to send funds to the seller's mobile money account.

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Withdrawal request approved and processed successfully via Fapshi",
  "data": {
    "id": 3,
    "seller": {
      "id": 3,
      "email": "seller2@example.com",
      "name": "Mike",
      "full_name": "Mike Seller",
      "role": "seller"
    },
    "amount": "1000.00",
    "status": "processed",
    "admin_notes": "Payout initiated via Fapshi. Trans ID: FAPSHI123456",
    "processed_at": "2024-01-20T14:15:00Z",
    "processed_by": {
      "id": 1,
      "email": "admin@example.com",
      "name": "Admin",
      "full_name": "Admin User",
      "role": "admin"
    },
    "created_at": "2024-01-20T11:00:00Z",
    "updated_at": "2024-01-20T14:15:00Z",
    "payout_trans_id": "FAPSHI123456",
    "payout_date_initiated": "2024-01-20"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Cannot approve withdrawal request with status: rejected"
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Insufficient balance. Available: $800.00"
}
```

**Response (Error - 500):**
```json
{
  "success": false,
  "message": "Withdrawal approval failed: Payout failed - Insufficient funds in Fapshi account",
  "error": "HTTP 400",
  "withdrawal_id": 3
}
```

**Processing Details:**
- Validates that the seller still has sufficient wallet balance
- Calls Fapshi payout API to send funds to seller's mobile money
- Uses seller's phone number from profile (or default if not provided)
- Automatically deducts amount from seller's wallet on successful payout
- Creates a transaction record for the withdrawal
- Updates withdrawal request status to 'processed'
- Records Fapshi transaction ID and initiation date
- Records which admin processed the request and when
- If payout fails, withdrawal request remains pending and no funds are deducted

**Fapshi Payout Integration:**
- Uses Fapshi's `/payout` endpoint for mobile money transfers
- Supports Cameroon mobile money providers (MTN, Orange, etc.)
- Transaction ID is stored for tracking and reconciliation
- Automatic retry logic can be implemented if needed

---

### 36. Reject Withdrawal Request (Admin)
**Endpoint:** `POST /api/admin/withdrawals/{id}/reject/`  
**Authentication:** Admin required

**Description:** Reject a pending withdrawal request with optional admin notes explaining the reason.

**Request Body:**
```json
{
  "admin_notes": "Insufficient documentation provided. Please upload bank statement for verification."
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Withdrawal request rejected successfully",
  "data": {
    "id": 4,
    "seller": {
      "id": 4,
      "email": "seller3@example.com",
      "name": "Sarah",
      "full_name": "Sarah Seller",
      "role": "seller"
    },
    "amount": "300.00",
    "status": "rejected",
    "admin_notes": "Insufficient documentation provided. Please upload bank statement for verification.",
    "processed_at": "2024-01-20T13:30:00Z",
    "processed_by": {
      "id": 1,
      "email": "admin@example.com",
      "name": "Admin",
      "full_name": "Admin User",
      "role": "admin"
    },
    "created_at": "2024-01-20T08:45:00Z",
    "updated_at": "2024-01-20T13:30:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Cannot reject withdrawal request with status: processed"
}
```

**Notes:**
- Admin notes are optional but recommended for transparency
- Rejected requests do not affect the seller's wallet balance
- Seller can create a new withdrawal request after rejection

---

### 37. Mark Withdrawal as Processed (Admin)
**Endpoint:** `POST /api/admin/withdrawals/{id}/mark_processed/`  
**Authentication:** Admin required

**Description:** Manually mark an approved withdrawal request as processed. Use this for manual processing scenarios where the approve endpoint wasn't used.

**Request Body:**
```json
{
  "admin_notes": "Processed via bank transfer - Transaction ID: BT202401200001"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Withdrawal request marked as processed successfully",
  "data": {
    "id": 5,
    "seller": {
      "id": 5,
      "email": "seller4@example.com",
      "name": "Tom",
      "full_name": "Tom Seller",
      "role": "seller"
    },
    "amount": "750.00",
    "status": "processed",
    "admin_notes": "Processed via bank transfer - Transaction ID: BT202401200001",
    "processed_at": "2024-01-20T15:45:00Z",
    "processed_by": {
      "id": 1,
      "email": "admin@example.com",
      "name": "Admin",
      "full_name": "Admin User",
      "role": "admin"
    },
    "created_at": "2024-01-19T16:20:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
  }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "message": "Cannot mark as processed. Current status: pending"
}
```

**Use Cases:**
- Manual bank transfers after approval
- External payment processing systems
- Record-keeping for offline withdrawals
- Correcting processing errors

---

## Withdrawal Workflow Examples

### Complete Withdrawal Process:

#### 1. Seller Creates Withdrawal Request
```bash
POST /api/seller/withdrawals/request/
Authorization: Bearer <seller_token>
{
  "amount": "500.00"
}
```

#### 2. Admin Reviews Pending Requests
```bash
GET /api/admin/withdrawals/?status=pending
Authorization: Bearer <admin_token>
```

#### 3. Admin Approves and Processes
```bash
POST /api/admin/withdrawals/3/approve/
Authorization: Bearer <admin_token>
```

#### 4. Seller Views Updated History
```bash
GET /api/seller/withdrawals/history/
Authorization: Bearer <seller_token>
```

### Alternative Manual Processing:

#### 1. Admin Approves (Optional Step)
```bash
POST /api/admin/withdrawals/3/approve/
Authorization: Bearer <admin_token>
```

#### 2. Admin Marks as Processed with Notes
```bash
POST /api/admin/withdrawals/3/mark_processed/
Authorization: Bearer <admin_token>
{
  "admin_notes": "Processed via bank transfer - Ref: BANK123456"
}
```

---

## Withdrawal Security Features

### Balance Validation
- All withdrawal operations validate current wallet balance
- Prevents negative balances and overdrafts
- Real-time balance checking during processing

### Atomic Transactions
- Database transactions ensure data consistency
- All-or-nothing processing prevents partial states
- Rollback capability if any step fails

### Audit Trail
- Complete tracking of who processed each withdrawal
- Timestamps for all status changes
- Admin notes for transparency and documentation

### Status Management
- Clear status progression: pending → approved → processed
- Prevents duplicate processing
- Allows rejection with reasons

---

## Common Withdrawal Scenarios

### Successful Withdrawal
1. Seller has $1000 in wallet
2. Creates $500 withdrawal request (status: pending)
3. Admin approves request via API
4. System calls Fapshi payout API
5. Fapshi sends $500 to seller's mobile money
6. System deducts $500 from wallet
7. Transaction record created with Fapshi transaction ID
8. Status updated to 'processed'

### Payout Failure
1. Seller has $1000 in wallet
2. Creates $500 withdrawal request (status: pending)
3. Admin approves request via API
4. System calls Fapshi payout API
5. Fapshi payout fails (insufficient funds, invalid phone, etc.)
6. Withdrawal request remains pending
7. Admin notes updated with failure reason
8. No funds deducted from seller wallet

### Insufficient Balance
1. Seller has $200 in wallet
2. Tries to create $500 withdrawal request
3. System rejects request immediately
4. Error message: "Insufficient balance. Available: $200.00"

### Multiple Pending Requests
1. Seller creates $300 withdrawal request (pending)
2. Tries to create another $200 withdrawal request
3. System rejects second request
4. Error message: "You already have a pending withdrawal request"

### Rejection with Reason
1. Admin reviews pending withdrawal
2. Rejects due to missing documentation
3. Adds admin notes explaining reason
4. Seller can create new request after resolving issues

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

7. **Withdrawal Security:** All withdrawal operations require admin approval and include comprehensive validation and audit trails.

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

### Seller Withdrawal Process:
1. Seller earns sales and wallet balance increases
2. Create withdrawal request: `POST /api/seller/withdrawals/request/`
3. Admin reviews pending requests: `GET /api/admin/withdrawals/?status=pending`
4. Admin approves and processes: `POST /api/admin/withdrawals/{id}/approve/`
5. Seller views withdrawal history: `GET /api/seller/withdrawals/history/`

