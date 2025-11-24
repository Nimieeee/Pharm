# Swiss Spa Design System
## The Anti-AI-Slop Aesthetic

---

## Philosophy

**"Every pixel must justify its existence."**

This design system rejects generic, AI-generated aesthetics in favor of:
- **Calm**: Breathing room, perfect spacing
- **Luxury**: Distinctive typography, subtle depth
- **Intentionality**: Every choice is deliberate

---

## Typography: The Distinctive Choice

### ❌ BANNED FONTS (AI Slop)
- Inter
- Roboto  
- Arial
- San Francisco (system default)

### ✅ OUR FONTS (Distinctive & Beautiful)

**Primary**: Manrope
- Modern geometric sans-serif
- Variable weights for hierarchy
- Excellent readability

**Accent**: Cormorant Garamond
- Luxury editorial feel
- Use for hero headlines
- Italic for emphasis

**Mono**: JetBrains Mono
- Code and technical content
- Clean, modern monospace

---

## Color Palette: Warm & Sophisticated

### Light Mode (Natural, Spa-like)
```
Cream:    #FAF9F6  (Primary background - warm off-white)
Sand:     #F5F3EF  (Secondary surfaces)
Stone:    #E8E6E1  (Tertiary surfaces)
Slate:    #D1CFC8  (Borders - barely there)

Ink:      #2B2B2A  (Primary text - deep, not black)
Charcoal: #4A4A48  (Secondary text)
Muted:    #8A8A88  (Tertiary text)
```

### Dark Mode (Deep, Sophisticated)
```
Midnight: #0A0A0B  (Primary background - deep, not pure black)
Obsidian: #141416  (Secondary surfaces)
Graphite: #1E1E20  (Tertiary surfaces)
Steel:    #2A2A2C  (Borders)

Pearl:    #E8E8E9  (Primary text - soft white)
Silver:   #A8A8AA  (Secondary text)
Muted:    #6A6A6C  (Tertiary text)
```

### Accent (ONE color, used sparingly)
```
Burnt Orange: #D97757  (Primary accent - warmth, energy)
Light:        #E89B7E  (Hover state)
Dark:         #C25E3A  (Active state)
```

### Success (Minimal usage)
```
Deep Teal:    #2D7A6E  (Confirmations only)
Light:        #3D9B8A  (Hover state)
```

---

## Spacing: Perfect Rhythm

### Base Unit: 4px (0.25rem)

```
Micro:    4px   (0.25rem)  - Tight grouping
Tiny:     8px   (0.5rem)   - Related elements
Small:    12px  (0.75rem)  - Component padding
Base:     16px  (1rem)     - Standard spacing
Medium:   24px  (1.5rem)   - Section spacing
Large:    32px  (2rem)     - Major sections
XLarge:   48px  (3rem)     - Page sections
XXLarge:  64px  (4rem)     - Hero sections
```

### Component Spacing Rules

**Cards**: 
- Padding: 24px (1.5rem)
- Gap: 16px (1rem)
- Margin: 16px mobile, 24px desktop

**Buttons**:
- Padding: 14px 24px (0.875rem 1.5rem)
- Min height: 44px (touch-friendly)
- Gap between: 12px (0.75rem)

**Forms**:
- Label to input: 8px (0.5rem)
- Input to input: 16px (1rem)
- Form to button: 24px (1.5rem)

---

## Atmosphere: Depth & Texture

### Subtle Noise Texture
```css
/* Applied to body::before */
opacity: 0.03;
/* Creates tactile, premium feel */
```

### Layered Gradients
```css
/* Light Mode */
--gradient-subtle: linear-gradient(135deg, #FAF9F6 0%, #F5F3EF 100%);
--gradient-depth: linear-gradient(180deg, rgba(250, 249, 246, 0) 0%, rgba(232, 230, 225, 0.4) 100%);

/* Dark Mode */
--gradient-subtle: linear-gradient(135deg, #0A0A0B 0%, #141416 100%);
--gradient-depth: linear-gradient(180deg, rgba(10, 10, 11, 0) 0%, rgba(30, 30, 32, 0.4) 100%);
```

### Glassmorphism (Overlays)
```css
background: rgba(250, 249, 246, 0.8);
backdrop-filter: blur(20px);
border: 1px solid rgba(209, 207, 200, 0.3);
```

