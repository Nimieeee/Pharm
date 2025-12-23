'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { AnimatePresence, motion } from 'framer-motion';
import { Moon, Sun, ArrowRight, Dna, BarChart3, Microscope, FileText, LogIn, LogOut, Globe, Database, Activity, FileSearch, Shield, Zap, Cpu, ChevronDown, CheckCircle2, Play } from 'lucide-react';
import { GlassCard, GlassNavbar } from '@/components/ui/GlassCard';

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

const capabilities = [
  {
    title: "Deep Literature Research",
    desc: "Autonomous agents scan millions of papers to find relevant interactions and contraindications.",
    className: "md:col-span-2",
    icon: Globe,
    gradient: "from-blue-500/10 to-cyan-500/10"
  },
  {
    title: "Real-time Docking",
    desc: "Predict binding affinities instantly.",
    className: "md:col-span-1",
    icon: Database,
    gradient: "from-purple-500/10 to-pink-500/10"
  },
  {
    title: "Clinical Trials",
    desc: "Track global patient recruitment.",
    className: "md:col-span-1",
    icon: Activity,
    gradient: "from-emerald-500/10 to-teal-500/10"
  },
  {
    title: "Patent Landscape",
    desc: "Visualize IP whitespace and operate freely.",
    className: "md:col-span-2 lg:col-span-1",
    icon: FileSearch,
    gradient: "from-orange-500/10 to-red-500/10"
  },
  {
    title: "Automated Compliance",
    desc: "Ensure FDA/EMA guideline adherence.",
    className: "md:col-span-3 lg:col-span-1",
    icon: Shield,
    gradient: "from-indigo-500/10 to-violet-500/10"
  }
];

const faqs = [
  { q: "How accurate is the molecular analysis?", a: "PharmGPT uses state-of-the-art vision models (Pixtral) combined with biochemical databases to ensure high fidelity in structure recognition." },
  { q: "Is my research data secure?", a: "Yes. We offer self-hosted deployment options (Docker) ensuring your proprietary data never leaves your infrastructure." },
  { q: "Can it ingest handwritten lab notes?", a: "Our vision capabilities can transcribe legible handwriting and integrate it into your knowledge base." }, // Fixed duplicate content in prompt
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
  const [query, setQuery] = useState('');
  const [activeDemoTab, setActiveDemoTab] = useState(demoTabs[0].id);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  // Warm up backend immediately when landing page loads
  // This ensures backend is ready by the time user logs in
  useEffect(() => {
    const API_BASE_URL = 'https://toluwanimi465-pharmgpt-backend.hf.space';
    fetch(`${API_BASE_URL}/`, { method: 'HEAD' }).catch(() => { });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/chat?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <div className="min-h-screen bg-atmospheric text-foreground selection:bg-indigo-500/20">

      {/* Navbar with Pill Design - Liquid Glass */}
      <nav className="!fixed top-0 left-0 right-0 rounded-none md:top-6 md:left-1/2 md:right-auto md:-translate-x-1/2 md:w-[90%] md:max-w-5xl md:rounded-full z-50 glass-effect transition-all duration-300">
        <div className="w-full h-16 md:h-14 px-4 md:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 relative rounded-xl overflow-hidden">
              <img
                src="/PharmGPT.png"
                alt="PharmGPT Logo"
                className="w-full h-full object-cover"
              />
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
            <h1 className="text-5xl md:text-7xl font-serif text-foreground mb-6 leading-tight tracking-tight">
              Your AI Research
              <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-500 to-violet-500 italic">
                Companion
              </span>
            </h1>
            <p className="text-foreground-muted max-w-xl mx-auto text-lg">
              Accelerate pharmacological research with intelligent document analysis,
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

      {/* Interactive Demo Section */}
      <section className="py-24 px-6 relative" >
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
      </section>

      {/* Bento Grid Features */}
      <section className="py-24 px-6 bg-surface/30" >
        <div className="max-w-[1200px] mx-auto">
          <h2 className="text-4xl font-serif text-foreground mb-16 text-center">Powerful Research Capabilities</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilities.map((cap, i) => (
              <GlassCard key={i} className={`${cap.className} p-8 relative overflow-hidden hover:scale-[1.01] transition-transform duration-500`}>
                <div className={`absolute inset-0 bg-gradient-to-br ${cap.gradient} opacity-20`} />
                <div className="relative z-10 flex flex-col h-full justify-between">
                  <div className="mb-6 p-3 w-fit rounded-2xl bg-foreground/5 text-foreground">
                    <cap.icon size={24} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-serif text-foreground mb-3">{cap.title}</h3>
                    <p className="text-foreground-muted">{cap.desc}</p>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 px-6" >
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
      </section>

      {/* CTA Banner */}
      <section className="py-24 px-6" >
        <div className="max-w-[1200px] mx-auto">
          <GlassCard className="p-12 md:p-20 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10" />
            <h2 className="text-4xl md:text-5xl font-serif text-foreground mb-8 relative z-10">Start accelerating your research today</h2>
            <button onClick={() => router.push('/register')} className="px-8 py-4 rounded-full bg-foreground text-background font-bold text-lg hover:scale-105 transition-transform shadow-lg relative z-10">
              Start Free Research
            </button>
          </GlassCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 border-t border-border bg-surface/20" >
        <div className="max-w-[1200px] mx-auto px-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12">
          <div className="col-span-2 lg:col-span-2">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <span className="text-white text-sm font-bold">P</span>
              </div>
              <span className="font-serif font-bold text-xl text-foreground">PharmGPT</span>
            </div>
            <p className="text-foreground-muted max-w-xs mb-6">
              Pioneering the future of pharmaceutical intelligence with autonomous AI agents.
            </p>
            <p className="text-xs text-foreground-muted">
              © 2025 PharmGPT. All rights reserved.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-foreground mb-6">Product</h4>
            <ul className="space-y-4 text-foreground-muted text-sm">
              <li className="hover:text-foreground cursor-pointer">Deep Research</li>
              <li className="hover:text-foreground cursor-pointer">Data Workbench</li>
              <li className="hover:text-foreground cursor-pointer">Clinical Intelligence</li>
              <li className="hover:text-foreground cursor-pointer">Enterprise API</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-foreground mb-6">Resources</h4>
            <ul className="space-y-4 text-foreground-muted text-sm">
              <li className="hover:text-foreground cursor-pointer">Documentation</li>
              <li className="hover:text-foreground cursor-pointer">API Reference</li>
              <li className="hover:text-foreground cursor-pointer">Case Studies</li>
              <li className="hover:text-foreground cursor-pointer">Community</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-foreground mb-6">Legal</h4>
            <ul className="space-y-4 text-foreground-muted text-sm">
              <li className="hover:text-foreground cursor-pointer">Privacy Policy</li>
              <li className="hover:text-foreground cursor-pointer">Terms of Service</li>
              <li className="hover:text-foreground cursor-pointer">Security</li>
              <li className="hover:text-foreground cursor-pointer">Compliance</li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
}
