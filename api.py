Generate a payment link POST
/
initiate-pay 
Endpoint
POST /initiate-pay
curl --request POST \
  --url https://sandbox.fapshi.com/initiate-pay \
  --header 'Content-Type: application/json' \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>' \
  --data '
{
  "amount": 101,
  "email": "jsmith@example.com",
  "redirectUrl": "<string>",
  "userId": "<string>",
  "externalId": "<string>",
  "message": "<string>"
}
'
200
{
  "message": "<string>",
  "link": "<string>",
  "transId": "<string>",
  "dateInitiated": "2023-12-25"
}


Initiate a Direct Payment Request
Send a payment request directly to a user’s mobile device.

POST
/
direct-pay

Try it
​
Endpoint
POST /direct-pay
Send a payment request directly to a user’s mobile device. You are responsible for building your own checkout and verifying payment status.
Direct payment transactions cannot and do not expire. Consequently, their final state is either SUCCESSFUL or FAILED.
Direct pay is disabled by default on live environment; Follow the steps in the Activate Direct pay on your Live Fapshi API guide to enable direct pay in live mode.
curl --request POST \
  --url https://sandbox.fapshi.com/direct-pay \
  --header 'Content-Type: application/json' \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>' \
  --data '
{
  "amount": 101,
  "phone": "<string>",
  "medium": "mobile money",
  "name": "<string>",
  "email": "jsmith@example.com",
  "userId": "<string>",
  "externalId": "<string>",
  "message": "<string>"
}
'
200
{
  "message": "<string>",
  "transId": "<string>",
  "dateInitiated": "2023-12-25"
}


Get Payment Transaction Status
Retrieve the status of a payment transaction using its transaction ID.

GET
/
payment-status
/
{transId}

Try it
​
Endpoint
GET /payment-status/:transId
curl --request GET \
  --url https://sandbox.fapshi.com/payment-status/{transId} \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>'
[
  {
    "transId": "<string>",
    "status": "CREATED",
    "medium": "mobile money",
    "serviceName": "<string>",
    "amount": 123,
    "revenue": 123,
    "payerName": "<string>",
    "email": "jsmith@example.com",
    "redirectUrl": "<string>",
    "externalId": "<string>",
    "userId": "<string>",
    "webhook": "<string>",
    "financialTransId": "<string>",
    "dateInitiated": "2023-12-25",
    "dateConfirmed": "2023-12-25"
  }
]



Expire a Payment Transaction
Expire a payment link to prevent further payments.

POST
/
expire-pay

Try it
​
Endpoint
POST /expire-pay
curl --request POST \
  --url https://sandbox.fapshi.com/expire-pay \
  --header 'Content-Type: application/json' \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>' \
  --data '
{
  "transId": "<string>"
}
200
{
  "transId": "<string>",
  "status": "EXPIRED",
  "medium": "mobile money",
  "serviceName": "<string>",
  "amount": 123,
  "revenue": 123,
  "payerName": "<string>",
  "email": "jsmith@example.com",
  "redirectUrl": "<string>",
  "externalId": "<string>",
  "userId": "<string>",
  "webhook": "<string>",
  "financialTransId": "<string>",
  "dateInitiated": "2023-12-25",
  "dateConfirmed": "2023-12-25"
}


Get Transactions by User ID
Retrieve all transactions associated with a specific user ID.

GET
/
transaction
/
{userId}

Try it
​
Endpoint
GET /transaction/:userId
curl --request GET \
  --url https://sandbox.fapshi.com/transaction/{userId} \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>'
  [
  {
    "transId": "<string>",
    "status": "CREATED",
    "medium": "mobile money",
    "serviceName": "<string>",
    "amount": 123,
    "revenue": 123,
    "payerName": "<string>",
    "email": "jsmith@example.com",
    "redirectUrl": "<string>",
    "externalId": "<string>",
    "userId": "<string>",
    "webhook": "<string>",
    "financialTransId": "<string>",
    "dateInitiated": "2023-12-25",
    "dateConfirmed": "2023-12-25"
  }
]

