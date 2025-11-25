'use client';

import { useRouter, usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { Home, MessageSquare, FileText, Moon, Sun } from 'lucide-react';

export default function MobileNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { icon: Home, label: 'Home', path: '/' },
    { icon: MessageSquare, label: 'Chat', path: '/chat' },
    { icon: FileText, label: 'Docs', path: '/chat' },
  ];

  return (
    <motion.nav
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
      className="md:hidden fixed bottom-24 left-4 right-4 z-40 max-w-[600px] mx-auto"
    >
      <div className="flex items-center justify-center gap-1 px-4 py-3 rounded-full bg-[rgba(var(--surface-rgb),0.85)] backdrop-blur-xl border border-[rgba(0,0,0,0.08)] dark:border-[rgba(255,255,255,0.1)] shadow-[0_8px_32px_-4px_rgba(0,0,0,0.12)]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.path;
          return (
            <button
              key={item.label}
              onClick={() => router.push(item.path)}
              className={`flex flex-col items-center gap-1 px-5 py-2 rounded-full transition-all btn-press ${
                isActive ? 'bg-[var(--surface-highlight)]' : ''
              }`}
            >
              <Icon 
                size={20} 
                strokeWidth={isActive ? 2 : 1.5} 
                className={`transition-colors ${isActive ? 'text-indigo-500' : 'text-[var(--text-secondary)]'}`}
              />
              <span className={`text-[10px] ${isActive ? 'text-indigo-500' : 'text-[var(--text-secondary)]'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
        <button
          onClick={toggleTheme}
          className="flex flex-col items-center gap-1 px-5 py-2 rounded-full transition-all btn-press"
        >
          {theme === 'light' ? (
            <Moon size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
          ) : (
            <Sun size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
          )}
          <span className="text-[10px] text-[var(--text-secondary)]">Theme</span>
        </button>
      </div>
    </motion.nav>
  );
}
