"""
Printify API integration for calendar fulfillment
Handles image uploads, product creation, and order submission
"""
import requests
import base64
import time
from flask import current_app

PRINTIFY_API_BASE = "https://api.printify.com/v1"

# Calendar product configurations (wall calendar only)
# All calendars use 3454x2725px images and 13 placeholders (front_cover + 12 months)
CALENDAR_PRODUCTS = {
    'wall_calendar': {
        'blueprint_id': 1253,  # Calendar (2026) - Today's Graphics
        'print_provider_id': 'auto',  # Auto-detect Today's Graphics provider
        'variant_id': 'auto',  # Auto-detect 10.8" × 8.4" variant
        'name': 'Calendar (2026)',
        'title': 'Custom Hunk Calendar 2026',
        'size': '10.8" × 8.4"',  # Today's Graphics size
        'description': '270gsm semi-glossy paper, wire binding, date grids',
        'price': 2650  # $26.50 (updated pricing)
    }
}

# Cache for auto-detected configurations
_config_cache = {}

def get_headers():
    """Get authorization headers for Printify API"""
    token = current_app.config.get('PRINTIFY_API_TOKEN')
    if not token:
        raise ValueError("PRINTIFY_API_TOKEN not configured")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def auto_detect_config(blueprint_id):
    """
    Auto-detect print provider and variant for a blueprint

    Args:
        blueprint_id: Printify blueprint ID

    Returns:
        dict: {'print_provider_id': X, 'variant_id': Y}
    """
    cache_key = f"blueprint_{blueprint_id}"

    # Check cache first
    if cache_key in _config_cache:
        return _config_cache[cache_key]

    try:
        # Get print providers for this blueprint
        response = requests.get(
            f"{PRINTIFY_API_BASE}/catalog/blueprints/{blueprint_id}/print_providers.json",
            headers=get_headers(),
            timeout=10
        )
        response.raise_for_status()
        providers = response.json()

        if not providers:
            raise Exception(f"No print providers found for blueprint {blueprint_id}")

        # Use first available provider
        provider_id = providers[0]['id']

        # Get variants for this provider
        response = requests.get(
            f"{PRINTIFY_API_BASE}/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json",
            headers=get_headers(),
            timeout=10
        )
        response.raise_for_status()
        variants_data = response.json()

        variants = variants_data.get('variants', [])
        if not variants:
            raise Exception(f"No variants found for blueprint {blueprint_id}, provider {provider_id}")

        # Use first variant
        variant_id = variants[0]['id']

        config = {
            'print_provider_id': provider_id,
            'variant_id': variant_id
        }

        # Cache it
        _config_cache[cache_key] = config

        print(f"  ℹ Auto-detected config for blueprint {blueprint_id}: provider={provider_id}, variant={variant_id}")
        return config

    except Exception as e:
        print(f"  ⚠️ Auto-detection failed for blueprint {blueprint_id}: {e}")
        raise Exception(f"Could not auto-detect configuration for blueprint {blueprint_id}. Please configure manually.")

def upload_image(image_data_bytes, filename="month.jpg"):
    """
    Upload image to Printify Media Library

    Args:
        image_data_bytes: Raw image bytes (JPEG/PNG)
        filename: Filename for the upload

    Returns:
        dict: Upload data with 'id' and 'file_name'
    """
    # Convert image bytes to base64
    image_b64 = base64.b64encode(image_data_bytes).decode('utf-8')

    payload = {
        "file_name": filename,
        "contents": image_b64
    }

    response = requests.post(
        f"{PRINTIFY_API_BASE}/uploads/images.json",
        headers=get_headers(),
        json=payload
    )

    response.raise_for_status()
    upload_data = response.json()

    print(f"  ✓ Uploaded {filename}: {upload_data['id']}")
    return upload_data

