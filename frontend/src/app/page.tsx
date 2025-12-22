'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { motion } from 'framer-motion';
import { Moon, Sun, ArrowRight, Dna, BarChart3, Microscope, FileText, LogIn, LogOut } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';

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
    <div className="min-h-screen bg-atmospheric text-foreground selection:bg-indigo-500/20">

      {/* Navbar with Pill Design - Liquid Glass */}
      <nav className="fixed top-0 left-0 right-0 rounded-none md:top-6 md:left-1/2 md:right-auto md:-translate-x-1/2 md:w-[90%] md:max-w-5xl md:rounded-full z-50 glass-effect transition-all duration-300">
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

          {/* Search Input - Wrapped in GlassCard for Liquid Effect */}
          <motion.div
            variants={item}
            className="max-w-2xl mx-auto mb-24"
          >
            <GlassCard className="p-2 flex items-center gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about drug interactions, compounds, clinical trials..."
                className="flex-1 h-12 bg-transparent border-none text-foreground placeholder:text-foreground-muted focus:outline-none px-4"
              />
              <button
                onClick={(e) => { e.preventDefault(); handleSubmit(e as any); }}
                className="w-10 h-10 rounded-xl bg-foreground text-background flex items-center justify-center btn-press transition-all hover:opacity-90"
              >
                <ArrowRight size={20} strokeWidth={1.5} />
              </button>
            </GlassCard>
          </motion.div>

          {/* Feature Cards */}
          <motion.div
            variants={item}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature) => (
              <GlassCard
                key={feature.title}
                className="p-8 h-full flex flex-col justify-between cursor-pointer group hover:scale-[1.02] hover:shadow-lg transition-all duration-300"
                onClick={() => router.push('/chat')}
              >
                <div>
                  <div className="mb-6 p-3 w-fit rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-colors duration-300">
                    <feature.icon size={28} strokeWidth={2} />
                  </div>
                  <h3 className="text-xl font-serif text-foreground mb-3 font-medium">
                    {feature.title}
                  </h3>
                  <p className="text-foreground-muted text-sm leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
              </GlassCard>
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
