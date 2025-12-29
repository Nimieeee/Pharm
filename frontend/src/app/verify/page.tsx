'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { Check, ArrowRight, Loader2, AlertCircle, Moon, Sun } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

import { API_BASE_URL } from '@/config/api';

function VerifyContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const email = searchParams.get('email') || '';

    // State
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/auth/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code })
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Verification failed');
            }

            setSuccess(true);

            // Trigger confetti
            import('canvas-confetti').then((confetti) => {
                confetti.default({
                    particleCount: 150,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899']
                });
            });

            setTimeout(() => {
                router.push('/login?verified=true');
            }, 2500);

        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md">
            <div className="text-center mb-8">
                <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 bg-[var(--surface-highlight)] rounded-2xl flex items-center justify-center">
                        <Check size={32} className="text-green-500" />
                    </div>
                </div>
                <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Verify your email</h1>
                <p className="text-[var(--text-secondary)] mt-2">
                    We sent a 6-digit code to <span className="font-medium text-[var(--text-primary)]">{email}</span>
                </p>
            </div>

            <form onSubmit={handleSubmit} className="card-swiss border border-[var(--border)] p-6 md:p-8">
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                        <AlertCircle size={20} strokeWidth={1.5} className="text-red-500 flex-shrink-0" />
                        <p className="text-sm text-red-500">{error}</p>
                    </div>
                )}
// ... (rest of form content) ...
            </form>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4 relative">
            <ThemeToggle className="fixed top-4 right-4 md:top-8 md:right-8 z-50" />
            <Suspense fallback={<Loader2 className="animate-spin" />}>
                <VerifyContent />
            </Suspense>
        </div>
    );
}
