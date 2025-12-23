"use client";

import React, { ReactNode, useState, useEffect } from 'react';

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    onClick?: () => void;
}

export const GlassCard = ({
    children,
    className = '',
    onClick,
}: GlassCardProps) => {
    // Always use the proven CSS glass effect
    // The liquid glass SVG approach has browser compatibility issues
    return (
        <div
            className={`glass-effect ${className}`}
            onClick={onClick}
        >
            {children}
        </div>
    );
};

// Enhanced glass effect with more prominent styling
export const GlassCardEnhanced = ({
    children,
    className = '',
    onClick,
}: GlassCardProps) => {
    return (
        <div
            className={`
                relative overflow-hidden rounded-2xl
                bg-white/10 dark:bg-white/5
                backdrop-blur-xl
                border border-white/20 dark:border-white/10
                shadow-lg shadow-black/5 dark:shadow-black/20
                ${className}
            `}
            onClick={onClick}
            style={{
                // Enhanced glass effect
                backgroundImage: `
                    linear-gradient(
                        135deg,
                        rgba(255, 255, 255, 0.1) 0%,
                        rgba(255, 255, 255, 0.05) 50%,
                        rgba(255, 255, 255, 0.02) 100%
                    )
                `,
            }}
        >
            {/* Specular highlight - top edge glow */}
            <div
                className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"
                aria-hidden="true"
            />
            {/* Content */}
            {children}
        </div>
    );
};

// Glass navbar with pill shape
export const GlassNavbar = ({
    children,
    className = '',
}: {
    children: ReactNode;
    className?: string;
}) => {
    return (
        <div className={`glass-effect ${className}`}>
            {children}
        </div>
    );
};
