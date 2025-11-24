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
        // Gemini Semantic Color System
        gemini: {
          // Dark Mode Colors
          'bg-primary': '#131314',
          'bg-secondary': '#1E1F20',
          'bg-tertiary': '#282A2C',
          'text-primary': '#E3E3E3',
          'text-secondary': '#C4C7C5',
          'text-tertiary': '#9AA0A6',
          
          // Light Mode Colors
          'light-bg-primary': '#FFFFFF',
          'light-bg-secondary': '#F0F4F9',
          'light-bg-tertiary': '#E8EDF2',
          'light-text-primary': '#1F1F1F',
          'light-text-secondary': '#444746',
          'light-text-tertiary': '#5F6368',
          
          // Gemini Gradient
          'gradient-start': '#4285F4',
          'gradient-end': '#D96570',
          
          // Borders
          'border-dark': '#3C4043',
          'border-light': '#E0E3E2',
        },
        emerald: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        }
      },
      fontFamily: {
        sans: ['Google Sans', 'Inter', 'Roboto', 'system-ui', 'sans-serif'],
        mono: ['Roboto Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        'gemini': '24px',
        'gemini-full': '9999px',
      },
      minHeight: {
        'touch': '44px',
      },
      minWidth: {
        'touch': '44px',
      },
      maxWidth: {
        'chat': '800px',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in-left': 'slideInLeft 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in-right': 'slideInRight 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}