"use client";

import React, { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  ExternalLink,
  CheckCircle2,
  Search,
  ChevronRight,
  AlertCircle,
  Loader2
} from "lucide-react";
import { useTranslation } from "@/hooks/use-translation";

// --- Types ---

export interface Source {
  id: number;
  title: string;
  url: string;
  snippet: string;
  journal?: string;
  year?: string;
  authors?: string;
  source_type?: string; // "PubMed", "Google Scholar", "Web"
}

interface DeepResearchProps {
  isLoading: boolean;
  progressStep: string; // e.g., "Analyzing Source 3/10..."
  progressPercent?: number; // 0-100
  reportContent: string; // The raw Markdown string
  sources: Source[];
  error?: string;
}

// --- Helper: Custom Citation Component ---
const CitationRenderer = ({
  children,
  onCitationClick
}: {
  children: string,
  onCitationClick: (id: number) => void
}) => {
  const parts = children.split(/(\[\d+\])/g);

  return (
    <span>
      {parts.map((part, index) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const id = parseInt(match[1]);
          return (
            <button
              key={index}
              onClick={() => onCitationClick(id)}
              className="inline-flex items-center justify-center mx-0.5 px-1.5 py-0.5 text-xs font-bold text-emerald-600 bg-emerald-50 rounded cursor-pointer hover:bg-emerald-100 hover:text-emerald-800 transition-colors border border-emerald-200 align-baseline dark:bg-emerald-900/40 dark:text-emerald-400 dark:border-emerald-700 dark:hover:bg-emerald-800/60"
              title={`Jump to Source ${id}`}
            >
              {id}
            </button>
          );
        }
        return part;
      })}
    </span>
  );
};

// --- Main Component ---

