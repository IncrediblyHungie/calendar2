# Sample Generation System - Quick Start

Generate AI calendar images AND Printify mockups for marketing and testing.

## 🚀 Quick Start

```bash
# 1. Set API keys
export GOOGLE_API_KEY='your-gemini-api-key'
export PRINTIFY_API_TOKEN='your-printify-token'  # Only if using --with-mockup

# 2. See available months
python generate_samples.py --list

# 3. Generate June sample (AI image only)
python generate_samples.py --month 6 --references face1.jpg face2.jpg face3.jpg

# 4. Generate June with Printify calendar mockup 📦
python generate_samples.py --month 6 --references face1.jpg face2.jpg face3.jpg --with-mockup
```

## 📦 What's New: Printify Calendar Mockups

The `--with-mockup` flag now generates **realistic calendar product mockups**!

### Before (AI image only):
```bash
python generate_samples.py --month 6 --references face.jpg
```
**Output:** `sample_month_06_june.jpg` (just the AI-generated hunk image)

### After (AI image + calendar mockup):
```bash
python generate_samples.py --month 6 --references face.jpg --with-mockup
```
**Output:**
- `sample_month_06_june.jpg` - AI-generated image
- `sample_month_06_june_mockup.jpg` - ⭐ **Image on actual calendar product**

## 🎯 Perfect For:

1. **Website Landing Page** - Show customers what the final product looks like
2. **Social Media Marketing** - Post realistic product previews
3. **Email Campaigns** - Beautiful product shots in promotional emails
4. **A/B Testing** - Test different calendar layouts/designs
5. **Client Presentations** - Show before buying sample prints

## 🔧 How Mockups Work

When you add `--with-mockup`:

1. ✅ Generates AI image with Gemini (10-20 seconds)
2. ✅ Uploads to Printify (~5 seconds)
3. ✅ Creates temporary calendar product (~10 seconds)
4. ✅ Waits for Printify to generate mockup (~15 seconds)
5. ✅ Downloads high-res mockup image (~5 seconds)
6. ✅ Deletes temporary product (cleanup)

**Total time:** ~45-60 seconds per mockup
**Cost:** Free (temporary products deleted automatically)

## 📸 Example Output Files

```
sample_output/
├── sample_month_06_june.jpg           # AI image (3:4 portrait)
└── sample_month_06_june_mockup.jpg    # ⭐ Calendar mockup (shows product)
```

## 🌟 Real-World Examples

### Generate 5 Marketing Samples
```bash
python generate_samples.py \
  --months 1 6 7 11 12 \
  --references face1.jpg face2.jpg face3.jpg \
  --with-mockup \
  --output ./marketing/
```

**Result:** 10 files ready for website
- 5 AI-generated hunk images
- 5 realistic calendar mockups

### Generate Social Media Post
```bash
# July cowboy (most dramatic month)
python generate_samples.py \
  --month 7 \
  --references face.jpg \
  --with-mockup \
  --output ./social_media/
```

Post the mockup on Instagram with caption: "Turn yourself into a calendar hunk! 🤠"

## 🔑 Environment Variables

```bash
# Required for AI generation
export GOOGLE_API_KEY='AIzaSy...'

# Required for mockups
export PRINTIFY_API_TOKEN='eyJ0eXAi...'
```

Get your Printify token at: https://printify.com/app/account/api

## 💰 Cost Analysis

| Item | AI Only | AI + Mockup |
|------|---------|-------------|
| Gemini API | ~$0.10 | ~$0.10 |
| Printify temp product | Free | Free |
| **Total per month** | **$0.10** | **$0.10** |

Mockups are free because we delete the temporary product after downloading!

## ⚡ Performance Tips

1. **Generate mockups for key months only** (not all 12)
   - Website landing: Generate 3-5 months with mockups
   - Social media: Generate 1-2 hero months

2. **Batch without mockups, then add mockups later**
   ```bash
   # Fast: Generate all 12 months (AI only) in 5 minutes
   python generate_samples.py --all --references face.jpg

   # Slower: Add mockups for just the best 3 months
   python generate_samples.py --months 6 7 11 --references face.jpg --with-mockup
   ```

3. **Increase delay between mockups** (Printify processing time)
   ```bash
   python generate_samples.py --months 1 6 11 --references face.jpg --with-mockup --delay 10
   ```

## 🐛 Troubleshooting

### "PRINTIFY_API_TOKEN environment variable not set"
```bash
export PRINTIFY_API_TOKEN='your-token-here'
```

### "Mockup not ready yet, waiting..."
This is normal! Printify takes 10-30 seconds to generate mockups. The script will retry automatically.

### "Failed to get mockup URL"
Printify might be slow. Try increasing delay:
```bash
python generate_samples.py --month 6 --references face.jpg --with-mockup --delay 10
```

### Mockup generation failed but AI image saved
The AI image is still saved! You can retry just the mockup later or use the AI image directly.

## 📚 Full Documentation

See `SAMPLE_GENERATION_GUIDE.md` for complete documentation including:
- All 13 month themes
- Reference image best practices
- Advanced use cases
- Troubleshooting guide

## 🎉 Next Steps

1. Generate your first sample: `python generate_samples.py --month 6 --references your_face.jpg`
2. Try with mockup: Add `--with-mockup` flag
3. Generate 3-5 months for website: `--months 1 6 7 11 12 --with-mockup`
4. Post on social media and start marketing! 🚀
