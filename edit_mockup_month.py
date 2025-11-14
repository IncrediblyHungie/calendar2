#!/usr/bin/env python3
"""
Edit Mockup Month Text
Replaces the month text on Printify calendar mockups
"""
import os
from PIL import Image, ImageDraw, ImageFont
import sys

def edit_mockup_month(input_path, output_path, new_month_text):
    """
    Edit the month text on a calendar mockup

    Args:
        input_path: Path to original mockup image
        output_path: Path to save edited mockup
        new_month_text: New month name (e.g., "FEBRUARY", "MARCH")
    """
    print(f"📝 Editing {input_path}...")

    # Open the image
    img = Image.open(input_path)
    draw = ImageDraw.Draw(img)

    # Get image dimensions
    width, height = img.size

    # Approximate location of "JANUARY" text on Printify mockup
    # This is based on the mockup layout we've seen
    text_x = width // 2 - 50  # Center-ish, adjust as needed
    text_y = int(height * 0.62)  # About 62% down the image

    # Cover the old "JANUARY" text with a white rectangle
    # Adjust these coordinates based on your mockup layout
    rect_left = text_x - 120
    rect_top = text_y - 30
    rect_right = text_x + 120
    rect_bottom = text_y + 40

    draw.rectangle([rect_left, rect_top, rect_right, rect_bottom], fill='white')

    # Try to use a bold font similar to the calendar
    try:
        # Try common system fonts
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            'C:\\Windows\\Fonts\\arialbd.ttf',
        ]

        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 28)
                break

        if font is None:
            # Fallback to default font
            font = ImageFont.load_default()
            print("   ⚠️  Using default font (may not match original)")
    except:
        font = ImageFont.load_default()
        print("   ⚠️  Using default font (may not match original)")

    # Draw the new month text
    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), new_month_text, font=font)
    text_width = bbox[2] - bbox[0]

    # Center the text
    final_x = width // 2 - text_width // 2

    draw.text((final_x, text_y), new_month_text, fill='black', font=font)

    # Save the edited image
    img.save(output_path, quality=95)
    print(f"   ✅ Saved: {output_path}")

if __name__ == "__main__":
    # Month mapping
    months = {
        1: "JANUARY",
        2: "FEBRUARY",
        3: "MARCH",
        4: "APRIL",
        5: "MAY",
        6: "JUNE",
        7: "JULY",
        8: "AUGUST",
        9: "SEPTEMBER",
        10: "OCTOBER",
        11: "NOVEMBER",
        12: "DECEMBER"
    }

    if len(sys.argv) < 4:
        print("Usage: python edit_mockup_month.py <input_mockup.jpg> <output_mockup.jpg> <month_number>")
        print("Example: python edit_mockup_month.py sample_month_02_mockup.jpg sample_month_02_mockup_edited.jpg 2")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    month_num = int(sys.argv[3])

    if month_num not in months:
        print(f"❌ Error: Month must be 1-12, got {month_num}")
        sys.exit(1)

    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    month_text = months[month_num]
    edit_mockup_month(input_file, output_file, month_text)
    print(f"✨ Done! Month changed to {month_text}")
