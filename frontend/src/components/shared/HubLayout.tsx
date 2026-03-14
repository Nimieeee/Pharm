'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { useTheme } from '@/lib/theme-context';
import { ResearchSidebar } from './ResearchSidebar';

interface HubLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  accentColor?: string; // e.g., 'amber', 'purple', 'teal', 'blue'
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
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);
  const accentClasses = colorMap[accentColor as keyof typeof colorMap] || colorMap.blue;
  const isDark = theme === 'dark';

  return (
    <div className={`flex h-screen overflow-hidden ${isDark ? 'bg-[#0a0a0b] text-slate-200' : 'bg-gray-50 text-slate-800'} selection:bg-blue-500/30`}>
      {/* Sidebar - Desktop */}
      <div className="hidden lg:block h-full shrink-0">
        <ResearchSidebar 
          isCollapsed={isSidebarCollapsed} 
          onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
        />
      </div>

      {/* Sidebar - Mobile Overlay */}
      <AnimatePresence>
        {isSidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSidebarOpen(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 w-64 z-50 lg:hidden"
            >
              <ResearchSidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Background Glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
          <div className={`absolute -top-24 -right-24 w-96 h-96 rounded-full blur-[120px] opacity-20 bg-${accentColor}-500`} />
          <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(${isDark ? '#1a1a1b' : '#94a3b8'}_1px,transparent_1px)] [background-size:20px_20px] opacity-10`} />
        </div>

        {/* Top Header / Nav */}
        <nav className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-surface-highlight text-foreground-muted transition-colors"
          >
            <Menu size={20} />
          </button>

          <div className="flex items-center gap-4 ml-auto">
            {/* Nav remains for other actions, ThemeToggle consolidated to Sidebar */}
          </div>
        </nav>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="max-w-6xl mx-auto px-6 py-10 w-full">
            {/* Page Title / Icon Section */}
            <header className="mb-12">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-6"
              >
                <div className={`p-4 rounded-2xl bg-gradient-to-br ${accentClasses} border shadow-soft`}>
                  <Icon className="w-10 h-10" />
                </div>
                <div>
                  <h1 className="text-4xl font-serif font-bold text-foreground mb-2">
                    {title}
                  </h1>
                  <p className="text-foreground-muted text-lg font-medium max-w-2xl">
                    {subtitle}
                  </p>
                </div>
              </motion.div>
            </header>

            {/* Content Slot */}
            <main>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.5 }}
              >
                {children}
              </motion.div>
            </main>

            {/* Footer */}
            <footer className="mt-24 pt-10 border-t border-border/50 text-center">
              <p className="text-xs text-foreground-muted uppercase tracking-widest font-medium opacity-50">
                &copy; 2026 Benchside Scientific &bull; Precision Pharmacological Intelligence
              </p>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
}
