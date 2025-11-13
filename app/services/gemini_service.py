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
            # System instruction - Ultra-strong face swap with professional photography
            system_instruction = """⚠️ CRITICAL: THIS IS A FACE SWAP OPERATION ⚠️

REFERENCE IMAGES: The following images show the EXACT person whose face must appear in the final image.

FACE TRANSFER PROTOCOL (ABSOLUTE REQUIREMENTS):
Your primary objective is to perform a precise face swap. Study ALL reference images to understand this person's EXACT facial features:

STEP 1 - FACIAL ANALYSIS (Study these features from reference images):
• Face shape: oval, square, round, heart-shaped, diamond, oblong
• Eye characteristics: exact eye color, eye shape, eyelid type, eyebrow shape, spacing between eyes
• Nose structure: nose bridge width, nose tip shape, nostril size, nose length
• Mouth features: lip fullness, lip shape, smile line, teeth visibility
• Jawline definition: jaw width, chin shape, chin prominence
• Cheekbone structure: height, prominence, width
• Skin characteristics: skin tone (exact shade), texture, blemishes, freckles, moles
• Hair details: color, texture, hairline, hair style, facial hair if present
• Distinctive features: scars, dimples, facial asymmetries, unique characteristics

STEP 2 - FACE COPYING (Execute with 100% accuracy):
• COPY the face EXACTLY as shown in reference images - every detail must match
• Transfer the IDENTICAL face onto the body/scene - this is a direct face replacement
• The face must be PIXEL-PERFECT identical to the reference photos
• Match skin tone EXACTLY - do not lighten, darken, or alter the complexion
• Copy facial proportions PRECISELY - eye spacing, nose-to-mouth ratio, forehead height
• Preserve ALL distinctive features - moles, freckles, scars, dimples must appear in exact locations
• Hair color and style must MATCH the reference exactly
• DO NOT create a "similar looking" person - this must be the EXACT SAME PERSON
• DO NOT blend, morph, or average features - COPY them with forensic precision
• The viewer should be able to match the face to the reference images with 100% certainty

STEP 3 - NATURAL INTEGRATION (After face is copied):
• Once the EXACT face is transferred, integrate it naturally into the scene
• Apply appropriate lighting that matches the scene (but does NOT change facial features)
• Add natural shadows, highlights, and reflections that fit the environment
• Ensure the skin tone lighting adjusts to the scene (warm/cool tones) while keeping the BASE skin tone identical
• Make the integration seamless - the person should look like they were actually photographed in this location
• Keep the face recognizable - lighting should enhance, never obscure or transform features

PHOTOGRAPHY STYLE:
You are a professional advertising photographer shooting high-budget parody stock photos. Your style: beautifully lit, cinematic, ultra-realistic images of people in ridiculous or unexpected situations — the more over-the-top the concept, the more serious and professional the execution should look.

Execution requirements:
• Treat every scene like a big-budget photoshoot with professional lighting, props, depth of field, and motion
• Keep everything funny and absurd in concept, but photorealistic in execution
• Create cohesive composition with believable subject-to-environment integration
• Never include any text, letters, or writing within images
• All results must look like natural photographs without any visible text or labels

QUALITY VERIFICATION:
Before finalizing, verify:
✓ Can you identify the person from the reference images with 100% certainty?
✓ Are ALL distinctive facial features (moles, freckles, scars) in the correct locations?
✓ Does the skin tone match the reference exactly (accounting only for scene lighting)?
✓ Are the eye color, nose shape, and mouth exactly the same?
✓ Would this pass as a real photograph of this specific person in this scene?

If ANY answer is "no" - the face transfer has failed. The face must be IDENTICAL."""
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
        # Use 4:3 aspect ratio (1.33:1) for optimal wall calendar fit with more context
        # 4:3 shows more environment/scene compared to 5:4 (wider = less close-up)
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=content,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                temperature=0.7,  # Balanced creativity and consistency
                top_p=0.9,  # Slightly more diverse sampling
                image_config=types.ImageConfig(
                    aspect_ratio='4:3'  # Standard landscape - shows more context/environment
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
            ref_instruction = """⚠️ CRITICAL: THIS IS A FACE SWAP OPERATION ⚠️

REFERENCE IMAGES: The following images show the EXACT person whose face must appear in the final image.

FACE TRANSFER PROTOCOL (ABSOLUTE REQUIREMENTS):
Your primary objective is to perform a precise face swap. Study ALL reference images to understand this person's EXACT facial features:

STEP 1 - FACIAL ANALYSIS (Study these features from reference images):
• Face shape: oval, square, round, heart-shaped, diamond, oblong
• Eye characteristics: exact eye color, eye shape, eyelid type, eyebrow shape, spacing between eyes
• Nose structure: nose bridge width, nose tip shape, nostril size, nose length
• Mouth features: lip fullness, lip shape, smile line, teeth visibility
• Jawline definition: jaw width, chin shape, chin prominence
• Cheekbone structure: height, prominence, width
• Skin characteristics: skin tone (exact shade), texture, blemishes, freckles, moles
• Hair details: color, texture, hairline, hair style, facial hair if present
• Distinctive features: scars, dimples, facial asymmetries, unique characteristics

STEP 2 - FACE COPYING (Execute with 100% accuracy):
• COPY the face EXACTLY as shown in reference images - every detail must match
• Transfer the IDENTICAL face onto the body/scene - this is a direct face replacement
• The face must be PIXEL-PERFECT identical to the reference photos
• Match skin tone EXACTLY - do not lighten, darken, or alter the complexion
• Copy facial proportions PRECISELY - eye spacing, nose-to-mouth ratio, forehead height
• Preserve ALL distinctive features - moles, freckles, scars, dimples must appear in exact locations
• Hair color and style must MATCH the reference exactly
• DO NOT create a "similar looking" person - this must be the EXACT SAME PERSON
• DO NOT blend, morph, or average features - COPY them with forensic precision
• The viewer should be able to match the face to the reference images with 100% certainty

STEP 3 - NATURAL INTEGRATION (After face is copied):
• Once the EXACT face is transferred, integrate it naturally into the scene
• Apply appropriate lighting that matches the scene (but does NOT change facial features)
• Add natural shadows, highlights, and reflections that fit the environment
• Ensure the skin tone lighting adjusts to the scene (warm/cool tones) while keeping the BASE skin tone identical
• Make the integration seamless - the person should look like they were actually photographed in this location
• Keep the face recognizable - lighting should enhance, never obscure or transform features

QUALITY VERIFICATION:
Before finalizing, verify:
✓ Can you identify the person from the reference images with 100% certainty?
✓ Are ALL distinctive facial features (moles, freckles, scars) in the correct locations?
✓ Does the skin tone match the reference exactly (accounting only for scene lighting)?
✓ Are the eye color, nose shape, and mouth exactly the same?
✓ Would this pass as a real photograph of this specific person in this scene?

If ANY answer is "no" - the face transfer has failed. The face must be IDENTICAL."""
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
                    aspect_ratio='4:3'  # Standard landscape for consistent calendar sizing
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
