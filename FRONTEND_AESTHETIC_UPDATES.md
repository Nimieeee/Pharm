# Frontend Aesthetic Updates

## Overview
Transformed the PharmGPT frontend from a generic design to a distinctive, pharmaceutical-inspired aesthetic.

## Key Changes

### Typography
- **Display Font**: Crimson Pro (elegant serif for headings)
- **Body Font**: JetBrains Mono (technical monospace for readability)
- Removed generic Inter font
- Added custom letter-spacing and font features

### Color Palette
- **Primary**: Deep teal/cyan (#14b8a6) - pharmaceutical/scientific vibe
- **Accent**: Warm amber (#f59e0b) - creates striking contrast
- **Dark Mode**: Rich teal-black (#0a1f1c) instead of generic gray
- Removed overused blue/purple gradients

### Visual Elements
- **Backgrounds**: Layered gradients with animated geometric grid patterns
- **Shadows**: Colored shadows (teal/amber) instead of generic gray
- **Borders**: 2px borders with rounded corners (rounded-xl, rounded-2xl)
- **Glass Effect**: Backdrop blur with semi-transparent backgrounds

### Animations
- Staggered fade-in animations on page load
- Floating elements with 6s ease-in-out cycles
- Smooth scale transforms on hover (scale-105, scale-110)
- Glow effects on interactive elements
- Custom AI loader with teal/amber gradient

### Components Updated
1. **HomePage**: Animated background, staggered content reveals, floating logo
2. **ChatPage**: Glass-effect sidebar, enhanced message bubbles, improved input area
3. **Navbar**: Gradient buttons, enhanced dropdowns, better mobile menu
4. **Global Styles**: New button styles, input fields, card components

### Design Principles Applied
- High contrast for accessibility
- Cohesive color system with CSS variables
- Distinctive pharmaceutical/scientific aesthetic
- Smooth micro-interactions
- Atmospheric depth with layered backgrounds
- No generic "AI slop" patterns

## Technical Implementation
- Tailwind CSS custom configuration
- CSS custom properties for theming
- Framer Motion ready (library already installed)
- Responsive design maintained
- Dark mode fully supported
