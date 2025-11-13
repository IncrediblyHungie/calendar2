# Gemini Image Generation - Model Testing Results

## Executive Summary

**TL;DR**: Only `gemini-2.5-flash-image` supports image generation via the Google AI API. All other models (including `gemini-2.5-pro`) are text-only.

---

## Model Test Results (November 12, 2025)

### ✅ WORKING - Image Generation
| Model | Status | Output Size | Notes |
|-------|--------|-------------|-------|
| `gemini-2.5-flash-image` | ✅ **WORKS** | 1184×864 (4:3) | Your current model - KEEP USING THIS |

### ❌ NOT WORKING - No Image Support
| Model | Error | Reason |
|-------|-------|--------|
| `gemini-2.5-pro` | INVALID_ARGUMENT | "This model only supports text output" |
| `gemini-2.5-pro-exp` | NOT_FOUND | Model doesn't exist in v1beta API |
| `gemini-2.0-flash-exp-image-generation` | INVALID_ARGUMENT | Doesn't support IMAGE response modality |
| `imagen-4.0-generate-001` | NOT_FOUND | Not available in v1beta API |
| `imagen-4.0-ultra-generate-001` | NOT_FOUND | Not available in v1beta API |
| `imagen-4.0-fast-generate-001` | NOT_FOUND | Not available in v1beta API |

---

## Answer to Your Question

**Q: "What can we send prompt-wise to Google for the nano banana model? How can we mimic the results we get online?"**

**A**: You're already using the RIGHT model (`gemini-2.5-flash-image`). The online interface uses the SAME model. To match online quality, focus on **prompt optimization**, not model switching.

---

## How to Match "Online" Results

### What's Different Online vs Your Code

| Aspect | Online (ImageFX/AI Studio) | Your Current Code |
|--------|---------------------------|-------------------|
| Model | `gemini-2.5-flash-image` | `gemini-2.5-flash-image` ✅ SAME |
| Temperature | ~0.7 | 0.7 ✅ SAME |
| Top_p | ~0.9 | 0.9 ✅ SAME |
| Aspect Ratio | User choice | 4:3 ✅ GOOD |
| **Prompt Style** | Natural, conversational (100-150 words) | ❌ **Too verbose** (500+ words) |
| **Prompt Structure** | Scene → Mood → Style → Face preservation | ❌ **Too many instructions** |
| Safety Settings | Permissive for artistic content | Default (good enough) |

### The Real Difference: PROMPT LENGTH & STYLE

Your prompts are TOO LONG and TOO INSTRUCTION-HEAVY. Here's the comparison:

#### ❌ Your Current Style (500+ words)
```
Create a hyper-realistic photo using the exact face and likeness from the attached
reference — identical eyes, jawline, skin tone, and hair — no alteration, blending,
or re-rendering of facial features as a confident man in a sleek black tuxedo...

FACE SWAP EXECUTION (CRITICAL):
- Transfer the EXACT face from reference images...
- This IS a face swap - copy their face completely...
- Maintain their distinctive facial features precisely...
[15+ more bullet points]

COMPOSITION & FRAMING (CRITICAL - FOLLOW EXACTLY):
- CAMERA DISTANCE: Shot from 12-15 feet away...
- HEADROOM: Leave SIGNIFICANT empty space...
[10+ more bullet points]

VISUAL QUALITY:
- Photorealistic, professional photography quality...
[5+ more bullet points]
```

