'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { AnimatePresence, motion } from 'framer-motion';
import { Moon, Sun, LogIn, LogOut, Database, ChevronDown, User, MessageSquare, ArrowRight, Clock, Plus, Zap, Beaker } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { HeroQupe } from '@/components/landing/HeroQupe';
import { useConversations } from '@/hooks/useSWRChat';
import { getSuggestionPool } from '@/config/suggestionPrompts';
import { API_BASE_URL } from '@/config/api';
import { FlaskConical, Dna, Sparkles, Search, AlertTriangle } from 'lucide-react';
import { ParticleNetwork } from '@/components/landing/ParticleNetwork';
import { StatsShowcase } from '@/components/landing/StatsShowcase';
import { HubsGrid } from '@/components/landing/HubsGrid';
import { PipelineShowcase } from '@/components/landing/PipelineShowcase';

const faqs = [

  { q: "Is my research data secure?", a: "Yes. We offer self-hosted deployment options (Docker) ensuring your proprietary data never leaves your infrastructure." },
  { q: "Can it ingest handwritten lab notes?", a: "Our vision capabilities can transcribe legible handwriting and integrate it into your knowledge base." },
  { q: "What is the token limit for RAG?", a: "We support context windows up to 128k tokens, allowing for analysis of extensive clinical trial reports." }
];

// Demo tabs removed in favor of HubsGrid

