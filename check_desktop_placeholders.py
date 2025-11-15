#!/usr/bin/env python3
"""
Check placeholders for Desktop Calendar (blueprint 1353)
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
    BLUEPRINT_ID = 1353  # Desktop Calendar 2026

    print(f"=" * 80)
    print(f"BLUEPRINT {BLUEPRINT_ID}: Desktop Calendar (2026)")
    print(f"=" * 80)
    print()

    # Auto-detect provider and variant
    config = auto_detect_config(BLUEPRINT_ID)
    PRINT_PROVIDER_ID = config['print_provider_id']
    VARIANT_ID = config['variant_id']

    print(f"Provider: {PRINT_PROVIDER_ID}, Variant: {VARIANT_ID}")
    print()

    # Get variant details
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{PRINT_PROVIDER_ID}/variants.json",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    # Save full response
    with open('/tmp/blueprint_1353_full_response.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Full API response saved to: /tmp/blueprint_1353_full_response.json")
    print()

    # Check variants
    if 'variants' in data:
        print(f"Found {len(data['variants'])} variants")
        for v in data['variants']:
            if v.get('id') == VARIANT_ID:
                print(f"\nOur variant ({VARIANT_ID}):")
                print(f"  Title: {v.get('title')}")
                if 'placeholders' in v:
                    placeholders = v.get('placeholders', [])
                    print(f"  Total Placeholders: {len(placeholders)}")
                    print(f"\n  All placeholder positions:")
                    for i, p in enumerate(placeholders, 1):
                        position = p.get('position')
                        width = p.get('width')
                        height = p.get('height')
                        print(f"    {i}. {position} ({width}x{height})")

                    # Check for back cover
                    positions = [p.get('position') for p in placeholders]
                    has_back = any(pos in ['back', 'back_cover', 'back_page'] for pos in positions)
                    if has_back:
                        print(f"\n  ✅ HAS BACK COVER PLACEHOLDER!")
                        for p in placeholders:
                            if p.get('position') in ['back', 'back_cover', 'back_page']:
                                print(f"     Position name: '{p.get('position')}'")
                                print(f"     Dimensions: {p.get('width')}x{p.get('height')}")
                    else:
                        print(f"\n  ❌ No back_cover placeholder found")
                        print(f"  Available positions: {', '.join(positions)}")
