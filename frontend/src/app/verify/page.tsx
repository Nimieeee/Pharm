'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { Check, ArrowRight, Loader2, AlertCircle, Moon, Sun } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? ''
    : 'http://localhost:8000';

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
            setTimeout(() => {
                router.push('/login?verified=true');
            }, 2000);

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

            <form onSubmit={handleSubmit} className="card-swiss border border-[var(--border)]">
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                        <AlertCircle size={20} strokeWidth={1.5} className="text-red-500 flex-shrink-0" />
                        <p className="text-sm text-red-500">{error}</p>
                    </div>
                )}

                {success && (
                    <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center gap-3">
                        <Check size={20} className="text-green-500 flex-shrink-0" />
                        <p className="text-sm text-green-500">Verified! Redirecting...</p>
                    </div>
                )}

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                            Verification Code
                        </label>
                        <input
                            type="text"
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            placeholder="123456"
                            required
                            maxLength={6}
                            className="w-full h-12 text-center text-2xl tracking-widest rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all font-mono"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading || success || code.length < 6}
                    className="w-full h-12 mt-6 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium flex items-center justify-center gap-2 btn-press hover:opacity-90 transition-all disabled:opacity-50"
                >
                    {isLoading ? (
                        <Loader2 size={20} strokeWidth={1.5} className="animate-spin" />
                    ) : success ? (
                        <>
                            Verified
                            <Check size={18} strokeWidth={1.5} />
                        </>
                    ) : (
                        <>
                            Verify Account
                            <ArrowRight size={18} strokeWidth={1.5} />
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4 relative">
            <ThemeToggle className="fixed top-8 right-8 z-50" />
            <Suspense fallback={<Loader2 className="animate-spin" />}>
                <VerifyContent />
            </Suspense>
        </div>
    );
}
