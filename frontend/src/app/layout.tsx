import './globals.css';
import { ThemeProvider } from '@/lib/theme-context';

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
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <div className="min-h-screen bg-[var(--background)] transition-colors duration-300">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
