#!/usr/bin/env python3
"""Quick test to see which models work for image generation"""
import os
from google import genai
from google.genai import types
from PIL import Image
import io

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# Models to test
MODELS = [
    'gemini-2.5-flash-image',
    'gemini-2.0-flash-exp-image-generation',
    'imagen-4.0-generate-001',
    'imagen-4.0-ultra-generate-001',
    'imagen-4.0-fast-generate-001',
]

# Simple test prompt
PROMPT = "A handsome man in a black tuxedo on a rooftop, champagne in hand, fireworks in the night sky, photorealistic"

def test_model(model_name):
    """Test if a model can generate images"""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"{'='*80}")

    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Try generation
        response = client.models.generate_content(
            model=model_name,
            contents=[PROMPT],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                temperature=0.7,
                top_p=0.9,
                image_config=types.ImageConfig(
                    aspect_ratio='4:3'
                )
            )
        )

        # Check for image
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save image
                        img = Image.open(io.BytesIO(part.inline_data.data))
                        filename = f"test_{model_name.replace('/', '_').replace('-', '_')}.png"
                        img.save(filename)
                        print(f"✅ SUCCESS! Image saved: {filename}")
                        print(f"   Size: {img.size}, Mode: {img.mode}")
                        return True

        print(f"❌ No image data in response")
        return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    print("="*80)
    print("QUICK MODEL TEST - Image Generation")
    print("="*80)

    results = {}
    for model in MODELS:
        results[model] = test_model(model)

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    for model, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{status}: {model}")
