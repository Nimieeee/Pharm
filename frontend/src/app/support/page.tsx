'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
    ArrowLeft,
    Send,
    HelpCircle,
    Loader2,
    MessageSquare,
    LifeBuoy
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import Link from 'next/link';
import { useTheme } from '@/lib/theme-context';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? ''
    : 'http://localhost:8000';

export default function SupportPage() {
    const { user, token } = useAuth();
    const router = useRouter();
    const { theme } = useTheme();

    const [subject, setSubject] = useState('');
    const [message, setMessage] = useState('');
    const [email, setEmail] = useState(user?.email || '');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/support/requests`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    email,
                    subject,
                    message
                })
            });

            if (res.ok) {
                setSuccess(true);
                setSubject('');
                setMessage('');
                if (!user) setEmail('');
            } else {
                const data = await res.json();
                setError(data.detail || 'Failed to submit ticket');
            }
        } catch (err) {
            setError('An error occurred. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--background)] flex flex-col md:flex-row">
            {/* Sidebar (Desktop) */}
            <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] p-6 hidden md:flex flex-col">
                <div className="mb-8">
                    <h1 className="text-xl font-serif font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <LifeBuoy className="text-indigo-500" />
                        Help Center
                    </h1>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">We are here to help</p>
                </div>

                <div className="mt-auto">
                    <Link href="/chat" className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)] hover:text-[var(--text-primary)] transition-colors">
                        <MessageSquare size={18} />
                        Back to Chat
                    </Link>
                </div>
            </aside>

            {/* Mobile Header */}
            <header className="md:hidden flex items-center justify-between p-4 border-b border-[var(--border)] bg-[var(--surface)]">
                <Link href="/chat" className="p-2 -ml-2 text-[var(--text-secondary)]">
                    <ArrowLeft size={20} />
                </Link>
                <h1 className="font-semibold text-[var(--text-primary)]">Help Center</h1>
                <ThemeToggle />
            </header>

            {/* Main Content */}
            <main className="flex-1 p-6 md:p-12 overflow-y-auto">
                <div className="max-w-2xl mx-auto">
                    <div className="flex items-center justify-between mb-8 hidden md:flex">
                        <h2 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Submit a Ticket</h2>
                        <ThemeToggle />
                    </div>

                    <div className="card-swiss border border-[var(--border)] p-8">
                        {success ? (
                            <div className="text-center py-12">
                                <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Send size={32} />
                                </div>
                                <h3 className="text-xl font-medium text-[var(--text-primary)] mb-2">Message Sent!</h3>
                                <p className="text-[var(--text-secondary)] mb-6">
                                    Thank you for reaching out. Our support team will respond to <strong>{email}</strong> shortly.
                                </p>
                                <button
                                    onClick={() => setSuccess(false)}
                                    className="text-indigo-500 font-medium hover:underline"
                                >
                                    Send another message
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                {error && (
                                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm">
                                        {error}
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">Email Address</label>
                                    <input
                                        type="email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        disabled={!!user} // Auto-filled for logged in users
                                        className="w-full text-input"
                                        placeholder="you@example.com"
                                    />
                                    {user && <p className="text-xs text-[var(--text-secondary)] mt-1 ml-1">Logged in as {user.first_name}</p>}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">Subject</label>
                                    <input
                                        type="text"
                                        required
                                        value={subject}
                                        onChange={(e) => setSubject(e.target.value)}
                                        className="w-full text-input"
                                        placeholder="Brief summary of the issue"
                                        minLength={5}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">Message</label>
                                    <textarea
                                        required
                                        value={message}
                                        onChange={(e) => setMessage(e.target.value)}
                                        rows={6}
                                        className="w-full text-input py-3 resize-none"
                                        placeholder="Describe your issue in detail..."
                                        minLength={10}
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full h-12 bg-[var(--text-primary)] text-[var(--background)] font-medium rounded-xl flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                                >
                                    {isSubmitting ? (
                                        <Loader2 size={20} className="animate-spin" />
                                    ) : (
                                        <>
                                            Submit Ticket
                                            <Send size={18} />
                                        </>
                                    )}
                                </button>
                            </form>
                        )}
                    </div>

                    <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)]">
                            <HelpCircle className="text-indigo-500 mb-4" size={24} />
                            <h3 className="font-medium text-[var(--text-primary)] mb-2">FAQs</h3>
                            <p className="text-sm text-[var(--text-secondary)]">Check our knowledge base for quick answers to common questions.</p>
                        </div>
                        <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)]">
                            <MessageSquare className="text-purple-500 mb-4" size={24} />
                            <h3 className="font-medium text-[var(--text-primary)] mb-2">Live Chat</h3>
                            <p className="text-sm text-[var(--text-secondary)]">Chat with our AI support agent for instant assistance 24/7.</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
