#!/usr/bin/env python3
"""
Sample Calendar Image Generator
Generate sample hunk calendar images for marketing/testing purposes

Usage:
    # Generate June image
    python generate_samples.py --month 6 --references ref1.jpg ref2.jpg ref3.jpg

    # Generate multiple months
    python generate_samples.py --months 1 2 6 11 --references ref1.jpg ref2.jpg ref3.jpg

    # Generate all 12 months
    python generate_samples.py --all --references ref1.jpg ref2.jpg ref3.jpg

    # Specify custom output directory
    python generate_samples.py --month 6 --references ref1.jpg ref2.jpg ref3.jpg --output ./samples/

    # Show available months
    python generate_samples.py --list
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.monthly_themes import MONTHLY_THEMES

# Import Gemini service only when needed (avoid API key check for --list)
def get_gemini_service():
    from services.gemini_service import generate_calendar_image
    return generate_calendar_image

def load_reference_images(image_paths):
    """Load reference images from file paths"""
    reference_data = []

    print(f"\n📸 Loading {len(image_paths)} reference images...")
    for path in image_paths:
        if not os.path.exists(path):
            print(f"❌ Error: Reference image not found: {path}")
            sys.exit(1)

        with open(path, 'rb') as f:
            image_data = f.read()
            reference_data.append(image_data)
            file_size_kb = len(image_data) / 1024
            print(f"   ✓ Loaded {os.path.basename(path)} ({file_size_kb:.1f} KB)")

    return reference_data

def generate_month_image(month_num, reference_images, output_dir, with_mockup=False):
    """Generate image for a specific month"""

    if month_num not in MONTHLY_THEMES:
        print(f"❌ Error: Invalid month number {month_num}. Use --list to see available months.")
        return False

    theme = MONTHLY_THEMES[month_num]
    month_name = theme['month']
    prompt = theme['prompt']

    print(f"\n🎨 Generating: {month_name} - {theme['title']}")
    print(f"   Theme: {theme['description']}")
    print(f"   Prompt length: {len(prompt)} characters")

    # Generate image
    print(f"   ⏳ Calling Gemini API...")
    start_time = time.time()

    try:
        generate_calendar_image = get_gemini_service()
        image_data = generate_calendar_image(prompt, reference_images)
        elapsed = time.time() - start_time

        # Save AI-generated image
        output_filename = f"sample_month_{month_num:02d}_{month_name.lower().replace(' ', '_')}.jpg"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'wb') as f:
            f.write(image_data)

        file_size_kb = len(image_data) / 1024
        print(f"   ✅ Generated in {elapsed:.1f}s ({file_size_kb:.1f} KB)")
        print(f"   💾 Saved AI image: {output_path}")

        # Generate Printify mockup if requested
        if with_mockup:
            mockup_filename = f"sample_month_{month_num:02d}_{month_name.lower().replace(' ', '_')}_mockup.jpg"
            mockup_path = os.path.join(output_dir, mockup_filename)

            # Import mockup service
            import printify_mockup_service
            success = printify_mockup_service.generate_printify_mockup(
                image_data,
                month_name,
                mockup_path,
                month_num=month_num
            )

            if success:
                print(f"   ✅ Mockup saved: {mockup_path}")
            else:
                print(f"   ⚠️  Mockup generation failed (AI image still saved)")

        return True

    except Exception as e:
        print(f"   ❌ Generation failed: {str(e)}")
        return False

def list_available_months():
    """Display all available months and their themes"""
    print("\n📅 Available Months:\n")
    print(f"{'Month':<6} {'Name':<12} {'Title':<30} {'Description'}")
    print("-" * 90)

    for month_num in sorted(MONTHLY_THEMES.keys()):
        theme = MONTHLY_THEMES[month_num]
        month_display = "Cover" if month_num == 0 else f"  {month_num}"
        print(f"{month_display:<6} {theme['month']:<12} {theme['title']:<30} {theme['description'][:40]}")

    print(f"\nTotal: {len(MONTHLY_THEMES)} months (0 = Cover, 1-12 = Monthly images)\n")

def main():
    parser = argparse.ArgumentParser(
        description='Generate sample KevCal hunk calendar images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate June image only
  python generate_samples.py --month 6 --references selfie1.jpg selfie2.jpg selfie3.jpg

  # Generate June with Printify calendar mockup
  python generate_samples.py --month 6 --references selfie1.jpg selfie2.jpg selfie3.jpg --with-mockup

  # Generate multiple months with mockups
  python generate_samples.py --months 1 2 6 11 --references selfie1.jpg selfie2.jpg selfie3.jpg --with-mockup

  # Generate all 12 months + cover (AI images only)
  python generate_samples.py --all --references selfie1.jpg selfie2.jpg selfie3.jpg

  # List available months
  python generate_samples.py --list
        """
    )

    # Month selection options
    month_group = parser.add_mutually_exclusive_group()
    month_group.add_argument('--month', type=int, metavar='N',
                            help='Generate single month (0-12, where 0=cover)')
    month_group.add_argument('--months', type=int, nargs='+', metavar='N',
                            help='Generate multiple months (e.g., --months 1 6 11)')
    month_group.add_argument('--all', action='store_true',
                            help='Generate all 13 images (cover + 12 months)')
    month_group.add_argument('--list', action='store_true',
                            help='List available months and exit')

    # Reference images
    parser.add_argument('--references', nargs='+', metavar='IMAGE',
                       help='Reference images (3-10 selfies recommended)')

    # Output directory
    parser.add_argument('--output', '-o', default='./sample_output',
                       help='Output directory (default: ./sample_output)')

    # Delay between generations
    parser.add_argument('--delay', type=int, default=3,
                       help='Delay in seconds between generations (default: 3)')

    # Printify mockup generation
    parser.add_argument('--with-mockup', action='store_true',
                       help='Also generate Printify calendar mockup (requires PRINTIFY_API_TOKEN)')

    args = parser.parse_args()

    # Handle --list option
    if args.list:
        list_available_months()
        return

    # Validate arguments
    if not args.month and not args.months and not args.all:
        parser.print_help()
        print("\n❌ Error: Must specify --month, --months, --all, or --list")
        sys.exit(1)

    if not args.references:
        parser.print_help()
        print("\n❌ Error: Must provide --references (3-10 selfie images recommended)")
        sys.exit(1)

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

    # Determine which months to generate
    if args.all:
        months_to_generate = sorted(MONTHLY_THEMES.keys())
    elif args.months:
        months_to_generate = args.months
    else:
        months_to_generate = [args.month]

    # Load reference images
    reference_images = load_reference_images(args.references)

    # Generate images
    print(f"\n🚀 Starting generation of {len(months_to_generate)} image(s)...")
    print(f"   Output directory: {args.output}")

    successful = 0
    failed = 0

    for i, month_num in enumerate(months_to_generate):
        # Add delay between requests (except first)
        if i > 0:
            print(f"\n   ⏸️  Waiting {args.delay}s before next generation...")
            time.sleep(args.delay)

        success = generate_month_image(month_num, reference_images, args.output, with_mockup=args.with_mockup)

        if success:
            successful += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*90)
    print(f"✨ Generation Complete!")
    print(f"   ✅ Successful: {successful}")
    if failed > 0:
        print(f"   ❌ Failed: {failed}")
    print(f"   📁 Output directory: {args.output}")
    print("="*90 + "\n")

if __name__ == '__main__':
    main()
