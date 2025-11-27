'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ChevronDown, ChevronUp, Globe, FileText, ExternalLink, BookOpen, Loader2 } from 'lucide-react';
import StreamdownWrapper from './StreamdownWrapper';

// ============================================================================
// TYPES
// ============================================================================

interface Source {
  title: string;
  url: string;
  favicon?: string;
  source?: string;
  authors?: string;
  year?: string;
  journal?: string;
  doi?: string;
}

interface DeepResearchState {
  status: string;
  progress: number;
  logs: string[];
  sources: Source[];
  isComplete: boolean;
  planOverview?: string;
  steps?: Array<{ id: number; topic: string; source: string }>;
  report?: string;
}

interface DeepResearchUIProps {
  state: DeepResearchState;
}

// ============================================================================
// ANIMATED COUNTER COMPONENT
// ============================================================================

function AnimatedCounter({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    const duration = 500;
    const startValue = displayValue;
    const diff = value - startValue;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(startValue + diff * eased));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value]);

  return <span>{displayValue}</span>;
}

// ============================================================================
// GRADIENT SPINNER COMPONENT
// ============================================================================

function GradientSpinner({ progress, isComplete }: { progress: number; isComplete: boolean }) {
  return (
    <div className="relative flex items-center justify-center">
      <div
        className={`h-16 w-16 sm:h-20 sm:w-20 rounded-full p-[3px] ${isComplete ? '' : 'animate-spin-slow'}`}
        style={{
          background: isComplete
            ? 'conic-gradient(from 0deg, #22c55e, #10b981, #22c55e)'
            : 'conic-gradient(from 0deg, #6366f1, #8b5cf6, #a855f7, #6366f1)'
        }}
      >
        <div className="h-full w-full rounded-full bg-[var(--surface)] flex items-center justify-center">
          <span className="text-base sm:text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-500">
            <AnimatedCounter value={progress} />%
          </span>
        </div>
      </div>

      <div
        className="absolute inset-0 rounded-full blur-xl opacity-20 dark:opacity-30"
        style={{
          background: isComplete
            ? 'radial-gradient(circle, #22c55e 0%, transparent 70%)'
            : 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)'
        }}
      />
    </div>
  );
}

// ============================================================================
// SHIMMER LOADING COMPONENT
// ============================================================================

function ShimmerText({ text }: { text: string }) {
  return (
    <span className="relative inline-block">
      <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%] animate-shimmer">
        {text}
      </span>
    </span>
  );
}

// ============================================================================
// APA CITATION FORMATTER
// ============================================================================

