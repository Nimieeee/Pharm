'use client';

import { useRouter, usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';

export default function MobileNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { icon: '🏠', label: 'Home', path: '/' },
    { icon: '💬', label: 'Chat', path: '/chat' },
    { icon: '📁', label: 'Docs', path: '/chat' },
    { icon: theme === 'light' ? '🌙' : '☀️', label: 'Theme', action: toggleTheme },
  ];

  return (
    <motion.nav
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
      className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
    >
      <div className="flex items-center gap-2 px-4 py-3 rounded-full glass border border-[var(--border)] shadow-lg">
        {navItems.map((item, i) => (
          <button
            key={i}
            onClick={() => item.action ? item.action() : router.push(item.path!)}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-full transition-all btn-press ${
              pathname === item.path ? 'bg-[var(--surface-highlight)]' : ''
            }`}
          >
            <span className="text-lg icon-hover transition-transform">{item.icon}</span>
            <span className="text-[10px] text-[var(--text-secondary)]">{item.label}</span>
          </button>
        ))}
      </div>
    </motion.nav>
  );
}
