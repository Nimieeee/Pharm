'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { motion } from 'framer-motion';

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

export default function HomePage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/chat?q=${encodeURIComponent(query)}`);
    }
  };

  const features = [
    { icon: '🧬', title: 'Drug Research', desc: 'Analyze compounds and interactions' },
    { icon: '📊', title: 'Clinical Data', desc: 'Process trial results and studies' },
    { icon: '🔬', title: 'Molecular Analysis', desc: 'Understand chemical structures' },
    { icon: '📄', title: 'Document RAG', desc: 'Query your research documents' },
  ];

  return (
    <div className="min-h-screen bg-atmospheric">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-strong border-b border-[var(--border)]">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-sm font-bold">P</span>
            </div>
            <span className="font-semibold text-[var(--text-primary)]">PharmGPT</span>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="w-10 h-10 rounded-full bg-[var(--surface-highlight)] flex items-center justify-center btn-press transition-all hover:scale-105"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <button
              onClick={() => router.push('/chat')}
              className="px-5 py-2.5 rounded-full bg-[var(--text-primary)] text-[var(--background)] font-medium text-sm btn-press transition-all hover:opacity-90"
            >
              Open Chat
            </button>
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
            <h1 className="text-hero text-[var(--text-primary)] mb-6">
              Your AI Research
              <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
                Companion
              </span>
            </h1>
            <p className="text-body max-w-xl mx-auto text-lg">
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
                className="w-full h-16 px-6 pr-14 rounded-2xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all shadow-lg"
              />
              <button
                type="submit"
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-[var(--text-primary)] text-[var(--background)] flex items-center justify-center btn-press transition-all hover:opacity-90"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </motion.form>

          {/* Feature Cards */}
          <motion.div 
            variants={item}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                variants={item}
                className="card-swiss border border-[var(--border)] cursor-pointer group"
                onClick={() => router.push('/chat')}
              >
                <div className="text-3xl mb-4 icon-hover transition-transform duration-300 inline-block">
                  {feature.icon}
                </div>
                <h3 className="text-section-header text-[var(--text-primary)] mb-2">
                  {feature.title}
                </h3>
                <p className="text-body text-sm">
                  {feature.desc}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.main>

      {/* Footer */}
      <footer className="py-8 border-t border-[var(--border)]">
        <div className="max-w-[1200px] mx-auto px-6 text-center">
          <p className="text-body text-sm">
            © 2025 PharmGPT. Built for pharmaceutical research excellence.
          </p>
        </div>
      </footer>
    </div>
  );
}
