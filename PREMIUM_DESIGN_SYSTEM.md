# Premium Swiss Spa Design System

## Philosophy: Sleek, Minimal, Worth $1000s/Month

This design system embodies the principles of Swiss minimalism - clean, precise, and timeless. Every pixel is intentional, every space is calculated, and every interaction is refined.

---

## Color Palette: Monochromatic Elegance

### Primary Palette (Light Mode)
```
Background Primary:   #FFFFFF (Pure white - clean canvas)
Background Secondary: #FAFAFA (Subtle grey - depth without noise)
Background Tertiary:  #F5F5F5 (Soft grey - layering)

Text Primary:         #212121 (Deep grey - never pure black)
Text Secondary:       #616161 (Medium grey - hierarchy)
Text Tertiary:        #9E9E9E (Light grey - subtle information)

Border:               #EEEEEE (Barely there - elegant separation)
```

### Primary Palette (Dark Mode)
```
Background Primary:   #000000 (Pure black - premium darkness)
Background Secondary: #0A0A0A (Subtle lift - depth)
Background Tertiary:  #141414 (Soft lift - layering)

Text Primary:         #FFFFFF (Pure white - clarity)
Text Secondary:       #BDBDBD (Light grey - hierarchy)
Text Tertiary:        #757575 (Medium grey - subtle information)

Border:               #1F1F1F (Barely visible - elegant separation)
```

### Accent Color (Minimal Usage)
```
Primary Accent:       #2563EB (Deep blue - trust, professionalism)
Accent Light:         #3B82F6 (Hover state)
Accent Dark:          #1E40AF (Active state)

Success:              #10B981 (Minimal green - confirmation only)
```

**Rule**: Use accent color ONLY for:
- Primary CTAs
- Active states
- Success confirmations
- Focus indicators

---

## Typography: Precision & Clarity

### Font Stack
```css
Primary: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 
         'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif

Mono: 'SF Mono', 'Monaco', 'Consolas', monospace
```

### Type Scale
```
xs:   12px / 16px line-height (0.01em letter-spacing)
sm:   14px / 20px line-height (0.01em letter-spacing)
base: 16px / 24px line-height (0 letter-spacing)
lg:   18px / 28px line-height (-0.01em letter-spacing)
xl:   20px / 28px line-height (-0.01em letter-spacing)
2xl:  24px / 32px line-height (-0.02em letter-spacing)
3xl:  30px / 36px line-height (-0.02em letter-spacing)
4xl:  36px / 40px line-height (-0.03em letter-spacing)
```

### Font Weights
```
Regular:  400 (body text)
Medium:   500 (emphasis)
Semibold: 600 (headings)
```

**Never use**: Bold (700) - too heavy for premium aesthetic

---

## Spacing System: Perfect Rhythm

### Base Unit: 4px

```
Micro:    4px   (tight grouping)
Tiny:     8px   (related elements)
Small:    12px  (component padding)
Base:     16px  (standard spacing)
Medium:   24px  (section spacing)
Large:    32px  (major sections)
XLarge:   48px  (page sections)
XXLarge:  64px  (hero sections)
```

### Component Spacing Rules

**Cards**:
- Padding: 24px (desktop), 16px (mobile)
- Gap between cards: 16px
- Margin from edges: 16px (mobile), 24px (desktop)

**Buttons**:
- Padding: 12px 24px (base)
- Gap between buttons: 12px
- Minimum touch target: 44px height

**Forms**:
- Label to input: 8px
- Input to input: 16px
- Form to button: 24px

**Sections**:
- Section to section: 48px (desktop), 32px (mobile)
- Content max-width: 1200px
- Content padding: 24px (desktop), 16px (mobile)

---

## Border Radius: Subtle Curves

```
Small:    8px   (buttons, inputs)
Medium:   12px  (cards, modals)
Large:    16px  (large cards)
XLarge:   20px  (hero sections)
Full:     9999px (pills, avatars)
```

**Rule**: Never mix border radius sizes within the same component

---

## Shadows: Barely There

### Light Mode
```
Small:  0 1px 3px 0 rgba(0, 0, 0, 0.05)
Medium: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 
        0 2px 4px -1px rgba(0, 0, 0, 0.03)
Large:  0 10px 15px -3px rgba(0, 0, 0, 0.05), 
        0 4px 6px -2px rgba(0, 0, 0, 0.03)
XLarge: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 
        0 10px 10px -5px rgba(0, 0, 0, 0.02)
```

### Dark Mode
```
Small:  0 1px 3px 0 rgba(0, 0, 0, 0.3)
Medium: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 
        0 2px 4px -1px rgba(0, 0, 0, 0.2)
Large:  0 10px 15px -3px rgba(0, 0, 0, 0.3), 
        0 4px 6px -2px rgba(0, 0, 0, 0.2)
XLarge: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 
        0 10px 10px -5px rgba(0, 0, 0, 0.2)
```

**Rule**: Shadows should be felt, not seen

---

## Components: Premium Patterns

### Buttons

**Primary** (Accent color - use sparingly)
```tsx
<button className="px-6 py-3 rounded-premium bg-premium-accent text-white 
                   hover:bg-premium-accent-dark transition-all duration-200
                   focus:outline-none focus:ring-2 focus:ring-premium-accent 
                   focus:ring-offset-2">
  Action
</button>
```

**Secondary** (Subtle, elegant)
```tsx
<button className="px-6 py-3 rounded-premium border border-primary 
                   hover:bg-secondary transition-all duration-200">
  Action
</button>
```