def get_optimal_scale(product_type, position):
    """
    Calculate optimal scale for 4:3 (1.33:1) landscape images based on product and position

    OPTIMIZED FOR 4:3 ASPECT RATIO (updated Nov 2025)
    - 4:3 shows more environment/context compared to 5:4 (wider = less close-up)
    - Good fit for 10.8"×8.4" wall calendar (only 3.7% mismatch)
    - Desktop monthly images now 40% LARGER (scale 0.95 vs 0.68)

    Scale values determined by placeholder aspect ratios:
    - Lower scale = more zoom out (show more of image with margins)
    - Higher scale = more zoom in (fill placeholder more, crop edges)

    Args:
        product_type: 'wall_calendar' or 'desktop'
        position: 'front_cover' or month name

    Returns:
        float: Optimal scale value
    """
    # Wall Calendar 10.8" × 8.4" (blueprint 1253, Today's Graphics): 1.286:1 aspect ratio
    # - 4:3 (1.33) vs 1.286 → Min scale: 0.964, using 0.98 for balanced fit
    # - Printify API has no "fit to screen" option (only x, y, scale, angle parameters)
    # - Zoomed out to show more environment/context (not too close to camera)
    # NOTE: Wall calendars do NOT have back_cover placeholder
    if product_type == 'wall_calendar':
        return 0.98  # Balanced - shows environment/context, minimal white space (~2%)

    # Fallback (should never reach here with wall calendar only)
    return 0.98

def create_calendar_product(product_type, month_image_ids, title="Custom Hunk Calendar 2026"):
    """
    Create a calendar product with user's images (wall calendar only)

    Args:
        product_type: 'wall_calendar'
        month_image_ids: Dict mapping month names to Printify upload IDs
                         {"january": "upload_id_1", "february": "upload_id_2", ...}
        title: Product title

    Returns:
        str: Printify product ID
    """
    if product_type not in CALENDAR_PRODUCTS:
        raise ValueError(f"Invalid product type: {product_type}")

    config = CALENDAR_PRODUCTS[product_type].copy()

    # Auto-detect configuration if needed
    if config['print_provider_id'] == 'auto' or config['variant_id'] == 'auto':
        print(f"  ℹ Auto-detecting configuration for {config['name']}...")
        auto_config = auto_detect_config(config['blueprint_id'])
        config['print_provider_id'] = auto_config['print_provider_id']
        config['variant_id'] = auto_config['variant_id']

    # Construct print_areas
    print_areas = [
        {
            "variant_ids": [config['variant_id']],
            "placeholders": []
        }
    ]

    # Add front cover (use dedicated cover image if available, fallback to January)
    cover_id = month_image_ids.get("cover")
    if not cover_id:
        cover_id = month_image_ids.get("january")
        print("  ℹ️  Using January image for front cover (no dedicated cover image)")
    else:
        print("  ✓ Using dedicated cover image for front cover")

    # Get optimal scale for cover based on product type
    cover_scale = get_optimal_scale(product_type, 'front_cover')
    print(f"  📐 Cover scale: {cover_scale} (optimized for {product_type})")

    print_areas[0]["placeholders"].append({
        "position": "front_cover",
        "images": [
            {
                "id": cover_id,
                "x": 0.5,  # Center horizontally
                "y": 0.5,  # Center vertically
                "scale": cover_scale,  # Product-specific scale for 16:9 landscape images
                "angle": 0
            }
        ]
    })

    # Add all 12 months
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]

    # Get optimal scale for monthly pages
    monthly_scale = get_optimal_scale(product_type, 'january')  # Same scale for all months
    print(f"  📐 Monthly pages scale: {monthly_scale} (optimized for {product_type})")

    for month in months:
        if month not in month_image_ids:
            raise ValueError(f"Missing image for {month}")

        print_areas[0]["placeholders"].append({
            "position": month,
            "images": [
                {
                    "id": month_image_ids[month],
                    "x": 0.5,
                    "y": 0.5,
                    "scale": monthly_scale,  # Product-specific scale for 16:9 landscape images
                    "angle": 0
                }
            ]
        })

    # NOTE: Wall calendars (blueprint 1253) do NOT have a back_cover placeholder
    # They only have 13 placeholders: front_cover + 12 months (january-december)
    # The back of wall calendars is typically blank or has generic calendar info
    # Desktop calendars may have different placeholder structures - TBD if they support back covers

    payload = {
        "title": title,
        "description": "Personalized calendar with AI-generated hunk images",
        "blueprint_id": config['blueprint_id'],
        "print_provider_id": config['print_provider_id'],
        "variants": [
            {
                "id": config['variant_id'],
                "price": 2499,  # Price in cents - Printify adds their margin
                "is_enabled": True
            }
        ],
        "print_areas": print_areas
    }

    # Get shop ID
    shop_id = get_shop_id()

    response = requests.post(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/products.json",
        headers=get_headers(),
        json=payload
    )

    response.raise_for_status()
    product_data = response.json()

    print(f"  ✓ Created product: {product_data['id']}")
    return product_data['id']

