'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface SkeletonLoaderProps {
  variant?: 'card' | 'text' | 'list' | 'circle';
  className?: string;
  count?: number;
}

export default function SkeletonLoader({ 
  variant = 'card', 
  className = '', 
  count = 1 
}: SkeletonLoaderProps) {
  const baseClasses = "bg-white/5 animate-pulse rounded-lg";
  
  const variantClasses = {
    card: "h-48 w-full",
    text: "h-4 w-3/4 mb-2",
    list: "h-12 w-full mb-3",
    circle: "h-12 w-12 rounded-full",
  };

  const selectedClasses = variantClasses[variant] || variantClasses.card;

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={`${baseClasses} ${selectedClasses} ${className}`}
        />
      ))}
    </>
  );
}
