'use client';

import { motion } from 'framer-motion';

export default function StreamingLogo() {
    return (
        <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="inline-block w-4 h-4 ml-1 align-baseline bg-[var(--accent)]"
            style={{
                WebkitMaskImage: 'url("/benchside-ring.png")',
                WebkitMaskSize: 'contain',
                WebkitMaskRepeat: 'no-repeat',
                WebkitMaskPosition: 'center',
                maskImage: 'url("/benchside-ring.png")',
                maskSize: 'contain',
                maskRepeat: 'no-repeat',
                maskPosition: 'center',
            }}
        />
    );
}
