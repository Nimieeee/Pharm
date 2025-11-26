import './globals.css';
import { ThemeProvider } from '@/lib/theme-context';
import { AuthProvider } from '@/lib/auth-context';
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

// GT Super Display - Headings and emphasis
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

export const metadata = {
  title: 'PharmGPT - AI-Powered Pharmaceutical Assistant',
  description: 'Intelligent pharmaceutical research assistant powered by AI',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${sohne.variable} ${gtSuper.variable}`}>
      <body className="font-sans bg-canvas text-ink antialiased">
        <AuthProvider>
          <ThemeProvider>
            <div className="min-h-screen transition-colors duration-300">
              {children}
            </div>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
