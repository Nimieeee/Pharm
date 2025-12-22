'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { motion } from 'framer-motion';
import { Moon, Sun, ArrowRight, Dna, BarChart3, Microscope, FileText, LogIn, LogOut } from 'lucide-react';
import Image from 'next/image';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.2, 0.8, 0.2, 1] } }
};

const features = [
  { icon: Dna, title: 'Drug Research', desc: 'Analyze compounds and interactions' },
  { icon: BarChart3, title: 'Clinical Data', desc: 'Process trial results and studies' },
  { icon: Microscope, title: 'Molecular Analysis', desc: 'Understand chemical structures' },
  { icon: FileText, title: 'Document RAG', desc: 'Query your research documents' },
];

export default function HomePage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/chat?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <div className="min-h-screen relative text-foreground selection:bg-indigo-500/20">
      {/* Nano Banana Background */}
      <div className="fixed inset-0 z-[-1]">
        <Image
          src="/background.png"
          alt="Background"
          fill
          className="object-cover"
          quality={100}
          priority
        />
        {/* Subtle overlay to ensure text readability while keeping vibrancy */}
        <div className="absolute inset-0 bg-background/30 backdrop-blur-[1px]" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/20 to-background" />
      </div>

      {/* Navbar with Pill Design on Desktop */}
      <nav className="fixed top-0 left-0 right-0 md:top-6 md:left-1/2 md:right-auto md:-translate-x-1/2 md:w-[90%] md:max-w-5xl z-50 glass-strong border-b md:border border-white/10 md:rounded-full transition-all duration-300 shadow-2xl shadow-indigo-500/10 backdrop-blur-xl">
        <div className="w-full h-16 md:h-14 px-4 md:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">P</span>
            </div>
            <span className="font-serif font-medium text-foreground hidden md:block">PharmGPT</span>
          </div>

          <div className="flex items-center gap-2 md:gap-6">
            <div className="hidden md:flex items-center gap-6 mr-4">
              <button onClick={() => router.push('/docs')} className="text-sm font-medium text-foreground-muted hover:text-foreground transition-colors">
                Docs
              </button>
              <button onClick={() => router.push('/faq')} className="text-sm font-medium text-foreground-muted hover:text-foreground transition-colors">
                FAQ
              </button>
            </div>

            <button
              onClick={toggleTheme}
              className="w-10 h-10 rounded-full bg-surface-highlight flex items-center justify-center btn-press transition-all hover:scale-105"
            >
              {theme === 'light' ? (
                <Moon size={18} strokeWidth={1.5} className="text-foreground-muted" />
              ) : (
                <Sun size={18} strokeWidth={1.5} className="text-foreground-muted" />
              )}
            </button>
            {user ? (
              <>
                <button
                  onClick={() => router.push('/chat')}
                  className="px-5 py-2.5 rounded-full bg-foreground text-background font-medium text-sm btn-press transition-all hover:opacity-90"
                >
                  Open Chat
                </button>
                <button
                  onClick={logout}
                  className="w-10 h-10 rounded-full bg-surface-highlight flex items-center justify-center btn-press transition-all hover:scale-105"
                  title="Sign out"
                >
                  <LogOut size={18} strokeWidth={1.5} className="text-foreground-muted" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => router.push('/login')}
                  className="px-4 py-2.5 rounded-full bg-surface-highlight text-foreground font-medium text-sm btn-press transition-all hover:bg-surface-hover flex items-center gap-2"
                >
                  <LogIn size={18} strokeWidth={1.5} />
                  Sign In
                </button>
                <button
                  onClick={() => router.push('/register')}
                  className="px-5 py-2.5 rounded-full bg-foreground text-background font-medium text-sm btn-press transition-all hover:opacity-90"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <motion.main
        className="pt-32 pb-24 px-6"
        variants={container}
        initial="hidden"
        animate="show"
      >
        <div className="max-w-[1200px] mx-auto">
          <motion.div variants={item} className="text-center mb-16">
            <h1 className="text-hero font-serif text-foreground mb-6">
              Your AI Research
              <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-500 to-violet-500">
                Companion
              </span>
            </h1>
            <p className="text-foreground-muted max-w-xl mx-auto text-lg">
              Accelerate pharmaceutical research with intelligent document analysis,
              drug interaction insights, and clinical data processing.
            </p>
          </motion.div>

          {/* Search Input */}
          <motion.form
            variants={item}
            onSubmit={handleSubmit}
            className="max-w-2xl mx-auto mb-24"
          >
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about drug interactions, compounds, clinical trials..."
                className="w-full h-16 px-6 pr-14 rounded-2xl bg-surface border border-border text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all shadow-lg"
              />
              <button
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-foreground text-background flex items-center justify-center btn-press transition-all hover:opacity-90"
              >
                <ArrowRight size={20} strokeWidth={1.5} />
              </button>
            </div>
          </motion.form>

          {/* Feature Cards */}
          <motion.div
            variants={item}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature) => (
              <motion.div
                key={feature.title}
                variants={item}
                className="card-swiss border border-border cursor-pointer group"
                onClick={() => router.push('/chat')}
              >
                <div className="mb-4 text-foreground-muted group-hover:text-indigo-500 transition-colors">
                  <feature.icon size={32} strokeWidth={1.5} />
                </div>
                <h3 className="text-section-header font-serif text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-foreground-muted text-sm">
                  {feature.desc}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.main>

      {/* Footer */}
      <footer className="py-8 border-t border-border">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-foreground-muted text-sm">
            © 2025 PharmGPT. Built for pharmaceutical research excellence.
          </p>
          <div className="flex items-center gap-6">
            <button onClick={() => router.push('/docs')} className="text-sm text-foreground-muted hover:text-foreground transition-colors">
              Documentation
            </button>
            <button onClick={() => router.push('/faq')} className="text-sm text-foreground-muted hover:text-foreground transition-colors">
              FAQ
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
