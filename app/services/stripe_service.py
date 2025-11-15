"""
Stripe payment processing integration
Handles checkout sessions, webhooks, and payment verification
"""
import stripe
from flask import current_app

# Product pricing in cents (wall calendar only)
CALENDAR_PRICES = {
    'wall_calendar': 2650,  # $26.50 (25% off $35.33)
}

PRODUCT_NAMES = {
    'wall_calendar': 'Wall Calendar 2026',
}

PRODUCT_DESCRIPTIONS = {
    'wall_calendar': 'Personalized wall calendar (10.8"×8.4") with your AI-generated hunk images. 270gsm semi-glossy paper, wire binding, date grids.',
}

# Combined product info (for cart checkout)
PRODUCT_INFO = {
    'wall_calendar': {
        'name': PRODUCT_NAMES['wall_calendar'],
        'description': PRODUCT_DESCRIPTIONS['wall_calendar'],
        'price': CALENDAR_PRICES['wall_calendar']
    }
}

def create_checkout_session(product_type, success_url, cancel_url, metadata=None, customer_email=None):
    """
    Create Stripe Checkout session for calendar purchase

    Args:
        product_type: 'wall_calendar' or 'desktop'
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels
        metadata: Optional dict of metadata to attach to session
        customer_email: Optional customer email to pre-fill checkout

    Returns:
        dict: {'session_id': str, 'url': str}
    """
    if product_type not in CALENDAR_PRICES:
        raise ValueError(f"Invalid product type: {product_type}")

    price_cents = CALENDAR_PRICES[product_type]
    product_name = PRODUCT_NAMES[product_type]
    description = PRODUCT_DESCRIPTIONS[product_type]

    # Prepare metadata
    session_metadata = {'product_type': product_type}
    if metadata:
        session_metadata.update(metadata)

    # Create checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card', 'link', 'apple_pay', 'google_pay'],  # Enable Apple Pay & Google Pay
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product_name,
                    'description': description,
                    'images': ['https://hunkofthemonth.shop/static/calendar_preview.jpg']
                },
                'unit_amount': price_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=customer_email,  # Pre-fill if provided, otherwise Stripe will collect
        billing_address_collection='auto',  # Collect billing address (shows "same as shipping" checkbox)
        shipping_address_collection={
            'allowed_countries': ['US', 'CA', 'GB', 'AU', 'DE', 'FR', 'ES', 'IT', 'NL', 'BE']
        },
        phone_number_collection={
            'enabled': True
        },
        metadata=session_metadata,
        allow_promotion_codes=True  # Enable discount codes
    )

    return {
        'session_id': session.id,
        'url': session.url
    }

def retrieve_checkout_session(session_id, expand=None):
    """
    Retrieve checkout session details from Stripe

    Args:
        session_id: Stripe checkout session ID
        expand: List of fields to expand (e.g., ['line_items', 'customer'])

    Returns:
        Stripe Session object
    """
    return stripe.checkout.Session.retrieve(
        session_id,
        expand=expand or []
    )

def verify_webhook_signature(payload, signature):
    """
    Verify Stripe webhook signature for security

    Args:
        payload: Raw webhook payload (bytes)
        signature: Stripe-Signature header value

    Returns:
        Stripe Event object if valid

    Raises:
        ValueError if signature invalid
    """
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return event
    except ValueError as e:
        # Invalid payload
        raise ValueError(f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise ValueError(f"Invalid signature: {e}")

def extract_shipping_address(checkout_session):
    """
    Extract shipping address from Stripe checkout session

    Args:
        checkout_session: Stripe Session object

    Returns:
        dict: Formatted shipping address
    """
    # Stripe API 2025-09-30+ stores shipping in collected_information
    if hasattr(checkout_session, 'collected_information') and checkout_session.collected_information:
        shipping = checkout_session.collected_information['shipping_details']['address']
        customer_name = checkout_session.collected_information['shipping_details']['name']
    else:
        # Fallback for older API versions
        shipping = checkout_session.shipping_details.address
        customer_name = checkout_session.customer_details.name

    # Split name into first and last
    name_parts = customer_name.split(maxsplit=1)
    first_name = name_parts[0] if name_parts else customer_name
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    return {
        'first_name': first_name,
        'last_name': last_name,
        'address1': shipping['line1'] if isinstance(shipping, dict) else shipping.line1,
        'address2': (shipping.get('line2') or '') if isinstance(shipping, dict) else (shipping.line2 or ''),
        'city': shipping['city'] if isinstance(shipping, dict) else shipping.city,
        'state': (shipping.get('state') or '') if isinstance(shipping, dict) else (shipping.state or ''),
        'zip': shipping['postal_code'] if isinstance(shipping, dict) else shipping.postal_code,
        'country': shipping['country'] if isinstance(shipping, dict) else shipping.country,
        'phone': checkout_session.customer_details.phone or ''
    }

# ============================================================================
# SETUP INTENT FUNCTIONS (3-Month Preview System)
# ============================================================================

def create_setup_intent(metadata=None):
    """
    Create Setup Intent for card authorization WITHOUT charging
    Used for 3-month preview unlock gate
    Supports Apple Pay, Google Pay, Link, and cards

    Args:
        metadata: Optional dict of metadata (internal_session_id, project_id, etc.)

    Returns:
        dict: {'client_secret': str, 'setup_intent_id': str}
    """
    setup_intent = stripe.SetupIntent.create(
        automatic_payment_methods={'enabled': True},  # Auto-enable Apple Pay, Google Pay, Link, cards
        usage='off_session',  # Allow charging later without customer present
        metadata=metadata or {}
    )

    return {
        'client_secret': setup_intent.client_secret,
        'setup_intent_id': setup_intent.id
    }

def charge_saved_payment_method(payment_method_id, amount_cents, customer_email, metadata=None):
    """
    Charge a previously saved payment method
    Used for final checkout after full calendar preview

    Args:
        payment_method_id: Stripe payment method ID (from Setup Intent)
        amount_cents: Amount in cents (e.g., 2999 for $29.99)
        customer_email: Customer email address
        metadata: Optional dict of metadata

    Returns:
        Stripe PaymentIntent object
    """
    payment_intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency='usd',
        payment_method=payment_method_id,
        confirm=True,
        off_session=True,  # Customer not present
        receipt_email=customer_email,
        metadata=metadata or {},
        description=f"Calendar purchase for {customer_email}"
    )

    return payment_intent
