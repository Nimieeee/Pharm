'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ChevronDown, ChevronUp, Globe, FileText, ExternalLink } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface Source {
  title: string;
  url: string;
  favicon?: string;
  source?: string;
}

interface DeepResearchState {
  status: string;
  progress: number;
  logs: string[];
  sources: Source[];
  isComplete: boolean;
  planOverview?: string;
  steps?: Array<{ id: number; topic: string; source: string }>;
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
      {/* The Gradient Ring */}
      <div 
        className={`h-20 w-20 rounded-full p-[3px] ${isComplete ? '' : 'animate-spin-slow'}`}
        style={{ 
          background: isComplete 
            ? 'conic-gradient(from 0deg, #22c55e, #10b981, #22c55e)'
            : 'conic-gradient(from 0deg, #6366f1, #8b5cf6, #a855f7, #6366f1)' 
        }}
      >
        {/* The Inner Mask (creates the ring effect) */}
        <div className="h-full w-full rounded-full bg-[var(--surface)] flex items-center justify-center">
          {/* Progress percentage inside */}
          <span className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-500">
            <AnimatedCounter value={progress} />%
          </span>
        </div>
      </div>
      
      {/* Glow effect */}
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
// MAIN COMPONENT
// ============================================================================

export default function DeepResearchUI({ state }: DeepResearchUIProps) {
  const [logsExpanded, setLogsExpanded] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll logs
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
      <div className="p-6 border-b border-[var(--border)]">
        <div className="flex items-center gap-5">
          <GradientSpinner progress={state.progress} isComplete={state.isComplete} />
          
          <div className="flex-1 min-w-0">
            {/* Status Text with Shimmer */}
            <motion.h3 
              key={state.status}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`text-lg font-semibold ${
                state.isComplete 
                  ? 'text-emerald-500' 
                  : 'text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%] animate-shimmer'
              }`}
            >
              {state.isComplete ? '✓ Research Complete' : state.status}
            </motion.h3>
            
            {/* Plan Overview */}
            {state.planOverview && (
              <p className="text-sm text-[var(--text-secondary)] mt-1 line-clamp-2">
                {state.planOverview}
              </p>
            )}
            
            {/* Progress Bar */}
            <div className="mt-3 h-1.5 bg-[var(--surface-highlight)] rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background: state.isComplete 
                    ? 'linear-gradient(90deg, #22c55e, #10b981)'
                    : 'linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7)'
                }}
                initial={{ width: 0 }}
                animate={{ width: `${state.progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================== */}
      {/* RESEARCH STEPS */}
      {/* ================================================================== */}
      {state.steps && state.steps.length > 0 && (
        <div className="px-6 py-4 border-b border-[var(--border)]">
          <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">
            Research Topics
          </p>
          <div className="flex flex-wrap gap-2">
            <AnimatePresence>
              {state.steps.map((step, i) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--surface-highlight)] border border-[var(--border)]"
                >
                  <span className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-[10px] font-bold flex items-center justify-center text-white">
                    {step.id}
                  </span>
                  <span className="text-xs text-[var(--text-primary)]">{step.topic}</span>
                  <span className="text-[10px] text-[var(--text-secondary)] px-1.5 py-0.5 rounded bg-[var(--border)]">
                    {step.source}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* ================================================================== */}
      {/* ACTIVITY LOG (Thoughts Accordion) */}
      {/* ================================================================== */}
      <div className="border-b border-[var(--border)]">
        <button
          onClick={() => setLogsExpanded(!logsExpanded)}
          className="w-full px-6 py-3 flex items-center justify-between hover:bg-[var(--surface-highlight)] transition-colors"
        >
          <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-2">
            <FileText size={14} />
            Activity Log
            {state.logs.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-[var(--surface-highlight)] text-[var(--text-secondary)] text-[10px]">
                {state.logs.length}
              </span>
            )}
          </span>
          {logsExpanded ? (
            <ChevronUp size={16} className="text-[var(--text-secondary)]" />
          ) : (
            <ChevronDown size={16} className="text-[var(--text-secondary)]" />
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
              <div className="px-6 pb-4 max-h-32 overflow-y-auto scrollbar-hide">
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
                        <span className="font-mono text-xs text-[var(--text-secondary)] leading-relaxed">
                          {log}
                        </span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={logsEndRef} />
                </div>
                
                {state.logs.length === 0 && (
                  <p className="font-mono text-xs text-[var(--text-secondary)] italic opacity-60">
                    Waiting for activity...
                  </p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ================================================================== */}
      {/* SOURCES CAROUSEL */}
      {/* ================================================================== */}
      {state.sources.length > 0 && (
        <div className="p-4">
          <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 px-2 flex items-center gap-2">
            <Globe size={14} />
            Sources Found
            <span className="px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-500 text-[10px]">
              {state.sources.length}
            </span>
          </p>
          
          <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
            <AnimatePresence>
              {state.sources.map((source, i) => (
                <motion.a
                  key={source.url || i}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, scale: 0.8, x: 20 }}
                  animate={{ opacity: 1, scale: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="group min-w-[200px] max-w-[200px] p-3 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] hover:border-indigo-500/50 transition-all hover:scale-[1.02]"
                >
                  {/* Source Header */}
                  <div className="flex items-center gap-2 mb-2">
                    {source.favicon ? (
                      <img 
                        src={source.favicon} 
                        alt="" 
                        className="w-4 h-4 rounded-full"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-4 h-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                        <Globe size={10} className="text-white" />
                      </div>
                    )}
                    <span className="text-[10px] text-[var(--text-secondary)] truncate flex-1">
                      {source.source || (source.url ? new URL(source.url).hostname : 'Source')}
                    </span>
                    <ExternalLink size={10} className="text-[var(--text-secondary)] group-hover:text-indigo-500 transition-colors" />
                  </div>
                  
                  {/* Source Title */}
                  <p className="text-xs font-medium text-[var(--text-primary)] line-clamp-2 leading-tight group-hover:text-indigo-500 transition-colors">
                    {source.title}
                  </p>
                </motion.a>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* ================================================================== */}
      {/* COMPLETION MESSAGE */}
      {/* ================================================================== */}
      {state.isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-6 py-4 bg-gradient-to-r from-emerald-500/10 to-indigo-500/10 border-t border-emerald-500/20"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Sparkles size={16} className="text-emerald-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-500">
                Research synthesis complete
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                {state.sources.length} sources analyzed • Report ready
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
