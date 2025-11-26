'use client';

import { ReactNode, useState, useId } from 'react';
import { motion } from 'framer-motion';

// ============================================
// 1. LIQUID BACKGROUND - Floating Blob Layer
// ============================================
export function LiquidBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
      {/* Blob 1 - Cyan */}
      <motion.div
        className="absolute w-[300px] h-[300px] md:w-[500px] md:h-[500px] rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-[60px] md:blur-[80px] opacity-70"
        style={{ backgroundColor: 'var(--liquid-blob-1)', top: '10%', left: '15%' }}
        animate={{
          x: [0, 30, -20, 50, 0],
          y: [0, -50, 20, 30, 0],
          rotate: [0, 90, 180, 270, 360],
          scale: [1, 1.1, 0.95, 1.05, 1],
        }}
        transition={{
          duration: 20,
          ease: 'easeInOut',
          repeat: Infinity,
          repeatType: 'loop',
        }}
      />
      
      {/* Blob 2 - Violet */}
      <motion.div
        className="absolute w-[250px] h-[250px] md:w-[450px] md:h-[450px] rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-[60px] md:blur-[80px] opacity-70"
        style={{ backgroundColor: 'var(--liquid-blob-2)', top: '40%', right: '10%' }}
        animate={{
          x: [0, -40, 20, -30, 0],
          y: [0, 30, -40, 20, 0],
          rotate: [0, -120, -240, -360],
          scale: [1, 0.92, 1.08, 0.95, 1],
        }}
        transition={{
          duration: 25,
          ease: 'easeInOut',
          repeat: Infinity,
          repeatType: 'loop',
        }}
      />
      
      {/* Blob 3 - Amber */}
      <motion.div
        className="absolute w-[200px] h-[200px] md:w-[350px] md:h-[350px] rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-[60px] md:blur-[80px] opacity-60"
        style={{ backgroundColor: 'var(--liquid-blob-3)', bottom: '15%', left: '30%' }}
        animate={{
          x: [0, 50, -30, 20, 0],
          y: [0, -30, 40, -20, 0],
          rotate: [0, 180, 360],
          scale: [1, 1.15, 0.9, 1.05, 1],
        }}
        transition={{
          duration: 18,
          ease: 'easeInOut',
          repeat: Infinity,
          repeatType: 'loop',
        }}
      />
    </div>
  );
}

// ============================================
// 2. REFRACTIVE CARD - Glass Container
// ============================================
interface RefractiveCardProps {
  children: ReactNode;
  className?: string;
}

export function RefractiveCard({ children, className = '' }: RefractiveCardProps) {
  return (
    <div
      className={`
        relative overflow-hidden rounded-2xl border
        bg-[var(--glass-surface)] border-[var(--glass-border)]
        shadow-xl
        backdrop-blur-md md:backdrop-blur-3xl
        before:absolute before:inset-0 before:bg-noise before:opacity-5 before:pointer-events-none
        ${className}
      `}
    >
      {/* Inner glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}


// ============================================
// 3. LIQUID BUTTON - Soap Bubble Distortion
// ============================================
interface LiquidButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export function LiquidButton({ 
  children, 
  onClick, 
  disabled = false,
  variant = 'primary',
  className = '' 
}: LiquidButtonProps) {
  const [isHovered, setIsHovered] = useState(false);
  const filterId = useId();

  const baseStyles = variant === 'primary'
    ? 'bg-gradient-to-r from-cyan-500 to-violet-500 text-white'
    : 'bg-[var(--glass-surface)] border border-[var(--glass-border)] text-[var(--text-primary)]';

  return (
    <div className="relative inline-block">
      {/* SVG Filter for Distortion Effect */}
      <svg className="absolute w-0 h-0">
        <defs>
          <filter id={filterId}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency={isHovered ? 0.02 : 0}
              numOctaves={2}
              result="turbulence"
            >
              <animate
                attributeName="baseFrequency"
                dur="0.3s"
                values={isHovered ? '0;0.02' : '0.02;0'}
                fill="freeze"
              />
            </feTurbulence>
            <feDisplacementMap
              in="SourceGraphic"
              in2="turbulence"
              scale={isHovered ? 8 : 0}
              xChannelSelector="R"
              yChannelSelector="G"
            />
          </filter>
        </defs>
      </svg>

      <motion.button
        onClick={onClick}
        disabled={disabled}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={`
          relative px-6 py-3 rounded-xl font-medium text-sm
          backdrop-blur-md shadow-lg
          transition-all duration-300
          disabled:opacity-50 disabled:cursor-not-allowed
          ${baseStyles}
          ${className}
        `}
        style={{
          filter: isHovered && !disabled ? `url(#${filterId})` : 'none',
        }}
      >
        {/* Shimmer overlay on hover */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: '-100%' }}
          animate={{ x: isHovered ? '100%' : '-100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />
        
        <span className="relative z-10">{children}</span>
      </motion.button>
    </div>
  );
}

// ============================================
// 4. LIQUID GLASS CONTAINER - Full Page Wrapper
// ============================================
interface LiquidGlassContainerProps {
  children: ReactNode;
  className?: string;
  showBackground?: boolean;
}

export function LiquidGlassContainer({ 
  children, 
  className = '',
  showBackground = true 
}: LiquidGlassContainerProps) {
  return (
    <div className={`relative min-h-screen overflow-hidden ${className}`}>
      {showBackground && <LiquidBackground />}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}

// ============================================
// 5. GLASS DIVIDER - Subtle Separator
// ============================================
export function GlassDivider({ className = '' }: { className?: string }) {
  return (
    <div 
      className={`h-px bg-gradient-to-r from-transparent via-[var(--glass-border)] to-transparent ${className}`}
    />
  );
}

// ============================================
// 6. GLASS BADGE - Status Indicator
// ============================================
interface GlassBadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
  className?: string;
}

export function GlassBadge({ 
  children, 
  variant = 'default',
  className = '' 
}: GlassBadgeProps) {
  const variantStyles = {
    default: 'bg-[var(--glass-surface)] text-[var(--text-primary)]',
    success: 'bg-emerald-500/20 text-emerald-500 border-emerald-500/30',
    warning: 'bg-amber-500/20 text-amber-500 border-amber-500/30',
    error: 'bg-red-500/20 text-red-500 border-red-500/30',
  };

  return (
    <span 
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        border border-[var(--glass-border)] backdrop-blur-sm
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}
