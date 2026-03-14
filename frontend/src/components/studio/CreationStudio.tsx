'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Presentation, FileText, Sparkles, Loader2, CheckCircle, AlertCircle, ArrowRight, History, Download, Clock } from 'lucide-react';
import { toast } from 'sonner';

// Shared Components
import HubLayout from '../shared/HubLayout';
import SkeletonLoader from '../shared/SkeletonLoader';
import { LoadingAnimation } from '../shared/LoadingAnimation';

import SlideOutlineEditor, { SlideOutline } from '../slides/SlideOutlineEditor';
import SlideProgress from '../slides/SlideProgress';
import DocOutlineEditor, { DocOutline } from '../docs/DocOutlineEditor';
import ThemeSelector from '../slides/ThemeSelector';
import { API_BASE_URL } from '@/config/api';

type CreationType = 'slides' | 'document';
type GenerationStep = 'input' | 'generating_outline' | 'edit_outline' | 'generating_final' | 'complete';

const RECENT_TOPICS_KEY = 'benchside_recent_topics';

export default function CreationStudio() {
  const [creationType, setCreationType] = useState<CreationType>('slides');
  const [step, setStep] = useState<GenerationStep>('input');
  const [topic, setTopic] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('ocean_gradient');
  const [numSlides, setNumSlides] = useState(12);
  const [recentTopics, setRecentTopics] = useState<string[]>([]);
  
  const [slideOutline, setSlideOutline] = useState<SlideOutline | null>(null);
  const [docOutline, setDocOutline] = useState<DocOutline | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });
  const [jobId, setJobId] = useState('');
  const [error, setError] = useState('');

  // Load recent topics
  useEffect(() => {
    const saved = localStorage.getItem(RECENT_TOPICS_KEY);
    if (saved) setRecentTopics(JSON.parse(saved));
  }, []);

  const saveRecentTopic = (newTopic: string) => {
    const updated = [newTopic, ...recentTopics.filter(t => t !== newTopic)].slice(0, 5);
    setRecentTopics(updated);
    localStorage.setItem(RECENT_TOPICS_KEY, JSON.stringify(updated));
  };

  const handleGenerateOutline = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic');
      return;
    }

    setStep('generating_outline');
    setError('');
    saveRecentTopic(topic.trim());

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const endpoint = creationType === 'slides' ? `${API_BASE_URL}/api/v1/slides/outline` : `${API_BASE_URL}/api/v1/docs/outline`;
      const body = creationType === 'slides' 
        ? { topic: topic.trim(), num_slides: numSlides, theme: selectedTheme } 
        : { topic: topic.trim(), doc_type: 'report' };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate outline');
      }

      const data = await response.json();
      if (creationType === 'slides') setSlideOutline(data); else setDocOutline(data);
      setStep('edit_outline');
      toast.success('Outline generated successfully');
    } catch (err: any) {
      setError(err.message);
      setStep('input');
      toast.error(err.message);
    }
  };

  const handleGenerateFinal = async () => {
    setStep('generating_final');
    setError('');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const endpoint = creationType === 'slides' ? `${API_BASE_URL}/api/v1/slides/generate` : `${API_BASE_URL}/api/v1/docs/generate`;
      const body = creationType === 'slides' 
        ? { outline: slideOutline, generate_images: true } 
        : { outline: docOutline, doc_type: docOutline?.doc_type || 'report' };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) throw new Error('Generation failed');

      const data = await response.json();
      setJobId(data.job_id);
      
      // Start polling/SSE - dynamic endpoint based on creationType
      const statusPath = creationType === 'slides' ? 'slides' : 'docs';
      const eventSource = new EventSource(`${API_BASE_URL}/api/v1/${statusPath}/status/${data.job_id}`);
      
      eventSource.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          
          // Handle standard progress updates
          setProgress({
            current: update.current || update.current_slide || 0,
            total: update.total || update.total_slides || 0,
            message: update.message || ''
          });

          if (update.status === 'complete') {
            setStep('complete');
            eventSource.close();
            toast.success('Generation complete!');
          } else if (update.status === 'error') {
            setError(update.error || 'Generation failed');
            setStep('edit_outline');
            eventSource.close();
            toast.error(update.error || 'Generation failed');
          }
        } catch (e) {
          console.error('Failed to parse SSE message:', e, event.data);
          // Don't crash the UI, just wait for next message
        }
      };

      eventSource.onerror = (e) => {
        console.error('SSE Error:', e);
        // Don't close immediately as browser might retry, 
        // but if we are in started state for too long without message, it might be dead.
      };
    } catch (err: any) {
      setError(err.message);
      setStep('edit_outline');
      toast.error('Generation failed');
    }
  };

  const handleDownload = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const endpoint = creationType === 'slides' 
        ? `${API_BASE_URL}/api/v1/slides/download/${jobId}`
        : `${API_BASE_URL}/api/v1/docs/download/${jobId}`;

      const response = await fetch(endpoint, {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
      });

      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = creationType === 'slides' ? 'presentation.pptx' : 'report.docx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      toast.error('Failed to download file');
    }
  };

  return (
    <HubLayout 
      title="Creation Studio" 
      subtitle="Generate visually stunning scientific presentations and documents"
      icon={Sparkles}
      accentColor="teal"
    >
      <div className="max-w-5xl mx-auto">
        <AnimatePresence mode="wait">
          {step === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-12"
            >
              {/* Type Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <button
                  onClick={() => setCreationType('slides')}
                  className={`
                    relative p-8 rounded-3xl border transition-all text-left group
                    ${creationType === 'slides' 
                      ? 'bg-teal-500/10 border-teal-500/50 shadow-2xl shadow-teal-500/10 scale-[1.02]' 
                      : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--border-hover)] hover:bg-[var(--surface-hover)]'}
                  `}
                >
                  <div className={`
                    w-12 h-12 rounded-2xl flex items-center justify-center mb-6 border transition-all
                    ${creationType === 'slides' ? 'bg-teal-500 text-black border-teal-400' : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] border-[var(--border)]'}
                  `}>
                    <Presentation className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">Scientific Presentation</h3>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                    Create multi-slide PowerPoint decks with AI-generated imagery and speaker notes.
                  </p>
                  {creationType === 'slides' && (
                    <motion.div layoutId="active-indicator" className="absolute top-4 right-4">
                      <div className="w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_10px_rgba(20,184,166,0.8)]" />
                    </motion.div>
                  )}
                </button>

                <button
                  onClick={() => setCreationType('document')}
                  className={`
                    relative p-8 rounded-3xl border transition-all text-left group
                    ${creationType === 'document' 
                      ? 'bg-teal-500/10 border-teal-500/50 shadow-2xl shadow-teal-500/10 scale-[1.02]' 
                      : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--border-hover)] hover:bg-[var(--surface-hover)]'}
                  `}
                >
                  <div className={`
                    w-12 h-12 rounded-2xl flex items-center justify-center mb-6 border transition-all
                    ${creationType === 'document' ? 'bg-teal-500 text-black border-teal-400' : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] border-[var(--border)]'}
                  `}>
                    <FileText className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">Technical Document</h3>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                    Generate structured reports, manuscripts, and whitepapers in Word format.
                  </p>
                  {creationType === 'document' && (
                    <motion.div layoutId="active-indicator" className="absolute top-4 right-4">
                      <div className="w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_10px_rgba(20,184,166,0.8)]" />
                    </motion.div>
                  )}
                </button>
              </div>

              {/* Theme Selection - Only show for slides */}
              {creationType === 'slides' && (
                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 space-y-6">
                  <div>
                    <label className="text-sm font-medium text-[var(--text-secondary)] mb-3 block">
                      Select Visual Theme
                    </label>
                    <ThemeSelector 
                      selectedTheme={selectedTheme}
                      onThemeChange={setSelectedTheme}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-[var(--text-secondary)] mb-3 block flex items-center justify-between">
                      <span>Number of Slides</span>
                      <span className="text-teal-500 font-bold">{numSlides}</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      step="1"
                      value={numSlides}
                      onChange={(e) => setNumSlides(parseInt(e.target.value))}
                      className="w-full h-2 bg-[var(--surface-highlight)] rounded-lg appearance-none cursor-pointer accent-teal-500"
                    />
                    <div className="flex justify-between text-xs text-[var(--text-muted)] mt-2">
                      <span>5</span>
                      <span>30</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Topic Input */}
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row gap-3">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Describe your topic (e.g., The role of CRISPR in immunotherapy)..."
                    className="flex-1 px-8 py-6 rounded-3xl bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-4 focus:ring-teal-500/20 focus:border-teal-500/50 outline-none transition-all shadow-xl"
                  />
                  <button
                    onClick={handleGenerateOutline}
                    disabled={!topic.trim()}
                    className="px-6 py-4 md:py-0 rounded-2xl bg-teal-500 text-black hover:bg-teal-400 disabled:opacity-30 transition-all flex items-center justify-center gap-2 group"
                  >
                    <span className="font-bold">Draft Outline</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>

                {/* Recent Topics */}
                {recentTopics.length > 0 && (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold flex items-center gap-2 mr-2">
                       <Clock className="w-3 h-3" />
                       Recent Topics
                    </span>
                    {recentTopics.map((t, i) => (
                      <button
                        key={i}
                        onClick={() => setTopic(t)}
                        className="text-xs px-4 py-2 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all flex items-center gap-2"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {step === 'generating_outline' && (
            <div className="py-20">
              <LoadingAnimation label="Architecting narrative and identifying key scientific milestones..." />
              <div className="max-w-md mx-auto mt-8">
                <SkeletonLoader variant="list" count={4} />
              </div>
            </div>
          )}

          {step === 'edit_outline' && (
            <motion.div
              key="edit_outline"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-8 pb-20"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="text-2xl font-bold text-[var(--text-primary)]">Review Outline</h3>
                  <p className="text-sm text-[var(--text-secondary)]">Fine-tune the structure before final assembly</p>
                </div>
                <button 
                  onClick={() => setStep('input')}
                  className="text-sm text-slate-500 hover:text-white transition-colors"
                >
                  Start Over
                </button>
              </div>

              {creationType === 'slides' && slideOutline && (
                <SlideOutlineEditor 
                  outline={slideOutline}
                  onOutlineChange={setSlideOutline}
                  onCancel={() => setStep('input')}
                  onGenerate={handleGenerateFinal}
                />
              )}

              {creationType === 'document' && docOutline && (
                <DocOutlineEditor 
                  outline={docOutline}
                  onOutlineChange={setDocOutline}
                  onCancel={() => setStep('input')}
                  onGenerate={handleGenerateFinal}
                />
              )}
            </motion.div>
          )}

          {(step === 'generating_final' || step === 'complete') && (
            <motion.div
              key="progress"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="max-w-3xl mx-auto rounded-3xl bg-[var(--surface)] border border-[var(--border)] backdrop-blur-xl overflow-hidden shadow-2xl"
            >
              {creationType === 'slides' ? (
                <SlideProgress 
                  currentStep={step === 'complete' ? 'complete' : 'content'}
                  currentSlide={progress.current}
                  totalSlides={progress.total}
                  totalImages={progress.total} // Assumption: 1 image per slide for now
                  message={progress.message}
                  onDownload={handleDownload}
                />
              ) : (
                <div className="p-12 text-center space-y-8">
                  {step === 'complete' ? (
                    <>
                      <div className="w-20 h-20 rounded-full bg-teal-500 flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-teal-500/20">
                        <CheckCircle className="w-10 h-10 text-black" />
                      </div>
                      <h3 className="text-2xl font-bold text-white">Document Assembled</h3>
                      <p className="text-slate-400">Your research report has been formatted and is ready for review.</p>
                      <button 
                        onClick={handleDownload}
                        className="px-10 py-4 rounded-2xl bg-teal-500 text-black font-bold hover:bg-teal-400 transition-all flex items-center justify-center gap-3 mx-auto"
                      >
                        <Download className="w-5 h-5" />
                        Download Word File
                      </button>
                    </>
                  ) : (
                    <div className="space-y-8">
                      <LoadingAnimation label={progress.message || 'Synthesizing professional prose...'} />
                      <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden max-w-md mx-auto">
                        <motion.div 
                          className="h-full bg-teal-500" 
                          animate={{ width: `${(progress.current / (progress.total || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error State */}
      {error && step !== 'generating_outline' && step !== 'generating_final' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-6 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-md flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <AlertCircle className="w-6 h-6 text-red-500" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
          <button 
            onClick={() => { setError(''); setStep('input'); }}
            className="text-xs font-bold text-red-500 hover:text-red-400 uppercase tracking-widest"
          >
            Reset
          </button>
        </motion.div>
      )}
    </HubLayout>
  );
}
