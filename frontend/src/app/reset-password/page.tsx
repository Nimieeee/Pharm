'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Lock, ArrowRight, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { API_BASE_URL } from '@/config/api';

function ResetPasswordContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error, setError] = useState('');

    if (!token) {
        return (
            <div className="text-center">
                <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 inline-flex items-center gap-3">
                    <AlertCircle size={20} strokeWidth={1.5} className="text-red-500" />
                    <p className="text-red-500">Invalid or missing reset token.</p>
                </div>
                <div>
                    <Link href="/forgot-password" className="text-indigo-500 hover:text-indigo-600 font-medium">
                        Request a new link
                    </Link>
                </div>
            </div>
        );
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token, new_password: password }),
            });

            const data = await response.json();

            if (response.ok) {
                setIsSuccess(true);
                setTimeout(() => {
                    router.push('/login');
                }, 3000);
            } else {
                setError(data.detail || 'Failed to reset password');
            }
        } catch (err) {
            setError('An error occurred. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (isSuccess) {
        return (
            <div className="card-swiss border border-[var(--border)] text-center py-8">
                <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
                <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Password Reset Successful</h3>
                <p className="text-[var(--text-secondary)] mb-6">
                    Your password has been updated. Redirecting to login...
                </p>
                <Link
                    href="/login"
                    className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium transition-all hover:opacity-90"
                >
                    Login Now
                </Link>
            </div>
        );
    }

    return (
        <div className="card-swiss border border-[var(--border)]">
            <form onSubmit={handleSubmit}>
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                        <AlertCircle size={20} strokeWidth={1.5} className="text-red-500 flex-shrink-0" />
                        <p className="text-sm text-red-500">{error}</p>
                    </div>
                )}

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                            New Password
                        </label>
                        <div className="relative">
                            <Lock size={18} strokeWidth={1.5} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="At least 8 characters"
                                required
                                className="w-full h-12 pl-12 pr-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                            Confirm Password
                        </label>
                        <div className="relative">
                            <Lock size={18} strokeWidth={1.5} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Confirm new password"
                                required
                                className="w-full h-12 pl-12 pr-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                            />
                        </div>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-12 mt-6 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium flex items-center justify-center gap-2 btn-press hover:opacity-90 transition-all disabled:opacity-50"
                >
                    {isLoading ? (
                        <Loader2 size={20} strokeWidth={1.5} className="animate-spin" />
                    ) : (
                        <>
                            Reset Password
                            <ArrowRight size={18} strokeWidth={1.5} />
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md"
            >
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Set New Password</h1>
                    <p className="text-[var(--text-secondary)] mt-2">Enter your new password below</p>
                </div>

                <Suspense fallback={<div className="flex justify-center"><Loader2 className="animate-spin" /></div>}>
                    <ResetPasswordContent />
                </Suspense>
            </motion.div>
        </div>
    );
}
