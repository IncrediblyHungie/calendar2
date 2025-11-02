"""
Google Gemini AI Service (Nano Banana)
Handles image generation using Google's Gemini 2.5 Flash Image API
with face-swapping and character consistency
"""
import os
import io
import time
from google import genai
from google.genai import types
from PIL import Image

# Configure Gemini API
# IMPORTANT: API key MUST be set as environment variable - never hardcode!
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required but not set")

def generate_calendar_image(prompt, reference_image_data_list=None):
    """
    Generate a calendar image using Google Gemini 2.5 Flash Image
    with seamless face blending and character consistency

    Args:
        prompt (str): Text description of desired hunky scene
        reference_image_data_list (list): List of image data bytes for character reference

    Returns:
        bytes: Generated image data as PNG bytes
    """
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Build content array with reference images first
        content = []

        # Add reference images if provided (for character consistency)
        if reference_image_data_list:
            # Add instruction about character identity (NOT "face swap")
            ref_instruction = """
REFERENCE IMAGES: Study the person shown in these images carefully.

IDENTITY TO MAINTAIN:
- Analyze ALL reference images to understand this exact person's facial features
- Note their distinctive characteristics: face shape, eye color, nose shape, jawline, skin tone, hair texture
- This is NOT a face swap - create a natural, seamless photo of THIS EXACT PERSON in the described scene
- The person should look like a natural blend of their features across all reference images
- Maintain their unique identity while placing them naturally in the scene
"""
            content.append(ref_instruction)

            # Add up to 3 best reference images for character consistency
            for img_data in reference_image_data_list[:3]:
                try:
                    # Load image and add to content
                    img = Image.open(io.BytesIO(img_data))
                    # Resize if too large (max 4MP for Gemini)
                    max_pixels = 4_000_000
                    if img.width * img.height > max_pixels:
                        ratio = (max_pixels / (img.width * img.height)) ** 0.5
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    content.append(img)
                except Exception as e:
                    print(f"Error loading reference image: {e}")

        # Enhanced prompt with seamless blending and framing
        enhanced_prompt = f"""
{prompt}

CHARACTER CONSISTENCY (CRITICAL):
- Create a photo of THIS EXACT PERSON (from reference images) in this scene
- Maintain their distinctive facial features naturally and seamlessly
- This should look like a real photo of them, not a composite or face swap
- Keep their eye color, skin tone, facial structure, and unique characteristics
- Blend their identity naturally into the scene

COMPOSITION & FRAMING (CRITICAL - FOLLOW EXACTLY):
- CAMERA DISTANCE: Shot from 12-15 feet away for WIDE framing with generous margins
- HEADROOM: Leave SIGNIFICANT empty space above the head (at least 15-20% of image height above head)
- MEDIUM-WIDE SHOT: Show full person from head to mid-thigh or knees - NEVER crop the head
- FULL BODY VISIBLE: Entire head, torso, and upper legs must be completely in frame with room to spare
- MARGINS: Ensure ample space on all sides - top, bottom, left, right (subject should occupy central 60-70% of frame)
- CENTERED COMPOSITION: Subject prominently centered with generous breathing room around them
- WIDER FRAMING: If in doubt, zoom OUT more - we need extra space for printing safety margins
- Use 50mm lens perspective (NOT 85mm) for wider field of view and more environmental context
- Professional fitness photography composition with commercial print safety margins

VISUAL QUALITY:
- Photorealistic, professional photography quality
- High resolution, suitable for calendar printing
- Vibrant colors, dramatic lighting that highlights muscular physique
- Dynamic pose that's ridiculously sexy and over-the-top hilarious
- Cinematic lighting with clear focus on subject

Style: Professional fitness/glamour photography meets comedy photoshoot - natural, seamless, hilarious
"""

        content.append(enhanced_prompt)

        # Generate the image using Gemini 2.5 Flash Image (Nano Banana)
        # Use 3:4 aspect ratio (portrait) for better full-body framing
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=content,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                temperature=0.7,  # Balanced for consistency and creativity
                image_config=types.ImageConfig(
                    aspect_ratio='3:4'  # Portrait orientation for full person visibility
                )
            )
        )

        # Extract PNG image data from response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        return part.inline_data.data

        raise Exception("No image generated in response")

    except Exception as e:
        print(f"Error generating image with Gemini: {str(e)}")
        raise


def generate_calendar_images_batch(project_id, prompts, reference_image_data_list):
    """
    Generate all 12 calendar images for a project using face-swapping

    Args:
        project_id (int): Calendar project ID
        prompts (dict): Dictionary mapping month number (1-12) to enhanced prompt text
        reference_image_data_list (list): List of image data bytes for face reference

    Returns:
        dict: Dictionary mapping month number to generated image data
    """
    from app import db
    from app.models import CalendarMonth, CalendarProject

    results = {}

    # Update project status
    project = CalendarProject.query.get(project_id)
    if project:
        project.status = 'processing'
        db.session.commit()

    print(f"Starting batch generation for project {project_id}")
    print(f"Using {len(reference_image_data_list)} reference images for face-swapping")

    # Generate each month
    for month_num in range(1, 13):
        try:
            print(f"\n{'='*60}")
            print(f"Generating Month {month_num}/12...")
            print(f"{'='*60}")

            # Get month record
            month = CalendarMonth.query.filter_by(
                project_id=project_id,
                month_number=month_num
            ).first()

            if not month:
                print(f"Warning: Month {month_num} record not found, skipping...")
                continue

            # Update status to processing
            month.generation_status = 'processing'
            db.session.commit()

            # Get the enhanced prompt for this month
            prompt = prompts.get(month_num, f"Month {month_num}")
            print(f"Prompt: {prompt[:100]}...")

            # Generate image with face-swapping
            image_data = generate_calendar_image(prompt, reference_image_data_list)

            # Convert PNG to JPEG for smaller file size
            img = Image.open(io.BytesIO(image_data))
            img_io = io.BytesIO()
            img.convert('RGB').save(img_io, format='JPEG', quality=95)
            jpeg_data = img_io.getvalue()

            # Save to database
            month.master_image_data = jpeg_data
            month.generation_status = 'completed'
            from datetime import datetime
            month.generated_at = datetime.utcnow()
            db.session.commit()

            results[month_num] = jpeg_data
            print(f"✅ Month {month_num} completed! Image size: {len(jpeg_data)} bytes")

            # Rate limiting - wait 3 seconds between requests to avoid quota issues
            if month_num < 12:
                print(f"Waiting 3 seconds before next generation...")
                time.sleep(3)

        except Exception as e:
            print(f"❌ Error generating month {month_num}: {e}")
            if month:
                month.generation_status = 'failed'
                month.error_message = str(e)
                db.session.commit()

    # Update project status to preview if all completed
    if project:
        completed_count = sum(
            1 for m in project.calendar_months
            if m.generation_status == 'completed'
        )
        print(f"\nGeneration complete: {completed_count}/12 months succeeded")

        if completed_count == 12:
            project.status = 'preview'
            print("✅ All months completed! Project ready for preview.")
        else:
            project.status = 'partial'
            print(f"⚠️  Partial completion: {completed_count}/12 months")

        db.session.commit()

    return results


def test_api_connection():
    """Test if Gemini API is configured and working"""
    try:
        if not GOOGLE_API_KEY:
            return False, "Google API key not configured"

        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Simple test generation
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=['A simple red circle on white background'],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
            )
        )

        if response.candidates:
            return True, "API connection successful"
        else:
            return False, "API returned no candidates"

    except Exception as e:
        return False, f"API connection failed: {str(e)}"
