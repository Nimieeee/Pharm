'use client';

import { motion } from 'framer-motion';

export default function StreamingLogo({ className = "inline-block w-6 h-6 ml-1 align-middle" }: { className?: string }) {
    return (
        <motion.img
            src="/benchside-ring.png"
            alt="Streaming Indicator"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className={className}
        />
    );
}
