#!/usr/bin/env python3
"""
Debug script to check Printify placeholder dimensions
Run this from the app directory where environment variables are loaded
"""
import os
import sys

# Add app to path
sys.path.insert(0, '/home/peteylinux/Projects/KevCal')

# Set Flask environment
os.environ['FLASK_APP'] = 'run.py'

from app import create_app
from app.services.printify_service import get_headers
import requests
import json

app = create_app()

with app.app_context():
    BLUEPRINT_ID = 965
    PRINT_PROVIDER_ID = 99
    VARIANT_ID = 103102

    print(f"=" * 70)
    print(f"GETTING PLACEHOLDER INFO FOR VARIANT {VARIANT_ID}")
    print(f"=" * 70)
    print()

    # Get variant details including placeholders
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{PRINT_PROVIDER_ID}/variants.json",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    # Find our variant
    variant = None
    for v in data.get('variants', []):
        if v['id'] == VARIANT_ID:
            variant = v
            break

    if not variant:
        print(f"ERROR: Variant {VARIANT_ID} not found")
        exit(1)

    print(f"Variant: {variant.get('title', 'Unknown')}")
    print(f"Options: {json.dumps(variant.get('options', {}), indent=2)}")
    print()

    # Get placeholder info
    placeholders = variant.get('placeholders', [])
    print(f"Found {len(placeholders)} placeholders:")
    print()

    for placeholder in placeholders:
        position = placeholder.get('position')
        height = placeholder.get('height')
        width = placeholder.get('width')

        if width and height:
            aspect_ratio = width / height
            print(f"Position: {position}")
            print(f"  Dimensions: {width}px × {height}px")
            print(f"  Aspect Ratio: {aspect_ratio:.3f}:1")
            print()

    print(f"=" * 70)
    print(f"RECOMMENDATION:")
    print(f"Our images are 16:9 = 1.778:1")
    print(f"Compare this to the placeholder aspect ratios above")
    print(f"=" * 70)
