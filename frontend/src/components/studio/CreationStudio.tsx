'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Presentation, FileText, Sparkles, Loader2 } from 'lucide-react';
import SlideOutlineEditor, { SlideOutline } from '../slides/SlideOutlineEditor';
import SlideProgress from '../slides/SlideProgress';
import DocOutlineEditor, { DocOutline } from '../docs/DocOutlineEditor';

type CreationType = 'slides' | 'document';
type GenerationStep = 'outline' | 'generating' | 'complete';

export default function CreationStudio() {
  const [creationType, setCreationType] = useState<CreationType>('slides');
  const [step, setStep] = useState<GenerationStep>('outline');
  const [topic, setTopic] = useState('');
  const [slideOutline, setSlideOutline] = useState<SlideOutline | null>(null);
  const [docOutline, setDocOutline] = useState<DocOutline | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });
  const [jobId, setJobId] = useState('');
  const [error, setError] = useState('');

  const handleGenerateOutline = async () => {
    if (!topic.trim()) return;

    setStep('generating');
    setError('');

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const endpoint = creationType === 'slides'
        ? '/api/v1/slides/outline'
        : '/api/v1/docs/outline';

      const body = creationType === 'slides'
        ? { topic: topic.trim(), num_slides: 12 }
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

      if (creationType === 'slides') {
        setSlideOutline(data);
      } else {
        setDocOutline(data);
      }

      setStep('outline');
    } catch (err: any) {
      setError(err.message);
      setStep('outline');
    }
  };

  const handleGenerateFinal = async () => {
    setStep('generating');
    setError('');

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const endpoint = creationType === 'slides'
        ? '/api/v1/slides/generate'
        : '/api/v1/docs/generate';

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

      if (!response.ok) {
        throw new Error('Generation failed');
      }

      // Handle SSE
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));

              if (data.event === 'progress') {
                const progressData = JSON.parse(data.data);
                setProgress({
                  current: progressData.current,
                  total: progressData.total,
                  message: progressData.message,
                });
              } else if (data.event === 'complete') {
                setJobId(data.data.job_id);
                setStep('complete');
              } else if (data.event === 'error') {
                throw new Error(data.data.error);
              }
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message);
      setStep('outline');
    }
  };

  const handleDownload = () => {
    const endpoint = creationType === 'slides'
      ? `/api/v1/slides/download/${jobId}`
      : `/api/v1/docs/download/${jobId}`;

    window.open(endpoint, '_blank');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-amber-600" />
          <h1 className="text-2xl font-bold">Creation Studio</h1>
        </div>
        <p className="text-muted-foreground">
          AI-powered slide and document generation
        </p>
      </motion.div>

      {/* Type Selector */}
      {step === 'outline' && !slideOutline && !docOutline && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 p-6 bg-card border border-border rounded-xl"
        >
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setCreationType('slides')}
              className={`flex-1 p-6 rounded-xl border-2 transition-colors ${
                creationType === 'slides'
                  ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/20'
                  : 'border-border hover:border-amber-300'
              }`}
            >
              <Presentation className={`w-8 h-8 mx-auto mb-3 ${
                creationType === 'slides' ? 'text-amber-600' : 'text-muted-foreground'
              }`} />
              <h3 className="font-semibold mb-2">Presentation</h3>
              <p className="text-sm text-muted-foreground">
                Generate professional slides with AI images
              </p>
            </button>
            <button
              onClick={() => setCreationType('document')}
              className={`flex-1 p-6 rounded-xl border-2 transition-colors ${
                creationType === 'document'
                  ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/20'
                  : 'border-border hover:border-amber-300'
              }`}
            >
              <FileText className={`w-8 h-8 mx-auto mb-3 ${
                creationType === 'document' ? 'text-amber-600' : 'text-muted-foreground'
              }`} />
              <h3 className="font-semibold mb-2">Document</h3>
              <p className="text-sm text-muted-foreground">
                Create structured reports and manuscripts
              </p>
            </button>
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={`Enter topic for ${creationType === 'slides' ? 'presentation' : 'document'}...`}
              className="flex-1 px-4 py-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && handleGenerateOutline()}
            />
            <button
              onClick={handleGenerateOutline}
              disabled={!topic.trim()}
              className="px-8 py-3 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white rounded-lg font-medium transition-colors"
            >
              Generate Outline
            </button>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-8 p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20"
        >
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
        </motion.div>
      )}

      {/* Outline Editor */}
      {step === 'outline' && slideOutline && creationType === 'slides' && (
        <SlideOutlineEditor
          outline={slideOutline}
          onOutlineChange={setSlideOutline}
          onGenerate={handleGenerateFinal}
          onCancel={() => {
            setSlideOutline(null);
            setTopic('');
          }}
        />
      )}

      {step === 'outline' && docOutline && creationType === 'document' && (
        <DocOutlineEditor
          outline={docOutline}
          onOutlineChange={setDocOutline}
          onGenerate={handleGenerateFinal}
          onCancel={() => {
            setDocOutline(null);
            setTopic('');
          }}
        />
      )}

      {/* Progress */}
      {step === 'generating' && (
        <SlideProgress
          currentStep="content"
          currentSlide={progress.current}
          totalSlides={progress.total}
          totalImages={0}
          message={progress.message}
        />
      )}

      {/* Complete */}
      {step === 'complete' && (
        <SlideProgress
          currentStep="complete"
          currentSlide={0}
          totalSlides={0}
          totalImages={0}
          message=""
          onDownload={handleDownload}
        />
      )}
    </div>
  );
}
