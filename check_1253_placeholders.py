#!/usr/bin/env python3
"""
Check placeholders for Wall Calendar 2026 (blueprint 1253)
"""
import os
import sys

# Add app to path
sys.path.insert(0, '/home/peteylinux/Projects/KevCal')

# Set Flask environment
os.environ['FLASK_APP'] = 'run.py'

from app import create_app
from app.services.printify_service import get_headers, auto_detect_config
import requests
import json

app = create_app()

with app.app_context():
    BLUEPRINT_ID = 1253  # Calendar 2026 - Today's Graphics

    print(f"=" * 80)
    print(f"BLUEPRINT {BLUEPRINT_ID}: Wall Calendar 2026 (Today's Graphics)")
    print(f"=" * 80)
    print()

    # Auto-detect provider and variant
    try:
        config = auto_detect_config(BLUEPRINT_ID)
        PRINT_PROVIDER_ID = config['print_provider_id']
        VARIANT_ID = config['variant_id']

        print(f"Auto-detected configuration:")
        print(f"  Print Provider: {PRINT_PROVIDER_ID}")
        print(f"  Variant: {VARIANT_ID}")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

    # Get variant details including placeholders
    print(f"Fetching variant details...")
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{PRINT_PROVIDER_ID}/variants.json",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    # Get placeholders from the response
    placeholders = data.get('placeholders', [])
    print(f"\nFound {len(placeholders)} placeholders:")
    print(f"=" * 80)

    for i, placeholder in enumerate(placeholders, 1):
        position = placeholder.get('position')
        height = placeholder.get('height')
        width = placeholder.get('width')

        if width and height:
            aspect_ratio = width / height
            print(f"\n#{i} - Position: '{position}'")
            print(f"     Dimensions: {width}px × {height}px")
            print(f"     Aspect Ratio: {aspect_ratio:.3f}:1")

    print(f"\n" + "=" * 80)
    print(f"ANALYSIS:")
    print(f"=" * 80)

    # Check for back cover
    positions = [p.get('position') for p in placeholders]
    if 'back' in positions or 'back_cover' in positions:
        print("✅ BACK COVER FOUND!")
        for p in placeholders:
            if p.get('position') in ['back', 'back_cover']:
                print(f"   Position name: '{p.get('position')}'")
                print(f"   Dimensions: {p.get('width')}px × {p.get('height')}px")
    else:
        print("❌ NO BACK COVER PLACEHOLDER")
        print(f"   Available positions: {', '.join(positions)}")

    print(f"\nOur images are 4:3 aspect ratio (1.333:1)")
    print(f"=" * 80)

    # Save full data
    with open('/tmp/blueprint_1253_placeholders.json', 'w') as f:
        json.dump(placeholders, f, indent=2)
    print(f"\nFull placeholder data saved to: /tmp/blueprint_1253_placeholders.json")
