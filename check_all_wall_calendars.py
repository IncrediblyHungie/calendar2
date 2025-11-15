#!/usr/bin/env python3
"""
Check ALL wall calendar blueprints available on Printify for back cover support
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

# All known calendar blueprints
CALENDAR_BLUEPRINTS = [
    (1253, "Calendar 2026 - Today's Graphics"),
    (965, "Standard Wall Calendar 2026"),
    (1183, "Wall Calendars 2026"),
    (1353, "Desktop Calendar 2026"),
]

with app.app_context():
    print("=" * 100)
    print("CHECKING ALL PRINTIFY CALENDAR BLUEPRINTS FOR BACK COVER SUPPORT")
    print("=" * 100)
    print()

    all_results = []

    for blueprint_id, blueprint_name in CALENDAR_BLUEPRINTS:
        print("-" * 100)
        print(f"BLUEPRINT {blueprint_id}: {blueprint_name}")
        print("-" * 100)

        try:
            # Get print providers
            response = requests.get(
                f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers.json",
                headers=get_headers(),
                timeout=10
            )

            if response.status_code == 401:
                print(f"❌ Unauthorized - API token issue")
                continue

            if response.status_code != 200:
                print(f"❌ Error: Status {response.status_code}")
                continue

            providers = response.json()
            if not providers:
                print(f"❌ No providers found")
                continue

            provider_id = providers[0]['id']
            provider_title = providers[0].get('title', 'Unknown')
            print(f"Provider: {provider_id} ({provider_title})")

            # Get variants
            response = requests.get(
                f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json",
                headers=get_headers(),
                timeout=10
            )

            if response.status_code != 200:
                print(f"❌ Error getting variants: Status {response.status_code}")
                continue

            data = response.json()
            variants = data.get('variants', [])

            if not variants:
                print(f"❌ No variants found")
                continue

            # Check first variant for placeholders
            first_variant = variants[0]
            placeholders = first_variant.get('placeholders', [])
            positions = [p.get('position') for p in placeholders]

            print(f"Variant: {first_variant.get('title')} (ID: {first_variant.get('id')})")
            print(f"Total Placeholders: {len(placeholders)}")
            print(f"Positions: {', '.join(positions)}")

            # Check for back cover
            back_cover_variants = ['back', 'back_cover', 'back_page', 'rear', 'rear_cover']
            has_back = any(pos in back_cover_variants for pos in positions)

            if has_back:
                print(f"\n✅ ✅ ✅ HAS BACK COVER! ✅ ✅ ✅")
                for p in placeholders:
                    if p.get('position') in back_cover_variants:
                        print(f"   Position name: '{p.get('position')}'")
                        print(f"   Dimensions: {p.get('width')}x{p.get('height')}")
                all_results.append((blueprint_id, blueprint_name, True, p.get('position')))
            else:
                print(f"\n❌ No back cover placeholder")
                all_results.append((blueprint_id, blueprint_name, False, None))

            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    print("=" * 100)
    print("FINAL SUMMARY - ALL CALENDAR BLUEPRINTS")
    print("=" * 100)
    print()

    has_any_back = any(result[2] for result in all_results)

    if has_any_back:
        print("✅ ✅ ✅ BACK COVER SUPPORT FOUND IN THESE BLUEPRINTS: ✅ ✅ ✅")
        print()
        for blueprint_id, name, has_back, position in all_results:
            if has_back:
                print(f"  Blueprint {blueprint_id}: {name}")
                print(f"    Back cover position: '{position}'")
                print()
    else:
        print("❌ ❌ ❌ NO BACK COVER SUPPORT IN ANY CALENDAR BLUEPRINT ❌ ❌ ❌")
        print()
        print("None of Printify's calendar products support back_cover customization:")
        print()
        for blueprint_id, name, has_back, position in all_results:
            print(f"  • Blueprint {blueprint_id}: {name} - NO back_cover")
        print()
        print("This means:")
        print("  - The back of calendars will have Printify's default template")
        print("  - Typically includes: barcodes, production info, SKU, etc.")
        print("  - This is standard for POD (Print-On-Demand) calendar products")
        print("  - Cannot be customized, blanked, or changed via API")
