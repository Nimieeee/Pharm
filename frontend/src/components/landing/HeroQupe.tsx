'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, MessageSquare, User, Settings as SettingsIcon } from 'lucide-react';
import { useTheme } from '@/lib/theme-context';

type Tab = 'chat' | 'profile' | 'settings';

export function HeroQupe() {
    const [activeTab, setActiveTab] = useState<Tab>('chat');
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    const tabs = [
        { id: 'chat', label: 'Chat', icon: MessageSquare },
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'settings', label: 'Settings', icon: SettingsIcon },
    ];

    const currentTheme = mounted ? (theme === 'system' ? 'light' : theme) : 'light';

    const getImageSrc = (device: 'desktop' | 'mobile') => {
        return `/assets/${device}-${activeTab}-${currentTheme}.png`;
    };

    return (
        <section className="relative w-full overflow-hidden bg-background pt-24 pb-32 md:pt-32 md:pb-48 lg:pt-40 lg:pb-56">
            {/* Background Image & Overlay */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <Image
                    src="/assets/hero-bg.png"
                    alt="Benchside Background"
                    fill
                    className="object-cover opacity-20 dark:opacity-40"
                    priority
                />
                <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/50 to-background" />
            </div>

            <div className="container relative z-10 mx-auto px-4 md:px-6 flex flex-col items-center text-center">

                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="inline-flex items-center space-x-2 bg-indigo-50/80 dark:bg-indigo-900/30 backdrop-blur-sm border border-indigo-100 dark:border-indigo-800 rounded-full px-3 py-1 mb-8 hover:bg-indigo-100/80 dark:hover:bg-indigo-900/50 transition-colors cursor-pointer"
                >
                    <span className="text-[11px] font-bold tracking-wider text-indigo-600 dark:text-indigo-300 uppercase">Benchside AI</span>
                </motion.div>

                {/* Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
                    className="text-5xl md:text-7xl lg:text-8xl font-serif text-foreground tracking-tight mb-6 max-w-5xl"
                >
                    Your Intelligent <br className="hidden md:block" />
                    <span className="text-indigo-500 dark:text-indigo-400">R&D Partner</span>
                </motion.h1>

                {/* Subtext */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
                    className="text-lg md:text-xl text-muted-foreground/80 max-w-2xl mb-10 leading-relaxed"
                >
                    Accelerate pharmacological discovery with AI-powered insights. Analyze drug interactions, clinical data, and research documents in seconds.
                </motion.p>

                {/* Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
                    className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-20"
                >
                    <button className="h-12 px-8 rounded-full bg-foreground text-background font-medium text-base hover:bg-foreground/90 transition-all flex items-center group">
                        Start Researching
                        <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>

                    <button className="h-12 px-8 rounded-full bg-transparent border border-border text-foreground font-medium text-base hover:bg-surface-hover/50 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all flex items-center">
                        View Demo
                    </button>
                </motion.div>

                {/* Interface Demo */}
                <motion.div
                    initial={{ opacity: 0, y: 100, rotateX: 10 }}
                    animate={{ opacity: 1, y: 0, rotateX: 0 }}
                    transition={{ duration: 1, delay: 0.4, type: "spring", stiffness: 50 }}
                    className="relative w-full max-w-5xl perspective-1000 flex flex-col items-center"
                >
                    {/* Controls */}
                    <div className="flex items-center space-x-4 mb-6 bg-white/50 dark:bg-black/50 backdrop-blur-md p-1.5 rounded-full border border-white/40 dark:border-white/10 shadow-sm z-20">
                        <div className="flex space-x-1 bg-gray-100/50 dark:bg-gray-800/50 rounded-full p-1">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as Tab)}
                                    className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center space-x-2 ${activeTab === tab.id
                                            ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-300 shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <tab.icon className="w-3.5 h-3.5" />
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="relative w-full rounded-2xl overflow-hidden shadow-2xl shadow-indigo-900/20 border border-white/20 dark:border-white/10 bg-white/40 dark:bg-black/40 backdrop-blur-md">
                        {/* Glossy Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-white/40 via-transparent to-transparent dark:from-white/5 z-10 pointer-events-none" />

                        {/* Desktop View */}
                        <div className="hidden md:block relative aspect-[2880/1580] w-full bg-gray-50/50 dark:bg-gray-900/50">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`${activeTab}-${currentTheme}-desktop`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={getImageSrc('desktop')}
                                        alt={`Benchside Desktop ${activeTab} ${currentTheme}`}
                                        fill
                                        className="object-cover object-top"
                                        priority
                                    />
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Mobile View */}
                        <div className="block md:hidden relative aspect-[642/1398] w-full bg-gray-50/50 dark:bg-gray-900/50">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`${activeTab}-${currentTheme}-mobile`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={getImageSrc('mobile')}
                                        alt={`Benchside Mobile ${activeTab} ${currentTheme}`}
                                        fill
                                        className="object-cover object-top"
                                        priority
                                    />
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Floating Elements (Optional Decoration) */}
                    <motion.div
                        animate={{ y: [0, -20, 0] }}
                        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                        className="absolute -top-12 -right-12 w-64 h-64 bg-gradient-to-br from-indigo-300/20 to-transparent rounded-full blur-3xl -z-10"
                    />
                </motion.div>

            </div>
        </section>
    );
}
