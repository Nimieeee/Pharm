'use client';

import React from 'react';
import { motion } from 'framer-motion';

export const HorizonGlow = () => {
    return (
        <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
            {/* 
        The "Stretched" Glow (The Key Feature) 
        - Centered, massive (150vw), heavily blurred
        - Color: #C85B20 (User Specific Orange) fading to transparent
      */}
            <motion.div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[150vw] h-[400px] rounded-[100%] blur-[120px] mix-blend-screen"
                style={{
                    background: 'radial-gradient(circle, #C85B20 0%, rgba(200, 91, 32, 0.5) 40%, transparent 70%)',
                    transform: 'translate(-50%, -50%) scaleY(0.5)', // Initial scaleY compressed
                }}
                animate={{
                    scaleY: [0.5, 0.55, 0.5], // Breathe vertically slightly
                    scaleX: [1, 1.05, 1],     // Breathe horizontally
                    opacity: [0.6, 0.8, 0.6], // Breathe opacity
                }}
                transition={{
                    duration: 10,
                    repeat: Infinity,
                    ease: "easeInOut",
                }}
            />

            {/* 
        Secondary Ambient Light (Top Center)
        - Simulates light source from above
        - Color: Lighter Orange/Amber to complement the core
      */}
            <motion.div
                className="absolute top-[-100px] left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full blur-[100px] opacity-30 mix-blend-screen"
                style={{
                    background: 'radial-gradient(circle, rgba(255, 165, 0, 0.3) 0%, transparent 70%)', // Orange/Gold
                }}
                animate={{
                    opacity: [0.2, 0.4, 0.2],
                    scale: [1, 1.1, 1],
                }}
                transition={{
                    duration: 8,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 2,
                }}
            />
        </div>
    );
};
