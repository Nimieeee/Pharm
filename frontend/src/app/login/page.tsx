'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { useTheme } from '@/lib/theme-context';
import { Mail, Lock, ArrowRight, Loader2, AlertCircle, Moon, Sun } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import Link from 'next/link';

import { createClient } from '@supabase/supabase-js';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? ''
  : 'http://localhost:8000';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Aggressive backend warmup - multiple pings
  useEffect(() => {
    const warmup = async () => {
      // Fire multiple warmup requests to ensure backend is awake
      const pings = [
        fetch(`${API_BASE_URL}/api/v1/`, { method: 'HEAD' }).catch(() => { }),
        fetch(`${API_BASE_URL}/api/v1/health`, { method: 'GET' }).catch(() => { }),
      ];
      await Promise.all(pings);

      // Second wave after 2 seconds
      setTimeout(() => {
        fetch(`${API_BASE_URL}/api/v1/health`, { method: 'GET' }).catch(() => { });
      }, 2000);
    };
    warmup();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await login(email, password);

      // Clear any stored conversation ID so we start fresh
      localStorage.removeItem('currentConversationId');

      // Pre-fetch conversations while navigating (primes the cache)
      const token = localStorage.getItem('token');
      if (token) {
        // Fire off the conversations request immediately (don't await)
        fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => { });
      }

      router.push('/chat');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      });
      if (error) throw error;
    } catch (err: any) {
      setError(err.message || 'Google login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4 relative">
      {/* Desktop: Advanced Theme Toggle */}
      <ThemeToggle className="hidden md:flex fixed top-8 right-8 z-50" />
      {/* Mobile: Simple Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="md:hidden fixed top-6 right-6 p-2.5 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors z-50"
      >
        {theme === 'light' ? (
          <Moon size={18} className="text-[var(--text-secondary)]" />
        ) : (
          <Sun size={18} className="text-[var(--text-secondary)]" />
        )}
      </button>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <img
              src="/PharmGPT.png"
              alt="PharmGPT Logo"
              className="w-20 h-20 object-contain rounded-2xl shadow-lg"
            />
          </div>
          <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Welcome back</h1>
          <p className="text-[var(--text-secondary)] mt-2">Sign in to continue to PharmGPT</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card-swiss border border-[var(--border)]">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
              <AlertCircle size={20} strokeWidth={1.5} className="text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <button
              type="button"
              onClick={handleGoogleLogin}
              className="w-full h-12 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] font-medium flex items-center justify-center gap-3 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.26z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-[var(--border)]" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-[var(--surface)] px-2 text-[var(--text-secondary)]">
                  Or continue with email
                </span>
              </div>
            </div>

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

            <div>
              <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                Password
              </label>
              <div className="relative">
                <Lock size={18} strokeWidth={1.5} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
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
                Sign In
                <ArrowRight size={18} strokeWidth={1.5} />
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center mt-6 text-[var(--text-secondary)]">
          Don't have an account?{' '}
          <Link href="/register" className="text-indigo-500 hover:underline">
            Sign up
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
