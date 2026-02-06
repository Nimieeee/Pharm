import './globals.css';
import 'katex/dist/katex.min.css';
import { ThemeProvider } from '@/lib/theme-context';
import { AuthProvider } from '@/lib/auth-context';
import { Fraunces } from 'next/font/google';
import localFont from 'next/font/local';

// Sohne Sans - UI and body text
const sohne = localFont({
  src: [
    {
      path: './fonts/Sohne-Buch.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/Sohne-Kraftig.otf',
      weight: '500',
      style: 'normal',
    },
  ],
  variable: '--font-sohne',
  display: 'swap',
});

// Fraunces - Headings and emphasis
const fraunces = Fraunces({
  subsets: ['latin'],
  variable: '--font-fraunces',
  display: 'swap',
});

// GT Super Display - Legacy font (keeping for safety but priority is Fraunces)
const gtSuper = localFont({
  src: [
    {
      path: './fonts/GT-Super-Display-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/GT-Super-Display-Medium.otf',
      weight: '500',
      style: 'normal',
    },
    {
      path: './fonts/GT-Super-Display-Italic.ttf',
      weight: '400',
      style: 'italic',
    },
  ],
  variable: '--font-gt-super',
  display: 'swap',
});

import type { Viewport, Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Benchside',
  description: 'AI-powered pharmaceutical bench-side assistant.',
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-icon.png' },
    ],
  },
  keywords: ['pharmacology', 'AI', 'drug discovery', 'research', 'medicine', 'benchside'],
  authors: [{ name: 'Benchside Team' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://benchside.ai',
    title: 'Benchside - AI Pharmacological Assistant',
    description: 'Intelligent pharmacological research assistant powered by AI',
  },
  other: {
    'mobile-web-app-capable': 'yes',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#faf9f5' },
    { media: '(prefers-color-scheme: dark)', color: '#262624' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
};

import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration';

import { Toaster } from 'sonner';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${sohne.variable} ${fraunces.variable} ${gtSuper.variable}`}>
      <body className="font-sans bg-[var(--background)] text-[var(--foreground)] antialiased">
        <ServiceWorkerRegistration />
        <AuthProvider>
          <ThemeProvider>
            <div className="min-h-screen transition-colors duration-300">
              {children}
            </div>
            <Toaster position="top-center" richColors />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
