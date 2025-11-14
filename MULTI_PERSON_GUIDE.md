# Multi-Person Sample Generation Guide

Generate calendar samples for **3 different people** with one command!

## 📁 Setup - Add Photos for 3 People

Your reference_faces directory is already set up:

```
reference_faces/
├── person1/         ← Add Person 1's selfies here
│   └── PUT_PHOTOS_HERE.txt
├── person2/         ← Add Person 2's selfies here
│   └── PUT_PHOTOS_HERE.txt
└── person3/         ← Add Person 3's selfies here
    └── PUT_PHOTOS_HERE.txt
```

### Step 1: Add Photos for Each Person

```bash
# Person 1
cp ~/Downloads/john_selfie*.jpg reference_faces/person1/

# Person 2
cp ~/Downloads/sarah_selfie*.jpg reference_faces/person2/

# Person 3
cp ~/Downloads/mike_selfie*.jpg reference_faces/person3/
```

**Each person needs 3-10 photos** (different angles, expressions)

## 🚀 Generate Samples for All 3 People

### Generate June for All 3 People

```bash
# AI images only
python generate_multi_person_samples.py --month 6

# With calendar mockups
python generate_multi_person_samples.py --month 6 --with-mockup
```

**Output** (in `sample_output/`):
```
person1_month_06_june.jpg
person1_month_06_june_mockup.jpg
person2_month_06_june.jpg
person2_month_06_june_mockup.jpg
person3_month_06_june.jpg
person3_month_06_june_mockup.jpg
```

**Total**: 6 files (3 AI images + 3 mockups)

### Generate Multiple Months for All 3 People

```bash
# Generate January, June, and November for all 3 people
python generate_multi_person_samples.py --months 1 6 11 --with-mockup
```

**Output**: 18 files (9 AI images + 9 mockups)

## 📊 What Gets Generated

| Command | People | Months | AI Images | Mockups | Total Files |
|---------|--------|--------|-----------|---------|-------------|
| `--month 6` | 3 | 1 | 3 | 0 | **3** |
| `--month 6 --with-mockup` | 3 | 1 | 3 | 3 | **6** |
| `--months 1 6 11 --with-mockup` | 3 | 3 | 9 | 9 | **18** |

## ⏱️ Performance

- **1 month, 3 people (no mockups)**: ~1 minute
- **1 month, 3 people (with mockups)**: ~3 minutes
- **3 months, 3 people (with mockups)**: ~10-12 minutes

## 📝 Example Workflow

```bash
# 1. Set API keys
export GOOGLE_API_KEY='your-gemini-key'
export PRINTIFY_API_TOKEN='your-printify-token'

# 2. Add photos for all 3 people
cp ~/Downloads/john*.jpg reference_faces/person1/
cp ~/Downloads/sarah*.jpg reference_faces/person2/
cp ~/Downloads/mike*.jpg reference_faces/person3/

# 3. Generate June samples for all 3 people
python generate_multi_person_samples.py --month 6 --with-mockup

# 4. Check output
ls sample_output/
person1_month_06_june.jpg
person1_month_06_june_mockup.jpg
person2_month_06_june.jpg
person2_month_06_june_mockup.jpg
person3_month_06_june.jpg
person3_month_06_june_mockup.jpg
```

## 🎯 Use Cases

### 1. Website Portfolio - Show 3 Different Examples

Generate different months for 3 different people:

```bash
python generate_multi_person_samples.py --months 1 6 11 --with-mockup --output ./website_examples/
```

Use on landing page to show variety!

### 2. Social Media Comparison

Generate same month (June) for 3 people to show "before and after":

```bash
python generate_multi_person_samples.py --month 6 --with-mockup --output ./social_media/
```

Post all 3: "Which hunk of the month calendar would YOU create? 🔥"

### 3. A/B Testing

Test which person/style resonates more with your audience:

```bash
python generate_multi_person_samples.py --month 7 --with-mockup --output ./ab_test/
```

## 🆚 Single Person vs Multi-Person Scripts

| Script | Use Case | Command |
|--------|----------|---------|
| `generate_samples.py` | Generate for 1 person, flexible options | `--month 6 --references face1.jpg face2.jpg` |
| `generate_multi_person_samples.py` | Generate for 3 people automatically | `--month 6` (auto-finds person folders) |

**Both scripts work!** Use multi-person when you want to generate for all 3 people at once.

## 🔧 Advanced Options

### Custom Output Directory

```bash
python generate_multi_person_samples.py --month 6 --output ./marketing/
```

### Adjust Delay Between Generations

```bash
# Increase delay to 10 seconds (default is 3)
python generate_multi_person_samples.py --month 6 --delay 10
```

### Custom Reference Directory

```bash
# Use different folder structure
python generate_multi_person_samples.py --month 6 --references-dir ./custom_faces/
```

## 📂 Output File Naming

Files are named: `{person_name}_month_{num}_{month_name}.jpg`

Examples:
- `person1_month_06_june.jpg` - AI image
- `person1_month_06_june_mockup.jpg` - Calendar mockup
- `person2_month_06_june.jpg` - AI image
- `person2_month_06_june_mockup.jpg` - Calendar mockup
- `person3_month_06_june.jpg` - AI image
- `person3_month_06_june_mockup.jpg` - Calendar mockup

## 🐛 Troubleshooting

### "No person folders with images found"

**Solution**: Make sure you have photos in the person folders:

```bash
ls reference_faces/person1/
# Should show .jpg files, not just PUT_PHOTOS_HERE.txt
```

### "Permission denied" when adding photos

**Solution**: Folders should be owned by you (fixed):

```bash
ls -la reference_faces/
# Should show: drwxr-xr-x peteylinux peteylinux
```

### Generation is slow

**Solution**:
- Don't use `--with-mockup` for testing (much faster)
- Increase `--delay` if API rate limiting
- Generate fewer months at once

## 💡 Pro Tips

1. **Name Person Folders Meaningfully**
   ```bash
   mv reference_faces/person1 reference_faces/john
   mv reference_faces/person2 reference_faces/sarah
   mv reference_faces/person3 reference_faces/mike
   ```

2. **Generate Test Batch First** (no mockups)
   ```bash
   python generate_multi_person_samples.py --month 6
   # Check if faces look good, then add --with-mockup
   ```

3. **Keep Reference Photos Organized**
   ```bash
   reference_faces/
   ├── john/
   │   ├── front.jpg        ← Descriptive names
   │   ├── 45_degree.jpg
   │   └── smiling.jpg
   ├── sarah/
   └── mike/
   ```

## 🎉 Next Steps

1. Add photos for 3 people to their folders
2. Run: `python generate_multi_person_samples.py --month 6`
3. Check `sample_output/` for results
4. Try with `--with-mockup` to get calendar mockups!
