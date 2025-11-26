# PharmGPT Premium Fonts

This directory contains the premium font files for the PharmGPT application.

## Required Font Files

Place the following font files in this directory:

### Sohne (Sans-serif - UI/Body)
- `Sohne-Buch.otf` - Regular weight (400)
- `Sohne-Kraftig.otf` - Medium weight (500)

### GT Super Display (Serif - Headings)
- `GT-Super-Display-Regular.otf` - Regular weight (400)
- `GT-Super-Display-Medium.otf` - Medium weight (500)
- `GT-Super-Display-Italic.otf` - Italic style (400)

## Usage

The fonts are configured in `app/layout.tsx` using Next.js `localFont`:

- **Sohne**: CSS variable `--font-sohne` → Tailwind class `font-sans`
- **GT Super**: CSS variable `--font-gt-super` → Tailwind class `font-serif`

## Design Tokens

- **Canvas**: `#FDFCF8` (warm cream background) → `bg-canvas`
- **Ink**: `#1A1A1A` (soft black text) → `text-ink`

## Example Usage

```tsx
// Body text (default)
<p className="font-sans text-ink">Regular body text</p>

// Headings
<h1 className="font-serif font-medium">Premium Heading</h1>

// Italic emphasis
<em className="font-serif italic">Emphasized text</em>
```