Search Transactions
Search for transactions using various filter criteria.

GET
/
search

Try it
​
Endpoint
curl --request GET \
  --url 'https://sandbox.fapshi.com/search?limit=10&sort=desc' \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>'
  [
  {
    "transId": "<string>",
    "status": "CREATED",
    "medium": "mobile money",
    "serviceName": "<string>",
    "amount": 123,
    "revenue": 123,
    "payerName": "<string>",
    "email": "jsmith@example.com",
    "redirectUrl": "<string>",
    "externalId": "<string>",
    "userId": "<string>",
    "webhook": "<string>",
    "financialTransId": "<string>",
    "dateInitiated": "2023-12-25",
    "dateConfirmed": "2023-12-25"
  }
]

Get Service Balance
Returns the current balance of the service account.

GET
/
balance

Try it
​
Endpoint
GET /balance

curl --request GET \
  --url https://sandbox.fapshi.com/balance \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>'

 200 {
  "service": "<string>",
  "balance": 123,
  "currency": "<string>"
}


Make a Payout
Send money to a user’s mobile money, orange money or fapshi account via a payout-enabled service.

POST
/
payout

Try it
​
Endpoint
POST /payout
Send money to a user’s mobile money, orange money or fapshi account via a payout-enabled service.
After enabling payouts for a service, that service can no longer collect payments. Use separate services for collections and payouts.
Payout is disabled by default in the live environment. To activate payouts in live environment, first implement and test payouts in sandbox environment, then send an email to Developer Support at support.fapshi.com with your Live API User ONLY and mention that you want to enable payouts on your service.
MAKE SURE YOU SEND THE LIVE API USER of your PAYOUT SERVICE.

curl --request POST \
  --url https://sandbox.fapshi.com/payout \
  --header 'Content-Type: application/json' \
  --header 'apikey: <api-key>' \
  --header 'apiuser: <api-key>' \
  --data '
{
  "amount": 101,
  "phone": "<string>",
  "medium": "mobile money",
  "name": "<string>",
  "email": "jsmith@example.com",
  "userId": "<string>",
  "externalId": "<string>",
  "message": "<string>"
}
'{
  "message": "<string>",
  "transId": "<string>",
  "dateInitiated": "2023-12-25"
}


Webhook Integration
Learn how to integrate webhooks to receive real-time payment status updates from Fapshi.

WEBHOOK
/
webhook
/
payment-status
A webhook is an API endpoint made available to external applications that can be called to notify your application whenever a significant event occurs. This allows your app to react or respond immediately to these events.
You can set a webhook URL per service on your Fapshi dashboard. When set, a POST request will be sent to this webhook URL whenever the status of a payment changes to:
SUCCESSFUL — when a payment attempt completes successfully
FAILED — when a payment attempt fails (usually on operator networks like MTN Mobile Money or Orange Money)
EXPIRED — when a payment link expires after 24 hours without successful payment
The body of the webhook request will be the same as the response body returned when querying a payment status.
Your server should respond quickly to webhook requests to avoid timeouts. Fapshi sends only one webhook request per event, regardless of whether your server responds or not.
Authorizations
​
apiuser
stringheaderrequired
​
apikey
stringheaderrequired
Response

200

application/json
Acknowledgement of webhook receipt

​
transId
string
Transaction ID of the payment.

[
  {
    "transId": "<string>",
    "status": "CREATED",
    "medium": "mobile money",
    "serviceName": "<string>",
    "amount": 123,
    "revenue": 123,
    "payerName": "<string>",
    "email": "jsmith@example.com",
    "redirectUrl": "<string>",
    "externalId": "<string>",
    "userId": "<string>",
    "webhook": "<string>",
    "financialTransId": "<string>",
    "dateInitiated": "2023-12-25",
    "dateConfirmed": "2023-12-25"
  }
]
'