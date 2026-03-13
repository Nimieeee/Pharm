'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { useTheme } from '@/lib/theme-context';

interface HubLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  accentColor?: string; // e.g., 'amber', 'purple', 'teal'
}

const colorMap = {
  amber: 'from-amber-500/10 to-transparent border-amber-500/20 text-amber-500',
  purple: 'from-purple-500/10 to-transparent border-purple-500/20 text-purple-500',
  teal: 'from-teal-500/10 to-transparent border-teal-500/20 text-teal-500',
  blue: 'from-blue-500/10 to-transparent border-blue-500/20 text-blue-500',
};

export default function HubLayout({
  children,
  title,
  subtitle,
  icon: Icon,
  accentColor = 'blue'
}: HubLayoutProps) {
  const { theme } = useTheme();
  const accentClasses = colorMap[accentColor as keyof typeof colorMap] || colorMap.blue;
  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen ${isDark ? 'bg-[#0a0a0b] text-slate-200' : 'bg-gray-50 text-slate-800'} selection:bg-blue-500/30`}>
      {/* Background Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute -top-24 -left-24 w-96 h-96 rounded-full blur-[120px] opacity-20 bg-${accentColor}-500`} />
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(${isDark ? '#1a1a1b' : '#94a3b8'}_1px,transparent_1px)] [background-size:20px_20px] opacity-20`} />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-8 flex items-center justify-between"
        >
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="hidden sm:inline">Back to Research Chat</span>
            <span className="sm:hidden">Home</span>
          </Link>
          <div className="flex items-center gap-4">
            <ThemeToggle />
          </div>
        </motion.div>

        {/* Header */}
        <header className="mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-4 mb-4"
          >
            <div className={`p-3 rounded-2xl bg-gradient-to-br ${accentClasses} border`}>
              <Icon className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white mb-1">
                {title}
              </h1>
              <p className="text-slate-500 dark:text-slate-400 font-medium">
                {subtitle}
              </p>
            </div>
          </motion.div>
        </header>

        {/* Main Content */}
        <main>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            {children}
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="mt-20 pt-8 border-t border-slate-200 dark:border-white/5 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            &copy; 2026 Benchside Scientific Platform. For research use only.
          </p>
        </footer>
      </div>
    </div>
  );
}
