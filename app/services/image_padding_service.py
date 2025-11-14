"""
Intelligent image padding service for calendar printing
Ensures faces are always fully visible with multiple safety layers
"""
import io
import os
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

# Safety configuration - optimized for landscape 16:9 (1.78:1) calendars
CONFIG = {
    'min_padding_percent': 20,       # Side padding (20%) - CRITICAL: protects body in narrow crops (desktop monthly 1.19:1)
    'top_padding_percent': 12,       # Top padding (12%) - moderate head protection in landscape
    'bottom_padding_percent': 12,    # Bottom padding (12%) - equal vertical padding for landscape
    'safe_zone_percent': 70,         # Central safe zone (70%) - narrower for landscape, keeps person centered
    'face_margin_percent': 15,       # Extra margin around detected faces (15%)
    'target_aspect_ratio': (16, 9),  # Landscape 16:9 ratio (1.78:1 - matches Gemini, works for all calendar formats)
    'blur_edge_pixels': 20,          # Blur radius for edge extension
    'use_asymmetric_padding': True,  # Use configured padding values
}

def add_watermark(img, logo_size_percent=8, margin_percent=2):
    """
    Add watermark logo to bottom right corner of image

    Args:
        img: PIL Image object
        logo_size_percent: Logo width as percentage of image width (default 8%)
        margin_percent: Margin from edges as percentage of image width (default 2%)

    Returns:
        PIL Image with watermark
    """
    try:
        # Get absolute path to logo
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logo_path = os.path.join(current_dir, 'app', 'static', 'assets', 'images', 'logo', 'logo-transparent.png')

        if not os.path.exists(logo_path):
            print(f"  ⚠️  Logo not found at {logo_path}, skipping watermark")
            return img

        # Load logo
        logo = Image.open(logo_path).convert('RGBA')

        # Calculate logo size (8% of image width by default)
        img_width, img_height = img.size
        logo_width = int(img_width * (logo_size_percent / 100))

        # Maintain logo aspect ratio
        logo_aspect = logo.height / logo.width
        logo_height = int(logo_width * logo_aspect)

        # Resize logo
        logo_resized = logo.resize((logo_width, logo_height), Image.LANCZOS)

        # Calculate position (bottom right with margin)
        margin = int(img_width * (margin_percent / 100))
        x_pos = img_width - logo_width - margin
        y_pos = img_height - logo_height - margin

        # Convert image to RGBA for transparency support
        if img.mode != 'RGBA':
            img_rgba = img.convert('RGBA')
        else:
            img_rgba = img.copy()

        # Paste logo with transparency
        img_rgba.paste(logo_resized, (x_pos, y_pos), logo_resized)

        # Convert back to RGB
        img_watermarked = img_rgba.convert('RGB')

        print(f"  ✨ Watermark added ({logo_width}x{logo_height}px at bottom right)")
        return img_watermarked

    except Exception as e:
        print(f"  ⚠️  Watermark failed: {e}, returning original image")
        return img

