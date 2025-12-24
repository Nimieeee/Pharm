'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    User,
    Camera,
    Mail,
    Shield,
    CheckCircle2,
    Loader2,
    ArrowLeft,
    LogOut,
    Calendar,
    Save,
    Trash2,
    AlertCircle,
    Moon,
    Sun
} from 'lucide-react';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? '' // Use relative path for production (proxied by Vercel)
    : 'http://localhost:8000';

export default function ProfilePage() {
    const { user, token, logout, checkUser } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [firstName, setFirstName] = useState(user?.first_name || '');
    const [lastName, setLastName] = useState(user?.last_name || '');
    const [isUpdating, setIsUpdating] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Redirect if not authenticated
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
        }

        if (user) {
            setFirstName(user.first_name || '');
            setLastName(user.last_name || '');
        }
    }, [user, router]);

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        setIsUpdating(true);
        setError(null);
        setSuccess(false);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    first_name: firstName,
                    last_name: lastName
                })
            });

            if (!response.ok) throw new Error('Failed to update profile');

            await checkUser(); // Refresh user context
            setSuccess(true);
            setTimeout(() => setSuccess(false), 3000);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsUpdating(false);
        }
    };

    const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !token) return;

        setIsUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile/avatar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) throw new Error('Failed to upload avatar');

            await checkUser(); // Refresh user context
            setSuccess(true);
            setTimeout(() => setSuccess(false), 3000);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) return;

        setIsDeleting(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to delete account');

            await logout();
            router.push('/login');
        } catch (err: any) {
            setError(err.message);
            setIsDeleting(false);
        }
    };

    if (!user) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
                <Loader2 size={32} className="text-indigo-500 animate-spin" />
            </div>
        );
    }

    const avatarUrl = user.avatar_url
        ? (user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`)
        : null;

    return (
        <div className="min-h-screen bg-[var(--background)] p-4 md:p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => router.push('/chat')}
                            className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors"
                        >
                            <ArrowLeft size={18} className="text-[var(--text-secondary)]" />
                        </button>
                        <h1 className="text-3xl font-serif font-bold text-[var(--text-primary)]">Profile Settings</h1>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={toggleTheme}
                            className="p-2.5 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors"
                        >
                            {theme === 'light' ? (
                                <Moon size={20} className="text-[var(--text-secondary)]" />
                            ) : (
                                <Sun size={20} className="text-[var(--text-secondary)]" />
                            )}
                        </button>
                        <button
                            onClick={async () => {
                                await logout();
                                router.push('/login');
                            }}
                            className="px-4 py-2 rounded-xl bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-all flex items-center gap-2 text-sm font-medium"
                        >
                            <LogOut size={16} />
                            Sign Out
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Left Panel - Avatar & Info Summary */}
                    <div className="space-y-6">
                        <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-3xl text-center">
                            <div className="relative w-32 h-32 mx-auto mb-6 group">
                                <div className="w-full h-full rounded-2xl overflow-hidden bg-[var(--surface-highlight)] border-4 border-[var(--surface)] shadow-xl relative">
                                    {isUploading ? (
                                        <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm z-10">
                                            <Loader2 size={24} className="text-white animate-spin" />
                                        </div>
                                    ) : avatarUrl ? (
                                        <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <User size={48} className="text-[var(--text-secondary)] opacity-30" />
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="absolute -bottom-2 -right-2 p-2.5 rounded-xl bg-indigo-500 text-white shadow-lg hover:bg-indigo-600 transition-all btn-press z-20"
                                >
                                    <Camera size={18} />
                                </button>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleAvatarUpload}
                                    accept="image/*"
                                    className="hidden"
                                />
                            </div>

                            <h2 className="text-xl font-medium text-[var(--text-primary)] mb-1">
                                {user.first_name} {user.last_name}
                            </h2>
                            <p className="text-sm text-[var(--text-secondary)] mb-6">{user.email}</p>

                            <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-surface-highlight text-xs text-[var(--text-secondary)]">
                                    <Calendar size={14} />
                                    Joined {new Date(user.created_at).toLocaleDateString()}
                                </div>
                                {user.is_admin && (
                                    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-indigo-500/10 text-indigo-500 text-xs font-semibold">
                                        <Shield size={14} />
                                        Administrator
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Account Status Card */}
                        <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-3xl">
                            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <CheckCircle2 size={16} className="text-emerald-500" />
                                Account Status
                            </h3>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-[var(--text-secondary)]">Verification</span>
                                    <span className="text-xs font-bold text-emerald-500 uppercase">Verified</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-[var(--text-secondary)]">2FA</span>
                                    <span className="text-xs font-bold text-[var(--text-secondary)] uppercase">Disabled</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Panel - Edit Form */}
                    <div className="md:col-span-2 space-y-6">
                        <form onSubmit={handleUpdateProfile} className="p-8 bg-[var(--surface)] border border-[var(--border)] rounded-3xl">
                            <h3 className="text-lg font-serif font-medium text-[var(--text-primary)] mb-6 flex items-center gap-2">
                                <User size={20} className="text-indigo-500" />
                                Personal Information
                            </h3>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[var(--text-secondary)]">First Name</label>
                                    <input
                                        type="text"
                                        value={firstName}
                                        onChange={(e) => setFirstName(e.target.value)}
                                        className="w-full h-12 px-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500 transition-all font-medium"
                                        placeholder="Your first name"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[var(--text-secondary)]">Last Name</label>
                                    <input
                                        type="text"
                                        value={lastName}
                                        onChange={(e) => setLastName(e.target.value)}
                                        className="w-full h-12 px-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:border-indigo-500 transition-all font-medium"
                                        placeholder="Your last name"
                                    />
                                </div>
                                <div className="space-y-2 sm:col-span-2">
                                    <label className="text-sm font-medium text-[var(--text-secondary)]">Email Address</label>
                                    <div className="relative">
                                        <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] opacity-50" />
                                        <input
                                            type="email"
                                            value={user.email}
                                            disabled
                                            className="w-full h-12 pl-12 pr-4 rounded-xl bg-[var(--background)] border border-[var(--border)] text-[var(--text-secondary)] opacity-60 cursor-not-allowed font-medium"
                                        />
                                    </div>
                                    <p className="text-[10px] text-[var(--text-secondary)] uppercase tracking-widest mt-1">Email cannot be changed manually</p>
                                </div>
                            </div>

                            <div className="mt-8 flex items-center justify-between">
                                <AnimatePresence>
                                    {success && (
                                        <motion.div
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0 }}
                                            className="flex items-center gap-2 text-emerald-500 text-sm font-medium"
                                        >
                                            <CheckCircle2 size={16} />
                                            Changes saved successfully
                                        </motion.div>
                                    )}
                                    {error && (
                                        <motion.div
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0 }}
                                            className="text-red-500 text-sm font-medium"
                                        >
                                            {error}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <button
                                    type="submit"
                                    disabled={isUpdating}
                                    className="ml-auto flex items-center gap-2 px-8 py-3 rounded-xl bg-foreground text-background font-bold btn-press disabled:opacity-50 transition-all hover:opacity-90"
                                >
                                    {isUpdating ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                                    Save Changes
                                </button>
                            </div>
                        </form>

                        {/* Notification/Preferences placeholder */}
                        <div className="p-8 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 border border-indigo-500/10 rounded-3xl">
                            <h3 className="font-serif font-medium text-[var(--text-primary)] mb-2">Security & Privacy</h3>
                            <p className="text-sm text-[var(--text-secondary)] mb-4">
                                Manage your experimental data access and session security.
                            </p>
                            <button
                                onClick={() => router.push('/docs')}
                                className="text-sm font-medium text-indigo-500 hover:underline"
                            >
                                Learn more about our data protection protocol →
                            </button>
                        </div>

                        {/* Danger Zone */}
                        <div className="p-8 mt-6 bg-red-500/5 border border-red-500/20 rounded-3xl">
                            <h3 className="font-serif font-medium text-red-600 dark:text-red-400 mb-2 flex items-center gap-2">
                                <AlertCircle size={20} />
                                Danger Zone
                            </h3>
                            <p className="text-sm text-[var(--text-secondary)] mb-6">
                                Once you delete your account, there is no going back. Please be certain.
                            </p>
                            <button
                                onClick={handleDeleteAccount}
                                disabled={isDeleting}
                                className="px-6 py-3 rounded-xl bg-red-500 text-white font-medium hover:bg-red-600 transition-all btn-press flex items-center gap-2 disabled:opacity-50"
                            >
                                {isDeleting ? <Loader2 size={18} className="animate-spin" /> : <Trash2 size={18} />}
                                Delete Account
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