function formatAPACitation(source: Source, index: number): string {
  // APA 7th Edition format:
  // Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. Journal Name, Volume(Issue), Pages. DOI

  const authors = source.authors || 'Unknown Author';
  const year = source.year || 'n.d.';
  const title = source.title || 'Untitled';
  const journal = source.journal || source.source || '';
  const doi = source.doi ? `https://doi.org/${source.doi}` : source.url;

  return `[${index + 1}] ${authors} (${year}). ${title}. ${journal ? `*${journal}*. ` : ''}${doi}`;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DeepResearchUI({ state }: DeepResearchUIProps) {
  const [logsExpanded, setLogsExpanded] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsEndRef.current && logsExpanded) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [state.logs, logsExpanded]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="w-full max-w-2xl mx-auto rounded-2xl bg-[var(--surface)] border border-[var(--border)] overflow-hidden shadow-lg"
    >
      {/* ================================================================== */}
      {/* HEADER - Spinner + Status */}
      {/* ================================================================== */}
      {/* ================================================================== */}
      {/* HEADER - Collapsible Accordion Status */}
      {/* ================================================================== */}
      <div className="border-b border-[var(--border)]">
        <button
          onClick={() => setLogsExpanded(!logsExpanded)}
          className={`w-full text-left transition-all duration-300 ${state.isComplete ? 'bg-[var(--surface)]' : 'bg-secondary/30'
            }`}
        >
          <div className={`flex items-center gap-4 p-4 ${state.isComplete ? '' : 'border-l-2 border-primary pl-4 py-2'}`}>
            {/* Icon / Status Indicator */}
            <div className="flex-shrink-0">
              {state.isComplete ? (
                <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <Sparkles size={14} className="text-emerald-500" />
                </div>
              ) : (
                <div className="w-6 h-6 flex items-center justify-center">
                  <Loader2 className="animate-spin text-primary" size={18} />
                </div>
              )}
            </div>

            {/* Text Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className={`text-sm font-medium ${state.isComplete ? 'text-[var(--text-secondary)] opacity-70' : 'text-[var(--text-primary)] font-bold'}`}>
                  {state.isComplete ? 'Research Complete' : state.status || 'Initializing Research Agent...'}
                </h3>
                {state.isComplete ? (
                  <ChevronDown size={16} className="text-[var(--text-secondary)]" />
                ) : (
                  <span className="text-xs text-primary animate-pulse">Processing...</span>
                )}
              </div>

              {/* Progress Bar (Only when active) */}
              {!state.isComplete && (
                <div className="mt-2 h-1 w-full bg-[var(--surface-highlight)] rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-primary rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${state.progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
            </div>
          </div>
        </button>
      </div>

      {/* ================================================================== */}
      {/* RESEARCH STEPS */}
      {/* ================================================================== */}
      {state.steps && state.steps.length > 0 && (
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-[var(--border)]">
          <p className="text-[10px] sm:text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2 sm:mb-3">
            Research Topics
          </p>
          <div className="flex flex-wrap gap-1.5 sm:gap-2">
            <AnimatePresence>
              {state.steps.map((step, i) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full bg-[var(--surface-highlight)] border border-[var(--border)]"
                >
                  <span className="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-[8px] sm:text-[10px] font-bold flex items-center justify-center text-white">
                    {step.id}
                  </span>
                  <span className="text-[10px] sm:text-xs text-[var(--text-primary)] max-w-[120px] sm:max-w-none truncate">{step.topic}</span>
                  <span className="hidden sm:inline text-[10px] text-[var(--text-secondary)] px-1.5 py-0.5 rounded bg-[var(--border)]">
                    {step.source}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* ================================================================== */}
      {/* ACTIVITY LOG (Collapsible) */}
      {/* ================================================================== */}
      <div className="border-b border-[var(--border)]">
        <button
          onClick={() => setLogsExpanded(!logsExpanded)}
          className="w-full px-4 sm:px-6 py-2 sm:py-3 flex items-center justify-between hover:bg-[var(--surface-highlight)] transition-colors"
        >
          <span className="text-[10px] sm:text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-2">
            <FileText size={12} className="sm:w-[14px] sm:h-[14px]" />
            Activity Log
            {state.logs.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-[var(--surface-highlight)] text-[var(--text-secondary)] text-[10px]">
                {state.logs.length}
              </span>
            )}
          </span>
          {logsExpanded ? (
            <ChevronUp size={14} className="sm:w-4 sm:h-4 text-[var(--text-secondary)]" />
          ) : (
            <ChevronDown size={14} className="sm:w-4 sm:h-4 text-[var(--text-secondary)]" />
          )}
        </button>

        <AnimatePresence>
          {logsExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-4 sm:px-6 pb-3 sm:pb-4 max-h-32 overflow-y-auto scrollbar-hide">
                <div className="space-y-1">
                  <AnimatePresence>
                    {state.logs.map((log, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2 }}
                        className="flex items-start gap-2"
                      >
                        <span className="text-[var(--text-secondary)] text-xs mt-0.5">›</span>
                        <span className="font-mono text-[10px] sm:text-xs text-[var(--text-secondary)] leading-relaxed">
                          {log}
                        </span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={logsEndRef} />
                </div>

                {state.logs.length === 0 && (
                  <p className="font-mono text-[10px] sm:text-xs text-[var(--text-secondary)] italic opacity-60">
                    Waiting for activity...
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ================================================================== */}
      {/* SOURCES / REFERENCES (APA Style) */}
      {/* ================================================================== */}
      {state.sources.length > 0 && (
        <div className="border-b border-[var(--border)]">
          <button
            onClick={() => setSourcesExpanded(!sourcesExpanded)}
            className="w-full px-4 sm:px-6 py-2 sm:py-3 flex items-center justify-between hover:bg-[var(--surface-highlight)] transition-colors"
          >
            <span className="text-[10px] sm:text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-2">
              <BookOpen size={12} className="sm:w-[14px] sm:h-[14px]" />
              References
              <span className="px-1.5 py-0.5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)] text-[10px]">
                {state.sources.length}
              </span>
            </span>
            {sourcesExpanded ? (
              <ChevronUp size={14} className="sm:w-4 sm:h-4 text-[var(--text-secondary)]" />
            ) : (
              <ChevronDown size={14} className="sm:w-4 sm:h-4 text-[var(--text-secondary)]" />
            )}
          </button>

          <AnimatePresence>
            {sourcesExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="px-4 sm:px-6 pb-3 sm:pb-4 max-h-48 overflow-y-auto scrollbar-hide">
                  <div className="space-y-2">
                    {state.sources.map((source, i) => (
                      <motion.a
                        key={source.url || i}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="block p-2 sm:p-3 rounded-lg bg-[var(--surface-highlight)] hover:bg-[var(--border)] transition-colors group"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-[10px] sm:text-xs font-medium text-[var(--accent)] flex-shrink-0">
                            [{i + 1}]
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-[10px] sm:text-xs text-[var(--text-primary)] leading-relaxed">
                              {source.authors && <span>{source.authors} </span>}
                              {source.year && <span>({source.year}). </span>}
                              <span className="font-medium">{source.title}</span>
                              {source.journal && <span className="italic">. {source.journal}</span>}
                            </p>
                            <p className="text-[10px] text-[var(--accent)] mt-1 truncate group-hover:underline flex items-center gap-1">
                              {source.doi ? `doi:${source.doi}` : source.url}
                              <ExternalLink size={10} className="flex-shrink-0" />
                            </p>
                          </div>
                        </div>
                      </motion.a>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* ================================================================== */}
      {/* REPORT OUTPUT (Using Streamdown) */}
      {/* ================================================================== */}
      {state.report && (
        <div className="p-4 sm:p-6">
          <p className="text-[10px] sm:text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 flex items-center gap-2">
            <Sparkles size={12} className="sm:w-[14px] sm:h-[14px]" />
            Research Report
          </p>
          <div className="text-sm text-[var(--text-primary)]">
            <StreamdownWrapper
              isAnimating={!state.isComplete}
              className="streamdown-content"
            >
              {state.report}
            </StreamdownWrapper>
          </div>
        </div>
      )}

      {/* ================================================================== */}
      {/* COMPLETION MESSAGE */}
      {/* ================================================================== */}
      {state.isComplete && !state.report && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-4 sm:px-6 py-3 sm:py-4 bg-gradient-to-r from-emerald-500/10 to-indigo-500/10 border-t border-emerald-500/20"
        >
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Sparkles size={14} className="sm:w-4 sm:h-4 text-emerald-500" />
            </div>
            <div>
              <p className="text-xs sm:text-sm font-medium text-emerald-500">
                Research synthesis complete
              </p>
              <p className="text-[10px] sm:text-xs text-[var(--text-secondary)]">
                {state.sources.length} sources analyzed • Report ready
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
