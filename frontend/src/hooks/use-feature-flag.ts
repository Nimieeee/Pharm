'use client';

import { useAuth } from '@/lib/auth-context';

/**
 * Feature flags for gating experimental features.
 * 
 * During development, features are gated behind admin-only access.
 * To release a feature to all users, change its gate from 'admin' to 'all'.
 */
const FEATURE_FLAGS: Record<string, 'admin' | 'all' | 'none'> = {
    'mermaid-diagrams': 'admin',    // Phase 3: Mermaid diagram rendering
    'chart-generation': 'admin',    // Phase 2: Matplotlib/Seaborn charts
    'image-generation': 'admin',    // Phase 4: Hugging Face image gen
};

/**
 * Hook to check if a feature is enabled for the current user.
 * Returns true if the feature is available.
 */
export function useFeatureFlag(featureName: string): boolean {
    const { user } = useAuth();
    const gate = FEATURE_FLAGS[featureName];

    if (!gate || gate === 'none') return false;
    if (gate === 'all') return true;
    if (gate === 'admin') return !!user?.is_admin;

    return false;
}

/**
 * Hook to check if any experimental features are enabled.
 */
export function useHasExperimentalFeatures(): boolean {
    const { user } = useAuth();
    if (!user?.is_admin) return false;
    return Object.values(FEATURE_FLAGS).some(gate => gate === 'admin');
}
