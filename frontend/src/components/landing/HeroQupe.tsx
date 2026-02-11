'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Moon, Sun, MessageSquare, User, Settings as SettingsIcon } from 'lucide-react';

type Tab = 'chat' | 'profile' | 'settings';
type Mode = 'light' | 'dark';

const IMAGE_MAP: Record<string, { desktop: string; mobile: string }> = {
    'chat-light': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.27.41 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.26.54 PM.png' },
    'chat-dark': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.27.56 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.27.07 PM.png' },
    'profile-light': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.29.46 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.32.12 PM.png' },
    'profile-dark': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.29.08 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.32.02 PM.png' },
    'settings-light': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.29.33 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.27.28 PM.png' },
    'settings-dark': { desktop: '/screenshots/Screenshot 2026-02-11 at 8.29.22 PM.png', mobile: '/screenshots/Screenshot 2026-02-11 at 8.27.19 PM.png' },
};

export function HeroQupe() {
    const [activeTab, setActiveTab] = useState<Tab>('chat');
    const [colorMode, setColorMode] = useState<Mode>('light');

    const tabs = [
        { id: 'chat', label: 'Chat', icon: MessageSquare },
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'settings', label: 'Settings', icon: SettingsIcon },
    ];

    const getImageSrc = (device: 'desktop' | 'mobile') => {
        const key = `${activeTab}-${colorMode}`;
        return IMAGE_MAP[key]?.[device] ?? '';
    };

    return (
        <section className="relative w-full overflow-hidden bg-background pt-24 pb-32 md:pt-32 md:pb-48 lg:pt-40 lg:pb-56">
            {/* Background Gradients */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-orange-200/30 rounded-full blur-[120px] mix-blend-multiply animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-5%] w-[50%] h-[50%] bg-orange-100/40 rounded-full blur-[100px] mix-blend-multiply" />
                <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] bg-peach-200/20 rounded-full blur-[80px]" />
            </div>

            <div className="container relative z-10 mx-auto px-4 md:px-6 flex flex-col items-center text-center">

                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="inline-flex items-center space-x-2 bg-orange-50/80 backdrop-blur-sm border border-orange-100 rounded-full px-3 py-1 mb-8 hover:bg-orange-100/80 transition-colors cursor-pointer"
                >
                    <span className="text-[11px] font-bold tracking-wider text-orange-600 uppercase">Qupe Finance</span>
                </motion.div>

                {/* Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
                    className="text-5xl md:text-7xl lg:text-8xl font-serif text-foreground tracking-tight mb-6 max-w-5xl"
                >
                    You've never made a <br className="hidden md:block" />
                    website this <span className="text-orange-500">fast before</span>
                </motion.h1>

                {/* Subtext */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
                    className="text-lg md:text-xl text-muted-foreground/80 max-w-2xl mb-10 leading-relaxed"
                >
                    Gain financial acumen using our expert tools and insights to efficiently manage your money and enhance personal wealth.
                </motion.p>

                {/* Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
                    className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-20"
                >
                    <button className="h-12 px-8 rounded-full bg-foreground text-background font-medium text-base hover:bg-foreground/90 transition-all flex items-center group">
                        Get started - for free
                        <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>

                    <button className="h-12 px-8 rounded-full bg-transparent border border-border text-foreground font-medium text-base hover:bg-surface-hover/50 hover:border-orange-200 transition-all flex items-center">
                        Discover Qupe
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
                    <div className="flex items-center space-x-4 mb-6 bg-white/50 backdrop-blur-md p-1.5 rounded-full border border-white/40 shadow-sm z-20">
                        <div className="flex space-x-1 bg-gray-100/50 rounded-full p-1">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as Tab)}
                                    className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center space-x-2 ${activeTab === tab.id
                                        ? 'bg-white text-orange-600 shadow-sm'
                                        : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <tab.icon className="w-3.5 h-3.5" />
                                    <span>{tab.label}</span>
                                </button>
                            ))}
                        </div>
                        <div className="w-px h-6 bg-gray-200" />
                        <button
                            onClick={() => setColorMode(colorMode === 'light' ? 'dark' : 'light')}
                            className="p-2 rounded-full hover:bg-gray-100 transition-colors text-muted-foreground hover:text-orange-500"
                        >
                            {colorMode === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                        </button>
                    </div>

                    <div className="relative w-full rounded-2xl overflow-hidden shadow-2xl shadow-orange-900/10 border border-white/20 bg-white/40 backdrop-blur-md">
                        {/* Glossy Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-white/40 via-transparent to-transparent z-10 pointer-events-none" />

                        {/* Desktop View */}
                        <div className="hidden md:block relative aspect-[2880/1580] w-full bg-gray-50/50">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`${activeTab}-${colorMode}-desktop`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={getImageSrc('desktop')}
                                        alt={`Benchside Desktop ${activeTab} ${colorMode}`}
                                        fill
                                        className="object-cover object-top"
                                        priority
                                    />
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Mobile View */}
                        <div className="block md:hidden relative aspect-[642/1398] w-full bg-gray-50/50">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`${activeTab}-${colorMode}-mobile`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={getImageSrc('mobile')}
                                        alt={`Benchside Mobile ${activeTab} ${colorMode}`}
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
                        className="absolute -top-12 -right-12 w-64 h-64 bg-gradient-to-br from-orange-300/20 to-transparent rounded-full blur-3xl -z-10"
                    />
                </motion.div>

            </div>
        </section>
    );
}