export default function DeepResearchUI({
  isLoading,
  progressStep,
  progressPercent = 0,
  reportContent,
  sources,
  error
}: DeepResearchProps) {
  const [activeSourceId, setActiveSourceId] = useState<number | null>(null);
  // Detect mobile for sidebar default state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(typeof window !== "undefined" ? window.innerWidth < 768 : false);
  const sidebarRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});
  const { t } = useTranslation();

  const handleCitationClick = (id: number) => {
    setActiveSourceId(id);
    // On mobile, keep sidebar collapsed but show the specific source somehow? 
    // Actually, on mobile we WANT to see the source, so we should expand and scroll.
    setSidebarCollapsed(false);
    const element = sidebarRefs.current[id];
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  // Handle window resize
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setSidebarCollapsed(false);
      } else {
        setSidebarCollapsed(true);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px] bg-red-50 dark:bg-red-950/20 rounded-xl border border-red-200 dark:border-red-900/50">
        <div className="text-center p-8">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-red-700 dark:text-red-400 mb-2">Research Error</h3>
          <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full bg-surface rounded-xl overflow-hidden border border-border shadow-sm transition-all duration-300">

      {/* 1. Header (Always show toggle on mobile) */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-30">
        <div className="flex items-center gap-2">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-500" />
              <h3 className="font-medium text-slate-800 dark:text-slate-200 text-sm">
                {t('researching')}
              </h3>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div className="p-1 bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 rounded-md">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
              <h3 className="font-medium text-slate-800 dark:text-slate-200 text-sm">
                {t('research_complete')}
              </h3>
            </div>
          )}
        </div>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 text-xs font-semibold shadow-sm transition-all active:scale-95"
          title={sidebarCollapsed ? t('sources') : t('close')}
        >
          <BookOpen className="w-3.5 h-3.5" />
          {sidebarCollapsed ? t('sources') : t('close')}
        </button>
      </div>

      {/* 2. Main Content Area */}
      <div className="flex flex-1 overflow-hidden relative min-h-[500px]">

        {/* Mobile Backdrop */}
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarCollapsed(true)}
              className="md:hidden absolute inset-0 bg-black/40 backdrop-blur-[2px] z-10"
            />
          )}
        </AnimatePresence>

        {/* LEFT PANEL: The Report */}
        <div className={`flex-1 overflow-y-auto p-6 md:p-10 scroll-smooth bg-surface ${sidebarCollapsed ? 'w-full' : ''}`}>
          <article className="prose prose-slate dark:prose-invert max-w-3xl mx-auto prose-sm md:prose-base prose-headings:scroll-mt-20 prose-headings:font-semibold prose-a:text-emerald-600 dark:prose-a:text-emerald-400 prose-img:rounded-xl">
            {isLoading && !reportContent ? (
              <LoadingState progress={progressStep} progressPercent={progressPercent} />
            ) : (
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="leading-relaxed text-foreground-muted mb-4 font-normal">
                      {React.Children.map(children, (child) => {
                        if (typeof child === "string") {
                          return <CitationRenderer onCitationClick={handleCitationClick}>{child}</CitationRenderer>;
                        }
                        return child;
                      })}
                    </p>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold text-foreground mb-6 pb-2 border-b border-border/50">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold text-foreground/90 mt-8 mb-3 flex items-center gap-2">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-medium text-foreground/90 mt-6 mb-2">
                      {children}
                    </h3>
                  ),
                  ul: ({ children }) => <ul className="list-disc pl-5 space-y-1.5 my-3 marker:text-emerald-500/50 text-slate-600 dark:text-slate-300">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1.5 my-3 marker:text-emerald-500/50 text-slate-600 dark:text-slate-300">{children}</ol>,
                  li: ({ children }) => (
                    <li className="pl-1">
                      {React.Children.map(children, (child) => {
                        if (typeof child === "string") {
                          return <CitationRenderer onCitationClick={handleCitationClick}>{child}</CitationRenderer>;
                        }
                        return child;
                      })}
                    </li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-emerald-500 pl-4 py-1 my-4 bg-surface-highlight text-foreground-muted italic rounded-r text-sm">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className;
                    if (isInline) {
                      return <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-[11px] font-mono text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700/50">{children}</code>;
                    }
                    return <code className={className}>{children}</code>;
                  },
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 no-underline hover:underline inline-flex items-center gap-0.5 transition-colors"
                    >
                      {children}
                      <ExternalLink className="w-2.5 h-2.5 opacity-70" />
                    </a>
                  ),
                  hr: () => <hr className="my-8 border-slate-100 dark:border-slate-800" />,
                }}
              >
                {reportContent}
              </ReactMarkdown>
            )}
          </article>
        </div>

        {/* RIGHT PANEL: The Source Map Sidebar */}
        <motion.div
          initial={false}
          animate={{
            x: sidebarCollapsed ? "100%" : 0,
            opacity: sidebarCollapsed ? 0 : 1
          }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className={`
            fixed md:relative inset-y-0 right-0 md:inset-auto
            ${sidebarCollapsed ? 'pointer-events-none' : 'pointer-events-auto'} 
            md:pointer-events-auto
            flex
            w-[85%] sm:w-80 md:w-72 lg:w-80
            z-20 md:z-auto
            border-l border-slate-100 dark:border-slate-800 
            bg-surface 
            flex-col shadow-2xl md:shadow-none
          `}
        >
          {/* Sidebar Header */}
          <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-surface/50 backdrop-blur-sm">
            <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              {t('sources')}
              <span className="bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded text-[10px] min-w-[20px] text-center">
                {sources.length}
              </span>
            </h4>
            <button
              onClick={() => setSidebarCollapsed(true)}
              className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Source Cards */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {sources.length === 0 && (
              <div className="flex flex-col items-center justify-center h-48 text-center opacity-40">
                {isLoading ? (
                  <div className="animate-pulse flex flex-col items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800"></div>
                    <div className="w-20 h-1.5 bg-slate-200 dark:bg-slate-800 rounded"></div>
                  </div>
                ) : (
                  <>
                    <BookOpen className="w-5 h-5 mb-2 text-slate-400" />
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide">{t('no_sources')}</p>
                  </>
                )}
              </div>
            )}

            {sources.map((source) => (
              <motion.div
                key={source.id}
                ref={(el) => { sidebarRefs.current[source.id] = el; }}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className={`
                  p-2.5 rounded-lg border text-sm transition-all duration-200 cursor-pointer group
                  ${activeSourceId === source.id
                    ? 'bg-white dark:bg-surface border-emerald-500/50 ring-1 ring-emerald-500/20 shadow-md transform scale-[1.02]'
                    : 'bg-surface/40 border-border hover:border-emerald-500/30'
                  }
                `}
                onClick={() => setActiveSourceId(activeSourceId === source.id ? null : source.id)}
              >
                <div className="flex items-start gap-2.5">
                  <div className={`
                      flex-shrink-0 w-4 h-4 flex items-center justify-center rounded text-[9px] font-bold mt-0.5 transition-colors
                      ${activeSourceId === source.id ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-400' : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 group-hover:text-emerald-500'}
                   `}>
                    {source.id}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h5 className={`text-xs font-medium leading-snug line-clamp-2 mb-0.5 ${activeSourceId === source.id ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-700 dark:text-slate-300'}`}>
                      {source.title}
                    </h5>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 dark:text-slate-500">
                      <span className="truncate max-w-[80px]">{source.source_type || "Web"}</span>
                      {source.year && <span> {source.year}</span>}
                    </div>
                  </div>
                </div>

                <AnimatePresence>
                  {activeSourceId === source.id && source.snippet && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/50">
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed italic opacity-90">
                          "{source.snippet}"
                        </p>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600 hover:underline mt-2 opacity-80 hover:opacity-100"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-2.5 h-2.5" /> {t('open_source')}
                        </a>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

// --- Minimal Loading State ---
function LoadingState({ progress, progressPercent }: { progress: string; progressPercent: number }) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] w-full max-w-md mx-auto px-4 animate-in fade-in duration-700">

      {/* Search Icon with Pulse Ring */}
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full animate-pulse"></div>
        <div className="relative w-16 h-16 bg-white dark:bg-surface rounded-2xl shadow-lg border border-slate-100 dark:border-border flex items-center justify-center group">
          <Search className="w-6 h-6 text-emerald-500 group-hover:scale-110 transition-transform duration-500" />

          {/* Spinner Ring */}
          <div className="absolute inset-0 -m-1 rounded-[1.2rem] border-2 border-emerald-500/20 border-t-emerald-500 animate-spin"></div>
        </div>
      </div>

      {/* Primary Status */}
      <h3 className="text-xl font-medium text-foreground mb-2 text-center tracking-tight">
        {progress || t('initializing_research')}
      </h3>

      {/* Secondary Progress Detail */}
      <p className="text-sm text-foreground-muted mb-8 text-center font-light">
        {t('processing_sources')} <span className="font-mono text-emerald-600 dark:text-emerald-400 ml-1">{progressPercent}%</span>
      </p>

      {/* Sleek Progress Bar */}
      <div className="w-full h-1 bg-slate-100 dark:bg-slate-800/50 rounded-full overflow-hidden mb-8">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-500 to-teal-400"
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(progressPercent, 5)}%` }} // Always show a little
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Context Tags (Visual Flavor) */}
      {/* Context Tags (Visual Flavor) - REMOVED per user request to avoid hardcoded values */}

    </div>
  );
}
