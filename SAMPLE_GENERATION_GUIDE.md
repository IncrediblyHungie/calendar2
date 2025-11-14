# Sample Calendar Image Generation Guide

Generate marketing samples and test images for KevCal using this standalone script.

## Quick Start

```bash
# 1. Make sure you have Google API key set
export GOOGLE_API_KEY='your-api-key-here'

# 2. List available months
python generate_samples.py --list

# 3. Generate June image (Lifeguard)
python generate_samples.py --month 6 --references selfie1.jpg selfie2.jpg selfie3.jpg

# 4. Generate June WITH Printify calendar mockup 📦
python generate_samples.py --month 6 --references selfie1.jpg selfie2.jpg selfie3.jpg --with-mockup

# 5. Generate multiple months for website examples
python generate_samples.py --months 1 2 6 7 11 --references selfie1.jpg selfie2.jpg selfie3.jpg

# 6. Generate all 13 images (cover + 12 months)
python generate_samples.py --all --references selfie1.jpg selfie2.jpg selfie3.jpg
```

## Printify Calendar Mockups

The `--with-mockup` flag generates realistic calendar product mockups using Printify's API:

```bash
# Set both API keys
export GOOGLE_API_KEY='your-gemini-key'
export PRINTIFY_API_TOKEN='your-printify-token'

# Generate June with mockup
python generate_samples.py --month 6 --references selfie1.jpg selfie2.jpg --with-mockup
```

**What you get:**
- `sample_month_06_june.jpg` - The AI-generated image
- `sample_month_06_june_mockup.jpg` - The image on an actual calendar mockup

**How it works:**
1. Generates AI image with Gemini
2. Uploads to Printify
3. Creates temporary calendar product
4. Downloads mockup image
5. Cleans up (deletes temporary product)

**Time:** ~30-60 seconds per mockup (includes upload, processing, download)
**Cost:** Free (temporary products are deleted)

## Available Months

| Month | Name      | Title                  | Theme                                      |
|-------|-----------|------------------------|--------------------------------------------|
| 0     | Cover     | Magazine Hero          | Epic magazine cover hero shot              |
| 1     | January   | Gentleman 🥵           | New Year's champagne in tuxedo             |
| 2     | February  | Valentine's Cop 💘     | Shirtless cupid police officer             |
| 3     | March     | Firefighter Hero 🚒    | CEO in glass corner office                 |
| 4     | April     | Pool Guy 💧            | Shirtless firefighter with kitten          |
| 5     | May       | Surfer 🏄              | Beach lifeguard rescuing from shark        |
| 6     | June      | Lifeguard 🏊           | Beverly Hills pool maintenance             |
| 7     | July      | Lumberjack 🌲          | Texas ranch cowboy at sunset               |
| 8     | August    | Cowboy 🤠              | Firefighter saving puppy from fire         |
| 9     | September | Fighter Pilot ✈️      | Fighter jet pilot at golden hour           |
| 10    | October   | Vampire 🧛             | Werewolf transformation at full moon       |
| 11    | November  | Plumber 👨‍🔧          | Fall lumberjack splitting wood             |
| 12    | December  | Hot Santa 🎅           | Muscular Santa on rooftop                  |

## Reference Images

### Best Practices

For optimal face consistency, provide 3-10 reference images with:

- **Multiple angles**: Front-facing, 45-degree angles, profile
- **Good lighting**: Natural light, well-lit, no harsh shadows
- **Clear face visibility**: No sunglasses, hats, or face coverings
- **High resolution**: At least 1024x1024 pixels
- **Variety**: Different expressions (smiling, serious, playful)

### Example Reference Set

```
references/
├── front_facing_neutral.jpg    # Straight-on, neutral expression
├── front_facing_smiling.jpg    # Straight-on, big smile
├── 45_degree_left.jpg          # Angled view from left
├── 45_degree_right.jpg         # Angled view from right
└── profile_side.jpg            # Side profile (optional)
```

## Command Options

### Generate Single Month

```bash
python generate_samples.py --month 6 --references ref1.jpg ref2.jpg ref3.jpg
```

### Generate Multiple Specific Months

```bash
# Generate January, June, and November
python generate_samples.py --months 1 6 11 --references ref1.jpg ref2.jpg ref3.jpg
```

### Generate All Months

```bash
# Generate cover + all 12 months (13 total images)
python generate_samples.py --all --references ref1.jpg ref2.jpg ref3.jpg
```

### Custom Output Directory

```bash
# Save to specific folder
python generate_samples.py --month 6 --references ref1.jpg ref2.jpg ref3.jpg --output ./marketing_samples/
```

### Adjust API Rate Limiting

```bash
# Increase delay between generations to 5 seconds (default is 3)
python generate_samples.py --months 1 2 3 --references ref1.jpg ref2.jpg ref3.jpg --delay 5
```

## Output Files

Generated images are saved with descriptive filenames:

```
sample_output/
├── sample_month_00_cover.jpg
├── sample_month_01_january.jpg
├── sample_month_06_june.jpg
├── sample_month_07_july.jpg
└── sample_month_11_november.jpg
```

## Use Cases

### 1. Website Marketing Examples (with Mockups!)

Generate 3-5 diverse months with calendar mockups to showcase on landing page:

```bash
python generate_samples.py \
  --months 1 6 7 11 12 \
  --references model_face1.jpg model_face2.jpg model_face3.jpg \
  --output ./app/static/assets/images/examples/ \
  --with-mockup
```

**Output:** 10 files (5 AI images + 5 mockups)
- `sample_month_01_january.jpg` + `sample_month_01_january_mockup.jpg`
- `sample_month_06_june.jpg` + `sample_month_06_june_mockup.jpg`
- etc.

### 2. Social Media Content

Generate single dramatic months for Instagram/TikTok:

```bash
# July cowboy (most dramatic)
python generate_samples.py --month 7 --references face.jpg --output ./social_media/

# December hot Santa (holiday marketing)
python generate_samples.py --month 12 --references face.jpg --output ./social_media/
```

### 3. Product Testing

Test new prompt variations by generating same month multiple times:

```bash
# Test June prompt 3 times with different reference sets
python generate_samples.py --month 6 --references set1/*.jpg --output ./test/run1/
python generate_samples.py --month 6 --references set2/*.jpg --output ./test/run2/
python generate_samples.py --month 6 --references set3/*.jpg --output ./test/run3/
```

### 4. Calendar Preview Page

Generate all 12 months for full calendar preview:

```bash
python generate_samples.py --all --references face1.jpg face2.jpg face3.jpg --output ./preview_calendar/
```

## Performance & Costs

- **Generation Time**: 10-20 seconds per image
- **API Cost**: ~$0.08-0.10 per image (Gemini 2.5 Flash Image)
- **Rate Limiting**: 3-second delay between requests (adjustable with --delay)

### Estimated Costs

| Task                  | Images | Time      | Cost       |
|-----------------------|--------|-----------|------------|
| Single month          | 1      | ~15 sec   | ~$0.10     |
| 5 months (marketing)  | 5      | ~2 min    | ~$0.50     |
| All 12 months         | 12     | ~5 min    | ~$1.20     |
| All + cover (13)      | 13     | ~6 min    | ~$1.30     |

## Troubleshooting

### "GOOGLE_API_KEY environment variable is required"

**Solution**: Export your API key before running:

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

Or add to your `.env` file:

```bash
echo "GOOGLE_API_KEY=your-api-key-here" >> .env
source .env
```

### "Reference image not found"

**Solution**: Provide full or relative paths to images:

```bash
# Relative path
python generate_samples.py --month 6 --references ./references/face1.jpg

# Absolute path
python generate_samples.py --month 6 --references /home/user/photos/selfie.jpg
```

### Generation Fails / Poor Face Consistency

**Solutions**:
1. Provide more reference images (5-10 instead of 3)
2. Ensure reference images are high quality and well-lit
3. Include multiple angles (front, 45-degree, profile)
4. Check that faces are clearly visible (no sunglasses, hats)

### Rate Limit Errors

**Solution**: Increase delay between requests:

```bash
python generate_samples.py --months 1 2 3 --references face.jpg --delay 5
```

## Advanced Usage

### Using Wildcard Paths

```bash
# Use all JPGs in a directory
python generate_samples.py --month 6 --references ./references/*.jpg

# Use specific pattern
python generate_samples.py --month 6 --references ./photos/face_*.jpg
```

### Batch Processing with Custom Script

```bash
#!/bin/bash
# generate_all_marketing.sh

REFS="ref1.jpg ref2.jpg ref3.jpg"
OUTPUT="./marketing_samples"

# Generate key months for website
for month in 1 6 7 11 12; do
    echo "Generating month $month..."
    python generate_samples.py --month $month --references $REFS --output $OUTPUT
    sleep 5
done

echo "All marketing samples generated in $OUTPUT"
```

## Integration with Main App

Generated samples can be used for:

1. **Landing page examples** (`/app/static/assets/images/examples/`)
2. **Social media marketing** (Instagram, TikTok, Facebook ads)
3. **Email marketing campaigns** (preview examples in emails)
4. **Product testing** (validate prompts before production)
5. **A/B testing** (test different prompts for same month)

## Tips for Best Results

1. **Face Consistency**: Use 5+ reference images from different angles
2. **Quality Over Quantity**: 3 excellent references > 10 mediocre ones
3. **Lighting Matters**: Well-lit faces in references = better AI results
4. **Test Before Batch**: Generate 1-2 samples first to verify quality
5. **Save Prompts**: Document which prompts worked best for future use
6. **Version Control**: Keep samples organized by date/version

## Example Workflow

```bash
# 1. Prepare reference images
mkdir references
cp ~/best_selfies/*.jpg references/

# 2. Test with one month
python generate_samples.py --month 6 --references references/*.jpg

# 3. Review output
open sample_output/sample_month_06_june.jpg

# 4. If good, generate all marketing samples
python generate_samples.py \
  --months 1 2 6 7 11 12 \
  --references references/*.jpg \
  --output ./marketing_samples/

# 5. Copy to website assets
cp marketing_samples/*.jpg app/static/assets/images/examples/
```

## Next Steps

- Generate 5 diverse months for website landing page
- Create social media calendar with monthly teasers
- Test different reference sets to find optimal face consistency
- Build automated marketing content pipeline