def publish_product(product_id):
    """
    Publish product to make it available for ordering

    Args:
        product_id: Printify product ID

    Returns:
        bool: Success status
    """
    shop_id = get_shop_id()

    payload = {
        "title": True,
        "description": True,
        "images": True,
        "variants": True,
        "tags": True
    }

    response = requests.post(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/products/{product_id}/publish.json",
        headers=get_headers(),
        json=payload
    )

    response.raise_for_status()
    print(f"  ✓ Published product: {product_id}")
    return True

def create_order(product_id, variant_id, quantity, shipping_address, customer_email):
    """
    Create Printify order for fulfillment

    Args:
        product_id: Printify product ID
        variant_id: Variant ID
        quantity: Number of calendars (usually 1)
        shipping_address: Dict with address fields
        customer_email: Customer email

    Returns:
        str: Printify order ID
    """
    shop_id = get_shop_id()

    # Create order payload
    payload = {
        "external_id": f"hotm_{int(time.time())}",  # Unique order reference
        "label": customer_email,
        "line_items": [
            {
                "product_id": product_id,
                "variant_id": variant_id,
                "quantity": quantity
            }
        ],
        "shipping_method": 1,  # Standard shipping (Printify default)
        "send_shipping_notification": True,
        "address_to": {
            "first_name": shipping_address['first_name'],
            "last_name": shipping_address['last_name'],
            "email": customer_email,
            "phone": shipping_address.get('phone', ''),
            "country": shipping_address['country'],
            "region": shipping_address.get('state', ''),
            "address1": shipping_address['address1'],
            "address2": shipping_address.get('address2', ''),
            "city": shipping_address['city'],
            "zip": shipping_address['zip']
        }
    }

    print(f"  🏪 Using Shop ID: {shop_id}")
    print(f"  📦 Product ID: {product_id}")
    print(f"  🔢 Variant ID: {variant_id}")
    print(f"  📧 Customer: {customer_email}")

    response = requests.post(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/orders.json",
        headers=get_headers(),
        json=payload
    )

    if response.status_code != 200:
        # Log the full error response from Printify
        print(f"\n  {'='*50}")
        print(f"  ❌ PRINTIFY CREATE ORDER FAILED")
        print(f"  {'='*50}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Shop ID: {shop_id}")
        print(f"  Product ID: {product_id}")
        print(f"  Variant ID: {variant_id}")
        print(f"  Customer: {customer_email}")
        print(f"  URL: {response.url}")
        print(f"  Raw Response: {response.text}")
        try:
            error_data = response.json()
            print(f"  Error JSON: {error_data}")
        except:
            pass

        # Provide helpful error messages based on status code
        if response.status_code == 400:
            print(f"\n  💡 COMMON CAUSES OF 400 ERROR:")
            print(f"     1. Invalid variant ID for this product")
            print(f"     2. Product not published to shop")
            print(f"     3. Invalid shipping address format")
            print(f"     4. Missing required fields")
        elif response.status_code == 401:
            print(f"\n  💡 AUTHENTICATION ERROR:")
            print(f"     API token may be invalid or expired")
            print(f"     Check PRINTIFY_API_TOKEN secret")
        elif response.status_code == 404:
            print(f"\n  💡 PRODUCT NOT FOUND:")
            print(f"     Product {product_id} doesn't exist in shop {shop_id}")

        print(f"  {'='*50}\n")

    response.raise_for_status()
    order_data = response.json()

    print(f"  ✓ Created order: {order_data['id']}")
    return order_data['id']

