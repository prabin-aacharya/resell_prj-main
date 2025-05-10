# Bike Resell Platform

A Django-based bike reselling platform with secure payment integration.

## Setup

1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```
   python manage.py migrate
   ```
4. Run the server:
   ```
   python manage.py runserver
   ```

## Payment Integration

The platform supports two payment gateways:

### Khalti (Popular in Nepal)

1. Sign up for a [Khalti merchant account](https://khalti.com/join/merchant/)
2. Get your API keys from the Khalti Merchant Dashboard
3. Update the following settings in `summproj/settings.py`:
   ```python
   KHALTI_SECRET_KEY = 'your_khalti_secret_key'
   KHALTI_PUBLIC_KEY = 'your_khalti_public_key'
   ```

### Stripe (International)

1. Sign up for a [Stripe account](https://dashboard.stripe.com/register)
2. Get your API keys from the Stripe Dashboard
3. Update the following settings in `summproj/settings.py`:
   ```python
   STRIPE_PUBLISHABLE_KEY = 'your_stripe_publishable_key'
   STRIPE_SECRET_KEY = 'your_stripe_secret_key'
   ```
4. Set up Stripe webhooks:
   - Go to the Stripe Dashboard > Developers > Webhooks
   - Create an endpoint with the URL: `https://yourdomain.com/payment/stripe/webhook/`
   - Add the following events:
     - `checkout.session.completed`
   - Get the signing secret and update:
     ```python
     STRIPE_ENDPOINT_SECRET = 'your_webhook_signing_secret'
     ```

## Testing Payments

### Test Khalti Payments
In test mode, use the following credentials:
- Mobile Number: 9800000000
- MPIN: 1111
- OTP: 987654

### Test Stripe Payments
In test mode, use the following test card:
- Card Number: 4242 4242 4242 4242
- Expiry: Any future date
- CVC: Any 3 digits

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Use real API keys instead of test keys
3. Set up proper domain names in allowed hosts
4. Configure a proper database like PostgreSQL
5. Set up HTTPS for secure payments