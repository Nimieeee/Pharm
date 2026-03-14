'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface LoadingAnimationProps {
  label?: string;
}

export const LoadingAnimation = ({ label = 'Processing...' }: LoadingAnimationProps) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full gap-8">
      <div className="relative">
        {/* Outer Glow */}
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute inset-0 bg-orange-500/20 blur-3xl rounded-full"
        />
        
        {/* Rotating Ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute -inset-4 border-2 border-dashed border-orange-500/30 rounded-full"
        />

        {/* Logo */}
        <motion.div
          animate={{
            y: [0, -10, 0],
            filter: [
              'drop-shadow(0 0 0px rgba(249, 115, 22, 0))',
              'drop-shadow(0 0 20px rgba(249, 115, 22, 0.4))',
              'drop-shadow(0 0 0px rgba(249, 115, 22, 0))',
            ]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="relative w-24 h-24 bg-surface rounded-3xl p-4 border border-border flex items-center justify-center shadow-2xl"
        >
          <img src="/Benchside.png" alt="Benchside" className="w-full h-full object-contain" />
        </motion.div>
      </div>

      <div className="flex flex-col items-center gap-2">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-lg font-serif font-medium bg-gradient-to-r from-foreground to-foreground-muted bg-clip-text text-transparent"
        >
          {label}
        </motion.p>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
              className="w-1.5 h-1.5 rounded-full bg-orange-500"
            />
          ))}
        </div>
      </div>
    </div>
  );
};
