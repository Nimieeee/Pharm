'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { Check, ArrowRight, Loader2, AlertCircle, Moon, Sun } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

import { API_BASE_URL } from '@/config/api';

function ResendButton({ email }: { email: string }) {
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [cooldown, setCooldown] = useState(0);

    const handleResend = async () => {
        if (!email) return;
        setLoading(true);
        setMessage('');

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/auth/verify/resend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            if (!res.ok) throw new Error('Failed to send code');

            setMessage('Code sent!');
            setCooldown(60);

            // Countdown timer
            const interval = setInterval(() => {
                setCooldown(prev => {
                    if (prev <= 1) {
                        clearInterval(interval);
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);

        } catch (err) {
            setMessage('Failed to send');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="text-center mt-6">
            <p className="text-sm text-[var(--text-secondary)]">
                Didn't receive the code?{' '}
                <button
                    type="button"
                    onClick={handleResend}
                    disabled={loading || cooldown > 0}
                    className="text-[var(--primary)] hover:underline font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Sending...' : cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Code'}
                </button>
            </p>
            {message && <p className="text-xs text-green-500 mt-2">{message}</p>}
        </div>
    );
}

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
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                            Verification Code
                        </label>
                        <input
                            type="text"
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            required
                            placeholder="Enter 6-digit code"
                            className="w-full h-12 px-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-all text-center tracking-[0.5em] text-lg font-mono"
                            maxLength={6}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || code.length !== 6}
                        className="w-full h-12 bg-gradient-to-r from-[var(--primary)] to-[var(--primary-hover)] text-white font-medium rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {isLoading ? <Loader2 className="animate-spin" size={20} /> : 'Verify Email'}
                    </button>

                    <ResendButton email={email} />
                </div>
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
