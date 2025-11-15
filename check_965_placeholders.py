#!/usr/bin/env python3
"""
Check placeholders for Standard Wall Calendar (blueprint 965)
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
    BLUEPRINT_ID = 965  # Standard Wall Calendar (2026)

    print(f"=" * 80)
    print(f"BLUEPRINT {BLUEPRINT_ID}: Standard Wall Calendar (2026)")
    print(f"=" * 80)
    print()

    # Get print providers
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers.json",
        headers=get_headers()
    )
    response.raise_for_status()
    providers = response.json()

    if not providers:
        print("No providers found")
        exit(1)

    PRINT_PROVIDER_ID = providers[0]['id']
    print(f"Provider: {PRINT_PROVIDER_ID}")

    # Get variants
    response = requests.get(
        f"https://api.printify.com/v1/catalog/blueprints/{BLUEPRINT_ID}/print_providers/{PRINT_PROVIDER_ID}/variants.json",
        headers=get_headers()
    )
    response.raise_for_status()
    data = response.json()

    # Check variants
    if 'variants' in data:
        for v in data['variants']:
            placeholders = v.get('placeholders', [])
            positions = [p.get('position') for p in placeholders]

            print(f"\nVariant: {v.get('title')} (ID: {v.get('id')})")
            print(f"  Placeholders: {len(placeholders)}")
            print(f"  Positions: {', '.join(positions)}")

            # Check for back cover
            if 'back' in positions or 'back_cover' in positions:
                print(f"  ✅ HAS BACK COVER!")
                for p in placeholders:
                    if p.get('position') in ['back', 'back_cover']:
                        print(f"     Position: '{p.get('position')}'")
                        print(f"     Dimensions: {p.get('width')}x{p.get('height')}")
