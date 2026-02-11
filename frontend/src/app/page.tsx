'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { AnimatePresence, motion } from 'framer-motion';
import { Moon, Sun, LogIn, LogOut, Database, ChevronDown, User, MessageSquare } from 'lucide-react';
import { GlassCard } from '@/components/ui/GlassCard';
import { HeroQupe } from '@/components/landing/HeroQupe';
import { API_BASE_URL } from '@/config/api';

const faqs = [

  { q: "Is my research data secure?", a: "Yes. We offer self-hosted deployment options (Docker) ensuring your proprietary data never leaves your infrastructure." },
  { q: "Can it ingest handwritten lab notes?", a: "Our vision capabilities can transcribe legible handwriting and integrate it into your knowledge base." },
  { q: "What is the token limit for RAG?", a: "We support context windows up to 128k tokens, allowing for analysis of extensive clinical trial reports." }
];

const demoTabs = [
  { id: 'discovery', label: 'Drug Discovery', content: 'Analyzing target protein structure... Found 3 potential binding sites. Generating ligand candidates...' },
  { id: 'clinical', label: 'Clinical Trials', content: 'Scanning ClinicalTrials.gov... 1,240 matches found. Filtering for Phase 3 oncology trials in EU...' },
  { id: 'market', label: 'Market Analysis', content: 'Competitor drug "X-200" approved in Japan. Projected impact on market share: -15% without innovation...' },
];

export default function HomePage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [activeDemoTab, setActiveDemoTab] = useState(demoTabs[0].id);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

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
    <div className="min-h-screen bg-atmospheric text-foreground selection:bg-indigo-500/20">

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

      {/* Hero Section */}
      <HeroQupe />


      {/* Interactive Demo Section */}
      < section className="py-24 px-6 relative" >
        <div className="max-w-[1200px] mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-serif text-foreground mb-4">Research at the Speed of Thought</h2>
            <p className="text-foreground-muted text-lg">See how PharmGPT adapts to your workflow.</p>
          </div>

          <div className="flex flex-col items-center">
            <div className="flex flex-wrap justify-center gap-2 mb-8 bg-surface/50 p-1.5 rounded-full border border-border backdrop-blur-sm">
              {demoTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveDemoTab(tab.id)}
                  className={`px-6 py-2 rounded-full text-sm font-serif font-medium transition-all duration-300 ${activeDemoTab === tab.id ? 'bg-foreground text-background shadow-lg' : 'text-foreground-muted hover:text-foreground'}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <GlassCard className="w-full max-w-3xl aspect-[16/9] md:aspect-[2/1] p-8 flex flex-col relative overflow-hidden group">
              <div className="absolute top-0 left-0 right-0 h-10 bg-indigo-500/5 px-4 flex items-center gap-2 border-b border-indigo-500/10">
                <div className="w-3 h-3 rounded-full bg-red-400/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-400/80" />
                <div className="w-3 h-3 rounded-full bg-green-400/80" />
              </div>
              <div className="mt-8 font-mono text-sm md:text-base text-foreground/90 whitespace-pre-wrap">
                <span className="text-indigo-500 mr-2">{'>'}</span>
                <AnimatePresence mode="wait">
                  <motion.span
                    key={activeDemoTab}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    transition={{ duration: 0.2 }}
                  >
                    {demoTabs.find(t => t.id === activeDemoTab)?.content}
                  </motion.span>
                </AnimatePresence>
                <motion.span
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ repeat: Infinity, duration: 0.8 }}
                  className="inline-block w-2.5 h-4 ml-1 mx-1 bg-indigo-500 align-middle"
                />
              </div>
            </GlassCard>
          </div>
        </div>
      </section >



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
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10" />
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
    </div >
  );
}
