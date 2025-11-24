/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Swiss Spa Luxury Palette
        spa: {
          // Light Mode - Warm, Natural
          'cream': '#FAF9F6',      // Off-white base (paper)
          'sand': '#F5F3EF',       // Subtle depth
          'stone': '#E8E6E1',      // Layering
          'slate': '#D1CFC8',      // Borders
          'charcoal': '#4A4A48',   // Secondary text
          'ink': '#2B2B2A',        // Primary text
          
          // Dark Mode - Deep, Sophisticated
          'midnight': '#0A0A0B',   // Deep base
          'obsidian': '#141416',   // Subtle lift
          'graphite': '#1E1E20',   // Layering
          'steel': '#2A2A2C',      // Borders
          'silver': '#A8A8AA',     // Secondary text
          'pearl': '#E8E8E9',      // Primary text
          
          // Accent - Burnt Orange (Warmth, Energy)
          'accent': '#D97757',     // Primary accent
          'accent-light': '#E89B7E',
          'accent-dark': '#C25E3A',
          
          // Success - Deep Teal
          'success': '#2D7A6E',
          'success-light': '#3D9B8A',
        }
      },
      fontFamily: {
        // Distinctive, Beautiful Typography
        sans: ['Manrope', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.125rem', letterSpacing: '0.02em', fontWeight: '400' }],
        'sm': ['0.875rem', { lineHeight: '1.375rem', letterSpacing: '0.01em', fontWeight: '400' }],
        'base': ['1rem', { lineHeight: '1.625rem', letterSpacing: '0', fontWeight: '400' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em', fontWeight: '400' }],
        'xl': ['1.25rem', { lineHeight: '1.875rem', letterSpacing: '-0.01em', fontWeight: '500' }],
        '2xl': ['1.5rem', { lineHeight: '2.125rem', letterSpacing: '-0.02em', fontWeight: '500' }],
        '3xl': ['2rem', { lineHeight: '2.5rem', letterSpacing: '-0.03em', fontWeight: '600' }],
        '4xl': ['2.5rem', { lineHeight: '3rem', letterSpacing: '-0.03em', fontWeight: '600' }],
        '5xl': ['3rem', { lineHeight: '3.5rem', letterSpacing: '-0.04em', fontWeight: '600' }],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'spa': '0.75rem',      // 12px - Standard
        'spa-lg': '1rem',      // 16px - Cards
        'spa-xl': '1.25rem',   // 20px - Large surfaces
      },
      boxShadow: {
        'spa-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'spa': '0 2px 8px 0 rgba(0, 0, 0, 0.04)',
        'spa-md': '0 4px 16px 0 rgba(0, 0, 0, 0.06)',
        'spa-lg': '0 8px 24px 0 rgba(0, 0, 0, 0.08)',
        'spa-xl': '0 16px 48px 0 rgba(0, 0, 0, 0.10)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        'fade-in-delay': 'fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both',
        'fade-in-delay-2': 'fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both',
        'slide-up': 'slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up-delay': 'slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      backdropBlur: {
        'spa': '20px',
      },
    },
  },
  plugins: [],
}