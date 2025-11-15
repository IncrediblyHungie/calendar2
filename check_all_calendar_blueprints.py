#!/usr/bin/env python3
"""
Check all calendar blueprints for back cover support
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

CALENDAR_BLUEPRINTS = [
    (1253, "Calendar 2026 - Today's Graphics"),
    (965, "Standard Wall Calendar 2026"),
    (1183, "Wall Calendars 2026"),
    (1353, "Desktop Calendar 2026"),
]

with app.app_context():
    results = []

    for blueprint_id, name in CALENDAR_BLUEPRINTS:
        print(f"\n{'=' * 80}")
        print(f"Checking Blueprint {blueprint_id}: {name}")
        print(f"{'=' * 80}")

        try:
            # Get print providers
            response = requests.get(
                f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers.json",
                headers=get_headers(),
                timeout=10
            )

            if response.status_code == 401:
                print(f"❌ Unauthorized - API token may have expired")
                continue

            if response.status_code != 200:
                print(f"❌ Error: Status {response.status_code}")
                continue

            providers = response.json()
            if not providers:
                print(f"❌ No providers found")
                continue

            provider_id = providers[0]['id']

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

            print(f"✅ Provider: {provider_id}")
            print(f"✅ Variant: {first_variant.get('title')} (ID: {first_variant.get('id')})")
            print(f"✅ Total Placeholders: {len(placeholders)}")
            print(f"✅ Positions: {', '.join(positions)}")

            # Check for back cover
            has_back = any(pos in ['back', 'back_cover'] for pos in positions)
            if has_back:
                print(f"\n🎉 HAS BACK COVER! 🎉")
                for p in placeholders:
                    if p.get('position') in ['back', 'back_cover']:
                        print(f"   Position name: '{p.get('position')}'")
                        print(f"   Dimensions: {p.get('width')}x{p.get('height')}")
                results.append((blueprint_id, name, True, provider_id, first_variant.get('id')))
            else:
                print(f"\n❌ No back cover placeholder")
                results.append((blueprint_id, name, False, provider_id, first_variant.get('id')))

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n{'=' * 80}")
    print(f"SUMMARY:")
    print(f"{'=' * 80}")

    for blueprint_id, name, has_back, provider_id, variant_id in results:
        status = "✅ HAS BACK COVER" if has_back else "❌ No back cover"
        print(f"\nBlueprint {blueprint_id}: {name}")
        print(f"  {status}")
        if has_back:
            print(f"  Provider: {provider_id}, Variant: {variant_id}")
