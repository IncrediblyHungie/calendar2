#!/usr/bin/env python3
"""
Multi-Person Sample Calendar Image Generator
Generate sample calendar images for multiple people at once

Usage:
    # Generate June image for all 3 people
    python generate_multi_person_samples.py --month 6

    # Generate June with mockups for all 3 people
    python generate_multi_person_samples.py --month 6 --with-mockup

    # Generate multiple months for all 3 people
    python generate_multi_person_samples.py --months 1 6 11

    # Custom reference directory
    python generate_multi_person_samples.py --month 6 --references-dir ./custom_faces/
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.monthly_themes import MONTHLY_THEMES

# Import Gemini service only when needed
def get_gemini_service():
    from services.gemini_service import generate_calendar_image
    return generate_calendar_image

def get_person_folders(references_dir):
    """
    Find all person folders in the references directory

    Returns:
        list: [(person_name, folder_path, image_files), ...]
    """
    references_path = Path(references_dir)

    if not references_path.exists():
        print(f"❌ Error: References directory not found: {references_dir}")
        sys.exit(1)

    person_folders = []

    # Find all subdirectories
    for folder in references_path.iterdir():
        if folder.is_dir():
            # Find all image files in this folder
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                image_files.extend(folder.glob(ext))

            if image_files:
                person_folders.append((folder.name, str(folder), [str(f) for f in image_files]))

    return person_folders

def load_reference_images(image_paths):
    """Load reference images from file paths"""
    reference_data = []

    for path in image_paths:
        if not os.path.exists(path):
            print(f"      ⚠️  Warning: Image not found: {path}")
            continue

        with open(path, 'rb') as f:
            image_data = f.read()
            reference_data.append(image_data)

    return reference_data

def generate_month_image_for_person(month_num, person_name, reference_images, output_dir, with_mockup=False):
    """Generate image for a specific month and person"""

    if month_num not in MONTHLY_THEMES:
        print(f"      ❌ Invalid month: {month_num}")
        return False

    theme = MONTHLY_THEMES[month_num]
    month_name = theme['month']
    prompt = theme['prompt']

    print(f"\n   🎨 {person_name} - {month_name} ({theme['title']})")

    # Generate image
    print(f"      ⏳ Calling Gemini API...")
    start_time = time.time()

    try:
        generate_calendar_image = get_gemini_service()
        image_data = generate_calendar_image(prompt, reference_images)
        elapsed = time.time() - start_time

        # Save AI-generated image
        output_filename = f"{person_name}_month_{month_num:02d}_{month_name.lower().replace(' ', '_')}.jpg"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'wb') as f:
            f.write(image_data)

        file_size_kb = len(image_data) / 1024
        print(f"      ✅ Generated in {elapsed:.1f}s ({file_size_kb:.1f} KB)")
        print(f"      💾 {output_path}")

        # Generate Printify mockup if requested
        if with_mockup:
            mockup_filename = f"{person_name}_month_{month_num:02d}_{month_name.lower().replace(' ', '_')}_mockup.jpg"
            mockup_path = os.path.join(output_dir, mockup_filename)

            import printify_mockup_service
            print(f"      📦 Generating calendar mockup...")
            success = printify_mockup_service.generate_printify_mockup(
                image_data,
                month_name,
                mockup_path,
                month_num=month_num
            )

            if success:
                print(f"      ✅ Mockup: {mockup_path}")
            else:
                print(f"      ⚠️  Mockup generation failed")

        return True

    except Exception as e:
        print(f"      ❌ Generation failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Generate sample calendar images for multiple people',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate June for all people in reference_faces/
  python generate_multi_person_samples.py --month 6

  # Generate June with mockups
  python generate_multi_person_samples.py --month 6 --with-mockup

  # Generate multiple months
  python generate_multi_person_samples.py --months 1 6 11 --with-mockup

Structure your reference_faces directory like:
  reference_faces/
  ├── person1/
  │   ├── face1.jpg
  │   ├── face2.jpg
  │   └── face3.jpg
  ├── person2/
  │   └── selfie.jpg
  └── person3/
      ├── photo1.jpg
      └── photo2.jpg
        """
    )

    # Month selection
    month_group = parser.add_mutually_exclusive_group(required=True)
    month_group.add_argument('--month', type=int, metavar='N',
                            help='Generate single month (0-12)')
    month_group.add_argument('--months', type=int, nargs='+', metavar='N',
                            help='Generate multiple months')

    # References directory
    parser.add_argument('--references-dir', default='./reference_faces',
                       help='Directory containing person folders (default: ./reference_faces)')

    # Output directory
    parser.add_argument('--output', '-o', default='./sample_output',
                       help='Output directory (default: ./sample_output)')

    # Delay between generations
    parser.add_argument('--delay', type=int, default=3,
                       help='Delay in seconds between generations (default: 3)')

    # Mockup generation
    parser.add_argument('--with-mockup', action='store_true',
                       help='Also generate Printify calendar mockup')

    args = parser.parse_args()

    # Check API keys
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("   Export it first: export GOOGLE_API_KEY='your-api-key'")
        sys.exit(1)

    if args.with_mockup and not os.getenv('PRINTIFY_API_TOKEN'):
        print("❌ Error: --with-mockup requires PRINTIFY_API_TOKEN environment variable")
        print("   Export it first: export PRINTIFY_API_TOKEN='your-token'")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Find person folders
    print(f"\n🔍 Scanning for people in: {args.references_dir}")
    person_folders = get_person_folders(args.references_dir)

    if not person_folders:
        print(f"\n❌ Error: No person folders with images found in {args.references_dir}")
        print("\nExpected structure:")
        print("  reference_faces/")
        print("  ├── person1/")
        print("  │   └── face1.jpg")
        print("  ├── person2/")
        print("  │   └── face2.jpg")
        print("  └── person3/")
        print("      └── face3.jpg")
        sys.exit(1)

    print(f"\n✅ Found {len(person_folders)} people:")
    for person_name, folder_path, image_files in person_folders:
        print(f"   • {person_name}: {len(image_files)} reference images")

    # Determine which months to generate
    if args.months:
        months_to_generate = args.months
    else:
        months_to_generate = [args.month]

    print(f"\n🚀 Generating {len(months_to_generate)} month(s) × {len(person_folders)} people = {len(months_to_generate) * len(person_folders)} total images")
    if args.with_mockup:
        print(f"   📦 With mockups: {len(months_to_generate) * len(person_folders) * 2} total files")
    print(f"   📁 Output: {args.output}\n")

    # Generate for each person and each month
    total_successful = 0
    total_failed = 0
    generation_count = 0

    for month_num in months_to_generate:
        if month_num not in MONTHLY_THEMES:
            print(f"\n❌ Error: Invalid month {month_num}. Must be 0-12.")
            continue

        theme = MONTHLY_THEMES[month_num]
        print(f"\n{'='*80}")
        print(f"📅 MONTH {month_num}: {theme['month']} - {theme['title']}")
        print(f"{'='*80}")

        for person_name, folder_path, image_files in person_folders:
            # Add delay between generations (except first)
            if generation_count > 0:
                print(f"\n   ⏸️  Waiting {args.delay}s before next generation...")
                time.sleep(args.delay)

            generation_count += 1

            # Load this person's reference images
            print(f"\n   📸 Loading {len(image_files)} reference images for {person_name}...")
            reference_images = load_reference_images(image_files)

            if not reference_images:
                print(f"   ❌ No valid images found for {person_name}")
                total_failed += 1
                continue

            print(f"   ✓ Loaded {len(reference_images)} images")

            # Generate
            success = generate_month_image_for_person(
                month_num,
                person_name,
                reference_images,
                args.output,
                with_mockup=args.with_mockup
            )

            if success:
                total_successful += 1
            else:
                total_failed += 1

    # Summary
    print("\n" + "="*80)
    print(f"✨ Generation Complete!")
    print(f"   ✅ Successful: {total_successful}")
    if total_failed > 0:
        print(f"   ❌ Failed: {total_failed}")
    print(f"   📁 Output directory: {args.output}")
    print("="*80 + "\n")

    # Show generated files
    print("📂 Generated files:")
    output_files = sorted(Path(args.output).glob('*'))
    for f in output_files:
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f} KB)")
    print()

if __name__ == '__main__':
    main()
