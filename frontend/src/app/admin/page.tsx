'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import {
    Users,
    MessageSquare,
    FileText,
    AlertCircle,
    Search,
    Trash2,
    CheckCircle2,
    ShieldAlert,
    BarChart3,
    Loader2,
    RefreshCw,
    MoreVertical,
    LifeBuoy,
    Clock,
    CheckCircle,
    XCircle,
    Send,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';

interface SystemStats {
    users: { total: number; active: number; new_this_month: number };
    conversations: { total: number; new_this_month: number };
    messages: { total: number; new_this_month: number };
    documents: { total: number; new_this_month: number };
    support: { total: number; open: number };
    last_updated: string;
}

interface UserProfile {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_admin: boolean;
    is_active: boolean;
    created_at: string;
    conversation_count: number;
}

interface SupportTicket {
    id: string;
    email: string;
    subject: string;
    message: string;
    status: 'open' | 'in_progress' | 'resolved' | 'closed';
    created_at: string;
    user?: { first_name: string; last_name: string; email: string };
    admin_response?: string;
}

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? ''
    : 'http://localhost:8000';

export default function AdminPage() {
    const { user, token } = useAuth();
    const router = useRouter();

    const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'support'>('overview');
    const [stats, setStats] = useState<SystemStats | null>(null);
    const [users, setUsers] = useState<UserProfile[]>([]);
    const [tickets, setTickets] = useState<SupportTicket[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isStatsLoading, setIsStatsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    // Support Ticket State
    const [ticketFilter, setTicketFilter] = useState<'all' | 'open' | 'resolved'>('all');
    const [expandedTicketId, setExpandedTicketId] = useState<string | null>(null);
    const [replyMessage, setReplyMessage] = useState('');
    const [replyStatus, setReplyStatus] = useState('resolved');
    const [isSubmittingReply, setIsSubmittingReply] = useState(false);

    // Verify Admin Access
    useEffect(() => {
        if (!user) return; // Wait for auth to load
        // @ts-ignore - is_admin checks
        if (!user.is_admin) {
            router.push('/chat');
        } else {
            fetchStats();
        }
    }, [user, router]);

    const fetchStats = async () => {
        if (!token) return;
        setIsStatsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/admin/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        } finally {
            setIsStatsLoading(false);
            setIsLoading(false);
        }
    };

    const fetchUsers = async () => {
        if (!token) return;
        try {
            const query = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '';
            const res = await fetch(`${API_BASE_URL}/api/v1/admin/users${query}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            }
        } catch (err) {
            console.error('Failed to fetch users:', err);
        }
    };

    const fetchTickets = async () => {
        if (!token) return;
        try {
            let url = `${API_BASE_URL}/api/v1/support/admin/requests`;
            if (ticketFilter !== 'all') {
                if (ticketFilter === 'open') url += '?status=open';
                else if (ticketFilter === 'resolved') url += '?status=resolved';
            }

            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                setTickets(data);
            }
        } catch (err) {
            console.error('Failed to load tickets', err);
        }
    };

    // Fetch data when tabs change
    useEffect(() => {
        if (!token) return;
        if (activeTab === 'users') fetchUsers();
        if (activeTab === 'support') fetchTickets();
    }, [activeTab, searchQuery, ticketFilter, token]);

    const handleDeleteUser = async (userId: string, email: string) => {
        if (!confirm(`Are you sure you want to delete user ${email}? This action CANNOT be undone.`)) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/admin/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                alert('User deleted successfully');
                fetchUsers(); // Refresh list
                fetchStats(); // Refresh stats
            } else {
                const err = await res.json();
                alert(`Failed to delete user: ${err.detail}`);
            }
        } catch (err) {
            alert('An error occurred while deleting user');
        }
    };

    const handleDeleteTicket = async (ticketId: string) => {
        if (!confirm('Are you sure you want to delete this ticket? This cannot be undone.')) return;

        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/support/admin/requests/${ticketId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                setTickets(prev => prev.filter(t => t.id !== ticketId));
                fetchStats();
            } else {
                const err = await res.json();
                alert(`Failed to delete ticket: ${err.detail}`);
            }
        } catch (err) {
            console.error(err);
            alert('Error deleting ticket');
        }
    };

    const handleReplyTicket = async (ticketId: string) => {
        if (!replyMessage.trim()) return;
        setIsSubmittingReply(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/support/admin/requests/${ticketId}/respond`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    response: replyMessage,
                    status_update: replyStatus
                })
            });

            if (res.ok) {
                // Success
                setReplyMessage('');
                setExpandedTicketId(null);
                fetchTickets(); // Refresh list
                fetchStats();
            } else {
                alert('Failed to send response');
            }
        } catch (err) {
            console.error(err);
            alert('Error sending response');
        } finally {
            setIsSubmittingReply(false);
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

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            </div>
        );
    }

    // @ts-ignore
    if (!user || !user.is_admin) return null;

    return (
        <div className="min-h-screen bg-[var(--background)] flex">
            {/* Sidebar */}
            <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col hidden md:flex">
                <div className="mb-8">
                    <h1 className="text-xl font-serif font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <ShieldAlert className="text-red-500" />
                        Admin Panel
                    </h1>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">System Management</p>
                </div>

                <nav className="space-y-2 flex-1">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeTab === 'overview'
                            ? 'bg-indigo-500/10 text-indigo-500 font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]'
                            }`}
                    >
                        <BarChart3 size={18} />
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeTab === 'users'
                            ? 'bg-indigo-500/10 text-indigo-500 font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]'
                            }`}
                    >
                        <Users size={18} />
                        User Management
                    </button>
                    <button
                        onClick={() => setActiveTab('support')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeTab === 'support'
                            ? 'bg-indigo-500/10 text-indigo-500 font-medium'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]'
                            }`}
                    >
                        <LifeBuoy size={18} />
                        Support Tickets
                    </button>
                </nav>

                <div className="mt-auto pt-6 border-t border-[var(--border)]">
                    <Link href="/chat" className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)] hover:text-[var(--text-primary)] transition-colors">
                        <MessageSquare size={18} />
                        Back to Chat
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <header className="h-16 border-b border-[var(--border)] bg-[var(--surface)]/50 backdrop-blur-sm sticky top-0 z-10 flex items-center justify-between px-8">
                    <h2 className="text-lg font-medium text-[var(--text-primary)] capitalize">
                        {activeTab.replace('_', ' ')}
                    </h2>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => {
                                fetchStats();
                                if (activeTab === 'users') fetchUsers();
                                if (activeTab === 'support') fetchTickets();
                            }}
                            className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-highlight)] rounded-full transition-colors"
                            disabled={isStatsLoading}
                        >
                            <RefreshCw size={18} className={isStatsLoading ? 'animate-spin' : ''} />
                        </button>
                        <ThemeToggle />
                        <div className="w-8 h-8 rounded-full bg-indigo-500 text-white flex items-center justify-center font-medium">
                            A
                        </div>
                    </div>
                </header>

                <div className="p-8">
                    {activeTab === 'overview' && stats && (
                        <div className="space-y-8">
                            {/* Stats Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <StatsCard
                                    title="Total Users"
                                    value={stats.users.total}
                                    subtext={`${stats.users.new_this_month} new this month`}
                                    icon={Users}
                                    color="blue"
                                />
                                <StatsCard
                                    title="Conversations"
                                    value={stats.conversations.total}
                                    subtext={`${stats.conversations.new_this_month} new this month`}
                                    icon={MessageSquare}
                                    color="indigo"
                                />
                                <StatsCard
                                    title="Documents"
                                    value={stats.documents.total}
                                    subtext={`${stats.documents.new_this_month} uploaded this month`}
                                    icon={FileText}
                                    color="purple"
                                />
                                <StatsCard
                                    title="Open Tickets"
                                    value={stats.support.open}
                                    subtext={`${stats.support.total} total tickets`}
                                    icon={AlertCircle}
                                    color="amber"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'users' && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-4 bg-[var(--surface)] p-2 rounded-xl border border-[var(--border)] max-w-md">
                                <Search className="text-[var(--text-secondary)] ml-2" size={20} />
                                <input
                                    type="text"
                                    placeholder="Search users by name or email..."
                                    className="bg-transparent border-none focus:outline-none flex-1 text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>

                            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden">
                                <table className="w-full text-left">
                                    <thead className="bg-[var(--surface-highlight)] border-b border-[var(--border)]">
                                        <tr>
                                            <th className="px-6 py-4 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">User</th>
                                            <th className="px-6 py-4 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Role</th>
                                            <th className="px-6 py-4 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Conversations</th>
                                            <th className="px-6 py-4 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Joined</th>
                                            <th className="px-6 py-4 text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--border)]">
                                        {users.map((u) => (
                                            <tr key={u.id} className="hover:bg-[var(--surface-highlight)]/50 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-medium text-xs">
                                                            {u.first_name?.[0] || u.email[0].toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <p className="font-medium text-[var(--text-primary)]">{u.first_name} {u.last_name}</p>
                                                            <p className="text-xs text-[var(--text-secondary)]">{u.email}</p>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    {u.is_admin ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-500">
                                                            <ShieldAlert size={12} /> Admin
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-500">
                                                            User
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-[var(--text-secondary)]">
                                                    {u.conversation_count}
                                                </td>
                                                <td className="px-6 py-4 text-[var(--text-secondary)] text-sm">
                                                    {new Date(u.created_at).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    {!u.is_admin && (
                                                        <button
                                                            onClick={() => handleDeleteUser(u.id, u.email)}
                                                            className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                                                            title="Delete User"
                                                        >
                                                            <Trash2 size={18} />
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {users.length === 0 && (
                                    <div className="p-8 text-center text-[var(--text-secondary)]">
                                        No users found.
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'support' && (
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 mb-6">
                                <button
                                    onClick={() => setTicketFilter('all')}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${ticketFilter === 'all' ? 'bg-[var(--text-primary)] text-[var(--background)]' : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                                >
                                    All Tickets
                                </button>
                                <button
                                    onClick={() => setTicketFilter('open')}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${ticketFilter === 'open' ? 'bg-blue-500 text-white' : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                                >
                                    Open
                                </button>
                                <button
                                    onClick={() => setTicketFilter('resolved')}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${ticketFilter === 'resolved' ? 'bg-green-500 text-white' : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                                >
                                    Resolved
                                </button>
                            </div>

                            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] overflow-hidden">
                                {tickets.length === 0 ? (
                                    <div className="p-12 text-center">
                                        <LifeBuoy className="mx-auto text-[var(--text-secondary)] mb-4" size={48} />
                                        <h3 className="text-lg font-medium text-[var(--text-primary)]">No tickets found</h3>
                                        <p className="text-[var(--text-secondary)]">There are no support tickets matching your filter.</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-[var(--border)]">
                                        {tickets.map((ticket) => (
                                            <div key={ticket.id} className="transition-all hover:bg-[var(--surface-highlight)]/30">
                                                <div
                                                    onClick={() => setExpandedTicketId(expandedTicketId === ticket.id ? null : ticket.id)}
                                                    className="p-6 cursor-pointer flex items-center justify-between group"
                                                >
                                                    <div className="flex items-center gap-4">
                                                        <div className={`p-2 rounded-full ${getStatusColor(ticket.status)} bg-opacity-10 border-0`}>
                                                            {ticket.status === 'open' && <AlertCircle size={20} />}
                                                            {ticket.status === 'in_progress' && <Clock size={20} />}
                                                            {ticket.status === 'resolved' && <CheckCircle size={20} />}
                                                            {ticket.status === 'closed' && <XCircle size={20} />}
                                                        </div>
                                                        <div>
                                                            <div className="flex items-center gap-3 mb-1">
                                                                <h3 className="font-medium text-[var(--text-primary)] text-lg">{ticket.subject}</h3>
                                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(ticket.status)}`}>
                                                                    {ticket.status.toUpperCase()}
                                                                </span>
                                                            </div>
                                                            <p className="text-sm text-[var(--text-secondary)]">
                                                                From: {ticket.email} • {new Date(ticket.created_at).toLocaleString()}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleDeleteTicket(ticket.id);
                                                            }}
                                                            className="p-2 text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 hover:text-red-500 hover:bg-red-500/10 rounded-full transition-all"
                                                            title="Delete Ticket"
                                                        >
                                                            <Trash2 size={18} />
                                                        </button>
                                                        <ChevronDown
                                                            size={20}
                                                            className={`text-[var(--text-secondary)] transition-transform duration-300 ${expandedTicketId === ticket.id ? 'rotate-180' : ''}`}
                                                        />
                                                    </div>
                                                </div>

                                                <AnimatePresence>
                                                    {expandedTicketId === ticket.id && (
                                                        <motion.div
                                                            initial={{ height: 0, opacity: 0 }}
                                                            animate={{ height: 'auto', opacity: 1 }}
                                                            exit={{ height: 0, opacity: 0 }}
                                                            className="border-t border-[var(--border)] bg-[var(--surface-highlight)]/10"
                                                        >
                                                            <div className="p-6 space-y-6">
                                                                <div className="bg-[var(--surface)] p-4 rounded-xl border border-[var(--border)]">
                                                                    <p className="text-sm text-[var(--text-primary)] whitespace-pre-wrap leading-relaxed">{ticket.message}</p>
                                                                </div>

                                                                {ticket.admin_response && (
                                                                    <div className="bg-indigo-500/10 p-4 rounded-xl border border-indigo-500/20">
                                                                        <p className="text-xs font-bold text-indigo-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                                                                            <ShieldAlert size={12} />
                                                                            Previous Response
                                                                        </p>
                                                                        <p className="text-sm text-[var(--text-primary)]">{ticket.admin_response}</p>
                                                                    </div>
                                                                )}

                                                                {ticket.status !== 'closed' && (
                                                                    <div className="bg-[var(--surface)] p-6 rounded-xl border border-[var(--border)] shadow-sm">
                                                                        <h4 className="font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                                                            <Send size={16} />
                                                                            Reply to Ticket
                                                                        </h4>
                                                                        <textarea
                                                                            value={replyMessage}
                                                                            onChange={(e) => setReplyMessage(e.target.value)}
                                                                            placeholder="Type your response here..."
                                                                            className="w-full h-32 p-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 mb-4 resize-none"
                                                                        />
                                                                        <div className="flex items-center justify-between">
                                                                            <div className="flex items-center gap-4">
                                                                                <label className="flex items-center gap-2 cursor-pointer">
                                                                                    <input
                                                                                        type="radio"
                                                                                        name="status"
                                                                                        checked={replyStatus === 'resolved'}
                                                                                        onChange={() => setReplyStatus('resolved')}
                                                                                        className="text-indigo-500 focus:ring-indigo-500"
                                                                                    />
                                                                                    <span className="text-sm text-[var(--text-primary)]">Mark Resolved</span>
                                                                                </label>
                                                                                <label className="flex items-center gap-2 cursor-pointer">
                                                                                    <input
                                                                                        type="radio"
                                                                                        name="status"
                                                                                        checked={replyStatus === 'in_progress'}
                                                                                        onChange={() => setReplyStatus('in_progress')}
                                                                                        className="text-indigo-500 focus:ring-indigo-500"
                                                                                    />
                                                                                    <span className="text-sm text-[var(--text-primary)]">In Progress</span>
                                                                                </label>
                                                                            </div>
                                                                            <button
                                                                                onClick={() => handleReplyTicket(ticket.id)}
                                                                                disabled={isSubmittingReply || !replyMessage.trim()}
                                                                                className="px-6 py-2.5 bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                                                            >
                                                                                {isSubmittingReply ? 'Sending...' : 'Send Response'}
                                                                                {!isSubmittingReply && <Send size={16} />}
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

function StatsCard({ title, value, subtext, icon: Icon, color }: any) {
    const colorStyles = {
        blue: "bg-blue-500/10 text-blue-500",
        indigo: "bg-indigo-500/10 text-indigo-500",
        purple: "bg-purple-500/10 text-purple-500",
        amber: "bg-amber-500/10 text-amber-500",
    }[color as string] || "bg-gray-500/10 text-gray-500";

    return (
        <div className="bg-[var(--surface)] p-6 rounded-2xl border border-[var(--border)] shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl ${colorStyles}`}>
                    <Icon size={24} />
                </div>
                <span className="text-xs font-medium text-[var(--text-secondary)] bg-[var(--surface-highlight)] px-2 py-1 rounded-full">+12%</span>
            </div>
            <h3 className="text-3xl font-bold text-[var(--text-primary)] mb-1">{value}</h3>
            <p className="text-sm text-[var(--text-secondary)]">{title}</p>
            <p className="text-xs text-[var(--text-muted)] mt-2">{subtext}</p>
        </div>
    );
}
