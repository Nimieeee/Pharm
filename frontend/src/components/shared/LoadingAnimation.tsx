import React from 'react';
import { motion } from 'framer-motion';
import StreamingLogo from '@/components/chat/StreamingLogo';

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
            duration: 8,
            repeat: Infinity,
            ease: "linear"
          }}
          className="absolute -inset-8 border border-orange-500/10 rounded-full"
        />

        {/* Branded Thinking Logo */}
        <div className="relative w-28 h-28 bg-surface rounded-3xl p-5 border border-border flex items-center justify-center shadow-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent" />
          <StreamingLogo className="w-full h-full relative z-10" />
        </div>
      </div>

      <div className="flex flex-col items-center gap-3">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-lg font-serif font-medium bg-gradient-to-r from-foreground to-foreground-muted bg-clip-text text-transparent lowercase tracking-wide"
        >
          {label}
        </motion.p>
        
        {/* Modern Progress Line instead of dots */}
        <div className="w-24 h-0.5 bg-surface-highlight rounded-full overflow-hidden relative">
          <motion.div
            animate={{
              x: ['-100%', '100%']
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute inset-0 w-full h-full bg-orange-500/50"
          />
        </div>
      </div>
    </div>
  );
};