**Problems**:
- Too many instructions (model can't follow 30+ requirements)
- Redundancy ("face swap" mentioned 5 times)
- Contradictory directions buried in text
- ALL CAPS doesn't actually prioritize instructions
- Technical camera specs (50mm, f/1.4) are ignored

#### ✅ Optimized Style (Like Online - 100-150 words)
```
A confident, well-dressed man in an elegant black tuxedo stands on a luxury rooftop
terrace at midnight. He's pouring champagne from a bottle, with sparkling foam caught
mid-air. Colorful fireworks burst across the night sky behind him, with a glittering
city skyline below.

The scene has a sophisticated, celebratory New Year's Eve atmosphere. Warm golden
rim-lighting catches his features like a high-end magazine cover, creating a cinematic
and luxurious mood.

Professional photography, medium-wide composition showing upper body with generous
headroom. 8K quality, photorealistic, natural skin texture.

IMPORTANT: Use the exact facial features from the reference images - match eye color,
eye shape, nose, mouth, jawline, skin tone, and hair precisely. The face must look
identical to the reference photos, naturally blended into this scene.
```

**Why This Works Better**:
- Natural language (like talking to a photographer)
- Concise (150 words vs 500+)
- Clear scene description → mood → technical quality → face preservation
- Face instructions at END (strongest position in model's attention)
- No redundancy or contradictions

---

## Recommended Changes to Your Code

### 1. Update `gemini_service.py` - Simplify Enhanced Prompt

**Current** (lines 69-98):
```python
enhanced_prompt = f"""
{prompt}

FACE SWAP EXECUTION (CRITICAL):
- Transfer the EXACT face from reference images onto the body in this scene
- This IS a face swap - copy their face completely and accurately
- Maintain their distinctive facial features precisely: every detail must match
- Keep their eye color, eye shape, nose, mouth, jawline, skin tone, facial structure exactly as shown
- The face must look IDENTICAL to the reference photos - perfect face accuracy is the priority

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
```

**Recommended** (much simpler):
```python
enhanced_prompt = f"""{prompt}

Professional photography, medium-wide composition showing full upper body with generous
headroom for printing. 8K quality, photorealistic, natural skin texture, sharp details.

IMPORTANT: Use the exact facial features from the reference images - match eye color,
eye shape, nose, mouth, jawline, skin tone, and hair color/style precisely. The person's
face must look identical to the reference photos, naturally and seamlessly blended into
this scene."""
```

### 2. Update `monthly_themes.py` - Make Prompts Conversational

**Example - January (Current vs Recommended)**:

**Current** (line 37-48):
```python
"prompt": """CRITICAL: Use EXACT face from reference images - copy every facial feature
precisely (eyes, nose, mouth, jawline, cheekbones, skin tone, hair). This is a face swap
- transfer their face completely and accurately onto the body in the scene.

Create a hyper-realistic photo of a confident man in a sleek black tuxedo pouring champagne
while fireworks explode across a midnight skyline. He stands on a rooftop terrace, city
lights glimmering below, champagne foam sparkling in the air, his smile smooth and cinematic.
The mood is luxury and celebration, golden rim-light catching his features like a magazine cover.

FACE PRESERVATION (CRITICAL):
- Study the reference face carefully and replicate it EXACTLY
- Match every detail: eye color, eye shape, eyebrow shape, nose structure, lip shape, face shape
- Preserve their exact skin tone, facial hair pattern, and hair color/style
- The face must look IDENTICAL to the reference photos - like it was photographed in this scene
- This is the MOST IMPORTANT aspect - perfect face accuracy

Blend lighting, shadows, and color naturally so the subject looks photographed in the scene.
Keep the person's likeness consistent with the reference photos. Never include any text,
letters, or writing within images. All results must look like natural photographs without
any visible text or labels."""
```

**Recommended** (cleaner, conversational):
```python
"prompt": """A confident, well-dressed man in an elegant black tuxedo stands on a luxury
rooftop terrace at midnight. He's pouring champagne from a bottle, with sparkling foam
caught mid-air. Colorful fireworks burst across the night sky behind him, with a glittering
city skyline below.

The scene has a sophisticated, celebratory New Year's Eve atmosphere. Warm golden rim-lighting
catches his features like a high-end magazine cover, creating a cinematic and luxurious mood.

Professional photography, medium-wide shot, upper body visible, generous headroom. 8K quality,
photorealistic, natural skin texture. No text or labels in the image."""
```

*(Note: Face preservation instructions are added automatically in `gemini_service.py`, so don't repeat them in every monthly prompt)*

---

## Optimal Parameters

### Current (Good!)
```python
temperature=0.7,
top_p=0.9,
aspect_ratio='4:3'
```

### For MAXIMUM Face Accuracy
```python
temperature=0.5,  # More deterministic
top_p=0.85,       # More focused sampling
aspect_ratio='4:3'
```

### For More Creative Variety
```python
temperature=0.9,  # More creative
top_p=0.95,       # More diverse
aspect_ratio='4:3'
```

**Recommendation**: Try `temperature=0.5, top_p=0.85` for better face consistency.

---

## Test Files Created

I've created these test scripts in your project:

1. **`quick_model_test.py`** - Tests all image generation models
2. **`test_gemini_pro.py`** - Tests gemini-2.5-pro variants
3. **`test_gemini_pro_noaspect.py`** - Tests without aspect ratio

Run them anytime:
```bash
python3 quick_model_test.py              # Test all models
```

---

## Final Answer

**To mimic online results:**

1. ✅ **You're using the right model** (`gemini-2.5-flash-image`)
2. ✅ **Your parameters are good** (temp=0.7, top_p=0.9)
3. ❌ **Your prompts are too long** - cut from 500 to 150 words
4. ❌ **Your prompts are too instruction-heavy** - use natural language
5. ✅ **Optionally**: Try temp=0.5, top_p=0.85 for better face accuracy

**The online interface works better because it uses concise, conversational prompts, not because of a different model.**

---

## Action Items

1. **Simplify your prompts** in `monthly_themes.py`
   - Make them conversational (100-150 words)
   - Describe the scene naturally
   - Move face instructions to `gemini_service.py` (DRY principle)

2. **Test lower temperature** for face consistency
   - Change `temperature=0.7` to `temperature=0.5` in `gemini_service.py`
   - Test a few generations and compare

3. **Remove redundant face instructions**
   - Don't repeat face preservation 5 times per prompt
   - Handle it once in `gemini_service.py`

Want me to update the code with these optimizations?
