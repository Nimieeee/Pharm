"use client";

import React, { ReactNode, useState, useEffect } from 'react';
import LiquidGlass from './LiquidGlass';

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    onClick?: () => void;
    // Liquid Glass options
    enableLiquidGlass?: boolean;
    bezelWidth?: number;
    glassThickness?: number;
    borderRadius?: number;
}

// Chrome detection
function isChrome(): boolean {
    if (typeof window === "undefined") return false;
    const userAgent = navigator.userAgent;
    return /Chrome/.test(userAgent) && !/Edge|Edg|OPR|Opera/.test(userAgent);
}

export const GlassCard = ({
    children,
    className = '',
    onClick,
    enableLiquidGlass = true,
    bezelWidth = 16,
    glassThickness = 6,
    borderRadius = 20
}: GlassCardProps) => {
    const [useAdvanced, setUseAdvanced] = useState(false);

    useEffect(() => {
        setUseAdvanced(enableLiquidGlass && isChrome());
    }, [enableLiquidGlass]);

    if (useAdvanced) {
        return (
            <LiquidGlass
                className={className}
                bezelWidth={bezelWidth}
                glassThickness={glassThickness}
                borderRadius={borderRadius}
                refractiveIndex={1.45}
                highlightIntensity={0.5}
                style={{ cursor: onClick ? 'pointer' : 'default' }}
            >
                <div onClick={onClick}>
                    {children}
                </div>
            </LiquidGlass>
        );
    }

    // Fallback to CSS glass effect
    return (
        <div
            className={`glass-effect ${className}`}
            onClick={onClick}
            style={{ borderRadius }}
        >
            {children}
        </div>
    );
};

// Preset for navigation bars
export const GlassNavbar = ({
    children,
    className = '',
}: {
    children: ReactNode;
    className?: string;
}) => {
    const [useAdvanced, setUseAdvanced] = useState(false);

    useEffect(() => {
        setUseAdvanced(isChrome());
    }, []);

    if (useAdvanced) {
        return (
            <LiquidGlass
                className={className}
                bezelWidth={12}
                glassThickness={4}
                borderRadius={9999}
                refractiveIndex={1.4}
                highlightIntensity={0.4}
            >
                {children}
            </LiquidGlass>
        );
    }

    return (
        <div className={`glass-effect ${className}`}>
            {children}
        </div>
    );
};
