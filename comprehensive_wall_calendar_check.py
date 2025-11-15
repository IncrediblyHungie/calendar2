#!/usr/bin/env python3
"""
COMPREHENSIVE check of wall calendar blueprint 1253 for back cover support
Checking ALL providers and ALL variants
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
    BLUEPRINT_ID = 1253  # Wall Calendar 2026 - Today's Graphics

    print("=" * 100)
    print(f"COMPREHENSIVE WALL CALENDAR BACK COVER INVESTIGATION")
    print(f"Blueprint: {BLUEPRINT_ID} (Calendar 2026 - Today's Graphics)")
    print("=" * 100)
    print()

    # Step 1: Get ALL print providers for this blueprint
    print("STEP 1: Getting ALL print providers...")
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers.json",
        headers=get_headers(),
        timeout=10
    )
    response.raise_for_status()
    providers = response.json()

    print(f"Found {len(providers)} print provider(s)")
    print()

    all_results = []

    # Step 2: Check EACH provider
    for provider in providers:
        provider_id = provider['id']
        provider_title = provider.get('title', 'Unknown')

        print("-" * 100)
        print(f"PROVIDER {provider_id}: {provider_title}")
        print("-" * 100)

        # Get variants for this provider
        response = requests.get(
            f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{provider_id}/variants.json",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ Error getting variants: Status {response.status_code}")
            continue

        data = response.json()
        variants = data.get('variants', [])

        print(f"  Found {len(variants)} variant(s)")
        print()

        # Check EACH variant
        for i, variant in enumerate(variants, 1):
            variant_id = variant.get('id')
            variant_title = variant.get('title')
            placeholders = variant.get('placeholders', [])

            print(f"  Variant {i}: {variant_title} (ID: {variant_id})")
            print(f"    Total Placeholders: {len(placeholders)}")

            # List ALL placeholder positions
            positions = [p.get('position') for p in placeholders]
            print(f"    Positions: {', '.join(positions)}")

            # Check for back cover (multiple possible names)
            back_cover_variants = ['back', 'back_cover', 'back_page', 'rear', 'rear_cover']
            has_back = any(pos in back_cover_variants for pos in positions)

            if has_back:
                print(f"    ✅ ✅ ✅ HAS BACK COVER! ✅ ✅ ✅")
                for p in placeholders:
                    if p.get('position') in back_cover_variants:
                        print(f"       Position: '{p.get('position')}'")
                        print(f"       Dimensions: {p.get('width')}x{p.get('height')}")
                all_results.append((provider_id, provider_title, variant_id, variant_title, True))
            else:
                print(f"    ❌ No back_cover placeholder")
                all_results.append((provider_id, provider_title, variant_id, variant_title, False))

            print()

        # Save this provider's full response
        with open(f'/tmp/blueprint_1253_provider_{provider_id}_full.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved: /tmp/blueprint_1253_provider_{provider_id}_full.json")
        print()

    # Step 3: SUMMARY
    print("=" * 100)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 100)
    print()

    has_any_back_cover = any(result[4] for result in all_results)

    if has_any_back_cover:
        print("✅ ✅ ✅ BACK COVER SUPPORT FOUND! ✅ ✅ ✅")
        print()
        print("Providers/Variants with back_cover support:")
        for provider_id, provider_title, variant_id, variant_title, has_back in all_results:
            if has_back:
                print(f"  • Provider {provider_id} ({provider_title})")
                print(f"    Variant {variant_id}: {variant_title}")
                print()
    else:
        print("❌ ❌ ❌ NO BACK COVER SUPPORT FOUND ❌ ❌ ❌")
        print()
        print("Wall Calendar Blueprint 1253 does NOT support back_cover customization")
        print("in ANY provider or variant.")
        print()
        print("All variants checked:")
        for provider_id, provider_title, variant_id, variant_title, has_back in all_results:
            print(f"  • Provider {provider_id} ({provider_title}), Variant {variant_id}: {variant_title}")
        print()
        print("The back of the calendar will have Printify's default template")
        print("(typically barcodes, production info, etc.)")
