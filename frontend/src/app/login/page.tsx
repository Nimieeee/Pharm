'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { Mail, Lock, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import Link from 'next/link';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? ''
  : 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Aggressive backend warmup - multiple pings
  useEffect(() => {
    const warmup = async () => {
      // Fire multiple warmup requests to ensure backend is awake
      const pings = [
        fetch(`${API_BASE_URL}/`, { method: 'HEAD' }).catch(() => { }),
        fetch(`${API_BASE_URL}/health`, { method: 'GET' }).catch(() => { }),
      ];
      await Promise.all(pings);

      // Second wave after 2 seconds
      setTimeout(() => {
        fetch(`${API_BASE_URL}/health`, { method: 'GET' }).catch(() => { });
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4 relative">
      <ThemeToggle className="absolute top-6 right-6 z-50" />
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
