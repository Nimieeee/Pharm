import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sohne)', 'sans-serif'],
        serif: ['var(--font-gt-super)', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Semantic Layered System
        background: 'var(--background)',
        surface: {
          DEFAULT: 'var(--surface)',
          hover: 'var(--surface-hover)',
          highlight: 'var(--surface-highlight)',
        },
        border: 'var(--border)',
        foreground: {
          DEFAULT: 'var(--foreground)',
          muted: 'var(--foreground-muted)',
        },

        // Legacy aliases (backward compatibility)
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'surface-highlight': 'var(--surface-highlight)',

        // Premium Scientific Journal palette (now theme-aware)
        canvas: 'var(--background)',
        ink: 'var(--foreground)',

        // Qupe Brand Colors
        peach: {
          50: '#fff5f1',
          100: '#ffe8df',
          200: '#ffcfc0',
          300: '#ffaa91',
          400: '#ff7b5c',
          500: '#ff522e',
          600: '#ed3b15',
          700: '#ca2b0b',
          800: '#a6240b',
          900: '#86210e',
        },
      },
      borderRadius: {
        '2xl': '24px',
        '3xl': '32px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      maxWidth: {
        'content': '1200px',
      },
      boxShadow: {
        'swiss': '0 20px 40px -12px rgba(0, 0, 0, 0.05)',
        'swiss-hover': '0 25px 50px -12px rgba(0, 0, 0, 0.1)',
        'swiss-dark': '0 0 0 1px #27272A, 0 20px 40px -12px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        'bounce-slow': 'bounce 1.5s infinite',
      },
      transitionTimingFunction: {
        'swiss': 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
      backdropBlur: {
        'xs': '4px',
      },
    },
  },
  plugins: [],
};

export default config;
