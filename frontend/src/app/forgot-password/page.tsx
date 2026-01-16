'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, ArrowRight, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { API_BASE_URL } from '@/config/api';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSent, setIsSent] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (response.ok) {
                setIsSent(true);
            } else {
                throw new Error('Failed to send reset email');
            }
        } catch (err) {
            setError('An error occurred. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md"
            >
                <div className="text-center mb-8">
                    <Link href="/login" className="inline-flex items-center text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-6 transition-colors">
                        <ArrowRight className="rotate-180 mr-2 w-4 h-4" />
                        Back to Login
                    </Link>
                    <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Reset Password</h1>
                    <p className="text-[var(--text-secondary)] mt-2">Enter your email to receive a reset link</p>
                </div>

                <div className="card-swiss border border-[var(--border)]">
                    {isSent ? (
                        <div className="text-center py-8">
                            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-8 h-8 text-green-500" />
                            </div>
                            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Check your email</h3>
                            <p className="text-[var(--text-secondary)] mb-6">
                                We've sent a password reset link to <br />
                                <span className="font-medium text-[var(--text-primary)]">{email}</span>
                            </p>
                            <button
                                onClick={() => setIsSent(false)}
                                className="text-indigo-500 hover:text-indigo-600 font-medium"
                            >
                                Try inputting another email
                            </button>
                        </div>
                    ) : (
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
                                        Email
                                    </label>
                                    <div className="relative">
                                        <Mail size={18} strokeWidth={1.5} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="you@example.com"
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
                                        Send Reset Link
                                        <ArrowRight size={18} strokeWidth={1.5} />
                                    </>
                                )}
                            </button>
                        </form>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
