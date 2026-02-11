'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
    ArrowLeft,
    Send,
    HelpCircle,
    Loader2,
    MessageSquare,
    LifeBuoy,
    ClipboardList,
    Clock,
    CheckCircle,
    XCircle,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import Link from 'next/link';
import { useTheme } from '@/lib/theme-context';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

import { API_BASE_URL } from '@/config/api';


interface SupportTicket {
    id: string;
    subject: string;
    message: string;
    status: 'open' | 'in_progress' | 'resolved' | 'closed';
    created_at: string;
    admin_response?: string;
}

export default function SupportPage() {
    const { user, token } = useAuth();
    const router = useRouter();
    const { theme } = useTheme();

    // View State
    const [view, setView] = useState<'create' | 'list' | 'chat'>('create');

    // Form State
    const [subject, setSubject] = useState('');
    const [message, setMessage] = useState('');
    const [email, setEmail] = useState(user?.email || '');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    // List State
    const [tickets, setTickets] = useState<SupportTicket[]>([]);
    const [isLoadingTickets, setIsLoadingTickets] = useState(false);
    const [expandedTicketId, setExpandedTicketId] = useState<string | null>(null);

    // Chat State
    const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
    const [chatInput, setChatInput] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);

    // Initial load check
    useEffect(() => {
        if (user) {
            setEmail(user.email);
        }
    }, [user]);

    const handleChatSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!chatInput.trim() || isChatLoading) return;

        const userMsg = chatInput;
        setChatInput('');
        setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsChatLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/support/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    message: userMsg,
                    history: chatMessages // Send previous history
                })
            });

            if (res.ok) {
                const data = await res.json();
                setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
            } else {
                setChatMessages(prev => [...prev, { role: 'assistant', content: "I apologize, I'm having trouble connecting right now. Please try again later." }]);
            }
        } catch (err) {
            setChatMessages(prev => [...prev, { role: 'assistant', content: "Network error occurred." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    // Fetch tickets when view changes to list
    useEffect(() => {
        if (view === 'list' && user && token) {
            fetchTickets();
        }
    }, [view, user, token]);

    const fetchTickets = async () => {
        setIsLoadingTickets(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/support/requests`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.ok) {
                const data = await res.json();
                setTickets(data);
            } else {
                console.error("Failed to fetch tickets");
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoadingTickets(false);
        }
    };

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
                // If user is logged in, refresh list (silently or on next view)
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

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'open': return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
            case 'in_progress': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
            case 'resolved': return 'text-green-500 bg-green-500/10 border-green-500/20';
            case 'closed': return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
            default: return 'text-gray-500 bg-gray-500/10';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'open': return <ClipboardList size={16} />;
            case 'in_progress': return <Clock size={16} />;
            case 'resolved': return <CheckCircle size={16} />;
            case 'closed': return <XCircle size={16} />;
            default: return <HelpCircle size={16} />;
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

                <nav className="space-y-2">
                    <button
                        onClick={() => setView('create')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left ${view === 'create' ? 'bg-[var(--surface-highlight)] text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]'}`}
                    >
                        <Send size={18} />
                        Submit Request
                    </button>
                    {user && (
                        <button
                            onClick={() => setView('list')}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left ${view === 'list' ? 'bg-[var(--surface-highlight)] text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]'}`}
                        >
                            <ClipboardList size={18} />
                            My Tickets
                        </button>
                    )}
                </nav>

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
            <main className="flex-1 p-4 md:p-12 overflow-y-auto">
                <div className="max-w-2xl mx-auto">
                    <div className="flex items-center justify-between mb-8 hidden md:flex">
                        <h2 className="text-2xl font-serif font-medium text-[var(--text-primary)]">
                            {view === 'create' ? 'Submit a Ticket' : 'My Support History'}
                        </h2>
                        <ThemeToggle />
                    </div>

                    {/* Mobile Tabs */}
                    {user && (
                        <div className="flex md:hidden mb-6 bg-[var(--surface-highlight)] p-1 rounded-xl">
                            <button
                                onClick={() => setView('create')}
                                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${view === 'create' ? 'bg-[var(--surface)] shadow-sm text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}
                            >
                                New Ticket
                            </button>
                            <button
                                onClick={() => setView('list')}
                                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${view === 'list' ? 'bg-[var(--surface)] shadow-sm text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}
                            >
                                History
                            </button>
                        </div>
                    )}

                    {view === 'create' ? (
                        <div className="card-swiss border border-[var(--border)] p-4 md:p-8">
                            {/* ... existing Create Ticket form ... */}
                            {success ? (
                                <div className="text-center py-12">
                                    <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <Send size={32} />
                                    </div>
                                    <h3 className="text-xl font-medium text-[var(--text-primary)] mb-2">Message Sent!</h3>
                                    <p className="text-[var(--text-secondary)] mb-6">
                                        Thank you for reaching out. Our support team will respond to <strong>{email}</strong> shortly.
                                    </p>
                                    <div className="flex flex-col gap-3">
                                        <button
                                            onClick={() => setSuccess(false)}
                                            className="text-indigo-500 font-medium hover:underline"
                                        >
                                            Send another message
                                        </button>
                                        {user && (
                                            <button
                                                onClick={() => setView('list')}
                                                className="text-[var(--text-secondary)] text-sm hover:text-[var(--text-primary)]"
                                            >
                                                View my tickets
                                            </button>
                                        )}
                                    </div>
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
                                            className="w-full rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] px-4 h-12 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all placeholder:text-[var(--text-secondary)]"
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
                                            className="w-full rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] px-4 h-12 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all placeholder:text-[var(--text-secondary)]"
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
                                            className="w-full rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] p-4 outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all resize-none placeholder:text-[var(--text-secondary)]"
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
                    ) : view === 'list' ? (
                        <div className="space-y-4">
                            {/* ... List view content (same as before) ... */}
                            {isLoadingTickets ? (
                                <div className="flex justify-center py-12">
                                    <Loader2 className="animate-spin text-indigo-500" size={32} />
                                </div>
                            ) : tickets.length === 0 ? (
                                <div className="text-center py-12 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
                                    <ClipboardList className="mx-auto text-[var(--text-secondary)] mb-4" size={48} />
                                    <h3 className="text-lg font-medium text-[var(--text-primary)]">No tickets found</h3>
                                    <p className="text-[var(--text-secondary)] mb-6">You haven't submitted any support requests yet.</p>
                                    <button
                                        onClick={() => setView('create')}
                                        className="text-indigo-500 font-medium hover:underline"
                                    >
                                        Create a new ticket
                                    </button>
                                </div>
                            ) : (
                                tickets.map((ticket) => (
                                    <div
                                        key={ticket.id}
                                        className="bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden transition-all hover:border-indigo-500/30"
                                    >
                                        <div
                                            onClick={() => setExpandedTicketId(expandedTicketId === ticket.id ? null : ticket.id)}
                                            className="p-4 flex items-center justify-between cursor-pointer hover:bg-[var(--surface-highlight)]/50"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-lg border ${getStatusColor(ticket.status)}`}>
                                                    {getStatusIcon(ticket.status)}
                                                </div>
                                                <div>
                                                    <h4 className="font-medium text-[var(--text-primary)]">{ticket.subject}</h4>
                                                    <p className="text-xs text-[var(--text-secondary)]">
                                                        {new Date(ticket.created_at).toLocaleDateString()} • ID: {ticket.id.slice(0, 8)}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(ticket.status)}`}>
                                                    {ticket.status.replace('_', ' ').toUpperCase()}
                                                </span>
                                                {expandedTicketId === ticket.id ? <ChevronUp size={16} className="text-[var(--text-secondary)]" /> : <ChevronDown size={16} className="text-[var(--text-secondary)]" />}
                                            </div>
                                        </div>
                                        <AnimatePresence>
                                            {expandedTicketId === ticket.id && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: 'auto', opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="border-t border-[var(--border)] bg-[var(--surface-highlight)]/20"
                                                >
                                                    <div className="p-4 space-y-4">
                                                        <div>
                                                            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-1">Your Message</p>
                                                            <p className="text-sm text-[var(--text-primary)] whitespace-pre-wrap">{ticket.message}</p>
                                                        </div>
                                                        {ticket.admin_response && (
                                                            <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-lg p-3">
                                                                <p className="text-xs font-medium text-indigo-500 uppercase tracking-wider mb-1 flex items-center gap-2">
                                                                    <LifeBuoy size={12} />
                                                                    Benchside Support Response
                                                                </p>
                                                                <p className="text-sm text-[var(--text-primary)] whitespace-pre-wrap">{ticket.admin_response}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                ))
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col h-[600px] bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
                            <div className="p-4 border-b border-[var(--border)] bg-[var(--surface-highlight)]/30 flex items-center gap-3">
                                <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-500">
                                    <MessageSquare size={20} />
                                </div>
                                <div>
                                    <h3 className="font-medium text-[var(--text-primary)]">Support Assistant</h3>
                                    <p className="text-xs text-[var(--text-secondary)]">Powered by Benchside AI</p>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                                {chatMessages.length === 0 && (
                                    <div className="text-center py-8 opacity-60">
                                        <LifeBuoy className="mx-auto text-indigo-500 mb-2" size={32} />
                                        <p className="text-sm text-[var(--text-secondary)]">
                                            Hi! I'm your Benchside Support Agent.<br />
                                            Ask me anything about how to use the platform!
                                        </p>
                                    </div>
                                )}

                                {chatMessages.map((msg, idx) => (
                                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div
                                            className={`max-w-[85%] rounded-2xl p-3 text-sm ${msg.role === 'user'
                                                ? 'bg-blue-600 text-white rounded-tr-none'
                                                : 'bg-[var(--surface-highlight)] text-[var(--text-primary)] rounded-tl-none border border-[var(--border)]'
                                                }`}
                                        >
                                            {msg.role === 'assistant' ? (
                                                <ReactMarkdown
                                                    components={{
                                                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                                                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                                                        ul: ({ children }) => <ul className="list-disc list-inside ml-1 my-1">{children}</ul>,
                                                        ol: ({ children }) => <ol className="list-decimal list-inside ml-1 my-1">{children}</ol>,
                                                        li: ({ children }) => <li className="mb-0.5">{children}</li>,
                                                    }}
                                                >{msg.content}</ReactMarkdown>
                                            ) : (
                                                msg.content
                                            )}
                                        </div>
                                    </div>
                                ))}
                                {isChatLoading && (
                                    <div className="flex justify-start">
                                        <div className="bg-[var(--surface-highlight)] rounded-2xl rounded-tl-none px-4 py-2 border border-[var(--border)]">
                                            <div className="flex gap-1">
                                                <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <form onSubmit={handleChatSubmit} className="p-4 border-t border-[var(--border)] bg-[var(--surface)]">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        placeholder="Ask a question..."
                                        className="flex-1 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-indigo-500/20"
                                        disabled={isChatLoading}
                                    />
                                    <button
                                        type="submit"
                                        disabled={!chatInput.trim() || isChatLoading}
                                        className="p-2 rounded-xl bg-indigo-500 text-white hover:bg-indigo-600 disabled:opacity-50 transition-colors"
                                    >
                                        <Send size={18} />
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <button
                            onClick={() => window.location.href = '/faq'}
                            className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-blue-500/30 transition-all text-left"
                        >
                            <HelpCircle className="text-indigo-500 mb-4" size={24} />
                            <h3 className="font-medium text-[var(--text-primary)] mb-2">FAQs</h3>
                            <p className="text-sm text-[var(--text-secondary)]">Check our knowledge base for quick answers to common questions.</p>
                        </button>
                        <button
                            onClick={() => setView('chat')}
                            className={`p-6 rounded-2xl border transition-all text-left ${view === 'chat' ? 'bg-indigo-500/5 border-indigo-500 ring-1 ring-indigo-500/20' : 'bg-[var(--surface)] border-[var(--border)] hover:border-purple-500/30'}`}
                        >
                            <MessageSquare className="text-purple-500 mb-4" size={24} />
                            <h3 className="font-medium text-[var(--text-primary)] mb-2">Live Chat</h3>
                            <p className="text-sm text-[var(--text-secondary)]">Chat with our AI support agent for instant assistance 24/7.</p>
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
}
