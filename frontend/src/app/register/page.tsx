'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { Mail, Lock, User, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await register(email, password, firstName, lastName);

      // Clear any stored conversation ID so we start fresh
      localStorage.removeItem('currentConversationId');

      router.push('/chat');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-atmospheric px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl font-bold">P</span>
          </div>
          <h1 className="text-2xl font-serif font-medium text-[var(--text-primary)]">Create account</h1>
          <p className="text-[var(--text-secondary)] mt-2">Get started with PharmGPT</p>
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
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  First Name
                </label>
                <div className="relative">
                  <User size={18} strokeWidth={1.5} className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="John"
                    className="w-full h-12 pl-12 pr-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                  className="w-full h-12 px-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                />
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
                  placeholder="Min 8 chars, uppercase, lowercase, digit"
                  required
                  minLength={8}
                  className="w-full h-12 pl-12 pr-4 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                />
              </div>
              <p className="text-xs text-[var(--text-secondary)] mt-2">
                Must contain uppercase, lowercase, and a number
              </p>
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
                Create Account
                <ArrowRight size={18} strokeWidth={1.5} />
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center mt-6 text-[var(--text-secondary)]">
          Already have an account?{' '}
          <Link href="/login" className="text-indigo-500 hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