def add_safe_padding(image_bytes, use_face_detection=False, skip_watermark=False):
    """
    Add intelligent padding to image with multiple safety layers

    CURRENTLY DISABLED: Returns original image with watermark for direct scaling

    Args:
        image_bytes: Input image as bytes
        use_face_detection: Enable face detection for smart padding (requires cv2)
        skip_watermark: Skip adding watermark/logo (for cover images that ARE the logo)

    Returns:
        bytes: Image with watermark as JPEG bytes
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        original_width, original_height = img.size

        print(f"  🖼️  Original size: {original_width}x{original_height}")
        print(f"  ⚠️  PADDING DISABLED - adding watermark only")

        # Add watermark to bottom right corner (unless skip_watermark=True)
        if skip_watermark:
            print(f"  🚫 Skipping watermark (cover image)")
        else:
            img = add_watermark(img, logo_size_percent=8, margin_percent=2)

        # Convert to JPEG bytes
        output = io.BytesIO()
        img.convert('RGB').save(output, format='JPEG', quality=95)
        return output.getvalue()

    except Exception as e:
        print(f"  ❌ Image processing failed: {e}")
        # Fallback - return original image bytes
        return image_bytes

def create_padded_canvas(img, pad_w, pad_top, pad_bottom, new_width, new_height):
    """
    Create padded canvas with intelligent background fill

    Supports asymmetric padding (different top/bottom values)

    Strategies:
    1. Solid color (average edge color)
    2. Blurred edges
    3. White background (safest fallback)
    """
    try:
        # Strategy 1: Get average edge color
        edge_color = get_average_edge_color(img)

        # Create new canvas with edge color
        padded = Image.new('RGB', (new_width, new_height), edge_color)

        # Strategy 2: Create blurred edge extension for more natural look
        # Extract edges and blur them
        edge_blur = create_blurred_edges(img, pad_w, pad_top, pad_bottom, new_width, new_height)
        if edge_blur:
            padded.paste(edge_blur, (0, 0))

        # Paste original image on canvas with asymmetric vertical positioning
        paste_x = pad_w
        paste_y = pad_top
        padded.paste(img, (paste_x, paste_y))

        return padded

    except Exception as e:
        print(f"    ⚠️  Smart padding failed, using white background: {e}")
        # Fallback: Simple white background
        padded = Image.new('RGB', (new_width, new_height), (255, 255, 255))
        padded.paste(img, (pad_w, pad_top))
        return padded

def get_average_edge_color(img):
    """Calculate average color of image edges"""
    try:
        width, height = img.size
        edge_pixels = []

        # Sample top/bottom edges
        for x in range(0, width, max(1, width // 20)):
            edge_pixels.append(img.getpixel((x, 0)))
            edge_pixels.append(img.getpixel((x, height - 1)))

        # Sample left/right edges
        for y in range(0, height, max(1, height // 20)):
            edge_pixels.append(img.getpixel((0, y)))
            edge_pixels.append(img.getpixel((width - 1, y)))

        # Calculate average
        avg_r = sum(p[0] for p in edge_pixels) // len(edge_pixels)
        avg_g = sum(p[1] for p in edge_pixels) // len(edge_pixels)
        avg_b = sum(p[2] for p in edge_pixels) // len(edge_pixels)

        return (avg_r, avg_g, avg_b)

    except Exception:
        # Fallback to white
        return (255, 255, 255)

def create_blurred_edges(img, pad_w, pad_top, pad_bottom, new_width, new_height):
    """
    Create blurred edge extension for natural-looking padding
    Supports asymmetric vertical padding
    """
    try:
        # Create canvas
        blurred_canvas = Image.new('RGB', (new_width, new_height), (255, 255, 255))

        # Resize image slightly larger to get edge content
        scale = 1.15  # Slightly more expansion for better edge coverage
        scaled_w = int(img.width * scale)
        scaled_h = int(img.height * scale)
        scaled_img = img.resize((scaled_w, scaled_h), Image.LANCZOS)

        # Apply heavy blur
        blurred = scaled_img.filter(ImageFilter.GaussianBlur(CONFIG['blur_edge_pixels']))

        # For asymmetric padding, adjust vertical offset
        # More top padding means we want more top edge content
        offset_x = (scaled_w - new_width) // 2

        # Calculate vertical offset based on asymmetric padding ratio
        total_vertical_pad = pad_top + pad_bottom
        if total_vertical_pad > 0:
            top_ratio = pad_top / total_vertical_pad
            # Shift offset toward top if we have more top padding
            offset_y = int((scaled_h - new_height) * (1 - top_ratio * 0.5))
        else:
            offset_y = (scaled_h - new_height) // 2

        # Crop blurred image to canvas size
        blurred_cropped = blurred.crop((offset_x, offset_y, offset_x + new_width, offset_y + new_height))

        return blurred_cropped

    except Exception:
        return None

def detect_face_position(img):
    """
    Detect face position in image (requires OpenCV/MediaPipe)
    Returns None if face detection unavailable or no face found
    """
    try:
        import cv2
        import numpy as np

        # Convert PIL to OpenCV format
        img_array = np.array(img)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Load OpenCV face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Detect faces
        faces = face_cascade.detectMultiScale(img_cv, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            return None

        # If multiple faces, get bounding box containing all
        if len(faces) > 1:
            x_min = min(f[0] for f in faces)
            y_min = min(f[1] for f in faces)
            x_max = max(f[0] + f[2] for f in faces)
            y_max = max(f[1] + f[3] for f in faces)
            return {
                'x': x_min,
                'y': y_min,
                'width': x_max - x_min,
                'height': y_max - y_min,
                'count': len(faces)
            }

        # Single face
        x, y, w, h = faces[0]
        return {
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'count': 1
        }

    except ImportError:
        # OpenCV not available - skip face detection
        return None
    except Exception:
        return None

def calculate_face_padding(face_info, img_width, img_height):
    """
    Calculate additional padding needed to keep face in safe zone
    """
    # Safe zone boundaries (central 70%)
    safe_zone = CONFIG['safe_zone_percent'] / 100
    safe_left = img_width * (1 - safe_zone) / 2
    safe_right = img_width * (1 + safe_zone) / 2
    safe_top = img_height * (1 - safe_zone) / 2
    safe_bottom = img_height * (1 + safe_zone) / 2

    face_left = face_info['x']
    face_right = face_info['x'] + face_info['width']
    face_top = face_info['y']
    face_bottom = face_info['y'] + face_info['height']

    # Calculate how much face extends beyond safe zone
    extra_pad_left = max(0, safe_left - face_left)
    extra_pad_right = max(0, face_right - safe_right)
    extra_pad_top = max(0, safe_top - face_top)
    extra_pad_bottom = max(0, face_bottom - safe_bottom)

    # Add face margin percentage
    face_margin = CONFIG['face_margin_percent'] / 100
    face_margin_w = int(img_width * face_margin)
    face_margin_h = int(img_height * face_margin)

    # Total extra padding needed
    extra_pad_w = int(max(extra_pad_left, extra_pad_right) + face_margin_w)
    extra_pad_h = int(max(extra_pad_top, extra_pad_bottom) + face_margin_h)

    return extra_pad_w, extra_pad_h

# Configuration helpers
def set_config(key, value):
    """Update configuration value"""
    if key in CONFIG:
        CONFIG[key] = value
        print(f"  ⚙️  Updated {key} = {value}")

def get_config():
    """Get current configuration"""
    return CONFIG.copy()
