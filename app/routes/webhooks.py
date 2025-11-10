"""
Webhook handlers for external service events
Currently handles Stripe payment confirmation webhooks
"""
from flask import Blueprint, request, jsonify
import stripe
from datetime import datetime
from app.services import stripe_service, printify_service, image_padding_service
from app import session_storage

bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events
    Primarily processes checkout.session.completed for order fulfillment
    """
    print("\n" + "="*80)
    print("🔔 WEBHOOK RECEIVED - Stripe event incoming")
    print("="*80)

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    print(f"   Payload size: {len(payload)} bytes")
    print(f"   Has signature: {bool(sig_header)}")

    try:
        # Verify webhook signature for security
        event = stripe_service.verify_webhook_signature(payload, sig_header)
        print(f"✅ Webhook signature verified successfully")
    except ValueError as e:
        print(f"❌ Webhook verification failed: {e}")
        print(f"   Check STRIPE_WEBHOOK_SECRET environment variable")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

    print(f"📨 Received Stripe webhook: {event['type']}")
    print(f"   Event ID: {event.get('id', 'unknown')}")

    # NEW: Handle setup_intent.succeeded event (3-month preview system)
    if event['type'] == 'setup_intent.succeeded':
        print(f"\n{'='*70}")
        print(f"🔓 SETUP INTENT SUCCEEDED - Payment Method Authorized!")
        print(f"{'='*70}")

        setup_intent = event['data']['object']
        internal_session_id = setup_intent.metadata.get('internal_session_id')
        project_id = setup_intent.metadata.get('project_id')
        payment_method_id = setup_intent.payment_method

        print(f"   Session ID: {internal_session_id}")
        print(f"   Project ID: {project_id}")
        print(f"   Payment Method: {payment_method_id}")

        if not internal_session_id:
            print(f"❌ No internal_session_id in metadata!")
            return jsonify({'error': 'Missing session ID'}), 400

        # Save payment method to session
        success = session_storage.save_payment_method_by_session_id(
            internal_session_id,
            payment_method_id
        )

        if success:
            print(f"✅ Payment method saved to session")
            print(f"📱 Frontend will poll and trigger generation")
            print(f"{'='*70}\n")
        else:
            print(f"❌ Failed to save payment method!")

        return jsonify({'success': True})

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']

        # Retrieve full checkout session with expanded data
        checkout_session = stripe_service.retrieve_checkout_session(
            session_obj['id'],
            expand=['line_items', 'customer']
        )

        # Extract payment and customer information
        payment_intent_id = checkout_session.payment_intent
        customer_email = checkout_session.customer_details.email
        product_type = checkout_session.metadata.get('product_type')
        internal_session_id = checkout_session.metadata.get('internal_session_id')
        is_cart_checkout = checkout_session.metadata.get('is_cart_checkout') == 'true'

        print(f"✅ Payment successful!")
        print(f"   Customer: {customer_email}")
        print(f"   Product: {product_type}")
        print(f"   Payment Intent: {payment_intent_id}")
        print(f"   Internal Session ID: {internal_session_id}")
        print(f"   Cart Checkout: {is_cart_checkout}")

        # Extract shipping address
        shipping_address = stripe_service.extract_shipping_address(checkout_session)

        # Create Printify order(s)
        # Note: In production, this should be a background task (Celery/RQ)
        try:
            if is_cart_checkout:
                # MULTI-ORDER FULFILLMENT: Process all cart items
                print("\n🛒 Processing cart checkout with multiple calendars...")
                print(f"   Looking up session ID: {internal_session_id}")

                # DEBUG: Check if session exists
                session_storage._load_storage()
                if internal_session_id in session_storage._storage:
                    session_data = session_storage._storage[internal_session_id]
                    print(f"   ✓ Session found in storage")
                    print(f"   Cart item count in session: {len(session_data.get('cart', []))}")
                    if session_data.get('cart'):
                        print(f"   Cart items: {session_data['cart']}")
                    else:
                        print(f"   ⚠️  Cart is empty in session data!")
                        print(f"   Session keys: {list(session_data.keys())}")
                else:
                    print(f"   ❌ Session ID not found in storage!")
                    print(f"   Available session IDs: {list(session_storage._storage.keys())[:5]}...")

                cart_items = session_storage.get_cart_by_session_id(internal_session_id)

                if not cart_items:
                    print("❌ No cart items found!")
                    return jsonify({'error': 'Cart is empty'}), 400

                print(f"   Found {len(cart_items)} items in cart")

                order_ids = []
                for i, cart_item in enumerate(cart_items, 1):
                    print(f"\n{'='*60}")
                    print(f"📦 Processing cart item {i}/{len(cart_items)}")
                    print(f"   Project ID: {cart_item['project_id']}")
                    print(f"   Product Type: {cart_item['product_type']}")
                    print(f"{'='*60}")

                    try:
                        order_id = create_printify_order(
                            internal_session_id=internal_session_id,
                            stripe_session_id=checkout_session.id,
                            payment_intent_id=payment_intent_id,
                            product_type=cart_item['product_type'],
                            customer_email=customer_email,
                            shipping_address=shipping_address,
                            project_id=cart_item['project_id']  # Specify which project to use
                        )

                        order_ids.append(order_id)
                        print(f"✅ Cart item {i} fulfilled: {order_id}")

                    except Exception as item_error:
                        print(f"❌ Cart item {i} failed: {item_error}")
                        import traceback
                        traceback.print_exc()
                        # Continue with other items even if one fails

                print(f"\n🎉 Cart fulfillment complete: {len(order_ids)}/{len(cart_items)} orders created")

                # Clear cart after successful fulfillment
                session_storage.clear_cart_by_session_id(internal_session_id)
                print("🗑️  Cart cleared")

            else:
                # SINGLE ORDER: Original flow
                order_id = create_printify_order(
                    internal_session_id=internal_session_id,
                    stripe_session_id=checkout_session.id,
                    payment_intent_id=payment_intent_id,
                    product_type=product_type,
                    customer_email=customer_email,
                    shipping_address=shipping_address
                )

                print(f"🎉 Order fulfilled successfully: {order_id}")

        except Exception as e:
            print(f"❌ Printify order creation failed: {e}")
            # In production: save to failed_orders table for manual retry
            import traceback
            traceback.print_exc()

    return jsonify({'success': True})

def create_printify_order(internal_session_id, stripe_session_id, payment_intent_id, product_type, customer_email, shipping_address, project_id=None):
    """
    Create Printify order after successful payment

    This function:
    1. Checks if preview product already exists (reuse if available)
    2. If not, uploads all 12 images to Printify and creates product
    3. Submits the order to Printify for fulfillment

    Args:
        internal_session_id: Internal session ID to look up user's calendar
        stripe_session_id: Stripe checkout session ID
        payment_intent_id: Stripe payment intent ID
        product_type: 'calendar_2026', 'desktop', or 'standard_wall'
        customer_email: Customer email address
        shipping_address: Dict with shipping address fields
        project_id: Optional project ID (for cart checkouts with multiple projects)

    Returns:
        str: Printify order ID

    Note: In production, this should be a background task to avoid
          blocking the webhook response
    """
    print("\n" + "="*60)
    print("📦 Starting Printify Order Creation")
    if project_id:
        print(f"   Project ID: {project_id}")
    print("="*60)

    # Step 1: Check if preview product already exists
    print(f"   Checking for existing preview product...")
    preview_mockup = session_storage.get_preview_mockup_by_session_id(internal_session_id)

    if preview_mockup and preview_mockup.get('product_id'):
        # Reuse existing product!
        product_id = preview_mockup['product_id']
        variant_id = preview_mockup['variant_id']
        print(f"   ✅ Reusing existing preview product: {product_id}")
        print(f"   ⚡ This is MUCH faster than creating a new product!")

        # If variant_id is "auto", auto-detect the real variant ID
        if variant_id == 'auto':
            print("  ℹ️  Variant ID is 'auto', auto-detecting...")
            product_config = printify_service.CALENDAR_PRODUCTS.get(product_type)
            auto_config = printify_service.auto_detect_config(product_config['blueprint_id'])
            variant_id = auto_config['variant_id']
            print(f"  ✓ Auto-detected variant ID: {variant_id}")

    else:
        # No preview product found - create new one
        print(f"   ℹ️  No preview product found, creating new product...")

        # Get user's generated month images from session storage
        # Use project_id if provided (cart checkout), otherwise use active project
        months = session_storage.get_months_by_session_id(internal_session_id, project_id=project_id)

        if not months or len(months) < 12:
            raise Exception(f"Insufficient month images: found {len(months)}, need 12")

        print(f"   Found {len(months)} months in session storage")

        # Upload all images to Printify (cover + 12 months, with smart padding)
        print("\n📤 Uploading images to Printify with face-safe padding...")
        month_names = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november", "december"]

        printify_image_ids = {}

        # Check for cover image (month_number = 0)
        cover_data = next((m for m in months if m['month_number'] == 0), None)
        if cover_data and cover_data.get('master_image_data'):
            print(f"  📸 Processing Cover image...")
            padded_cover = image_padding_service.add_safe_padding(
                cover_data['master_image_data'],
                use_face_detection=False
            )
            upload_data = printify_service.upload_image(
                padded_cover,
                filename="cover.jpg"
            )
            printify_image_ids['cover'] = upload_data['id']
            print(f"  ✓ Cover image uploaded")
        else:
            print(f"  ℹ️  No cover image found (month 0), will use January for front cover")

        # Upload all 12 month images
        for i, month_name in enumerate(month_names):
            month_num = i + 1
            month_data = next((m for m in months if m['month_number'] == month_num), None)

            if not month_data or not month_data.get('master_image_data'):
                raise Exception(f"Missing image data for month {month_num}")

            print(f"  📸 Processing {month_name.capitalize()}...")

            # Apply smart padding to ensure face is fully visible
            padded_image_data = image_padding_service.add_safe_padding(
                month_data['master_image_data'],
                use_face_detection=False  # Set to True if OpenCV installed
            )

            # Upload padded image to Printify
            upload_data = printify_service.upload_image(
                padded_image_data,
                filename=f"{month_name}.jpg"
            )

            printify_image_ids[month_name] = upload_data['id']

        print(f"✅ Uploaded {len(printify_image_ids)} padded images successfully")

        # Get product configuration
        product_config = printify_service.CALENDAR_PRODUCTS.get(product_type)
        if not product_config:
            raise Exception(f"Invalid product type: {product_type}")

        # Create Printify product with uploaded images
        print("\n🎨 Creating Printify product...")
        product_id = printify_service.create_calendar_product(
            product_type=product_type,
            month_image_ids=printify_image_ids,
            title=f"Custom Hunk Calendar for {customer_email}"
        )

        # Get variant ID and resolve if "auto"
        variant_id = product_config['variant_id']

        # If variant_id is "auto", auto-detect the real variant ID
        if variant_id == 'auto':
            print("  ℹ️  Variant ID is 'auto', auto-detecting...")
            auto_config = printify_service.auto_detect_config(product_config['blueprint_id'])
            variant_id = auto_config['variant_id']
            print(f"  ✓ Auto-detected variant ID: {variant_id}")

    # Publish the product (works for both new and existing products)
    print("\n📢 Publishing product...")
    printify_service.publish_product(product_id)

    # Create order
    print("\n📦 Creating Printify order...")
    order_id = printify_service.create_order(
        product_id=product_id,
        variant_id=variant_id,  # Now using real numeric variant ID
        quantity=1,
        shipping_address=shipping_address,
        customer_email=customer_email
    )

    # Auto-submit orders to production
    print("\n🏭 Submitting order to production...")
    printify_service.submit_order(order_id)
    print("✅ Order submitted to production successfully!")

    print("\n✅ Order creation complete!")
    print(f"   Printify Order ID: {order_id}")
    print(f"   Product ID: {product_id}")
    print(f"   Customer: {customer_email}")
    print("="*60 + "\n")

    # Save order details to session storage
    order_info = {
        'stripe_checkout_session_id': stripe_session_id,
        'stripe_payment_intent_id': payment_intent_id,
        'printify_order_id': order_id,
        'printify_product_id': product_id,
        'product_type': product_type,
        'customer_email': customer_email,
        'shipping_address': shipping_address,
        'status': 'submitted',
        'created_at': datetime.now().isoformat()
    }

    session_storage.save_order_info(internal_session_id, order_info)
    print(f"💾 Order info saved to session storage")

    return order_id
