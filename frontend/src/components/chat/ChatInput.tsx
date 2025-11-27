'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, Loader2, Zap, BookOpen, Search, Send,
  Paperclip
} from 'lucide-react';
import { useSidebar } from '@/contexts/SidebarContext';

export type Mode = 'fast' | 'detailed' | 'deep_research';

interface ChatInputProps {
  onSend: (message: string, mode: Mode) => void;
  onFileUpload?: (files: FileList) => void;
  isLoading: boolean;
  isUploading?: boolean;
  mode: Mode;
  setMode: (mode: Mode) => void;
}

const modes: { id: Mode; label: string; icon: typeof Zap; desc: string }[] = [
  { id: 'fast', label: 'Fast', icon: Zap, desc: 'Quick answers' },
  { id: 'detailed', label: 'Detailed', icon: BookOpen, desc: 'Comprehensive' },
  { id: 'deep_research', label: 'Deep Research', icon: Search, desc: 'PubMed literature review' },
];

export default function ChatInput({ onSend, onFileUpload, isLoading, isUploading = false, mode, setMode }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { sidebarOpen } = useSidebar();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && onFileUpload) {
      onFileUpload(e.target.files);
      e.target.value = '';
    }
    setShowAttachMenu(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0 && onFileUpload) {
      onFileUpload(e.dataTransfer.files);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim(), mode);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const currentMode = modes.find(m => m.id === mode)!;

  return (
    <>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.pptx,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp"
        multiple
        onChange={handleFileChange}
      />

      {/* Gradient Fade Mask - Desktop */}
      <div
        className="hidden md:block fixed bottom-0 right-0 h-32 pointer-events-none z-40 bg-gradient-to-t from-[var(--background)] to-transparent transition-all duration-300"
        style={{ left: sidebarOpen ? '280px' : '0' }}
      />

      {/* Desktop Floating Capsule */}
      <div
        className="hidden md:block fixed bottom-8 z-[50] w-[60%] min-w-[500px] max-w-[700px] transition-all duration-300"
        style={{
          left: sidebarOpen ? 'calc(140px + 50%)' : '50%',
          transform: 'translateX(-50%)'
        }}
      >
        {/* Action Chips Floating Above */}
        <div className="flex items-center justify-center gap-2 mb-3">
          {modes.map((m) => {
            const Icon = m.icon;
            const isActive = mode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border
                  ${isActive
                    ? 'bg-[var(--surface)] border-[var(--accent)] text-[var(--accent)] shadow-sm scale-105'
                    : 'bg-[var(--surface)]/80 border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface)] hover:text-[var(--text-primary)] backdrop-blur-sm'
                  }
                `}
              >
                <Icon size={12} strokeWidth={2} />
                {m.label}
              </button>
            );
          })}
        </div>

        <form onSubmit={handleSubmit}>
          <div
            className={`relative rounded-[28px] border-2 transition-all ${isDragging
                ? 'border-[var(--accent)] bg-[var(--accent)]/5'
                : 'border-[var(--border)] hover:border-[var(--text-secondary)]/30'
              } bg-[var(--surface)]/80 backdrop-blur-xl shadow-2xl`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            {/* Left: Plus Button (Attach Menu) */}
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowAttachMenu(!showAttachMenu)}
                  disabled={isUploading}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isUploading
                      ? 'bg-[var(--accent)]/20 cursor-not-allowed'
                      : 'bg-[var(--surface-highlight)] hover:bg-[var(--border)]'
                    }`}
                >
                  {isUploading ? (
                    <Loader2 size={18} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
                  ) : (
                    <Plus size={20} strokeWidth={2} className="text-[var(--text-secondary)]" />
                  )}
                </button>

                {/* Attach Menu Dropdown - Glassmorphism */}
                <AnimatePresence>
                  {showAttachMenu && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9, y: 10, originX: 0, originY: 1 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9, y: 10 }}
                      className="absolute bottom-full left-0 mb-4 w-64 p-2 rounded-2xl bg-white/80 dark:bg-[#1E1E1E]/80 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-2xl z-50"
                    >
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full flex items-center gap-3 p-3 rounded-xl text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50 transition-colors"
                      >
                        <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                          <Paperclip size={16} strokeWidth={1.5} className="text-[var(--accent)]" />
                        </div>
                        <div className="text-left">
                          <span className="text-sm font-medium block">Upload File</span>
                          <span className="text-[10px] text-[var(--text-secondary)]">PDF, DOCX, CSV, Images</span>
                        </div>
                      </button>

                      <div className="h-px bg-[var(--border)]/50 my-1 mx-2" />

                      {modes.map((m) => {
                        const Icon = m.icon;
                        const isActive = mode === m.id;
                        return (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => { setMode(m.id); setShowAttachMenu(false); }}
                            className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${isActive
                                ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
                                : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50'
                              }`}
                          >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isActive ? 'bg-[var(--accent)]/20' : 'bg-[var(--surface-highlight)]'
                              }`}>
                              <Icon size={16} strokeWidth={1.5} />
                            </div>
                            <div className="text-left">
                              <p className="text-sm font-medium">{m.label}</p>
                              <p className="text-[10px] text-[var(--text-secondary)]">{m.desc}</p>
                            </div>
                          </button>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Center: Text Input or Upload Status */}
            {isUploading ? (
              <div className="w-full py-4 pl-16 pr-16 flex items-center justify-center gap-2 text-[var(--text-primary)]" style={{ minHeight: '60px' }}>
                <Loader2 size={16} strokeWidth={1.5} className="animate-spin text-[var(--accent)]" />
                <span className="text-sm font-medium">Scanning Document...</span>
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder={`Ask anything in ${currentMode.label} mode...`}
                disabled={isLoading}
                rows={1}
                className="w-full py-4 pl-16 pr-16 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-base"
                style={{ minHeight: '60px', maxHeight: '200px' }}
              />
            )}

            {/* Right: Send Button ONLY */}
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center">
              <motion.button
                type="submit"
                disabled={!message.trim() || isLoading || isUploading}
                whileTap={{ scale: 0.95 }}
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${message.trim() && !isLoading && !isUploading
                    ? 'bg-[var(--foreground)] text-[var(--background)]'
                    : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)]'
                  }`}
              >
                {isLoading ? (
                  <Loader2 size={18} strokeWidth={1.5} className="animate-spin" />
                ) : (
                  <Send size={18} strokeWidth={2} />
                )}
              </motion.button>
            </div>
          </div>

          <div className="text-center mt-2">
            <p className="text-[10px] text-[var(--text-secondary)]">
              PharmGPT can make mistakes. Consider checking important information.
            </p>
          </div>
        </form>
      </div>

      {/* Mobile Floating Capsule - ChatGPT Style */}
      <div className="md:hidden fixed bottom-4 left-4 right-4 z-[50]">
        {/* Gradient Fade - Mobile */}
        <div className="fixed bottom-0 left-0 right-0 h-24 pointer-events-none -z-10 bg-gradient-to-t from-[var(--background)] to-transparent" />

        <form onSubmit={handleSubmit}>
          <div className={`relative rounded-full border-2 transition-all ${isDragging
              ? 'border-[var(--accent)] bg-[var(--accent)]/5'
              : 'border-[var(--border)]'
            } bg-[var(--surface)]/80 backdrop-blur-xl dark:bg-[#1E1E1E]/80 shadow-xl`}>
            {/* Left: Plus Button */}
            <div className="absolute left-1.5 top-1/2 -translate-y-1/2">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowAttachMenu(!showAttachMenu)}
                  disabled={isUploading}
                  className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${isUploading
                      ? 'bg-[var(--accent)]/20 cursor-not-allowed'
                      : 'bg-[var(--surface-highlight)] dark:bg-[#2A2A2A]'
                    }`}
                >
                  {isUploading ? (
                    <Loader2 size={16} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
                  ) : (
                    <Plus size={18} strokeWidth={2} className="text-[var(--text-secondary)]" />
                  )}
                </button>

                {/* Mobile Attach Menu - Glassmorphism */}
                <AnimatePresence>
                  {showAttachMenu && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9, y: 10, originX: 0, originY: 1 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9, y: 10 }}
                      className="absolute bottom-full left-0 mb-2 w-64 p-2 rounded-2xl bg-white/80 dark:bg-[#1E1E1E]/80 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-2xl z-50"
                    >
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full flex items-center gap-3 p-3 rounded-xl text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50 transition-colors"
                      >
                        <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                          <Paperclip size={16} strokeWidth={1.5} className="text-[var(--accent)]" />
                        </div>
                        <div className="text-left">
                          <span className="text-sm font-medium block">Upload File</span>
                          <span className="text-[10px] text-[var(--text-secondary)]">PDF, DOCX, CSV, Images</span>
                        </div>
                      </button>

                      <div className="h-px bg-[var(--border)]/50 my-1 mx-2" />

                      {modes.map((m) => {
                        const Icon = m.icon;
                        const isActive = mode === m.id;
                        return (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => { setMode(m.id); setShowAttachMenu(false); }}
                            className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${isActive
                                ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
                                : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50'
                              }`}
                          >
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isActive ? 'bg-[var(--accent)]/20' : 'bg-[var(--surface-highlight)]'
                              }`}>
                              <Icon size={16} strokeWidth={1.5} />
                            </div>
                            <div className="text-left">
                              <p className="text-sm font-medium">{m.label}</p>
                              <p className="text-[10px] text-[var(--text-secondary)]">{m.desc}</p>
                            </div>
                          </button>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Center: Text Input or Upload Status */}
            {isUploading ? (
              <div className="w-full py-3 pl-12 pr-12 flex items-center justify-center gap-2 text-[var(--text-primary)]">
                <Loader2 size={14} strokeWidth={1.5} className="animate-spin text-[var(--accent)]" />
                <span className="text-xs font-medium">Scanning...</span>
              </div>
            ) : (
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Message..."
                disabled={isLoading}
                className="w-full py-3 pl-12 pr-12 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none text-sm text-center"
              />
            )}

            {/* Right: Send Button ONLY */}
            <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center">
              <motion.button
                type="submit"
                disabled={!message.trim() || isLoading || isUploading}
                whileTap={{ scale: 0.95 }}
                className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${message.trim() && !isLoading && !isUploading
                    ? 'bg-[var(--text-primary)] text-[var(--background)]'
                    : 'bg-transparent text-[var(--text-secondary)]'
                  }`}
              >
                {isLoading ? (
                  <Loader2 size={16} strokeWidth={1.5} className="animate-spin" />
                ) : (
                  <Send size={14} strokeWidth={2} />
                )}
              </motion.button>
            </div>
          </div>
        </form>
      </div>
    </>
  );
}
