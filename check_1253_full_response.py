#!/usr/bin/env python3
"""
Check full API response for Wall Calendar 2026 (blueprint 1253)
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

    print(f"Checking blueprint {BLUEPRINT_ID}...")
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
    with open('/tmp/blueprint_1253_full_response.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Full API response saved to: /tmp/blueprint_1253_full_response.json")
    print()
    print("Top-level keys in response:")
    for key in data.keys():
        print(f"  - {key}")
    print()

    # Check if placeholders exist at top level
    if 'placeholders' in data:
        print(f"Placeholders found at top level: {len(data['placeholders'])} items")
        if data['placeholders']:
            print("First placeholder:")
            print(json.dumps(data['placeholders'][0], indent=2))
    else:
        print("No 'placeholders' key at top level")

    # Check variants
    if 'variants' in data:
        print(f"\nFound {len(data['variants'])} variants")
        for v in data['variants']:
            if v.get('id') == VARIANT_ID:
                print(f"\nOur variant ({VARIANT_ID}):")
                print(f"  Title: {v.get('title')}")
                if 'placeholders' in v:
                    print(f"  Placeholders: {len(v.get('placeholders', []))} items")