def submit_order(order_id):
    """
    Submit order to Printify for production

    Args:
        order_id: Printify order ID

    Returns:
        bool: Success status
    """
    shop_id = get_shop_id()
    print(f"  🏪 Using Shop ID: {shop_id}")
    print(f"  📦 Order ID: {order_id}")

    response = requests.post(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/orders/{order_id}/send_to_production.json",
        headers=get_headers()
    )

    if response.status_code != 200:
        # Log the full error response from Printify
        print(f"\n  {'='*50}")
        print(f"  ❌ PRINTIFY SUBMIT ORDER FAILED")
        print(f"  {'='*50}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Shop ID: {shop_id}")
        print(f"  Order ID: {order_id}")
        print(f"  URL: {response.url}")
        print(f"  Raw Response: {response.text}")
        try:
            error_data = response.json()
            print(f"  Error JSON: {error_data}")
        except:
            pass

        # Provide helpful error messages based on status code
        if response.status_code == 400:
            print(f"\n  💡 COMMON CAUSES OF 400 ERROR:")
            print(f"     1. Manual approval required in Printify account settings")
            print(f"        → Check: https://printify.com/app/account/connections")
            print(f"        → Disable 'Require manual approval for orders'")
            print(f"     2. Missing or invalid payment method in Printify")
            print(f"        → Check: https://printify.com/app/account/billing")
            print(f"     3. Order already submitted or in invalid state")
        elif response.status_code == 401:
            print(f"\n  💡 AUTHENTICATION ERROR:")
            print(f"     API token may be invalid or expired")
            print(f"     Check PRINTIFY_API_TOKEN secret")
        elif response.status_code == 404:
            print(f"\n  💡 ORDER NOT FOUND:")
            print(f"     Order {order_id} doesn't exist in shop {shop_id}")

        print(f"  {'='*50}\n")

    response.raise_for_status()
    print(f"  ✓ Submitted order to production: {order_id}")
    return True

def get_shop_id():
    """
    Get first shop ID from Printify account
    Caches the result in app config
    """
    if current_app.config.get('PRINTIFY_SHOP_ID'):
        return current_app.config['PRINTIFY_SHOP_ID']

    response = requests.get(
        f"{PRINTIFY_API_BASE}/shops.json",
        headers=get_headers()
    )
    response.raise_for_status()
    shops = response.json()

    if not shops:
        raise Exception("No Printify shops found. Please create a shop at printify.com first.")

    shop_id = shops[0]['id']
    current_app.config['PRINTIFY_SHOP_ID'] = shop_id
    print(f"  ℹ Using Printify shop: {shop_id}")
    return shop_id

