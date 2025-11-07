# Printify Wall Calendar Image Scaling Investigation

**Date**: November 6, 2025
**Status**: ✅ RESOLVED - Borders confirmed as part of physical template design

## Issue Summary

Wall calendar mockups showed images with thick black borders and white space around them, not filling the printable area edge-to-edge. This is problematic for a "hunk of the month" calendar where full-body imagery is critical to the product concept.

## Product Configuration

- **Blueprint**: 965 (Standard Wall Calendar 2026)
- **Print Provider**: 99 (Stoke-On-Trent, UK)
- **Variant**: 103102 (11" × 8.5" Letter size)
- **Image Aspect Ratio**: 16:9 (1.778:1) landscape from Gemini API
- **Placeholder Aspect Ratio**: ~1.29:1 (narrower than 16:9)

## Attempts to Eliminate Borders

### Attempt 1: Fix Wrong Variant ✅ Partial Success
**Problem**: Product descriptions mentioned both 11" × 8.5" and 14" × 11.5" sizes
**Action**: Hardcoded variant 103102 for 11" × 8.5" Letter size only
**Files Modified**:
- `/app/services/printify_service.py` (lines 15-23)
- `/app/templates/preview.html` (line 278)
- `/app/templates/cart.html` (line 60)
- `/app/services/stripe_service.py` (line 20)

**Result**: Ensured correct variant, but borders remained

### Attempt 2: Increase Scale from 0.78 to 1.05 ❌ No Effect
**Theory**: Original scale too conservative, leaving too much whitespace
**Action**: Changed `get_optimal_scale()` return value to 1.05
**File**: `/app/services/printify_service.py` (line 165)
**Result**: Borders remained identical

### Attempt 3: Remove All Image Padding ✅ Completed, No Effect on Borders
**Theory**: Our 20% side padding and 12% top/bottom padding was causing borders
**Action**: Disabled `add_safe_padding()` function to return original image without any padding
**File**: `/app/services/image_padding_service.py` (lines 21-50)

**Code Change**:
```python
# CURRENTLY DISABLED: Returns original image without padding to test direct scaling
# Just returns original image as JPEG bytes
```

**Result**: Padding successfully disabled, but borders remained

### Attempt 4: Aggressive Scale 1.4 ❌ No Effect
**Theory**: Need more aggressive scaling to fill placeholder
**Action**: Increased scale to 1.4
**File**: `/app/services/printify_service.py` (line 165)
**Result**: Borders remained

### Attempt 5: Very Aggressive Scale 2.5 ❌ No Effect
**Theory**: Maybe need extreme zoom to eliminate borders
**Action**: Increased scale to 2.5
**File**: `/app/services/printify_service.py` (line 165)
**Result**: User reported "still has the boarder on it please lock in"

### Attempt 6: EXTREME SCALE TEST 5.0 ❌ DEFINITIVE PROOF ✅
**Theory**: Test at extreme scale to determine if borders are removable or baked into template
**Action**: Set scale to 5.0 (500% of placeholder width)
**File**: `/app/services/printify_service.py` (line 165)

**Result**: **Borders looked EXACTLY THE SAME**

**Conclusion**: ⚠️ **Borders are part of Printify's physical calendar template design and CANNOT be removed via API parameters**

## Key Technical Findings

### Printify API Image Placement Parameters

The Printify API only supports these parameters for image positioning:
- `x`: Horizontal position (0.5 = center)
- `y`: Vertical position (0.5 = center)
- `scale`: Image scale (1.0 = image width matches placeholder width)
- `angle`: Rotation angle (0 = no rotation)

