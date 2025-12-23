"use client";

import React, { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  ExternalLink,
  CheckCircle2,
  Loader2,
  Search,
  ChevronRight,
  FileText,
  AlertCircle
} from "lucide-react";

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
              className="inline-flex items-center justify-center mx-0.5 px-1.5 py-0.5 text-xs font-bold text-emerald-600 bg-emerald-50 rounded cursor-pointer hover:bg-emerald-100 hover:text-emerald-800 transition-colors border border-emerald-200 align-super dark:bg-emerald-900/40 dark:text-emerald-400 dark:border-emerald-700 dark:hover:bg-emerald-800/60"
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const sidebarRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});

  const handleCitationClick = (id: number) => {
    setActiveSourceId(id);
    setSidebarCollapsed(false);
    const element = sidebarRefs.current[id];
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px] bg-red-50 dark:bg-red-950/50 rounded-xl border border-red-200 dark:border-red-900">
        <div className="text-center p-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 mb-2">Research Error</h3>
          <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full bg-white dark:bg-black rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-lg">

      {/* 1. Header / Status Bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-gradient-to-r from-slate-50 to-white dark:from-black dark:to-slate-950">
        <div className="flex items-center gap-3 flex-1">
          <div className={`p-2.5 rounded-xl ${isLoading ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400'}`}>
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                {isLoading ? "Deep Research Agent" : "Research Complete"}
              </h3>
              {isLoading && progressPercent > 0 && (
                <span className="px-2 py-0.5 text-xs font-bold bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 rounded-full">
                  {progressPercent}%
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              {isLoading ? progressStep : `${sources.length} sources analyzed`}
            </p>
            {/* Progress Bar */}
            {isLoading && (
              <div className="mt-2 w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPercent}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Toggle Sidebar Button (Mobile) */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="md:hidden p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
        >
          <BookOpen className="w-5 h-5" />
        </button>
      </div>

      {/* 2. Main Content Area (Split View) */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* LEFT PANEL: The Report */}
        <div className={`flex-1 overflow-y-auto p-6 md:p-8 scroll-smooth bg-white dark:bg-black ${sidebarCollapsed ? 'w-full' : ''}`}>
          <article className="prose prose-slate dark:prose-invert max-w-none prose-headings:scroll-mt-20">
            {isLoading && !reportContent ? (
              <LoadingState progress={progressStep} progressPercent={progressPercent} />
            ) : (
              <ReactMarkdown
                components={{
                  p: ({ children }) => {
                    return (
                      <p className="leading-relaxed text-slate-700 dark:text-slate-300 mb-4">
                        {React.Children.map(children, (child) => {
                          if (typeof child === "string") {
                            return <CitationRenderer onCitationClick={handleCitationClick}>{child}</CitationRenderer>;
                          }
                          return child;
                        })}
                      </p>
                    );
                  },
                  h1: ({ children }) => (
                    <h1 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-white mb-6 pb-3 border-b-2 border-emerald-500">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl md:text-2xl font-semibold text-slate-800 dark:text-slate-100 mt-10 mb-4 flex items-center gap-2">
                      <span className="w-1 h-6 bg-emerald-500 rounded-full"></span>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 mt-6 mb-3">
                      {children}
                    </h3>
                  ),
                  ul: ({ children }) => <ul className="list-disc pl-6 space-y-2 my-4 marker:text-emerald-500">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-6 space-y-2 my-4 marker:text-emerald-500">{children}</ol>,
                  li: ({ children }) => (
                    <li className="text-slate-700 dark:text-slate-300 pl-1">
                      {React.Children.map(children, (child) => {
                        if (typeof child === "string") {
                          return <CitationRenderer onCitationClick={handleCitationClick}>{child}</CitationRenderer>;
                        }
                        return child;
                      })}
                    </li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-emerald-500 pl-4 py-2 my-6 bg-emerald-50 dark:bg-emerald-950/30 rounded-r-lg italic text-slate-600 dark:text-slate-300">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className;
                    if (isInline) {
                      return <code className="bg-slate-100 dark:bg-slate-900 px-1.5 py-0.5 rounded text-sm font-mono text-emerald-600 dark:text-emerald-400">{children}</code>;
                    }
                    return <code className={className}>{children}</code>;
                  },
                  strong: ({ children }) => <strong className="font-semibold text-slate-900 dark:text-white">{children}</strong>,
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-emerald-600 dark:text-emerald-400 hover:underline inline-flex items-center gap-1"
                    >
                      {children}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ),
                  hr: () => <hr className="my-8 border-slate-200 dark:border-slate-800" />,
                }}
              >
                {reportContent}
              </ReactMarkdown>
            )}
          </article>
        </div>

        {/* RIGHT PANEL: The Source Map Sidebar */}
        <div className={`
          ${sidebarCollapsed ? 'hidden' : 'flex'} 
          md:flex
          w-full md:w-80 lg:w-96
          absolute md:relative inset-0 md:inset-auto
          z-20 md:z-auto
          border-l border-slate-200 dark:border-slate-800 
          bg-slate-50 dark:bg-slate-950 
          flex-col shadow-inner
        `}>
          {/* Sidebar Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-black z-10 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-500" /> Source Map
              <span className="ml-1 px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 text-xs rounded-full">
                {sources.length}
              </span>
            </h4>
            <button
              onClick={() => setSidebarCollapsed(true)}
              className="md:hidden p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Source Cards */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50 dark:bg-slate-950">
            {sources.length === 0 && isLoading && (
              <div className="text-center py-10 opacity-50">
                <Search className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                <p className="text-xs text-slate-500">Gathering sources...</p>
              </div>
            )}

            {sources.length === 0 && !isLoading && (
              <div className="text-center py-10 opacity-50">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                <p className="text-xs text-slate-500">No sources found</p>
              </div>
            )}

            {sources.map((source) => (
              <motion.div
                key={source.id}
                ref={(el) => { sidebarRefs.current[source.id] = el; }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: source.id * 0.03 }}
                className={`
                  relative p-3 rounded-xl border text-sm transition-all duration-300 cursor-pointer group
                  ${activeSourceId === source.id
                    ? 'bg-emerald-50 border-emerald-500 shadow-lg ring-2 ring-emerald-500/20 dark:bg-emerald-950/50 dark:border-emerald-500'
                    : 'bg-white border-slate-200 hover:border-emerald-300 hover:shadow-md dark:bg-black dark:border-slate-800 dark:hover:border-emerald-700'
                  }
                `}
                onClick={() => setActiveSourceId(activeSourceId === source.id ? null : source.id)}
              >
                {/* ID Badge */}
                <div className={`
                  absolute -top-2 -right-2 w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold border shadow-sm
                  ${activeSourceId === source.id
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-slate-100 text-slate-600 border-slate-200 group-hover:bg-emerald-100 group-hover:text-emerald-600 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700 dark:group-hover:bg-emerald-900 dark:group-hover:text-emerald-400'
                  }
                `}>
                  {source.id}
                </div>

                {/* Source Type Badge */}
                <div className="flex items-center gap-2 mb-2">
                  <span className={`
                    px-2 py-0.5 text-xs font-medium rounded-full
                    ${source.source_type === 'PubMed'
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
                      : source.source_type === 'Google Scholar'
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-950/50 dark:text-purple-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                    }
                  `}>
                    {source.source_type || "Web"}
                  </span>
                  {source.year && (
                    <span className="text-xs text-slate-500 dark:text-slate-500">{source.year}</span>
                  )}
                </div>

                {/* Title */}
                <h5 className="font-semibold text-slate-800 dark:text-slate-200 line-clamp-2 leading-tight mb-1 pr-4">
                  {source.title}
                </h5>

                {/* Authors */}
                {source.authors && (
                  <p className="text-xs text-slate-500 dark:text-slate-500 mb-2 line-clamp-1">
                    {source.authors}
                  </p>
                )}

                {/* Snippet (Only show if active) */}
                <AnimatePresence>
                  {activeSourceId === source.id && source.snippet && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <p className="text-xs text-slate-600 dark:text-slate-400 my-2 leading-relaxed bg-slate-50 dark:bg-slate-900 p-2 rounded-lg border border-slate-100 dark:border-slate-800">
                        &ldquo;{source.snippet}&rdquo;
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Link */}
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 hover:underline dark:text-emerald-400 dark:hover:text-emerald-300 mt-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  View Source <ExternalLink className="w-3 h-3" />
                </a>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Sub-component: Loading State with Progress ---
function LoadingState({ progress, progressPercent }: { progress: string; progressPercent: number }) {
  const steps = [
    "Planning research strategy...",
    "Searching PubMed database...",
    "Querying Google Scholar...",
    "Analyzing web sources...",
    "Cross-referencing findings...",
    "Synthesizing report..."
  ];

  const currentStepIndex = steps.findIndex(s => progress.toLowerCase().includes(s.split(" ")[0].toLowerCase()));
  const activeIndex = currentStepIndex >= 0 ? currentStepIndex : 0;

  return (
    <div className="space-y-6">
      {/* Animated Header Skeleton */}
      <div className="space-y-2">
        <div className="h-8 bg-gradient-to-r from-slate-200 via-slate-100 to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 rounded-lg w-3/4 animate-pulse"></div>
        <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-1/2 animate-pulse"></div>
      </div>

      {/* Progress Card */}
      <div className="p-5 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-black border border-slate-200 dark:border-slate-800 rounded-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <Loader2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 animate-spin" />
            </div>
            <div>
              <h4 className="font-semibold text-slate-800 dark:text-slate-200">Deep Research in Progress</h4>
              <p className="text-xs text-slate-500 dark:text-slate-500">This may take 30-60 seconds</p>
            </div>
          </div>
          {progressPercent > 0 && (
            <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{progressPercent}%</span>
          )}
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden mb-4">
          <motion.div
            className="h-full bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        <div className="space-y-2">
          {steps.map((step, index) => (
            <div
              key={step}
              className={`
                flex items-center gap-2 text-sm transition-all duration-300
                ${index < activeIndex
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : index === activeIndex
                    ? 'text-blue-600 dark:text-blue-400 font-medium'
                    : 'text-slate-400 dark:text-slate-600'
                }
              `}
            >
              {index < activeIndex ? (
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              ) : index === activeIndex ? (
                <Loader2 className="w-4 h-4 flex-shrink-0 animate-spin" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-300 dark:border-slate-700 flex-shrink-0" />
              )}
              <span>{step}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="space-y-4 pt-4">
        <div className="h-6 bg-slate-200 dark:bg-slate-900 rounded w-1/3 animate-pulse"></div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-full animate-pulse"></div>
          <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-5/6 animate-pulse"></div>
          <div className="h-4 bg-slate-100 dark:bg-slate-900 rounded w-4/6 animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
