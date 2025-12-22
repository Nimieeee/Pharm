import React, { ReactNode } from 'react';

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    onClick?: () => void;
}

export const GlassCard = ({ children, className = '', onClick }: GlassCardProps) => {
    return (
        <div
            className={`glass-effect ${className}`}
            onClick={onClick}
        >
            {children}
        </div>
    );
};