def get_product_details(product_id):
    """
    Fetch product details including mockup images

    Args:
        product_id: Printify product ID

    Returns:
        dict: Product data including 'images' array with mockup URLs
    """
    shop_id = get_shop_id()

    response = requests.get(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/products/{product_id}.json",
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()
    return response.json()

def create_product_for_preview(month_image_data, product_type='wall_calendar'):
    """
    Create Printify product for preview mockups (BEFORE payment)

    This creates a draft product and returns mockup image URLs
    so users can see realistic calendar preview before purchasing.

    Args:
        month_image_data: Dict mapping month numbers (0-12) to binary image data
                         {0: bytes (cover), 1: bytes, 2: bytes, ..., 12: bytes}
        product_type: 'wall_calendar'

    Returns:
        dict: {
            'product_id': str,
            'variant_id': int,
            'mockup_images': [
                {'src': 'https://...', 'position': 'front', 'variant_ids': [...], 'is_default': bool},
                ...
            ],
            'status': 'success'
        }
    """
    print(f"\n{'='*70}")
    print(f"🎨 CREATING PRODUCT FOR PREVIEW MOCKUPS")
    print(f"{'='*70}\n")

    try:
        # Step 1: Upload cover and all 12 month images with padding
        print("📤 STEP 1: Uploading padded images to Printify...")
        month_image_ids = {}
        month_names = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]

        # Upload cover image (month 0)
        if 0 in month_image_data:
            print("  📸 Uploading front cover image...")
            from app.services.image_padding_service import add_safe_padding
            # Skip watermark for wall calendar cover only (cover IS the logo)
            # Desktop calendar covers still get watermark
            skip_logo = (product_type == 'wall_calendar')
            padded_cover = add_safe_padding(
                month_image_data[0],
                use_face_detection=False,
                skip_watermark=skip_logo
            )
            upload_data = upload_image(padded_cover, "cover_preview.jpg")
            month_image_ids["cover"] = upload_data['id']
            print(f"  ✅ Front cover image uploaded")
            time.sleep(0.1)

        # NOTE: Back cover NOT uploaded - wall calendars don't have back_cover placeholder
        # Blueprint 1253 only supports: front_cover + 12 months (january-december)

        # Upload monthly images (months 1-12)
        for month_num in range(1, 13):
            if month_num not in month_image_data:
                raise ValueError(f"Missing image data for month {month_num}")

            month_name = month_names[month_num - 1]
            filename = f"{month_name}_preview.jpg"

            # Apply padding for print safety
            from app.services.image_padding_service import add_safe_padding
            padded_image = add_safe_padding(
                month_image_data[month_num],
                use_face_detection=False
            )

            upload_data = upload_image(padded_image, filename)
            month_image_ids[month_name] = upload_data['id']

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        print(f"✅ Uploaded {len(month_image_ids)} images (cover + 12 months)\n")

        # Step 2: Create calendar product
        print("🎨 STEP 2: Creating calendar product...")
        product_id = create_calendar_product(
            product_type,
            month_image_ids,
            title=f"Preview Calendar - {int(time.time())}"
        )
        print(f"✅ Product created: {product_id}\n")

        # Step 3: Fetch product details to get mockup images
        print("📸 STEP 3: Fetching product mockup images...")
        product_data = get_product_details(product_id)

        # Extract mockup images
        mockup_images = product_data.get('images', [])
        print(f"✅ Retrieved {len(mockup_images)} mockup images\n")

        # Get variant ID
        config = CALENDAR_PRODUCTS[product_type].copy()
        if config['variant_id'] == 'auto':
            auto_config = auto_detect_config(config['blueprint_id'])
            variant_id = auto_config['variant_id']
        else:
            variant_id = config['variant_id']

        print(f"{'='*70}")
        print(f"✅ PREVIEW PRODUCT CREATION COMPLETE")
        print(f"{'='*70}")
        print(f"🎨 Product ID: {product_id}")
        print(f"🖼️  Mockup Images: {len(mockup_images)}")
        print(f"📦 Variant ID: {variant_id}")
        print(f"{'='*70}\n")

        return {
            'product_id': product_id,
            'variant_id': variant_id,
            'mockup_images': mockup_images,
            'product_type': product_type,
            'status': 'success'
        }

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ PREVIEW PRODUCT CREATION FAILED")
        print(f"{'='*70}")
        print(f"Error: {str(e)}")
        print(f"{'='*70}\n")
        raise

