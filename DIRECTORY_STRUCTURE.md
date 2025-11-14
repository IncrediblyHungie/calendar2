# KevCal Directory Structure for Sample Generation

## 📁 Where to Put Files

### 1. **Reference Face Images** (INPUT - Your Selfies)
Put your reference face photos here:
```
/home/peteylinux/Projects/KevCal/reference_faces/
```

**Example:**
```bash
reference_faces/
├── face1.jpg      # Front-facing photo
├── face2.jpg      # 45-degree angle
├── face3.jpg      # Different expression
├── face4.jpg      # Optional: more angles
└── face5.jpg      # Optional: more variety
```

**To add your photos:**
```bash
# Copy photos from Downloads
cp ~/Downloads/selfie*.jpg reference_faces/

# Or from anywhere
cp /path/to/your/photos/*.jpg reference_faces/
```

---

### 2. **Generated Samples** (OUTPUT - AI-Generated Calendar Images)
Generated images will be saved here by default:
```
/home/peteylinux/Projects/KevCal/sample_output/
```

**Generated files:**
```bash
sample_output/
├── sample_month_06_june.jpg              # AI-generated image
├── sample_month_06_june_mockup.jpg       # Calendar mockup (with --with-mockup)
├── sample_month_07_july.jpg
└── sample_month_07_july_mockup.jpg
```

---

### 3. **Website Examples** (PUBLIC - For Website Display)
To generate samples directly for your website:
```
/home/peteylinux/Projects/KevCal/app/static/assets/images/examples/
```

**Current examples:**
- `january.png`
- `february.png`
- `july.png`

**To replace with new samples:**
```bash
python generate_samples.py \
  --months 1 2 6 7 11 \
  --references reference_faces/*.jpg \
  --output ./app/static/assets/images/examples/ \
  --with-mockup
```

---

## 🚀 Quick Start Workflow

### Step 1: Add Your Reference Photos
```bash
# Copy your selfies to reference_faces folder
cp ~/Downloads/my_face*.jpg reference_faces/
```

### Step 2: Generate Samples
```bash
# Set API keys
export GOOGLE_API_KEY='your-gemini-key'
export PRINTIFY_API_TOKEN='your-printify-token'

# Generate June (goes to sample_output/ by default)
python generate_samples.py --month 6 --references reference_faces/*.jpg --with-mockup
```

### Step 3: Check Output
```bash
# View generated files
ls -lh sample_output/

# Open images
xdg-open sample_output/sample_month_06_june.jpg
xdg-open sample_output/sample_month_06_june_mockup.jpg
```

---

## 📂 Full Project Structure

```
KevCal/
├── reference_faces/              ⬅️ PUT YOUR FACE PHOTOS HERE
│   ├── face1.jpg
│   ├── face2.jpg
│   └── face3.jpg
│
├── sample_output/                ⬅️ GENERATED SAMPLES GO HERE (default)
│   ├── sample_month_06_june.jpg
│   └── sample_month_06_june_mockup.jpg
│
├── app/
│   └── static/
│       └── assets/
│           └── images/
│               └── examples/     ⬅️ WEBSITE PUBLIC EXAMPLES
│                   ├── january.png
│                   ├── february.png
│                   └── july.png
│
├── generate_samples.py           ⬅️ RUN THIS SCRIPT
├── printify_mockup_service.py
├── SAMPLE_GENERATION_README.md
└── SAMPLE_GENERATION_GUIDE.md
```

---

## 🎯 Common Usage Patterns

### Pattern 1: Test Generation (Default Output)
```bash
# Quick test - saves to sample_output/
python generate_samples.py --month 6 --references reference_faces/*.jpg
```

### Pattern 2: Generate Website Examples
```bash
# Save directly to website - public access
python generate_samples.py \
  --months 1 6 7 11 12 \
  --references reference_faces/*.jpg \
  --output ./app/static/assets/images/examples/ \
  --with-mockup
```

### Pattern 3: Generate Marketing Samples
```bash
# Create separate marketing folder
mkdir -p marketing_samples

python generate_samples.py \
  --months 1 6 7 11 12 \
  --references reference_faces/*.jpg \
  --output ./marketing_samples/ \
  --with-mockup
```

### Pattern 4: Generate Social Media Posts
```bash
# One dramatic month for Instagram
mkdir -p social_media

python generate_samples.py \
  --month 7 \
  --references reference_faces/*.jpg \
  --output ./social_media/ \
  --with-mockup
```

---

## 💡 Pro Tips

### Organize Reference Faces by Person
If testing with multiple people:
```bash
reference_faces/
├── person1/
│   ├── front.jpg
│   ├── angle.jpg
│   └── side.jpg
├── person2/
│   ├── front.jpg
│   └── angle.jpg
└── person3/
    └── face.jpg
```

**Generate for specific person:**
```bash
python generate_samples.py --month 6 --references reference_faces/person1/*.jpg
```

### Keep Original vs Generated Separate
```bash
# Original reference faces (never delete)
reference_faces/

# Test generations (can delete and regenerate)
sample_output/

# Production samples (keep for website)
app/static/assets/images/examples/

# Marketing content (for campaigns)
marketing_samples/
```

### Clean Up Old Samples
```bash
# Delete all generated samples (safe - won't delete reference faces)
rm -rf sample_output/*

# Regenerate fresh samples
python generate_samples.py --months 1 6 7 --references reference_faces/*.jpg
```

---

## ❓ FAQ

**Q: Where do I put my selfies?**
A: `reference_faces/` directory

**Q: Where will generated images be saved?**
A: `sample_output/` by default, or use `--output` to specify

**Q: How do I add samples to my website?**
A: Generate with `--output ./app/static/assets/images/examples/`

**Q: Can I use different output folders?**
A: Yes! Use `--output /any/path/you/want/`

**Q: What if I accidentally delete reference_faces?**
A: Always backup your reference photos elsewhere! These are your original selfies.

---

## 🔐 .gitignore Recommendations

Add to `.gitignore`:
```
# Don't commit reference face photos (privacy)
reference_faces/

# Don't commit test samples (can regenerate)
sample_output/

# Don't commit marketing samples (can regenerate)
marketing_samples/
social_media/
```

**Do commit:**
- Final website examples in `app/static/assets/images/examples/`
