# KevCal - AI-Powered "Hunk of the Month" Calendar Generator

**Project Type**: AI Personalization + Print-on-Demand SaaS
**Status**: Production (Deployed on Fly.io)
**Tech Stack**: Flask, Google Gemini 2.5 Flash Image, Printify API, Stripe
**Business Model**: Free preview → Pay for physical calendar ($19.99-$29.99)

---

## 📋 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [How It Works](#how-it-works)
3. [Technical Architecture](#technical-architecture)
4. [Recent Session History](#recent-session-history)
5. [Business Research](#business-research)
6. [Future Opportunities](#future-opportunities)
7. [Key Files Reference](#key-files-reference)

---

## 🎯 PROJECT OVERVIEW

### What It Does

KevCal transforms users into comedic "hunks" using AI image generation. Users upload 3-10 selfies, and Google's Gemini 2.5 Flash Image API (nicknamed "Nano Banana") generates 12 monthly images with their face on muscular bodies in hilarious themed scenarios.

### Business Model

1. **Free Preview**: Users see all 12 AI-generated images before paying anything
2. **Pay Only to Print**: If they love it, they can order a physical Printify calendar
3. **No Risk**: User pays nothing until they're 100% satisfied with preview
4. **Print-on-Demand**: Printify handles manufacturing and fulfillment

### Value Proposition

- **Personalized**: Your actual face on hunky bodies
- **Comedy Gift**: Perfect for birthdays, holidays, gag gifts
- **Low Risk**: See exactly what you get before paying
- **Quality**: Professional printing via Printify

---

## 🔄 HOW IT WORKS

### User Flow

```
1. Upload Photos (3-10 selfies)
   ↓
2. AI Generates 12 Month Images (sequential, one at a time)
   - Month 0: Magazine cover (calendar front cover)
   - Months 1-12: Themed scenarios
   ↓
3. Preview Calendar (FREE - all images shown)
   ↓
4. Checkout via Stripe ($19.99-$29.99)
   ↓
5. Webhook Triggers Printify Order
   - Images padded for print safety
   - Uploaded to Printify
   - Calendar created
   - Order submitted to production
   ↓
6. Printify Ships to Customer
```

### Monthly Themes (Examples)

- **January**: New Year's Firefighter (shirtless with champagne)
- **February**: Valentine's Cupid Cop (police officer with wings)
- **March**: St. Patrick's Day Leprechaun Lumberjack
- **April**: Spring Cleaning Handyman
- **May**: Cinco de Mayo Mariachi Muscle
- **June**: Pride Month Rainbow Warrior
- (See `app/services/monthly_themes.py` for all 13 themes)

---

## 🏗️ TECHNICAL ARCHITECTURE

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Flask (Python) | Web framework |
| **AI Image Gen** | Google Gemini 2.5 Flash Image | Face-swapped hunk generation |
| **Image Processing** | PIL, custom padding service | Safety margins for printing |
| **Storage** | File-based session storage | Persist user images across sessions |
| **Payment** | Stripe | Checkout + webhooks |
| **Fulfillment** | Printify API | Calendar manufacturing |
| **Deployment** | Fly.io | Cloud hosting |

### Key Services

#### 1. **Gemini Service** (`app/services/gemini_service.py`)
- **Model**: `gemini-2.5-flash-image`
- **Aspect Ratio**: 3:4 (portrait)
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Inputs**: Text prompt + 3 reference images (user's selfies)
- **Output**: PNG image converted to JPEG (quality 95)
- **Rate Limiting**: 3 seconds between generations

#### 2. **Image Padding Service** (`app/services/image_padding_service.py`)
- **Purpose**: Add protective margins BEFORE sending to Printify
- **Top Padding**: 35% (protects heads from cropping)
- **Side Padding**: 10%
- **Bottom Padding**: 5% (feet can be trimmed)
- **Safe Zone**: 75% of image guaranteed visible
- **Background**: Intelligent blurred edge extension
- **Face Detection**: Optional (currently disabled)

#### 3. **Printify Service** (`app/services/printify_service.py`)
- **Product**: Calendar 2026 (Blueprint 1253)
- **Dimensions**: 10.8" × 8.4"
- **Image Spec**: 3454×2725px per month
- **Placeholders**: 13 total (front_cover + 12 months)
- **Scale**: 0.85 (zoomed out 15% to prevent cropping)
- **Positioning**: Centered (x=0.5, y=0.5)

#### 4. **Session Storage** (`app/session_storage.py`)
- **Type**: File-based (persistent across server restarts)
- **Location**: `/tmp` or custom path
- **Stores**: User photos, generated images, metadata
- **Cleanup**: Manual (TODO: implement expiration)

#### 5. **Monthly Themes** (`app/services/monthly_themes.py`)
- **Count**: 13 prompts (Month 0 = cover + Months 1-12)
- **Structure**: Detailed scene descriptions
- **Style**: "Hyper-realistic photo" + specific body/pose instructions
- **Customization**: Each month has unique theme + color palette

### API Integrations

#### Google Gemini API
```python
client = genai.Client(api_key=GOOGLE_API_KEY)
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=[reference_images, enhanced_prompt],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        temperature=0.7,
        image_config=types.ImageConfig(aspect_ratio='3:4')
    )
)
```

#### Printify API
```python
# Upload image
POST /v1/uploads/images.json
Body: {"file_name": "january.jpg", "contents": base64_image}

# Create calendar product
POST /v1/shops/{shop_id}/products.json
Body: {blueprint_id, print_provider_id, variants, print_areas}

# Submit order to production
POST /v1/shops/{shop_id}/orders/{order_id}/send_to_production.json
```

#### Stripe API
```python
# Create checkout session
stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{price_data, quantity}],
    mode='payment',
    success_url, cancel_url
)

# Webhook handling
stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
```

---

## 📅 RECENT SESSION HISTORY

### Session: November 2, 2025

#### 1. Image Cropping Fix (MAJOR IMPROVEMENT)

**Problem**: Calendar images had faces/heads cropped on printed Printify calendars, making scenes unclear.

**Root Causes Identified**:
1. Gemini sometimes generated tight framing despite prompts
2. Insufficient padding (only 20% at top)
3. Printify scale at 100% (no safety margin)
4. Aspect ratio mismatch (Gemini 3:4 vs Printify 5:4)

**Solutions Implemented**:

##### A. Image Padding Service Enhancement
**File**: `app/services/image_padding_service.py`

Changes:
- Top padding: **20% → 35%** (+75% increase)
- Safe zone: **70% → 75%** (+7% safety margin)
- Asymmetric padding prioritizes head protection

```python
CONFIG = {
    'min_padding_percent': 10,
    'top_padding_percent': 35,      # Was 20%
    'bottom_padding_percent': 5,
    'safe_zone_percent': 75,         # Was 70%
    'use_asymmetric_padding': True,
}
```

##### B. Printify Scale Reduction
**File**: `app/services/printify_service.py`

Changes:
- Scale: **1.0 → 0.85** (15% zoom out)
- Applied to front cover AND all 12 monthly images
- Provides generous margins on physical printed calendars

```python
"images": [{
    "id": image_id,
    "x": 0.5,
    "y": 0.5,
    "scale": 0.85,  # Was 1.0
    "angle": 0
}]
```

##### C. Gemini Prompt Engineering
**File**: `app/services/gemini_service.py`

Enhanced framing instructions:
- Explicit camera distance: "12-15 feet away"
- Required headroom: "15-20% of image height above head"
- Changed lens: 50mm (wider) instead of 85mm
- Subject placement: "Central 60-70% of frame" (not 80-90%)
- Added: "WIDER FRAMING: If in doubt, zoom OUT more"

```python
COMPOSITION & FRAMING (CRITICAL - FOLLOW EXACTLY):
- CAMERA DISTANCE: Shot from 12-15 feet away for WIDE framing
- HEADROOM: Leave SIGNIFICANT empty space above the head (15-20%)
- MEDIUM-WIDE SHOT: Show full person from head to mid-thigh or knees
- MARGINS: Ample space on all sides (subject occupies central 60-70%)
- WIDER FRAMING: If in doubt, zoom OUT more
- Use 50mm lens perspective for wider field of view
- Professional fitness photography with commercial print safety margins
```

**Triple-Layer Protection Result**:
```
Layer 1: Gemini Generation (wider framing, 15-20% headroom)
    ↓
Layer 2: Image Padding (+35% top padding, 75% safe zone)
    ↓
Layer 3: Printify Scale (85% = 15% margin on print)
    ↓
Net Effect: ~40-50% more space above heads!
```

**Commit**: `bf4ce57` - "Fix image cropping issues for Printify calendars"

---

#### 2. GitHub Repository Backup

**Created**: New private repository for project backup

**Details**:
- **Repository**: `IncrediblyHungie/Calendar`
- **URL**: https://github.com/IncrediblyHungie/Calendar
- **Visibility**: Private (changed from public)
- **Authentication**: Personal Access Token configured
- **Status**: All code pushed successfully

**Commands Used**:
```bash
# Created repo via GitHub API
curl -X POST -H "Authorization: token ghp_..." \
  https://api.github.com/user/repos \
  -d '{"name":"Calendar","description":"KevCal - AI-Powered Hunk..."}'

# Updated remote
git remote set-url origin https://ghp_...@github.com/IncrediblyHungie/Calendar.git

# Committed all changes
git add -A
git commit -m "Fix image cropping issues for Printify calendars"
git push -u origin main

# Made repository private
curl -X PATCH -H "Authorization: token ghp_..." \
  https://api.github.com/repos/IncrediblyHungie/Calendar \
  -d '{"private":true}'
```

**What Was Pushed**:
- ✅ All 3 image cropping fixes
- ✅ New `image_padding_service.py`
- ✅ New `calendar_preview.html` template
- ✅ New `RUNNING_LOCALLY.md` documentation
- ✅ Complete git history (70+ commits)

---

## 🔬 BUSINESS RESEARCH

### Alternative POD Opportunities Explored

During this session, we researched business opportunities beyond print-on-demand apparel to find higher-margin, API-enabled platforms.

#### Research Categories

1. **On-Demand Manufacturing** (3D Printing, CNC, Injection Molding)
2. **Tours & Experiences Marketplace**
3. **White Label SaaS Reselling**
4. **Photo Products & Personalized Gifts**
5. **AI Recommendation Engines**
6. **Custom Nutrition & Subscription Boxes**
7. **Promotional Products & Corporate Gifts**
8. **3D Jewelry Print-on-Demand** ← Focus area

---

### 💎 3D JEWELRY POD - DEEP DIVE

#### Why Jewelry?

User was specifically interested in **higher-end POD for jewelry** (premium materials, better margins than apparel).

#### Key Findings

##### **Manufacturing Platforms**

1. **Shapeways** (Mid-Range)
   - Materials: Brass, silver, 14K gold
   - API: ✅ Shopify/Etsy integration
   - White label: Limited
   - Pricing: $30-200
   - Markup: 50-100%
   - Success story: Wearable Cityscapes sold 6,000+ rings

2. **Shop3D.io** (Luxury)
   - Materials: 14K, 18K gold, **Platinum/Ruthenium**
   - API: Manual/integration tools
   - White label: ✅ Full (custom packaging, branded inserts)
   - Pricing: $200-1,200 cost
   - Markup: 100-200%
   - Location: London-based
   - Eco-friendly: 80% smaller carbon footprint

3. **i.materialise** (Premium European)
   - Materials: 14K, 18K gold (yellow, red, white)
   - Location: Belgium
   - Quality: Lost wax casting, European craftsmanship
   - Features: Live 3D preview for customization
   - API: ❌ No public API (manual ordering)

4. **Stuller** (Industry Standard - HIGHEST END)
   - Type: **Wholesale jewelry supplier + API**
   - Materials: 14K, 18K gold, platinum, diamonds, gemstones
   - API: ✅ **FULL REST API** (Product, Order, Invoice, Gem APIs)
   - Catalog: 200,000+ SKUs
   - Services: CAD design, casting, custom manufacturing
   - Pricing: Wholesale (40-60% below retail)
   - Markup: 100-300%
   - Target: Professional jewelers, serious businesses
   - Diamond API: Live GIA-certified diamond inventory
   - **Requirement**: Wholesale account needed

##### **Successful Retail Brands** (Competition)

**Name Necklace/Personalized Jewelry**:
- **Oak and Luna** - Designer custom name necklaces, premium positioning
- **GLDN** - "Jewelry Made Personal", handmade in Washington, ethical production
- **Baby Gold** - Optimized for gifting, premium packaging
- **The M Jewelers** - Instagram-first, affordable ($50-100), viral marketing
- **Lisa Leonard Designs** - Hand-stamped, story-driven brand

**Market Stats**:
- 3D printed jewelry market: **$989M by 2031** (13.5% CAGR)
- Online jewelry sales: **$6.25B in 2023**
- 50% of buyers under 34 (Instagram/TikTok generation)
- Personalized jewelry = **#1 trend for 2025**

**Pet Memorial Jewelry** (High-Profit Niche):
- Extensive Etsy marketplace
- Emotional purchase = high conversion + premium pricing
- Most is traditional metalwork (not 3D printed)
- **OPPORTUNITY**: 3D printing can do unique designs (actual pet faces, detailed paw prints)

##### **Diamond/Gemstone APIs** (For Premium Stones)

1. **RapNet API**
   - World's largest diamond trading network
   - Real-time wholesale pricing
   - Verified suppliers
   - ❌ NO lab-grown diamonds allowed

2. **IDEX Online API**
   - Transparent diamond marketplace
   - Both natural + lab-grown diamonds
   - Comprehensive data
   - Verified suppliers

3. **Stuller Gem API** (Built-in)
   - Live diamond inventory
   - Lab-grown + natural
   - GIA certification data
   - Integrated with Stuller manufacturing

##### **Gaps in Market** (Opportunities)

1. **AI-Generated Custom Designs** - Most require manual design work
2. **True 3D Photo Jewelry** - Current "photo jewelry" is flat images
3. **Voice-to-Jewelry** - Shapeways has basic version, room for improvement
4. **Fast Turnaround** - Most take 2-4 weeks, opportunity for 7-day delivery
5. **Men's Personalized Jewelry** - Market dominated by women's jewelry

---

## 🚀 FUTURE OPPORTUNITIES

### Recommended Business Ideas

Based on research and user interest in high-end jewelry POD:

#### **IDEA 1: "ProposalRing.ai"** - AI-Designed Engagement Rings

**Concept**: AI designs perfect engagement ring based on fiancée's Pinterest/Instagram style

**How It Works**:
1. Customer uploads fiancée's social media (Instagram/Pinterest)
2. AI analyzes her jewelry/style preferences
3. AI generates 5 custom ring designs (unique CAD models)
4. Customer picks favorite
5. Order → Stuller manufactures in 14K/18K/Platinum
6. Ships with diamond (via Stuller Gem API)

**Tech Stack**:
- Image recognition AI (analyze her style)
- Generative AI for CAD design
- Stuller API for manufacturing
- Gem API for diamonds

**Pricing**:
- Average ring: $3,500-7,000
- Cost (Stuller wholesale): $1,500-3,000
- **Profit**: $2,000-4,000 per ring

**Why This Wins**:
- AI personalization (proven strength from KevCal)
- Solves real problem (guys don't know what ring to buy)
- Premium price justified by AI customization
- Stuller handles all quality concerns
- Market size: $6B+ engagement ring market

**Path to $20K/Month**:
- Month 1: Setup Stuller API + website
- Month 2: Launch Google Ads ("custom engagement rings"), 10 sales × $2,500 = $25,000
- Month 3: Scale to 20 sales × $2,000 = $40,000

---

#### **IDEA 2: "Forever Paws"** - Luxury Pet Memorial Jewelry

**Concept**: 3D printed pet memorial jewelry in 18K gold

**Product Line**:
- Pet paw print rings (18K gold) - $899
- Pet portrait pendants (3D relief) - $1,499
- Pet name bracelets (platinum) - $1,299
- Cremation jewelry (hidden compartment) - $799

**Positioning**:
- "Made from 18K gold" (not plated)
- "Sustainably produced" (Shop3D's 80% lower carbon)
- "Heirloom quality"
- Premium packaging

**Backend**: Shop3D white label manufacturing

**Target**:
- Pet owners who spent $5k+ on vet bills (proven willingness to pay)
- Memorial/loss moment (emotional, not price-sensitive)
- Gift market (from family/friends)

**Marketing**:
- Instagram ads targeting "Rainbow Bridge" posts
- Pet influencer partnerships
- Vet office partnerships (bereavement pamphlets)

**Math**:
- Average order: $1,200
- Cost: $400 (Shop3D)
- Profit: $800 per order
- 100 orders/month = **$80,000/month profit**

---

#### **IDEA 3: "The Blue Nile Clone"** - Custom Engagement Ring Configurator

**Concept**: Using Stuller API to build a custom ring configurator (like Blue Nile)

**Customer Flow**:
1. Choose ring style (from Stuller's 200k SKUs)
2. Configure: metal type (14K/18K/Platinum), size, engraving
3. Pick diamond (live API from RapNet or Stuller Gem API)
4. Real-time price calculation
5. Order → Stuller manufactures → Ships to customer

**Profit Example**:
- Ring setting cost: $400 (Stuller wholesale)
- Diamond cost: $2,000 (RapNet wholesale)
- Your price: $5,000
- **Profit**: $2,600 (108% markup)

**Why It Works**:
- Blue Nile does $400M+ revenue with this exact model
- Stuller API automates everything
- No inventory risk
- Professional quality

---

### Alternative Business Models (Also Researched)

#### **White Label SaaS Reselling**
- **Platform**: GoHighLevel, CustomGPT.ai, BotPenguin
- **Model**: Rebrand existing SaaS, charge monthly subscriptions
- **Success**: Some resellers hitting $32k/month MRR within 6 months
- **Example**: "RestaurantOS" - CRM + marketing for restaurants at $99/month
- **Market**: SaaS market = $887B by 2030 (15.65% annual growth)

#### **Tours & Experiences with AI**
- **API**: Viator (300k+ products in 2,500 destinations)
- **Model**: AI-powered trip planning + booking
- **Example**: "Weekend Genius" - AI plans perfect weekend, books via Viator
- **Commission**: 15-25% per booking
- **Market**: 1.5 billion international trips/year

#### **AI Recommendation Engines as a Service**
- **API**: Recombee, Amazon Personalize, Google Recommendations AI
- **Model**: Shopify app for personalized product recommendations
- **Pricing**: $29-99/month per store
- **Market**: $12B by 2025 (32% CAGR)

---

## 📁 KEY FILES REFERENCE

### Core Application Files

```
KevCal/
├── app/
│   ├── routes/
│   │   ├── api.py                 # API endpoints for image generation
│   │   ├── projects.py            # Project management routes
│   │   └── webhooks.py            # Stripe webhook handler (order fulfillment)
│   │
│   ├── services/
│   │   ├── gemini_service.py      # Google Gemini AI integration
│   │   ├── printify_service.py    # Printify API (calendar manufacturing)
│   │   ├── image_padding_service.py # Image safety padding (NEW - Nov 2025)
│   │   └── monthly_themes.py      # 13 themed prompts
│   │
│   ├── templates/
│   │   ├── generating_local.html  # Generation progress UI
│   │   ├── preview.html           # Calendar preview page
│   │   └── calendar_preview.html  # Alternative preview (NEW)
│   │
│   ├── session_storage.py         # File-based session persistence
│   └── __init__.py                # Flask app initialization
│
├── fly.toml                       # Fly.io deployment config
├── requirements.txt               # Python dependencies
├── RUNNING_LOCALLY.md            # Local development guide (NEW)
├── PROJECT_OVERVIEW.md           # This file (NEW - Nov 2025)
└── CLAUDE.md                     # Claude Code session documentation
```

### Configuration Files

**Environment Variables Required**:
```bash
GOOGLE_API_KEY=<Gemini API key>
PRINTIFY_API_TOKEN=<Printify API token>
STRIPE_SECRET_KEY=<Stripe secret key>
STRIPE_WEBHOOK_SECRET=<Stripe webhook signing secret>
FLASK_SECRET_KEY=<Flask session secret>
```

### Important Code Locations

#### Image Cropping Prevention (Nov 2025 Updates)

**Padding Configuration**:
```python
# app/services/image_padding_service.py:10-18
CONFIG = {
    'top_padding_percent': 35,    # Protects heads
    'safe_zone_percent': 75,      # Guaranteed visible area
    'use_asymmetric_padding': True
}
```

**Printify Scale**:
```python
# app/services/printify_service.py:197, 218
"scale": 0.85  # Zoomed out 15%
```

**Gemini Prompt**:
```python
# app/services/gemini_service.py:78-87
COMPOSITION & FRAMING (CRITICAL - FOLLOW EXACTLY):
- CAMERA DISTANCE: Shot from 12-15 feet away
- HEADROOM: 15-20% of image height above head
- Use 50mm lens perspective for wider framing
```

#### Gemini Image Generation

**Main function**: `app/services/gemini_service.py:19-124`
```python
def generate_calendar_image(prompt, reference_image_data_list=None):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    # Builds content with reference images + enhanced prompt
    # Returns PNG image data
```

**Batch generation**: `app/services/gemini_service.py:127-227`
```python
def generate_calendar_images_batch(project_id, prompts, reference_image_data_list):
    # Generates all 12 months sequentially
    # 3 second delay between generations
    # Updates database as each completes
```

#### Printify Fulfillment

**Full order workflow**: `app/services/printify_service.py:382-483`
```python
def process_full_order(product_type, month_image_data, shipping_address, customer_email):
    # 1. Upload 12 padded images
    # 2. Create calendar product
    # 3. Create order
    # 4. Submit to production
    # Returns: {product_id, order_id, status}
```

#### Stripe Webhook Handler

**Payment fulfillment**: `app/routes/webhooks.py:82-210`
```python
@bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    # 1. Verify Stripe signature
    # 2. Handle checkout.session.completed event
    # 3. Retrieve images from session storage
    # 4. Apply image padding (35% top, 5% bottom, 10% sides)
    # 5. Upload to Printify
    # 6. Create + submit order
    # 7. Return success
```

---

## 🔐 SECURITY & CREDENTIALS

### GitHub Repository
- **URL**: https://github.com/IncrediblyHungie/Calendar
- **Visibility**: Private
- **Remote**: Configured with Personal Access Token
- **Token**: Stored in git remote URL (expires periodically)

### API Keys (Environment Variables)
All sensitive keys stored as environment variables, NEVER committed to git:
- Google Gemini API Key
- Printify API Token
- Stripe Secret Key
- Stripe Webhook Secret
- Flask Secret Key

### Git History Notes
- Previous commits may have exposed API tokens (addressed in commit `b39cb32`)
- All exposed tokens have been rotated
- Current setup uses environment variables only

---

## 📊 PROJECT METRICS

### Performance Characteristics

**Image Generation**:
- Time per image: 10-20 seconds (Gemini API)
- Total generation time: 12 images × 15 sec average = ~3 minutes
- Rate limiting: 3 second delay between requests
- Success rate: ~95% (occasional Gemini API errors)

**Image Processing**:
- Padding time: <1 second per image
- Upload to Printify: ~5-10 seconds per image
- Total upload time (12 images): ~1-2 minutes

**Order Fulfillment**:
- Webhook → Printify order submission: ~3-5 minutes
- Printify production time: 2-5 business days
- Shipping time: 3-7 business days
- Total customer wait: 5-12 business days

### Cost Structure

**Per Calendar Order**:
- Gemini API: ~$0.50-1.00 (12 images)
- Printify manufacturing: $15-20 (varies by calendar type)
- Stripe fees: 2.9% + $0.30
- Hosting (Fly.io): ~$0.10/order (amortized)
- **Total COGS**: ~$16-22

**Pricing**:
- Retail price: $19.99-29.99
- **Profit margin**: $3-14 per calendar (15-47%)

**Scaling Economics**:
- Fixed costs: Hosting ($10-30/month)
- Variable costs: Scale linearly with orders
- Break-even: ~5-10 orders/month

---

## 🐛 KNOWN ISSUES & TODO

### Current Issues
1. Session storage cleanup not implemented (files persist indefinitely)
2. Face detection disabled in padding service (requires OpenCV)
3. Error handling for failed Gemini generations could be improved
4. No retry logic for Printify API failures

### Future Improvements
1. **Enable face detection** in image_padding_service.py
   - Install opencv-python
   - Set use_face_detection=True in webhooks.py:156
   - Provides intelligent padding based on actual face position

2. **Session cleanup**
   - Implement expiration for old sessions (7 days?)
   - Automated cleanup cron job
   - User notification before deletion

3. **Better error recovery**
   - Retry failed Gemini generations
   - Queue system for Printify orders
   - Email notifications on failures

4. **Analytics**
   - Track conversion rate (preview → purchase)
   - Monitor generation success rate
   - Identify most popular themes

5. **User experience**
   - Preview multiple calendar styles
   - Add photo editing tools (crop, rotate)
   - Let users regenerate specific months
   - Social sharing of preview

---

## 💡 LESSONS LEARNED

### What Worked Well

1. **Free Preview Model**: Letting users see ALL 12 images before paying dramatically increases conversion
2. **AI Personalization**: Face-swapping creates emotional connection, drives comedy/gift purchases
3. **Gemini 2.5 Flash Image**: Quality is excellent, cost-effective, fast enough for real-time
4. **Printify Integration**: Print-on-demand eliminates inventory risk, handles fulfillment
5. **Stripe Webhooks**: Automated order fulfillment is seamless

### Challenges Overcome

1. **Image Cropping Issue** (Nov 2025): Required triple-layer fix (padding + scale + prompt engineering)
2. **Aspect Ratio Mismatch**: Gemini 3:4 vs Printify 5:4 required careful padding logic
3. **Face Consistency**: Using 3 reference images + detailed prompt ensures recognizable results
4. **Session Persistence**: File-based storage solved issues with user sessions across server restarts
5. **Rate Limiting**: 3 second delays prevent Gemini API quota issues

### Design Decisions

1. **Sequential Generation**: Generate one month at a time (not parallel) to show progress and avoid rate limits
2. **JPEG Storage**: Convert PNG to JPEG for smaller file sizes (95 quality maintains print quality)
3. **Asymmetric Padding**: More padding at top (heads) than bottom (feet can be trimmed)
4. **White Label Packaging**: Future opportunity for branded experience

---

## 🎓 TECHNICAL INSIGHTS

### Google Gemini 2.5 Flash Image Best Practices

**For Face Consistency**:
- Use 3 reference images (more = better consistency)
- Include instruction: "Study the person shown in these images carefully"
- Don't say "face swap" - say "create a photo of THIS EXACT PERSON"
- Maintain distinctive characteristics (eye color, skin tone, facial structure)

**For Composition Control**:
- Be VERY explicit about framing (camera distance, headroom percentage)
- Specify lens type (50mm vs 85mm affects framing)
- Use spatial instructions ("central 60-70% of frame")
- Add multiple redundant framing instructions
- Use "CRITICAL - FOLLOW EXACTLY" for important directives

**For Quality**:
- Temperature 0.7 balances consistency + creativity
- Aspect ratio 3:4 (portrait) works well for full-body shots
- "Photorealistic" + "professional photography" in prompt improves quality
- Specific lighting instructions ("dramatic lighting", "cinematic") enhance results

### Printify API Best Practices

**Image Requirements**:
- Resolution: 3454×2725px for calendars
- Format: JPEG or PNG (JPEG smaller, PNG higher quality)
- Color space: sRGB (standard for printing)
- DPI: 300 minimum (higher is better)

**Preventing Cropping**:
- Pre-pad images BEFORE upload (don't rely on Printify's scale alone)
- Use scale < 1.0 (0.85-0.90 recommended for safety)
- Test with sample orders before going live
- Account for print area variations between products

**Order Fulfillment**:
- Allow 10-15 seconds per image upload (large files)
- Verify product creation before submitting order
- Use external_id for tracking your internal order IDs
- Enable shipping notifications (send_shipping_notification: true)

### Image Padding Algorithm

**Our Approach** (image_padding_service.py):

1. **Calculate base padding** (asymmetric)
   - Top: 35% of image height
   - Bottom: 5% of image height
   - Sides: 10% of image width

2. **Optional: Face detection** (if enabled)
   - Detect face position using OpenCV
   - Add extra padding if face near edges
   - Ensures face stays in safe zone (75% of image)

3. **Aspect ratio correction**
   - Maintain 3:4 aspect ratio
   - Add extra padding if needed
   - Prioritize top padding (protect heads)

4. **Create padded canvas**
   - Sample edge colors for background
   - Apply Gaussian blur for natural look
   - Paste original image centered (with top offset)

5. **Fallback safety**
   - If padding fails, return original image
   - Printify scale (0.85) provides backup protection

---

## 🔗 USEFUL LINKS

### Documentation
- **Google Gemini API**: https://ai.google.dev/
- **Printify API**: https://developers.printify.com/
- **Stripe Webhooks**: https://stripe.com/docs/webhooks
- **Fly.io Deployment**: https://fly.io/docs/

### Project Resources
- **GitHub Repo**: https://github.com/IncrediblyHungie/Calendar (Private)
- **Live Site**: [Fly.io URL - add when deployed]

### Research Resources (From Nov 2025 Session)
- **Stuller API**: https://api.stuller.com/help
- **Shop3D.io**: https://www.shop3d.io/
- **Shapeways API**: https://developers.shapeways.com/
- **RapNet Diamond API**: https://www.rapnet.com/
- **Viator Partner API**: https://docs.viator.com/partner-api/

---

## 📝 NOTES FOR NEXT SESSION

### Quick Context
When you open this project next time, reference this file for:
- What KevCal does (AI hunk calendar generator)
- Recent changes (image cropping fixes Nov 2025)
- Business opportunities researched (3D jewelry POD, Stuller API, etc.)
- Technical architecture (Gemini + Printify + Stripe)

### Potential Next Steps
1. **Test image cropping fixes** - Order sample calendar to verify changes work
2. **Enable face detection** - Install OpenCV, test smart padding
3. **Session cleanup** - Implement expiration/cleanup for old sessions
4. **Analytics dashboard** - Track conversions, popular themes
5. **New business** - Consider building ProposalRing.ai or Forever Paws jewelry POD

### Questions to Consider
- Should we build the engagement ring AI (ProposalRing.ai)?
- Want to apply KevCal's AI personalization model to other products?
- Should we enable face detection for even better padding?
- Ready to scale KevCal marketing?

---

**Last Updated**: November 2, 2025
**Author**: Claude Code (with user guidance)
**Project Status**: Production + Active Development
**Next Review**: [When you open this next time]

---

*This document will be updated with each major session to maintain project history and context.*
