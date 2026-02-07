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

    // 1. Listen for system preference changes ONLY when in 'system' mode
    React.useEffect(() => {
        if (!mounted || mode !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        const handleChange = (e: MediaQueryListEvent) => {
            const newSystemTheme = e.matches ? 'dark' : 'light';
            // Use functional update or ref to avoid dependency loop, but here theme is needed.
            // If system changes, we MUST update theme.
            if (theme !== newSystemTheme) toggleTheme();
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [mode, mounted, theme, toggleTheme]);

    // 2. When mode explicitly changes to 'system', enforce it once.
    React.useEffect(() => {
        if (!mounted || mode !== 'system') return;
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        if (theme !== systemTheme) toggleTheme();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mode, mounted]); // Intentionally exclude 'theme' to prevent revert loop

    // 3. Sync internal 'mode' state when 'theme' changes externally (e.g. mobile toggle)
    React.useEffect(() => {
        if (!mounted) return;

        if (mode === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            if (theme !== systemTheme) {
                // Theme changed to something that isn't system default -> User must have manually toggled it elsewhere
                setMode(theme);
                localStorage.setItem('theme_mode_preference', theme);
            }
        } else if (mode !== theme) {
            // Theme changed explicitly (e.g. was light, now dark), sync mode
            setMode(theme);
            localStorage.setItem('theme_mode_preference', theme);
        }
    }, [theme, mounted]); // Dependency on 'mode' omitted to avoid circularity, effectively we check current mode ref equivalent

    if (!mounted) return null;

    const tabs = [
        { id: 'system', icon: Monitor, label: 'System' },
        { id: 'light', icon: Sun, label: 'Light' },
        { id: 'dark', icon: Moon, label: 'Dark' },
    ] as const;

    return (
        <div className={`flex items-center p-1 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-full ${className}`}>
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    onClick={() => handleModeChange(tab.id)}
                    className={`relative w-7 h-7 flex items-center justify-center rounded-full transition-colors z-10 ${mode === tab.id ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                        }`}
                    title={tab.label}
                >
                    {mode === tab.id && (
                        <motion.div
                            layoutId="theme-toggle-active"
                            className="absolute inset-0 bg-[var(--surface)] shadow-sm rounded-full border border-[var(--border)]"
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
