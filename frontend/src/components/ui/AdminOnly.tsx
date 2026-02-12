'use client';

import { ReactNode } from 'react';
import { useAuth } from '@/lib/auth-context';

interface AdminOnlyProps {
    children: ReactNode;
    /** Optional fallback to render for non-admin users */
    fallback?: ReactNode;
}

/**
 * Wrapper component that only renders children for admin users.
 * Use this to gate experimental UI elements during development.
 * 
 * Usage:
 * <AdminOnly>
 *   <ExperimentalButton />
 * </AdminOnly>
 */
export function AdminOnly({ children, fallback = null }: AdminOnlyProps) {
    const { user } = useAuth();

    if (!user?.is_admin) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
}