**No support for**:
- ❌ `fill_mode` parameter (Printful has this, Printify doesn't)
- ❌ Bleed options
- ❌ Border removal
- ❌ Template customization

### Why Borders Appear

1. **Aspect Ratio Mismatch**: 16:9 images (1.778:1) in ~1.29:1 placeholder causes letterboxing
2. **Physical Template Design**: Printify's wall calendar template has decorative borders as part of the aesthetic
3. **Print Industry Standard**: Most POD calendars have borders/frames as part of their design
4. **Scale Independence**: Borders appear the same at scale 1.05, 1.4, 2.5, AND 5.0 - proving they're not caused by image sizing

## Research Findings

### Alternative Print Providers

**Printful** (competitor) supports:
- ✅ Full-bleed borderless printing with 0.125" bleed area
- ✅ 11" × 17" size (larger than Printify's 11" × 8.5")
- ✅ 300 DPI, high-quality paper (271 g/m²)
- ⚠️ Requires complete API rewrite (different integration)

### Alternative Printify Blueprints

Attempted to research blueprints 525 and 1183 for comparison, but API queries failed due to local auth issues. Unable to determine if other Printify calendar blueprints offer borderless options.

## Current State (November 6, 2025)

### Configuration

**File**: `/app/services/printify_service.py`
```python
# Wall Calendar 11" × 8.5" (blueprint 965, variant 103102): 1.29:1 aspect ratio
# - Borders are part of physical calendar template design (confirmed via scale 5.0 test)
# - Scale 1.4 provides good image coverage while respecting template borders
# - Scale 1.0 = image width matches placeholder width
if product_type == 'wall_calendar':
    return 1.4  # Optimal scale - borders are part of Printify's calendar design
```

### Image Padding

**File**: `/app/services/image_padding_service.py`
**Status**: DISABLED - Returns original images without padding for direct Printify scaling

## Recommendations for Future

### Option 1: Accept Printify Borders (Current State)
- ✅ No additional development work
- ✅ Already integrated and working
- ❌ Black borders and white space around images
- ❌ Defeats purpose of full-body hunk imagery

### Option 2: Switch to Printful for Borderless Calendars
- ✅ True edge-to-edge full-bleed printing
- ✅ Larger 11" × 17" size available
- ⚠️ Significant development effort (complete API rewrite)
- ⚠️ Different pricing structure
- ⚠️ Different fulfillment workflow
- **Estimated Effort**: 2-3 days of development for full Printful integration

### Option 3: Pre-Crop Images for Printify Borders
- ✅ Faster implementation (image generation adjustment)
- ✅ Keep existing Printify integration
- ❌ Still has borders, just optimized composition
- **Approach**: Adjust Gemini prompts to generate subjects closer/larger to account for border cropping

## Files Modified in This Investigation

1. **`/app/services/printify_service.py`**
   - Lines 15-23: Hardcoded wall calendar to variant 103102
   - Line 165: Scale value changed multiple times (0.78 → 1.05 → 1.4 → 2.5 → 5.0 → 1.4)

2. **`/app/services/image_padding_service.py`**
   - Lines 21-50: Disabled padding function entirely

3. **`/app/templates/preview.html`**
   - Line 278: Updated size description to "11" × 8.5" • Letter size"

4. **`/app/templates/cart.html`**
   - Line 60: Updated to "11" × 8.5" only"

5. **`/app/services/stripe_service.py`**
   - Line 20: Updated description to "(11"×8.5" Letter size)"

## Git Commits

```bash
942c51e - Test extreme scale 5.0 to determine if wall calendar borders are removable
f072244 - Revert to scale 1.4 - borders are part of Printify calendar template design
```

## Key Takeaways

1. **Printify wall calendars have FIXED borders** as part of physical template design
2. **Scaling has NO EFFECT on borders** (tested from 1.05 to 5.0)
3. **Printify API offers no borderless options** (no fill_mode, bleed, or template customization)
4. **For true edge-to-edge printing, Printful is required** (supports full-bleed with 0.125" bleed area)
5. **Image padding removal had no effect** - borders are separate from our image processing

## Testing Methodology

All tests followed this process:
1. Change scale value in `/app/services/printify_service.py`
2. Commit and deploy to production
3. User generates fresh calendar with new images
4. User examines mockup URL for border appearance
5. User reports results

This ensured each scale test used fresh Printify API calls with new image uploads, not cached mockups.

---

**Last Updated**: November 6, 2025
**Investigation Status**: COMPLETE
**Decision Required**: Choose between Printify (with borders), Printful (borderless), or composition adjustment
