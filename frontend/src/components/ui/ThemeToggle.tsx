'use client';

import * as React from 'react';
import { Monitor, Sun, Moon } from 'lucide-react';
import { useTheme } from '@/lib/theme-context';
import { motion } from 'framer-motion';

type ThemeMode = 'system' | 'light' | 'dark';

export function ThemeToggle({ className = '' }: { className?: string }) {
    const { theme, toggleTheme } = useTheme();
    const [mode, setMode] = React.useState<ThemeMode>('system');
    const [mounted, setMounted] = React.useState(false);

    React.useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem('theme_mode_preference') as ThemeMode;
        if (stored) {
            setMode(stored);
        }
    }, []);

    const handleModeChange = (newMode: ThemeMode) => {
        setMode(newMode);
        localStorage.setItem('theme_mode_preference', newMode);

        if (newMode === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            if (theme !== systemTheme) toggleTheme();
        } else {
            if (theme !== newMode) toggleTheme();
        }
    };

    // Sync with system changes
    React.useEffect(() => {
        if (!mounted || mode !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        // Check immediately
        const systemTheme = mediaQuery.matches ? 'dark' : 'light';
        if (theme !== systemTheme) toggleTheme();

        const handleChange = (e: MediaQueryListEvent) => {
            const newSystemTheme = e.matches ? 'dark' : 'light';
            if (theme !== newSystemTheme) toggleTheme();
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [mode, mounted, theme, toggleTheme]);

    if (!mounted) return null;

    const tabs = [
        { id: 'system', icon: Monitor, label: 'System' },
        { id: 'light', icon: Sun, label: 'Light' },
        { id: 'dark', icon: Moon, label: 'Dark' },
    ] as const;

    return (
        <div className={`relative flex items-center p-1 bg-black/80 backdrop-blur-md border border-white/10 rounded-full ${className}`}>
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    onClick={() => handleModeChange(tab.id)}
                    className={`relative w-7 h-7 flex items-center justify-center rounded-full transition-colors z-10 ${mode === tab.id ? 'text-black' : 'text-white/50 hover:text-white'
                        }`}
                    title={tab.label}
                >
                    {mode === tab.id && (
                        <motion.div
                            layoutId="theme-toggle-active"
                            className="absolute inset-0 bg-white rounded-full"
                            transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                            style={{ zIndex: -1 }}
                        />
                    )}
                    <tab.icon size={14} strokeWidth={2} />
                </button>
            ))}
        </div>
    );
}
