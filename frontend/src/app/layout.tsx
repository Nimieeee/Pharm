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
  title: 'PharmGPT - AI-Powered Pharmaceutical Assistant',
  description: 'Intelligent pharmacological research assistant powered by AI. Analyze drug interactions, clinical data, and research documents.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'PharmGPT',
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: '/icons/icon-192x192.png',
    apple: '/icons/icon-192x192.png',
  },
  openGraph: {
    title: 'PharmGPT - AI Pharmacological Assistant',
    description: 'Intelligent pharmacological research assistant powered by AI',
    type: 'website',
  },
  other: {
    'mobile-web-app-capable': 'yes',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FDFCF8' },
    { media: '(prefers-color-scheme: dark)', color: '#09090B' },
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
