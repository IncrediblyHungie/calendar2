"""
Standalone Printify Mockup Service
For generating sample calendar mockups without Flask dependencies
"""
import os
import requests
import base64
import time

PRINTIFY_API_BASE = "https://api.printify.com/v1"

# Calendar blueprint configuration
WALL_CALENDAR_CONFIG = {
    'blueprint_id': 1253,  # Calendar (2026) - Today's Graphics
    'name': 'Wall Calendar 2026'
}

def get_headers():
    """Get authorization headers for Printify API"""
    token = os.getenv('PRINTIFY_API_TOKEN')
    if not token:
        raise ValueError("PRINTIFY_API_TOKEN environment variable not set")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_shop_id():
    """Get first shop ID from Printify account"""
    response = requests.get(
        f"{PRINTIFY_API_BASE}/shops.json",
        headers=get_headers(),
        timeout=10
    )
    response.raise_for_status()
    shops = response.json()

    if not shops:
        raise Exception("No Printify shops found. Please create a shop at printify.com first.")

    return shops[0]['id']

def upload_image_to_printify(image_data_bytes, filename="sample.jpg"):
    """
    Upload image to Printify Media Library

    Args:
        image_data_bytes: Raw image bytes (JPEG/PNG)
        filename: Filename for the upload

    Returns:
        str: Printify upload ID
    """
    print(f"   📤 Uploading to Printify: {filename}...")

    # Convert image bytes to base64
    image_b64 = base64.b64encode(image_data_bytes).decode('utf-8')

    payload = {
        "file_name": filename,
        "contents": image_b64
    }

    response = requests.post(
        f"{PRINTIFY_API_BASE}/uploads/images.json",
        headers=get_headers(),
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    upload_data = response.json()

    print(f"   ✓ Uploaded to Printify: {upload_data['id']}")
    return upload_data['id']

def auto_detect_config(blueprint_id):
    """
    Auto-detect print provider and variant for a blueprint

    Returns:
        dict: {'print_provider_id': X, 'variant_id': Y}
    """
    print(f"   🔍 Auto-detecting calendar configuration...")

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
    print(f"   ✓ Found print provider: {provider_id}")

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
    print(f"   ✓ Found variant: {variant_id}")

    return {
        'print_provider_id': provider_id,
        'variant_id': variant_id
    }

def create_sample_calendar(image_id, month_name="June", month_num=6, title="Sample Calendar"):
    """
    Create a simple calendar product with one month's image for mockup preview

    Args:
        image_id: Printify upload ID
        month_name: Month name for the sample
        month_num: Month number (1-12)
        title: Product title

    Returns:
        str: Printify product ID
    """
    print(f"   🎨 Creating calendar product for mockup...")

    shop_id = get_shop_id()
    config = auto_detect_config(WALL_CALENDAR_CONFIG['blueprint_id'])

    # Month position mapping
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]

    placeholders = []

    # Add image to ALL 12 months (calendar needs to be complete for mockup)
    # We'll use camera_label to show the specific month we want
    for month in months:
        placeholders.append({
            "position": month,
            "images": [{
                "id": image_id,
                "x": 0.5,
                "y": 0.5,
                "scale": 0.98,
                "angle": 0
            }]
        })

    payload = {
        "title": title,
        "description": f"Sample calendar with {month_name} image",
        "blueprint_id": WALL_CALENDAR_CONFIG['blueprint_id'],
        "print_provider_id": config['print_provider_id'],
        "variants": [{
            "id": config['variant_id'],
            "price": 2499,
            "is_enabled": True
        }],
        "print_areas": [{
            "variant_ids": [config['variant_id']],
            "placeholders": placeholders
        }]
    }

    response = requests.post(
        f"{PRINTIFY_API_BASE}/shops/{shop_id}/products.json",
        headers=get_headers(),
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    product_data = response.json()

    print(f"   ✓ Created product: {product_data['id']}")
    return product_data['id']

def get_calendar_mockup_url(product_id, month_num=6):
    """
    Get mockup image URL from Printify product

    Args:
        product_id: Printify product ID
        month_num: Month number (1-12) to show in mockup

    Returns:
        str: Mockup image URL (or None if not ready yet)
    """
    print(f"   🖼️  Fetching mockup URL...")

    shop_id = get_shop_id()

    # Map month numbers to camera labels
    # Printify calendars typically have camera labels for each month
    month_names = ["january", "february", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november", "december"]
    camera_label = month_names[month_num - 1]

    # Printify may take a few seconds to generate mockups
    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(
            f"{PRINTIFY_API_BASE}/shops/{shop_id}/products/{product_id}.json",
            headers=get_headers(),
            timeout=30
        )

        response.raise_for_status()
        product_data = response.json()

        # Check if mockup images are available
        images = product_data.get('images', [])
        if images:
            # Get the base mockup URL and modify camera_label to show correct month
            mockup_url = images[0]['src']

            # Replace camera_label parameter to show the correct month
            if '?' in mockup_url:
                base_url = mockup_url.split('?')[0]
                mockup_url = f"{base_url}?camera_label={camera_label}"
            else:
                mockup_url = f"{mockup_url}?camera_label={camera_label}"

            print(f"   ✓ Mockup URL: {mockup_url}")
            return mockup_url

        # Wait and retry
        if attempt < max_attempts - 1:
            print(f"   ⏳ Mockup not ready yet, waiting 3s... (attempt {attempt+1}/{max_attempts})")
            time.sleep(3)

    print(f"   ⚠️  Mockup not generated after {max_attempts} attempts")
    return None

def download_mockup_image(mockup_url, output_path):
    """
    Download mockup image from URL

    Args:
        mockup_url: Image URL from Printify
        output_path: Local file path to save image

    Returns:
        bool: Success status
    """
    print(f"   💾 Downloading mockup image...")

    response = requests.get(mockup_url, timeout=60)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    file_size_kb = len(response.content) / 1024
    print(f"   ✓ Saved mockup: {output_path} ({file_size_kb:.1f} KB)")
    return True

def delete_product(product_id):
    """
    Delete product from Printify (cleanup)

    Args:
        product_id: Printify product ID

    Returns:
        bool: Success status
    """
    try:
        shop_id = get_shop_id()

        response = requests.delete(
            f"{PRINTIFY_API_BASE}/shops/{shop_id}/products/{product_id}.json",
            headers=get_headers(),
            timeout=10
        )

        response.raise_for_status()
        print(f"   🗑️  Deleted product: {product_id}")
        return True

    except Exception as e:
        print(f"   ⚠️  Failed to delete product: {e}")
        return False

def generate_printify_mockup(image_data_bytes, month_name, output_path, month_num=6):
    """
    Complete workflow: Upload image → Create product → Get mockup → Download → Cleanup

    Args:
        image_data_bytes: Raw image bytes
        month_name: Month name for labeling
        output_path: Where to save mockup image
        month_num: Month number (1-12) to display in mockup

    Returns:
        bool: Success status
    """
    print(f"\n   📦 Generating Printify calendar mockup...")

    product_id = None

    try:
        # Step 1: Upload image
        upload_id = upload_image_to_printify(
            image_data_bytes,
            filename=f"sample_{month_name.lower()}.jpg"
        )

        # Step 2: Create calendar product with image on specific month
        product_id = create_sample_calendar(
            upload_id,
            month_name=month_name,
            month_num=month_num,
            title=f"Sample {month_name} Calendar"
        )

        # Step 3: Get mockup URL for the specific month
        mockup_url = get_calendar_mockup_url(product_id, month_num=month_num)

        if not mockup_url:
            print(f"   ❌ Failed to get mockup URL")
            return False

        # Step 4: Download mockup
        success = download_mockup_image(mockup_url, output_path)

        # Step 5: Cleanup (delete product)
        if product_id:
            delete_product(product_id)

        return success

    except Exception as e:
        print(f"   ❌ Mockup generation failed: {e}")

        # Cleanup on failure
        if product_id:
            delete_product(product_id)

        return False