export default function HomePage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);
  const [isClient, setIsClient] = useState(false);

  const { conversations } = useConversations();
  const recentConversations = conversations?.slice(0, 5) || [];
  const suggestions = getSuggestionPool().slice(0, 4);

  const isLoggedIn = isClient && (user || localStorage.getItem('token'));

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleSuggestionClick = (suggestion: any) => {
    router.push(`/chat?q=${encodeURIComponent(suggestion.text)}`);
  };

  const handleNewSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get('q') as string;
    if (query?.trim()) {
      router.push(`/chat?q=${encodeURIComponent(query)}`);
    }
  };

  // Warm up backend immediately when landing page loads
  // This ensures backend is ready by the time user logs in
  // Aggressive backend warmup
  useEffect(() => {
    // Use centralized config to prevent Mixed Content errors
    // const API_BASE_URL = ... (Imported from config/api now, but useEffect scope is tricky)
    // Actually, just use the imported constant.


    const warmup = async () => {
      // Fire multiple warmup requests using centralized config
      const pings = [
        fetch(`${API_BASE_URL}/`, { method: 'HEAD' }).catch(() => { }),
        fetch(`${API_BASE_URL}/api/v1/health/`, { method: 'GET' }).catch(() => { }),
      ];
      await Promise.all(pings);

      // Second wave
      setTimeout(() => {
        fetch(`${API_BASE_URL}/api/v1/health/`, { method: 'GET' }).catch(() => { });
      }, 2000);
    };
    warmup();
  }, []);



  return (
    <div className="min-h-screen bg-atmospheric text-foreground selection:bg-orange-500/20">
      <ParticleNetwork />

      {/* Navbar with Pill Design - Liquid Glass */}
      <nav className="!fixed top-0 left-0 right-0 rounded-none md:top-6 md:left-1/2 md:right-auto md:-translate-x-1/2 md:w-[90%] md:max-w-5xl md:rounded-full z-50 glass-effect transition-all duration-300">
        <div className="w-full h-16 md:h-14 px-4 md:px-6 flex items-center justify-between">
          <div className="flex flex-row items-center gap-3">
            <div className="h-10 w-10 relative">
              <img
                src="/Benchside.png"
                alt="Benchside Logo"
                className="object-contain"
              />
            </div>
            <p className="font-bold text-xl text-foreground tracking-tight">Benchside</p>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-2 md:gap-4">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 md:w-10 md:h-10 rounded-full bg-surface-highlight flex items-center justify-center btn-press transition-all hover:scale-105"
            >
              {theme === 'light' ? (
                <Moon size={18} strokeWidth={1.5} className="text-foreground-muted" />
              ) : (
                <Sun size={18} strokeWidth={1.5} className="text-foreground-muted" />
              )}
            </button>

            {/* Auth Buttons */}
            {!isClient ? (
              <div className="w-24 h-9 md:h-10 rounded-full bg-surface-highlight/50 animate-pulse" />
            ) : (user || localStorage.getItem('token')) ? (
              <>
                <button
                  onClick={() => router.push('/chat')}
                  className="h-9 w-9 md:w-auto md:h-10 md:px-5 rounded-full bg-foreground text-background font-medium text-sm btn-press transition-all hover:opacity-90 flex items-center justify-center gap-2"
                  title="Open Chat"
                >
                  <MessageSquare size={18} strokeWidth={1.5} />
                  <span className="hidden md:inline">Open Chat</span>
                </button>
                <button
                  onClick={() => router.push('/profile')}
                  className="w-9 h-9 md:w-10 md:h-10 rounded-full bg-surface-highlight flex items-center justify-center btn-press transition-all hover:scale-105"
                  title="Profile"
                >
                  <User size={18} strokeWidth={1.5} className="text-foreground-muted" />
                </button>
                <button
                  onClick={logout}
                  className="w-9 h-9 md:w-10 md:h-10 rounded-full bg-surface-highlight flex items-center justify-center btn-press transition-all hover:scale-105"
                  title="Sign out"
                >
                  <LogOut size={18} strokeWidth={1.5} className="text-foreground-muted" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => router.push('/login')}
                  className="h-9 px-3 md:h-10 md:px-4 rounded-full bg-surface-highlight text-foreground font-medium text-sm btn-press transition-all hover:bg-surface-hover flex items-center gap-2"
                >
                  <LogIn size={18} strokeWidth={1.5} />
                  <span className="hidden md:inline">Sign In</span>
                </button>
                <button
                  onClick={() => router.push('/register')}
                  className="h-9 px-4 md:h-10 md:px-5 rounded-full bg-foreground text-background font-medium text-sm btn-press transition-all hover:opacity-90"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {isLoggedIn ? (
        <div className="pt-24 md:pt-32 px-4 md:px-6 max-w-4xl mx-auto flex flex-col gap-10 min-h-screen">
          {/* Compact Header & Input */}
          <div className="flex flex-col items-center text-center mt-6 md:mt-10">
            <h1 className="text-3xl md:text-5xl font-serif text-foreground mb-4">What shall we research today?</h1>
            <p className="text-foreground-muted mb-8 text-sm md:text-base">Deep clinical insights, literature analysis, and trial data.</p>

            <form onSubmit={handleNewSearch} className="w-full relative max-w-2xl">
              <input
                name="q"
                type="text"
                placeholder="Ask Benchside anything..."
                className="w-full h-14 pl-6 pr-14 rounded-full bg-[var(--surface-highlight)] border border-[var(--border)] shadow-xl focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 text-foreground text-sm md:text-base transition-all"
              />
              <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-orange-500 text-white flex items-center justify-center hover:bg-orange-600 transition-colors">
                <ArrowRight size={18} />
              </button>
            </form>
          </div>

          {/* Smart Suggestions */}
          <div>
            <div className="flex items-center gap-2 mb-4 px-2">
              <Zap size={16} className="text-orange-500" />
              <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wider">Suggestions</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="flex items-start gap-4 p-4 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-orange-500/50 hover:bg-[var(--surface-highlight)] transition-all text-left group"
                >
                  <div className="p-2.5 rounded-xl bg-[var(--surface-highlight)] group-hover:bg-orange-500/10 transition-colors shrink-0">
                    {suggestion.mode === 'deep_research' ? <Beaker size={18} className="text-orange-500" /> : <Search size={18} className="text-foreground-muted group-hover:text-orange-500" />}
                  </div>
                  <div>
                    <p className="text-sm text-foreground font-medium mb-1 line-clamp-2">{suggestion.text}</p>
                    <p className="text-[10px] text-foreground-muted uppercase tracking-wider font-semibold">{suggestion.mode.replace('_', ' ')}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Research Hubs */}
          <div>
            <div className="flex items-center gap-2 mb-4 px-2">
              <Database size={16} className="text-purple-500" />
              <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wider">Research Hubs</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {/* ADMET Lab */}
              <button
                onClick={() => router.push('/lab')}
                className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-amber-500/50 hover:bg-amber-50 dark:hover:bg-amber-950/20 transition-all group"
              >
                <div className="p-3 rounded-xl bg-amber-100 dark:bg-amber-900/40 group-hover:bg-amber-200 dark:group-hover:bg-amber-900/60 transition-colors">
                  <FlaskConical size={24} className="text-amber-600 dark:text-amber-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground mb-1">ADMET Lab</p>
                  <p className="text-xs text-foreground-muted">Drug discovery & toxicity</p>
                </div>
              </button>

              {/* Literature Search */}
              <button
                onClick={() => router.push('/literature')}
                className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-teal-500/50 hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-all group"
              >
                <div className="p-3 rounded-xl bg-teal-100 dark:bg-teal-900/40 group-hover:bg-teal-200 dark:group-hover:bg-teal-900/60 transition-colors">
                  <Search size={24} className="text-teal-600 dark:text-teal-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground mb-1">Literature</p>
                  <p className="text-xs text-foreground-muted">PubMed search</p>
                </div>
              </button>

              {/* Drug Interactions */}
              <button
                onClick={() => router.push('/ddi')}
                className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-red-500/50 hover:bg-red-50 dark:hover:bg-red-950/20 transition-all group"
              >
                <div className="p-3 rounded-xl bg-red-100 dark:bg-red-900/40 group-hover:bg-red-200 dark:group-hover:bg-red-900/60 transition-colors">
                  <AlertTriangle size={24} className="text-red-600 dark:text-red-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground mb-1">Interactions</p>
                  <p className="text-xs text-foreground-muted">Drug-drug checker</p>
                </div>
              </button>

              {/* Genetics Hub */}
              <button
                onClick={() => router.push('/genetics')}
                className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-purple-500/50 hover:bg-purple-50 dark:hover:bg-purple-950/20 transition-all group"
              >
                <div className="p-3 rounded-xl bg-purple-100 dark:bg-purple-900/40 group-hover:bg-purple-200 dark:group-hover:bg-purple-900/60 transition-colors">
                  <Dna size={24} className="text-purple-600 dark:text-purple-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground mb-1">Genetics Hub</p>
                  <p className="text-xs text-foreground-muted">Pharmacogenomics</p>
                </div>
              </button>

              {/* Creation Studio */}
              <button
                onClick={() => router.push('/studio')}
                className="flex flex-col items-center gap-3 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:border-orange-500/50 hover:bg-orange-50 dark:hover:bg-orange-950/20 transition-all group"
              >
                <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/40 group-hover:bg-orange-200 dark:group-hover:bg-orange-900/60 transition-colors">
                  <Sparkles size={24} className="text-orange-600 dark:text-orange-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground mb-1">Creation Studio</p>
                  <p className="text-xs text-foreground-muted">Slides & documents</p>
                </div>
              </button>
            </div>
          </div>

          {/* Recent Conversations */}
          {recentConversations.length > 0 && (
            <div className="mb-20">
              <div className="flex items-center gap-2 mb-4 px-2">
                <Clock size={16} className="text-foreground-muted" />
                <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wider">Recent Conversations</h3>
              </div>
              <div className="flex flex-col gap-2">
                {recentConversations.map((chat: any) => (
                  <button
                    key={chat.id}
                    onClick={() => {
                      localStorage.setItem('currentConversationId', chat.id);
                      router.push('/chat');
                    }}
                    className="flex items-center justify-between p-4 rounded-2xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors text-left group"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-8 h-8 rounded-full bg-[var(--surface-highlight)] flex items-center justify-center shrink-0 group-hover:bg-[var(--background)] transition-colors">
                        <MessageSquare size={14} className="text-foreground-muted group-hover:text-foreground transition-colors" />
                      </div>
                      <span className="text-sm text-foreground truncate font-medium">{chat.title || 'Untitled Chat'}</span>
                    </div>
                    <span className="text-xs text-foreground-muted shrink-0 whitespace-nowrap pl-4">{new Date(chat.created_at).toLocaleDateString()}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Hero Section */}
          <HeroQupe />


          {/* Showcase Sections */}
          <StatsShowcase />
          <HubsGrid />
          <PipelineShowcase />



          {/* FAQ Section */}
          < section className="py-24 px-6" >
            <div className="max-w-[800px] mx-auto">
              <h2 className="text-4xl font-serif text-foreground mb-12 text-center">Frequently Asked Questions</h2>
              <div className="space-y-4">
                {faqs.map((faq, i) => (
                  <GlassCard key={i} className="px-6 py-4 cursor-pointer overflow-hidden" onClick={() => setOpenFaqIndex(openFaqIndex === i ? null : i)}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-lg text-foreground">{faq.q}</span>
                      <ChevronDown className={`text-foreground-muted transition-transform duration-300 ${openFaqIndex === i ? 'rotate-180' : ''}`} />
                    </div>
                    <AnimatePresence>
                      {openFaqIndex === i && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="mt-4 text-foreground-muted border-t border-border/50 pt-4"
                        >
                          {faq.a}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </GlassCard>
                ))}
              </div>
            </div>
          </section >

          {/* CTA Banner */}
          < section className="py-24 px-6" >
            <div className="max-w-[1200px] mx-auto">
              <GlassCard className="p-12 md:p-20 text-center relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 via-orange-500/10 to-pink-500/10" />
                <h2 className="text-4xl md:text-5xl font-serif text-foreground mb-8 relative z-10">Start accelerating your research today</h2>
                <button onClick={() => router.push('/register')} className="px-8 py-4 rounded-full bg-foreground text-background font-bold text-lg hover:scale-105 transition-transform shadow-lg relative z-10">
                  Start Free Research
                </button>
              </GlassCard>
            </div>
          </section >

          {/* Footer */}
          < footer className="py-20 border-t border-border bg-surface/20" >
            <div className="max-w-[1200px] mx-auto px-6 grid grid-cols-2 md:grid-cols-3 gap-12">
              <div className="col-span-2 md:col-span-1">
                {/* Logo area */}
                <div className="flex items-center gap-3 mb-4 md:mb-0">
                  <img
                    src="/Benchside.png"
                    alt="Benchside Logo"
                    className="w-8 h-8 md:w-10 md:h-10 opacity-90"
                  />
                  <span className="font-serif font-bold text-xl text-foreground">Benchside</span>
                </div>

                <p className="text-foreground-muted max-w-xs mb-6">
                  Pioneering the future of pharmacological intelligence with autonomous AI agents.
                </p>
                {/* Copyright */}
                <div className="text-sm text-foreground-muted opacity-60">
                  © 2026 Benchside. All rights reserved.
                </div>
              </div>
              <div>
                <h4 className="font-bold text-foreground mb-6">Product</h4>
                <ul className="space-y-4 text-foreground-muted text-sm">
                  <li onClick={() => router.push('/chat')} className="hover:text-foreground cursor-pointer transition-colors">Deep Research</li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold text-foreground mb-6">Resources</h4>
                <ul className="space-y-4 text-foreground-muted text-sm">
                  <li onClick={() => router.push('/docs')} className="hover:text-foreground cursor-pointer transition-colors">Documentation</li>
                  <li onClick={() => router.push('/faq')} className="hover:text-foreground cursor-pointer transition-colors">FAQ</li>
                </ul>
              </div>
            </div>
          </footer >

          {/* End of Logged-Out Block */}
        </>
      )}
    </div >
  );
}
