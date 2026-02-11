'use client';

import React, { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { useTheme } from '@/lib/theme-context';

type Tab = 'chat' | 'profile' | 'settings';

export function HeroQupe() {
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>('chat');
    const containerRef = useRef<HTMLDivElement>(null);
    const [isHovering, setIsHovering] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    const currentTheme = mounted ? theme : 'light';
    const isDark = currentTheme === 'dark';

    // Semantic button style (Matches platform theme: Black in Light, White in Dark)
    const buttonStyle = "bg-foreground text-background hover:opacity-90";

    const tabs: Tab[] = ['chat', 'profile', 'settings'];

    // Autoplay for Mobile (and Desktop when not hovering)
    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (!isHovering) {
            interval = setInterval(() => {
                setActiveTab((prev) => {
                    const currentIndex = tabs.indexOf(prev);
                    const nextIndex = (currentIndex + 1) % tabs.length;
                    return tabs[nextIndex];
                });
            }, 3000); // 3 seconds per slide
        }

        return () => clearInterval(interval);
    }, [isHovering]);

    // Mouse Move Logic for Desktop "Scrubbing"
    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!containerRef.current) return;

        setIsHovering(true);
        const rect = containerRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const width = rect.width;
        const percentage = x / width;

        if (percentage < 0.33) {
            setActiveTab('chat');
        } else if (percentage < 0.66) {
            setActiveTab('profile');
        } else {
            setActiveTab('settings');
        }
    };

    const handleMouseLeave = () => {
        setIsHovering(false);
    };

    return (
        <section className="relative w-full overflow-hidden bg-background pt-24 pb-32 md:pt-32 md:pb-48 lg:pt-40 lg:pb-56">
            {/* Background Gradient (Aligned with Platform Theme) */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-background" />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />

                {/* Subtle Ambient Glows (Using Platform Accents) */}
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[var(--accent)]/5 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-[var(--accent)]/5 rounded-full blur-[100px]" />
            </div>

            <div className="container relative z-10 mx-auto px-4 md:px-6 flex flex-col items-center text-center">

                {/* Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
                    className="text-5xl md:text-7xl lg:text-8xl font-serif text-foreground tracking-tight mb-8 max-w-5xl relative z-10 mt-12"
                >
                    Your Intelligent <br className="hidden md:block" />
                    {/* Text Highlight using Platform Accent with gradient fallback */}
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--accent)] to-[var(--accent-light)]">
                        R&D Partner
                    </span>
                </motion.h1>

                {/* Subtext */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
                    className="text-lg md:text-xl text-muted-foreground/90 max-w-2xl mb-12 leading-relaxed"
                >
                    Accelerate pharmacological discovery with AI-powered insights. Analyze drug interactions, clinical data, and research documents in seconds.
                </motion.p>

                {/* Buttons */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
                    className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-24 relative z-20"
                >
                    {/* Primary Button with Semantic Theme Colors */}
                    <Link href="/chat">
                        <button className={`h-12 px-8 rounded-full ${buttonStyle} font-medium text-base hover:scale-105 hover:shadow-lg transition-all duration-300 flex items-center group relative overflow-hidden`}>
                            <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                            <span className="relative z-10">Start Researching</span>
                            <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform relative z-10" />
                        </button>
                    </Link>
                </motion.div>

                {/* Dashboard Anchor (Interactive Slideshow) */}
                <motion.div
                    initial={{ opacity: 0, y: 100, rotateX: 5 }}
                    animate={{ opacity: 1, y: 0, rotateX: 0 }}
                    transition={{ duration: 1, delay: 0.4, type: "spring", stiffness: 40, damping: 20 }}
                    className="relative w-full max-w-6xl perspective-1000 flex flex-col items-center group"
                    ref={containerRef}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                >
                    <div className={`
                        relative w-full rounded-2xl overflow-hidden
                        transition-all duration-500
                        ${isDark
                            ? 'border border-white/10 shadow-[0_0_60px_-15px_rgba(88,101,242,0.15)] bg-gray-900/50' // Dark Mode Glow
                            : 'shadow-[0_20px_50px_-12px_rgba(0,0,0,0.25)] border border-gray-200/50 bg-white'     // Light Mode Heavy Shadow
                        }
                    `}>
                        {/* Glossy Overlay/Reflection */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-white/10 via-white/5 to-transparent z-10 pointer-events-none" />

                        {/* Interactive Hint (Only visible on hover when mounted) */}
                        <div className={`absolute top-4 left-1/2 -translate-x-1/2 z-30 transition-opacity duration-300 ${isHovering ? 'opacity-100' : 'opacity-0'}`}>
                            <div className="bg-black/50 backdrop-blur-md text-white text-[10px] px-3 py-1 rounded-full border border-white/10">
                                {activeTab === 'chat' ? 'Chat Interface' : activeTab === 'profile' ? 'Researcher Profile' : 'System Settings'}
                            </div>
                        </div>

                        {/* Desktop View */}
                        <div className="hidden md:block relative aspect-[2880/1580] w-full">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`desktop-${activeTab}-${currentTheme}`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={`/assets/desktop-${activeTab}-${currentTheme}.png`}
                                        alt={`Benchside Interface Desktop - ${activeTab}`}
                                        fill
                                        className="object-cover object-top"
                                        priority
                                    />
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Mobile View */}
                        <div className="block md:hidden relative aspect-[642/1398] w-full">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={`mobile-${activeTab}-${currentTheme}`}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="absolute inset-0"
                                >
                                    <Image
                                        src={`/assets/mobile-${activeTab}-${currentTheme}.png`}
                                        alt={`Benchside Interface Mobile - ${activeTab}`}
                                        fill
                                        className="object-cover object-top"
                                        priority
                                    />
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Progress Indicators (Bottom) */}
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 flex space-x-2">
                            {tabs.map((tab) => (
                                <div
                                    key={tab}
                                    className={`h-1 rounded-full transition-all duration-300 ${activeTab === tab ? 'w-8 bg-[var(--accent)]' : 'w-2 bg-gray-400/50'}`}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Ambient Glow underneath */}
                    <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-[80%] h-20 bg-[var(--accent)]/20 blur-[100px] -z-10 rounded-full pointer-events-none" />
                </motion.div>

            </div>
        </section>
    );
}