def process_full_order(product_type, month_image_data, shipping_address, customer_email):
    """
    Complete workflow: Upload images, create product, create order, submit to production

    Args:
        product_type: 'wall_calendar'
        month_image_data: Dict mapping month numbers (0-12) to binary image data
                         {0: bytes (cover), 1: bytes, 2: bytes, ..., 12: bytes}
        shipping_address: Dict with required address fields
                         {'first_name', 'last_name', 'address1', 'address2',
                          'city', 'state', 'zip', 'country', 'phone'}
        customer_email: Customer email address

    Returns:
        dict: {
            'product_id': str,
            'order_id': str,
            'status': 'success'
        }
    """
    print(f"\n{'='*70}")
    print(f"🚀 STARTING PRINTIFY FULFILLMENT FOR {product_type.upper()}")
    print(f"{'='*70}\n")

    try:
        # Step 1: Upload cover and all 12 month images
        print("📤 STEP 1: Uploading images...")
        month_image_ids = {}
        month_names = ["january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]

        # Upload cover image (month 0)
        if 0 in month_image_data:
            print("  📸 Uploading front cover image...")
            upload_data = upload_image(month_image_data[0], "cover.jpg")
            month_image_ids["cover"] = upload_data['id']
            print(f"  ✅ Front cover image uploaded")
            time.sleep(0.1)

        # Upload back cover image (month -1) for wall calendar
        if -1 in month_image_data:
            print("  📸 Uploading back cover image...")
            upload_data = upload_image(month_image_data[-1], "back_cover.jpg")
            month_image_ids["back_cover"] = upload_data['id']
            print(f"  ✅ Back cover image uploaded")
            time.sleep(0.1)

        # Upload monthly images (months 1-12)
        for month_num in range(1, 13):
            if month_num not in month_image_data:
                raise ValueError(f"Missing image data for month {month_num}")

            month_name = month_names[month_num - 1]
            filename = f"{month_name}.jpg"

            upload_data = upload_image(month_image_data[month_num], filename)
            month_image_ids[month_name] = upload_data['id']

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        print(f"✅ Uploaded {len(month_image_ids)} images (cover + 12 months)\n")

        # Step 2: Create calendar product
        print("🎨 STEP 2: Creating calendar product...")
        product_id = create_calendar_product(
            product_type,
            month_image_ids,
            title=f"Hunk of the Month Calendar - {customer_email}"
        )
        print(f"✅ Product created: {product_id}\n")

        # Step 3: Get variant ID for this product type
        config = CALENDAR_PRODUCTS[product_type].copy()
        if config['variant_id'] == 'auto':
            auto_config = auto_detect_config(config['blueprint_id'])
            variant_id = auto_config['variant_id']
        else:
            variant_id = config['variant_id']

        # Step 4: Create order
        print("📦 STEP 3: Creating order...")
        order_id = create_order(
            product_id,
            variant_id,
            quantity=1,
            shipping_address=shipping_address,
            customer_email=customer_email
        )
        print(f"✅ Order created: {order_id}\n")

        # Step 5: Submit to production
        print("🏭 STEP 4: Submitting to production...")
        submit_order(order_id)
        print(f"✅ Order submitted to production!\n")

        print(f"{'='*70}")
        print(f"✅ FULFILLMENT COMPLETE")
        print(f"{'='*70}")
        print(f"📦 Order ID: {order_id}")
        print(f"🎨 Product ID: {product_id}")
        print(f"📧 Customer: {customer_email}")
        print(f"📍 Ship to: {shipping_address['city']}, {shipping_address['country']}")
        print(f"{'='*70}\n")

        return {
            'product_id': product_id,
            'order_id': order_id,
            'status': 'success'
        }

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ FULFILLMENT FAILED")
        print(f"{'='*70}")
        print(f"Error: {str(e)}")
        print(f"{'='*70}\n")
        raise