---

## Shadows: Felt, Not Seen

### Light Mode
```
Small:  0 2px 8px rgba(0, 0, 0, 0.04)
Medium: 0 4px 16px rgba(0, 0, 0, 0.06)
Large:  0 8px 24px rgba(0, 0, 0, 0.08)
XLarge: 0 16px 48px rgba(0, 0, 0, 0.10)
```

### Dark Mode
```
Small:  0 2px 8px rgba(0, 0, 0, 0.3)
Medium: 0 4px 16px rgba(0, 0, 0, 0.4)
Large:  0 8px 24px rgba(0, 0, 0, 0.5)
XLarge: 0 16px 48px rgba(0, 0, 0, 0.6)
```

---

## Icons: Lucide React

### Rules
1. **Stroke weight**: 2px (matches font weight)
2. **Sizes**: 16px, 20px, 24px, 32px
3. **Color**: Inherit from text color
4. **Spacing**: 8px gap from text

### Common Icons
```tsx
import {
  Home, MessageSquare, User, Settings,
  Search, Plus, X, Check, AlertCircle,
  ChevronRight, ChevronDown, Menu,
  Sun, Moon, Upload, Download
} from 'lucide-react'
```

---

## Motion: Orchestrated & Cinematic

### Timing
```
Fast:     200ms  (hover states)
Base:     300ms  (standard transitions)
Slow:     600ms  (page load sequences)
```

### Easing
```
Standard: cubic-bezier(0.16, 1, 0.3, 1)  (Smooth, premium feel)
```

### Page Load Sequence
```tsx
// Header
animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1)

// Hero
animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both

// Content
animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both
```

### Micro-interactions
```css
/* Button Hover */
transform: translateY(-1px);
box-shadow: 0 4px 12px rgba(217, 119, 87, 0.3);

/* Card Hover */
transform: translateY(-2px);
box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
```

---

## Components

### Button
```tsx
<button className="btn-spa btn-primary">
  <Icon size={20} />
  <span>Action</span>
</button>
```

### Input
```tsx
<input 
  className="input-spa" 
  placeholder="Enter text..."
/>
```

### Card
```tsx
<div className="card-spa">
  <h3>Title</h3>
  <p>Content</p>
</div>
```

---

## Responsive: Mobile-First

### Breakpoints
```
Mobile:  < 640px
Tablet:  640px - 1024px
Desktop: > 1024px
```

### Rules
1. Design for mobile first
2. Touch targets: 44px minimum
3. Font size: 16px minimum (prevents iOS zoom)
4. Spacing: Reduce by 33% on mobile
5. Max-width: 1280px (80rem) on desktop

---

## The "Slop" List (What to Avoid)

### ❌ Never Use
- Purple gradients on white
- Generic shadows (dirty look)
- Bootstrap/Material Design defaults
- Emojis in UI
- Multiple accent colors
- Pure #000000 or #FFFFFF
- Cramped spacing
- Random animations

### ✅ Always Use
- Monochromatic base
- ONE accent color
- Perfect spacing
- Lucide icons
- Subtle shadows
- Orchestrated animations
- Distinctive typography
- Breathing room

---

## Success Criteria

A design succeeds when:
- Users describe it as "calm" and "luxurious"
- Navigation feels effortless
- Every element has purpose
- Works flawlessly on all devices
- Competitors notice and copy
- Worth $1000s/month subscription

---

## Implementation Checklist

### Foundation
- [x] Typography (Manrope + Cormorant Garamond)
- [x] Color variables (CSS custom properties)
- [x] Spacing system (4px base unit)
- [x] Component classes (buttons, inputs, cards)
- [x] Atmospheric effects (noise, gradients)

### Components
- [ ] Navigation
- [ ] Hero section
- [ ] Cards
- [ ] Forms
- [ ] Modals
- [ ] Chat interface

### Pages
- [ ] Homepage
- [ ] Chat
- [ ] Login/Register
- [ ] Dashboard
- [ ] Settings

### Polish
- [ ] Page load sequences
- [ ] Micro-interactions
- [ ] Responsive testing
- [ ] Accessibility audit
- [ ] Performance optimization

---

**Remember**: This is not about decoration. It's about restraint, precision, and intentionality. Every pixel earns its place.