**Ghost** (Minimal)
```tsx
<button className="px-6 py-3 rounded-premium text-secondary 
                   hover:bg-secondary transition-all duration-200">
  Action
</button>
```

### Inputs

**Standard**
```tsx
<input className="w-full px-4 py-3 rounded-premium border border-primary
                  bg-primary text-primary placeholder:text-tertiary
                  focus:outline-none focus:ring-2 focus:ring-premium-accent
                  transition-all duration-200" />
```

### Cards

**Standard**
```tsx
<div className="rounded-premium-lg border border-primary bg-primary
                shadow-premium hover:shadow-premium-md 
                transition-all duration-200 p-6">
  Content
</div>
```

---

## Icons: Lucide React (Consistent, Clean)

### Icon Sizes
```
Small:  16px (inline with text)
Base:   20px (buttons, inputs)
Medium: 24px (section headers)
Large:  32px (hero sections)
```

### Icon Usage Rules
1. Always use stroke-width: 2 (consistent line weight)
2. Match icon color to text color
3. Add 2px padding around icons in buttons
4. Use currentColor for automatic theme adaptation

### Common Icons
```tsx
import { 
  Home,           // Navigation
  MessageSquare,  // Chat
  User,           // Profile
  Settings,       // Configuration
  Search,         // Search
  Plus,           // Add
  X,              // Close
  Check,          // Success
  AlertCircle,    // Warning
  Info,           // Information
  ChevronRight,   // Navigation
  ChevronDown,    // Dropdown
  Menu,           // Mobile menu
  Sun,            // Light mode
  Moon,           // Dark mode
} from 'lucide-react'
```

---

## Animations: Subtle & Fast

### Timing
```
Fast:     150ms (hover states)
Base:     200ms (standard transitions)
Slow:     300ms (complex animations)
```

### Easing
```
Standard: cubic-bezier(0.4, 0, 0.2, 1)
Smooth:   cubic-bezier(0.4, 0, 0.6, 1)
```

### What to Animate
- Opacity (fade in/out)
- Transform (scale, translate)
- Background color
- Border color
- Shadow

### What NOT to Animate
- Width/Height (causes reflow)
- Margin/Padding (causes reflow)
- Font size (jarring)

---

## Responsive Breakpoints

```
Mobile:  < 640px
Tablet:  640px - 1024px
Desktop: > 1024px
```

### Mobile-First Rules
1. Design for mobile first
2. Add complexity for larger screens
3. Touch targets: minimum 44px
4. Font size: minimum 16px (prevents iOS zoom)
5. Spacing: reduce by 33% on mobile

---

## Layout Patterns

### Container
```tsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  Content
</div>
```

### Grid (Cards)
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  Cards
</div>
```

### Flex (Navigation)
```tsx
<div className="flex items-center justify-between gap-4">
  Nav items
</div>
```

---

## Accessibility: Non-Negotiable

### Contrast Ratios
- Normal text: 4.5:1 minimum (WCAG AA)
- Large text: 3:1 minimum (WCAG AA)
- UI components: 3:1 minimum

### Focus States
- Always visible
- 2px ring with accent color
- 2px offset from element

### Keyboard Navigation
- Tab order follows visual order
- All interactive elements focusable
- Escape closes modals/dropdowns

### Screen Readers
- Semantic HTML
- ARIA labels where needed
- Alt text for images
- Skip links for navigation

---

## Performance: Instant Feel

### Optimization Rules
1. Use CSS transforms (GPU accelerated)
2. Avoid layout thrashing
3. Lazy load images
4. Code split routes
5. Minimize bundle size

### Loading States
- Skeleton screens (not spinners)
- Optimistic UI updates
- Progressive enhancement

---

## Do's and Don'ts

### ✅ Do
- Use monochromatic palette
- Add accent color sparingly
- Perfect spacing between elements
- Use icons instead of emojis
- Keep animations subtle
- Design for touch
- Test in both themes
- Maintain consistency

### ❌ Don't
- Use multiple accent colors
- Add unnecessary decorations
- Use emojis in UI
- Mix border radius sizes
- Over-animate
- Use pure black/white for text
- Ignore mobile users
- Sacrifice accessibility

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Update color variables
- [ ] Implement typography scale
- [ ] Create spacing system
- [ ] Define component patterns
- [ ] Set up icon library

### Phase 2: Components
- [ ] Update buttons
- [ ] Update inputs
- [ ] Update cards
- [ ] Update navigation
- [ ] Update modals

### Phase 3: Pages
- [ ] Homepage
- [ ] Chat page
- [ ] Login/Register
- [ ] Dashboard
- [ ] Settings

### Phase 4: Polish
- [ ] Perfect spacing
- [ ] Test responsiveness
- [ ] Verify accessibility
- [ ] Optimize performance
- [ ] User testing

---

## Inspiration: Swiss Design Principles

1. **Clarity**: Every element has a purpose
2. **Precision**: Perfect alignment and spacing
3. **Simplicity**: Remove until nothing can be removed
4. **Functionality**: Form follows function
5. **Timelessness**: Avoid trends, embrace classics

---

## Success Metrics

A premium design system succeeds when:
- Users describe it as "clean" and "professional"
- Navigation is intuitive without explanation
- Loading feels instant
- Works perfectly on all devices
- Accessible to all users
- Competitors try to copy it

---

## Maintenance

### Monthly Review
- Check for inconsistencies
- Update documentation
- Gather user feedback
- Refine patterns

### Quarterly Audit
- Accessibility testing
- Performance benchmarks
- Cross-browser testing
- Mobile device testing

---

**Remember**: Premium design is about restraint, not decoration. Every element earns its place.
