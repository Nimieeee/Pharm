# PharmGPT Typography Configuration

## ✅ Completed Setup

### Font Files Installed
All premium font files have been copied to `frontend/src/app/fonts/`:

**Sohne (Sans-serif - UI/Body)**
- ✅ `Sohne-Buch.otf` - Regular (400)
- ✅ `Sohne-Kraftig.otf` - Medium (500)

**GT Super Display (Serif - Headings)**
- ✅ `GT-Super-Display-Regular.otf` - Regular (400)
- ✅ `GT-Super-Display-Medium.otf` - Medium (500) *using Tiempos Semibold*
- ✅ `GT-Super-Display-Italic.ttf` - Italic (400)

### Configuration Files Updated

#### 1. `frontend/src/app/layout.tsx`
- ✅ Configured `next/font/local` for both font families
- ✅ Created CSS variables: `--font-sohne` and `--font-gt-super`
- ✅ Applied to `<html>` element
- ✅ Set body classes: `font-sans bg-canvas text-ink antialiased`

#### 2. `frontend/tailwind.config.ts`
- ✅ Updated `fontFamily.sans` to use `var(--font-sohne)`
- ✅ Updated `fontFamily.serif` to use `var(--font-gt-super)`
- ✅ Added custom colors:
  - `canvas`: `#FDFCF8` (warm cream background)
  - `ink`: `#1A1A1A` (soft black text)

## Usage Examples

```tsx
// Default body text (Sohne Regular)
<p className="text-ink">Regular body text</p>

// Headings (GT Super)
<h1 className="font-serif text-4xl font-medium">Premium Heading</h1>

// Italic emphasis (GT Super Italic)
<em className="font-serif italic">Emphasized scientific term</em>

// Medium weight UI text (Sohne Medium)
<button className="font-sans font-medium">Action Button</button>

// Canvas background
<div className="bg-canvas">Content area</div>
```

## Design System

### Typography Scale
- **Headings**: `font-serif` (GT Super Display)
- **Body**: `font-sans` (Sohne)
- **UI Elements**: `font-sans` (Sohne)

### Color Palette
- **Background**: `bg-canvas` (#FDFCF8)
- **Text**: `text-ink` (#1A1A1A)

### Font Weights
- Regular: `font-normal` (400)
- Medium: `font-medium` (500)

## Scientific Journal Aesthetic
This configuration achieves a high-end "Scientific Journal" look similar to LiteFold:
- Serif headings for authority and elegance
- Clean sans-serif for readability
- Warm cream background reduces eye strain
- Soft black text for comfortable reading
