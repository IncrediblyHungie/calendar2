# Figma Design Specification - "Kate's Version"
## Hunk of the Month - UI Redesign

**Last Updated**: 2025-11-10
**Figma File**: QclKZx4qpf9vC8qS1lNQTk
**Design Node**: 141:3 (Kate's Version)
**Exported Image**: https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/a7ed60eb-675d-4799-96a0-ef7b433b62d8

---

## Color Palette

### Primary Colors
- **Primary Pink/Magenta**: `#F73E97` (RGB: 247, 62, 151)
  `rgb(0.969, 0.243, 0.592)` - Used for CTAs, cart icon, accents

- **Dark Text**: `#172439` (RGB: 23, 36, 57)
  `rgb(0.090, 0.141, 0.204)` - Primary text color

- **Light Text**: `#F5F5F5` (RGB: 245, 245, 245)
  `rgb(0.960, 0.960, 0.960)` - Headings on dark backgrounds

- **Secondary Text**: `#ABABAB` (RGB: 171, 171, 171)
  `rgb(0.671, 0.671, 0.671)` - Subheadings, descriptions

### Background Colors
- **Primary Background**: White/Light
- **Card Background**: `#1A1A1A` (RGB: 26, 26, 26)
  `rgb(0.102, 0.102, 0.102)` - Dark cards for carousel

- **Overlay Gradient**: Linear gradient from `#0C0C0C` to transparent
  Used for image overlays in carousel cards

### Border Colors
- **Card Border**: `#ABABAB` (RGB: 171, 171, 171)
  `rgb(0.671, 0.671, 0.671)` - 1px solid borders on cards

---

## Typography

### Font Families
1. **Space Grotesk** - Brand/Logo
   - Font Weight: 400 (Regular)
   - Used for: "Hunk of the Month" logo text
   - Size: ~24px
   - Line Height: 100% (intrinsic)

2. **Inter** - Body Text
   - Font Weights: Regular (400), Medium (500)
   - Used for: All UI text, headings, paragraphs
   - Variable font spacing and sizes

### Text Styles

#### Headings
- **H2 (Section Headings)**:
  - Font: Inter Medium (500)
  - Size: 24px
  - Line Height: 32px (133.33%)
  - Letter Spacing: 0.07031px
  - Color: #F5F5F5 (light on dark) or #172439 (dark on light)
  - Example: "See how others did it 👀"

#### Paragraphs
- **Body Text**:
  - Font: Inter Regular (400)
  - Size: 16px
  - Line Height: 24px (150%)
  - Letter Spacing: -0.3125px
  - Color: #ABABAB
  - Example: "From gym bros to husbands — everyone's got a month."

- **Small Text**:
  - Font: Inter Regular (400)
  - Size: 14px
  - Line Height: 20px (142.86%)
  - Letter Spacing: -0.15039px
  - Color: #ABABAB
  - Example: "Preview blurred for privacy"

---

## Layout & Spacing

### Navigation Bar
- **Height**: ~44px
- **Padding**: Standard horizontal spacing
- **Layout**: Flex row, space-between
- **Components**:
  - Left: Logo (image + text)
  - Right: Shopping cart button (pink outlined)

### Logo Component
- **Image Size**: 43.89px × 43.89px (1:1 ratio)
- **Text**: "Hunk of the Month"
- **Spacing**: Image and text horizontally aligned
- **Total Width**: ~279px

### Cart Button
- **Width**: 56px
- **Height**: 34.59px
- **Border**: 2px solid #F73E97
- **Border Radius**: 69.88px (fully rounded)
- **Icon Size**: ~25.67px × 22px (shopping cart)
- **Icon Color**: #F73E97

### Carousel Section
- **Heading Spacing**: 8px between heading and paragraph
- **Container Width**: 976px (centered)
- **Card Layout**: Horizontal scroll
- **Card Spacing**: 16px between cards
- **Card Padding**: 16px left padding

### Carousel Cards
- **Width**: 384px
- **Height**: Variable (509px - 575px depending on image)
- **Border Radius**: 14px
- **Border**: 1px solid #ABABAB
- **Background**: #1A1A1A (dark)
- **Image**: Fills card with 70% opacity + 4px blur effect
- **Overlay**: Linear gradient from top (#0C0C0C to transparent at 50%)

---

## Component Specifications

### Button Styles
**Primary Button (Cart)**:
- Background: Transparent
- Border: 2px solid #F73E97
- Border Radius: 70px (pill shape)
- Padding: ~6px vertical, ~15px horizontal
- Icon: Pink (#F73E97)
- Hover: (TBD - add background fill)

### Card Component
**Preview Card**:
```css
{
  width: 384px;
  background: #1A1A1A;
  border: 1px solid #ABABAB;
  border-radius: 14px;
  overflow: hidden;
  position: relative;
}

/* Image with overlay */
.card-image {
  width: 100%;
  opacity: 0.7;
  filter: blur(4px);
}

.card-overlay {
  position: absolute;
  top: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    180deg,
    #0C0C0C 0%,
    transparent 50%,
    transparent 100%
  );
}

.card-caption {
  position: absolute;
  bottom: 20px;
  text-align: center;
  width: 350px;
  margin: 0 16px;
  font-size: 14px;
  color: #ABABAB;
}
```

---

## Icons & Assets

### Shopping Cart Icon
- **Source**: Material Symbols (shopping-cart)
- **Size**: 25.67px × 22px
- **Color**: #F73E97
- **Stroke Weight**: 0.94px

### Logo Image
- **Format**: PNG/WebP recommended
- **Size**: 44px × 44px (square)
- **Display**: Preserved 1:1 aspect ratio
- **Current Image Ref**: `314555e9d51adb9f294e7ebf159af85d98a00114`

---

## Key Design Patterns

### Dark Mode Landing Page
- Primary theme appears to be a **dark hero section** with light carousel cards
- High contrast between dark backgrounds and bright CTAs
- Images use blur + overlay technique for privacy/aesthetics

### Content Hierarchy
1. Navigation (fixed top)
2. Hero heading + subheading (centered, 976px container)
3. Horizontal carousel (full-width scrollable)
4. Each card shows blurred preview with caption overlay

### Responsive Considerations
- Desktop-first design (976px content width)
- Carousel should scroll horizontally on mobile
- Cards maintain fixed 384px width
- Navigation adapts to mobile (burger menu TBD)

---

## Implementation Priority

### Phase 1: Core Branding
1. ✅ Add Space Grotesk font
2. ✅ Update color variables throughout app
3. ✅ Redesign logo component (image + text)
4. ✅ Implement new cart button style

### Phase 2: Layout Changes
1. Redesign navigation bar
2. Create carousel component
3. Implement card component with blur/overlay
4. Update section headings and typography

### Phase 3: Page Updates
1. Landing page hero section
2. Product cards and previews
3. Cart page styling
4. Checkout flow styling

---

## Notes for Development

- **Font Loading**: Space Grotesk should be loaded via Google Fonts or self-hosted
- **Image Optimization**: Carousel images need blur effect applied via CSS `filter: blur(4px)`
- **Gradients**: Linear gradients use consistent 180deg angle (top to bottom)
- **Accessibility**: Ensure pink CTAs have sufficient contrast (WCAG AA minimum)
- **Icons**: Consider using Material Design icon library for consistency

---

## Current vs. New Design Comparison

| Element | Current | New (Figma) |
|---------|---------|-------------|
| Primary Color | Various | Pink #F73E97 |
| Logo Font | Default | Space Grotesk |
| Body Font | Default | Inter |
| Nav Style | Basic | Dark with pink cart |
| Card Style | Simple | Dark with blur overlay |
| Overall Theme | Basic/Light | Dark mode aesthetic |

---

**Design Export**: [View Full Landing Page](https://figma-alpha-api.s3.us-west-2.amazonaws.com/images/a7ed60eb-675d-4799-96a0-ef7b433b62d8)
