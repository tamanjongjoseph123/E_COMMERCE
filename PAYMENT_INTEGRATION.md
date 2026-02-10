# Payment Gateway Integration Documentation

## Overview
This e-commerce platform now supports Mobile Money (MoMo) payments through the Fapshi payment gateway. The integration allows customers to pay for orders using payment links.

## Environment Variables
Add the following environment variables to your `.env` file:

```env
FAPSHI_API_KEY=your-fapshi-api-key
FAPSHI_API_USER=your-fapshi-api-user
FAPSHI_BASE_URL=https://sandbox.fapshi.com  # Use https://fapshi.com for production
PAYMENT_REDIRECT_URL=https://your-domain.com/payment/success  # Optional: for payment link redirects
```

## Payment Flow

### 1. Checkout Process
1. Customer adds items to cart
2. Customer proceeds to checkout with delivery information
3. Order is created with `payment_status: 'pending'`
4. Customer must initiate payment to confirm the order

### 2. Payment Initiation
Customers use payment links to complete their orders:

#### Payment Link (`initiate_pay`)
- Generates a secure payment link that customer can click to pay
- Customer can pay via web interface using Mobile Money
- No phone number required
- Payment link is sent to customer's email

## API Endpoints

### 1. Initiate Payment
```
POST /api/orders/{order_id}/pay/
```

**Request Body:**
```json
{
    "payment_type": "initiate_pay"  // Only payment links supported
}
```

**Response:**
```json
{
    "success": true,
    "message": "Payment initiated successfully",
    "data": {
        "payment": {
            "id": 1,
            "trans_id": "FAPSHI_TRANSACTION_ID",
            "status": "created",
            "amount": "100.00",
            "payment_type": "initiate_pay"
        },
        "payment_link": "https://sandbox.fapshi.com/pay/xyz123",
        "trans_id": "FAPSHI_TRANSACTION_ID"
    }
}
```

### 2. Check Payment Status
```
GET /api/orders/{order_id}/payment/status/
```

**Response:**
```json
{
    "success": true,
    "message": "Payment status retrieved successfully",
    "data": {
        "id": 1,
        "trans_id": "FAPSHI_TRANSACTION_ID",
        "status": "successful",  // pending, created, successful, failed, expired
        "amount": "100.00",
        "payment_link": "https://sandbox.fapshi.com/pay/xyz123",
        "date_confirmed": "2024-01-01T12:00:00Z"
    }
}
```

### 3. Retry Payment
```
POST /api/orders/{order_id}/payment/retry/
```

Use this endpoint when a payment has failed or expired.

### 4. Payment Webhook
```
POST /api/payments/webhook/
```

This endpoint receives real-time payment status updates from Fapshi. Configure this URL in your Fapshi dashboard.

### 5. View Payments
```
GET /api/payments/my/           // Customer's payments
GET /api/admin/payments/        // All payments (admin only)
```

## Payment Status Flow

1. **pending** - Payment initiated but not yet processed
2. **created** - Payment transaction created with Fapshi
3. **successful** - Payment completed successfully
4. **failed** - Payment failed
5. **expired** - Payment link expired (after 24 hours)

## Order Status Updates

- When payment is **successful**, order `payment_status` changes to `'paid'` and `status` changes to `'processing'`
- Product stock is reduced
- Seller wallets are credited
- Transactions are created

## Customer Payment Experience

1. Customer completes checkout
2. System generates payment link
3. Customer receives payment link via email and can click to pay
4. Customer is redirected to Fapshi's secure payment page
5. Customer selects their Mobile Money provider and confirms payment
6. Payment is processed and customer is redirected back

## Webhook Configuration

1. Log into your Fapshi dashboard
2. Navigate to webhook settings
3. Set webhook URL: `https://your-domain.com/api/payments/webhook/`
4. Select events: `SUCCESSFUL`, `FAILED`, `EXPIRED`

## Error Handling

Common error scenarios:
- Insufficient stock during checkout
- Payment initiation failures
- Network timeouts with Fapshi API
- Expired payment links

## Security Considerations

- All payment endpoints require authentication
- Webhook endpoint validates Fapshi signatures (implement as needed)
- Sensitive payment data is not stored locally
- API keys are stored in environment variables
- Payment links are secure and time-limited

## Testing

Use the Fapshi sandbox environment for testing:
- Base URL: `https://sandbox.fapshi.com`
- Test credentials available in Fapshi documentation
- Test with small amounts first

## Production Deployment

1. Update `FAPSHI_BASE_URL` to `https://fapshi.com`
2. Use production API credentials
3. Configure proper webhook URL
4. Set up SSL certificate for webhook endpoint
5. Monitor payment logs and errors
6. Set up `PAYMENT_REDIRECT_URL` for better user experience

## Support

For Fapshi-specific issues:
- Fapshi Documentation: https://docs.fapshi.com
- Support: support@fapshi.com

For platform-specific issues:
- Check application logs
- Verify environment variables
- Test with sandbox credentials first
