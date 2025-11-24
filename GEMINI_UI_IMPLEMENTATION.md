# Gemini-Style UI Implementation

## Overview
Complete implementation of a Google Gemini-inspired chat interface with robust light/dark theme support and mobile-first responsive design.

## Design System

### Color Palette

#### Dark Mode (Default)
- **Background Primary**: `#131314` - Main app background
- **Background Secondary**: `#1E1F20` - Sidebar, input containers
- **Background Tertiary**: `#282A2C` - User message bubbles
- **Text Primary**: `#E3E3E3` - Main text (never pure white)
- **Text Secondary**: `#C4C7C5` - Secondary text
- **Text Tertiary**: `#9AA0A6` - Tertiary/muted text

#### Light Mode
- **Background Primary**: `#FFFFFF` - Main app background
- **Background Secondary**: `#F0F4F9` - Sidebar, input containers (Gemini blue tint)
- **Background Tertiary**: `#E8EDF2` - User message bubbles
- **Text Primary**: `#1F1F1F` - Main text (never pure black)
- **Text Secondary**: `#444746` - Secondary text
- **Text Tertiary**: `#5F6368` - Tertiary/muted text

#### Accent Colors
- **Gemini Gradient**: `#4285F4` (Blue) → `#D96570` (Purple)
- **Border Dark**: `#3C4043`
- **Border Light**: `#E0E3E2`

### Typography
- **Primary Font**: Google Sans, Inter, Roboto
- **Monospace**: Roboto Mono, Fira Code
- **Base Size**: 16px (prevents iOS auto-zoom)
- **Font Weight**: 400 (regular), 500 (medium), 600 (semibold)

## Semantic Color System

### CSS Variables (Auto-switching)
```css
:root {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F0F4F9;
  --bg-tertiary: #E8EDF2;
  --text-primary: #1F1F1F;
  --text-secondary: #444746;
  --text-tertiary: #5F6368;
  --border-color: #E0E3E2;
  --shadow-color: rgba(0, 0, 0, 0.08);
}

.dark {
  --bg-primary: #131314;
  --bg-secondary: #1E1F20;
  --bg-tertiary: #282A2C;
  --text-primary: #E3E3E3;
  --text-secondary: #C4C7C5;
  --text-tertiary: #9AA0A6;
  --border-color: #3C4043;
  --shadow-color: rgba(0, 0, 0, 0.3);
}
```

### Utility Classes
- `.bg-surface-primary` - Main background
- `.bg-surface-secondary` - Secondary surfaces
- `.bg-surface-tertiary` - Tertiary surfaces
- `.text-content-primary` - Primary text
- `.text-content-secondary` - Secondary text
- `.text-content-tertiary` - Tertiary text
- `.border-surface` - Border color
- `.bg-gemini-gradient` - Gemini gradient background
- `.text-gemini-gradient` - Gemini gradient text

## Responsive Layout

### Desktop (≥768px)
- **Sidebar**: Persistent, 260px width, left-aligned
- **Chat Container**: Centered, max-width 800px
- **Input**: Floating pill at bottom, centered with margins

### Mobile (<768px)
- **Sidebar**: Hidden by default, slides in as overlay with backdrop blur
- **Chat Container**: 100% width with 16px padding
- **Input**: Fixed at bottom, full width with safe-area-inset-bottom
- **Touch Targets**: Minimum 44x44px for all interactive elements

## Key Components

### 1. Gemini Input Pill
```tsx
<div className="bg-surface-secondary rounded-gemini-full px-4 py-2 border border-surface">
  <textarea className="gemini-input" />
</div>
```

**Features**:
- Border radius: 9999px (fully rounded)
- Font size: 16px (prevents iOS zoom)
- Auto-resize up to 200px height
- Safe area inset for iOS notch

### 2. Message Bubbles

**User Messages**:
- Align right
- Background: `var(--bg-tertiary)`
- Border radius: 1.5rem
- Max width: 80%

**AI Messages**:
- Align left
- No background bubble
- Sparkle icon (✨) in gradient circle
- Full width for content

### 3. Sidebar
- Slide-over drawer on mobile
- Persistent on desktop
- Smooth transitions (300ms ease-in-out)
- Backdrop blur overlay on mobile

### 4. Theme Toggle
- Sun/Moon icon
- Desktop: Top-right corner
- Mobile: Inside hamburger menu
- Persists to localStorage

## Mobile Optimizations

### iOS Specific
```css
.safe-bottom {
  padding-bottom: env(safe-area-inset-bottom, 16px);
}
```

### Scrollbar Hiding
```css
::-webkit-scrollbar {
  display: none;
}

* {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
```

### Touch Targets
```css
.touch-target {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

## Anti-Invisible Rule

**Critical Constraint**: Never use pure white (#FFFFFF) or pure black (#000000) for text.

### Safe Pairings
- `bg-surface-primary` → `text-content-primary`
- `bg-surface-secondary` → `text-content-primary`
- `bg-surface-tertiary` → `text-content-primary`
- `bg-gemini-gradient` → `text-white` (exception for gradient)

### Shadows
- **Light Mode**: Subtle shadows (`rgba(0, 0, 0, 0.08)`)
- **Dark Mode**: Minimal/invisible shadows (`rgba(0, 0, 0, 0.3)`)

### Borders
- **Light Mode**: Subtle borders (`#E0E3E2`)
- **Dark Mode**: Rare borders, use sparingly (`#3C4043`)

## File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   └── GeminiChatPage.tsx      # Main Gemini-style chat interface
│   ├── index.css                    # Global styles with CSS variables
│   └── tailwind.config.js           # Tailwind config with Gemini colors
```

## Usage

### Switching to Gemini UI
Replace the current ChatPage route with GeminiChatPage:

```tsx
// In your router configuration
import GeminiChatPage from '@/pages/GeminiChatPage'

<Route path="/chat" element={<GeminiChatPage />} />
```

### Theme Toggle
The theme automatically syncs with the existing ThemeContext:

```tsx
const { darkMode, toggleDarkMode } = useTheme()
```

## Features Implemented

✅ Pixel-perfect Gemini visual design
✅ Semantic color system (no hardcoded colors)
✅ Robust light/dark theme support
✅ Mobile-first responsive layout
✅ iOS-safe input (no auto-zoom)
✅ Touch-friendly buttons (44x44px)
✅ Smooth sidebar transitions
✅ Hidden scrollbars (functional)
✅ Gemini gradient accents
✅ Auto-resizing textarea
✅ Safe area insets for iOS
✅ Zero horizontal scrolling
✅ High contrast text (WCAG compliant)

## Browser Support

- Chrome/Edge: Full support
- Safari: Full support (including iOS)
- Firefox: Full support
- Mobile browsers: Optimized for touch

## Performance

- CSS variables for instant theme switching
- Hardware-accelerated transitions
- Minimal re-renders
- Optimized for 60fps scrolling

## Accessibility

- WCAG AA contrast ratios
- Keyboard navigation support
- Screen reader friendly
- Focus indicators
- Touch target sizes (44x44px minimum)

## Next Steps

1. Integrate with existing chat API
2. Add conversation persistence
3. Implement file upload UI
4. Add voice input functionality
5. Implement message streaming
6. Add conversation search
7. Implement conversation deletion
8. Add user settings panel
