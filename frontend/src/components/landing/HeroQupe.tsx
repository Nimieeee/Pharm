'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { useTheme } from '@/lib/theme-context';

export function HeroQupe() {
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    const currentTheme = mounted ? theme : 'light';
    const isDark = currentTheme === 'dark';

    // Deep gradient for button (Dark Blue -> Black)
    const buttonGradient = "bg-gradient-to-br from-indigo-950 via-gray-900 to-black";

    return (
        <section className="relative w-full overflow-hidden bg-background pt-24 pb-32 md:pt-32 md:pb-48 lg:pt-40 lg:pb-56">
            {/* Background Gradient (No Image) */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-white to-white dark:from-gray-950 dark:via-gray-900 dark:to-black" />

                {/* Subtle Ambient Glows for Depth */}
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-100/30 dark:bg-indigo-900/20 rounded-full blur-[120px] mix-blend-multiply dark:mix-blend-screen animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-teal-100/30 dark:bg-teal-900/10 rounded-full blur-[100px] mix-blend-multiply dark:mix-blend-screen" />
            </div>

            <div className="container relative z-10 mx-auto px-4 md:px-6 flex flex-col items-center text-center">

                {/* Badge with Glow */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="relative inline-flex items-center space-x-2 bg-indigo-50/80 dark:bg-indigo-900/30 backdrop-blur-sm border border-indigo-100 dark:border-indigo-800 rounded-full px-4 py-1.5 mb-8 cursor-default overflow-hidden group"
                >
                    {/* Badge Glow */}
                    <div className="absolute inset-0 bg-indigo-500/10 blur-xl group-hover:bg-indigo-500/20 transition-all duration-500" />

                    <span className="relative text-[11px] font-bold tracking-wider text-indigo-600 dark:text-indigo-200 uppercase flex items-center">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-2 animate-pulse" />
                        Benchside AI
                    </span>
                </motion.div>

                {/* Heading */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
                    className="text-5xl md:text-7xl lg:text-8xl font-serif text-foreground tracking-tight mb-8 max-w-5xl relative z-10"
                >
                    Your Intelligent <br className="hidden md:block" />
                    {/* Neon Text Effect for Dark Mode: Lavender -> Cyan */}
                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-300 dark:via-purple-200 dark:to-cyan-200 animate-gradient-x pb-2">
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
                    {/* Primary Button with Deep Gradient */}
                    <button className={`h-12 px-8 rounded-full ${buttonGradient} text-white font-medium text-base hover:scale-105 hover:shadow-lg hover:shadow-indigo-500/20 transition-all duration-300 flex items-center group relative overflow-hidden`}>
                        <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <span className="relative z-10">Start Researching</span>
                        <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform relative z-10" />
                    </button>

                    <button className="h-12 px-8 rounded-full bg-transparent border border-border text-foreground font-medium text-base hover:bg-surface-hover/50 hover:border-indigo-300 dark:hover:border-indigo-700 transition-all flex items-center">
                        View Demo
                    </button>
                </motion.div>

                {/* Dashboard Anchor (The "Float" Fix) */}
                <motion.div
                    initial={{ opacity: 0, y: 100, rotateX: 5 }}
                    animate={{ opacity: 1, y: 0, rotateX: 0 }}
                    transition={{ duration: 1, delay: 0.4, type: "spring", stiffness: 40, damping: 20 }}
                    className="relative w-full max-w-6xl perspective-1000 flex flex-col items-center"
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

                        {/* Desktop View Only (Simplified for Impact) */}
                        <div className="relative aspect-[2880/1580] w-full">
                            <Image
                                src={`/assets/desktop-chat-${currentTheme}.png`}
                                alt="Benchside Interface"
                                fill
                                className="object-cover object-top"
                                priority
                            />
                        </div>
                    </div>

                    {/* Ambient Glow underneath */}
                    <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-[80%] h-20 bg-indigo-500/20 blur-[100px] -z-10 rounded-full pointer-events-none" />
                </motion.div>

            </div>
        </section>
    );
}
