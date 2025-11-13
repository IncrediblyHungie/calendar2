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
            # System instruction - Professional photographer persona
            system_instruction = """You are a professional advertising photographer and creative director who shoots high-budget parody stock photos.

Your style: beautifully lit, cinematic, ultra-realistic images of people in ridiculous or unexpected situations — the more over-the-top the concept, the more serious and professional the execution should look.

Rules:
1. Preserve the uploaded person's recognizable facial identity and proportions, but allow re-lighting, color grading, and texture blending for seamless realism.
2. Treat every scene like a big-budget photoshoot — real lighting, props, depth of field, and motion.
3. Keep everything funny and absurd.
4. Prioritize cohesive composition and believable integration between the subject and environment.

Never include any text, letters, or writing within images.
All results must look like natural photographs without any visible text or labels.

REFERENCE IMAGES: Study the person shown in these images carefully. Preserve their recognizable facial identity and proportions while seamlessly integrating them into the scene."""
            content.append(system_instruction)

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

        # Prompts are now complete and optimized - pass through as-is
        content.append(prompt)

        # Generate the image using Gemini 2.5 Flash Image (Nano Banana)
        # Use 4:3 aspect ratio (1.33:1 landscape) - optimized for calendar placeholders
        # This reduces wasted space by 80% compared to 16:9
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=content,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.9,  # Slightly more diverse sampling
                image_config=types.ImageConfig(
                    aspect_ratio='4:3'  # Standard landscape (1.33:1) - near-perfect fit for calendars
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


def generate_delivery_worker_image(reference_image_data_list=None):
    """
    Generate a custom image of the customer as a handsome postal worker delivering a calendar
    This image is shown ONLY on the order success page, not included in the calendar

    Args:
        reference_image_data_list (list): List of user's reference image data bytes

    Returns:
        bytes: Generated image data as PNG bytes
    """
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        content = []

        # Add reference images if provided (to match the customer's appearance)
        if reference_image_data_list:
            ref_instruction = """
REFERENCE IMAGES: Study the person shown in these images carefully.

FACE SWAP INSTRUCTIONS (CRITICAL):
- Analyze ALL reference images to understand this exact person's facial features
- This IS a face swap - transfer their face completely and accurately onto the postal worker body
- Copy every facial feature precisely: eyes, nose, mouth, jawline, cheekbones, skin tone, hair
- Note their distinctive characteristics: face shape, eye color, nose shape, jawline, skin tone, hair texture
- The face must look IDENTICAL to the reference photos
- Maintain their unique identity while placing their exact face as a handsome postal worker
"""
            content.append(ref_instruction)

            # Add up to 3 best reference images
            for img_data in reference_image_data_list[:3]:
                try:
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

        # Use the bonus delivery prompt from monthly themes
        from app.services.monthly_themes import BONUS_DELIVERY_PROMPT
        content.append(BONUS_DELIVERY_PROMPT)

        # Generate the image using Gemini 2.5 Flash Image
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=content,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.9,  # Slightly more diverse sampling
                image_config=types.ImageConfig(
                    aspect_ratio='4:3'  # Standard landscape for web display
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

        raise Exception("No delivery worker image generated in response")

    except Exception as e:
        print(f"Error generating delivery worker image: {str(e)}")
        raise


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
