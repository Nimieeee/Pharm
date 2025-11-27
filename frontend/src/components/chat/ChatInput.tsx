'use client';

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Paperclip, ArrowRight, Loader2, Zap, BookOpen, Search, Send } from 'lucide-react';
import { useSidebar } from '@/contexts/SidebarContext';

type Mode = 'fast' | 'detailed' | 'deep_research';

interface ChatInputProps {
  onSend: (message: string, mode: Mode) => void;
  onFileUpload?: (files: FileList) => void;
  isLoading: boolean;
  isUploading?: boolean;
}

const modes: { id: Mode; label: string; icon: typeof Zap; desc: string }[] = [
  { id: 'fast', label: 'Fast', icon: Zap, desc: 'Quick answers' },
  { id: 'detailed', label: 'Detailed', icon: BookOpen, desc: 'Comprehensive' },
  { id: 'deep_research', label: 'Deep Research', icon: Search, desc: 'PubMed literature review' },
];

export default function ChatInput({ onSend, onFileUpload, isLoading, isUploading = false }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState<Mode>('detailed');
  const [showModes, setShowModes] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Get sidebar state to adjust input position
  const { sidebarOpen } = useSidebar();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && onFileUpload) {
      onFileUpload(e.target.files);
      // Reset input so same file can be selected again
      e.target.value = '';
    }
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
  const ModeIcon = currentMode.icon;

  return (
    <>
      {/* Gradient Fade Mask - Desktop */}
      <div 
        className="hidden md:block fixed bottom-0 right-0 h-28 pointer-events-none z-40 bg-gradient-to-t from-[var(--background)] to-transparent transition-all duration-300"
        style={{ left: sidebarOpen ? '280px' : '0' }}
      />

      {/* Desktop Floating Capsule */}
      <div 
        className="hidden md:block fixed bottom-6 z-50 w-[60%] min-w-[500px] max-w-[700px] transition-all duration-300"
        style={{
          left: sidebarOpen ? 'calc(140px + 50%)' : '50%',
          transform: 'translateX(-50%)'
        }}
      >
        <form onSubmit={handleSubmit}>
          <div
            className={`relative rounded-full border-2 transition-all ${
              isDragging 
                ? 'border-[var(--accent)] bg-[var(--accent)]/5' 
                : 'border-[var(--border)] hover:border-[var(--text-secondary)]/30'
            } bg-[var(--surface)] shadow-xl`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            {/* Left Actions: Mode + File Upload */}
            <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {/* Mode Selector */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowModes(!showModes)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-full bg-[var(--surface-highlight)] hover:bg-[var(--border)] transition-colors btn-press"
                >
                  <ModeIcon size={14} strokeWidth={1.5} className="text-[var(--accent)]" />
                  <span className="text-xs font-medium text-[var(--text-primary)]">{currentMode.label}</span>
                </button>
                
                {/* Mode Dropdown */}
                {showModes && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute bottom-full left-0 mb-2 w-52 p-2 rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-xl"
                  >
                    {modes.map((m) => {
                      const Icon = m.icon;
                      return (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => { setMode(m.id); setShowModes(false); }}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                            mode === m.id ? 'bg-[var(--accent)]/10 text-[var(--accent)]' : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]'
                          }`}
                        >
                          <Icon size={18} strokeWidth={1.5} />
                          <div className="text-left">
                            <p className="text-sm font-medium">{m.label}</p>
                            <p className="text-xs text-[var(--text-secondary)]">{m.desc}</p>
                          </div>
                        </button>
                      );
                    })}
                  </motion.div>
                )}
              </div>

              {/* File Upload */}
              <input 
                ref={fileInputRef} 
                type="file" 
                className="hidden" 
                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.pptx,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp" 
                multiple 
                onChange={handleFileChange}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                title="Upload files"
                className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors btn-press ${
                  isUploading 
                    ? 'bg-[var(--accent)]/20 cursor-not-allowed' 
                    : 'hover:bg-[var(--surface-highlight)]'
                }`}
              >
                {isUploading ? (
                  <Loader2 size={16} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
                ) : (
                  <Paperclip size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                )}
              </button>
            </div>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about pharmaceutical research..."
              disabled={isLoading}
              rows={1}
              className="w-full py-4 pl-36 pr-14 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm"
              style={{ minHeight: '56px', maxHeight: '120px' }}
            />

            {/* Send Button */}
            <motion.button
              type="submit"
              disabled={!message.trim() || isLoading}
              whileTap={{ scale: 0.95 }}
              className={`absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                message.trim() && !isLoading
                  ? 'bg-[var(--text-primary)] text-[var(--background)]'
                  : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)]'
              }`}
            >
              {isLoading ? (
                <Loader2 size={18} strokeWidth={1.5} className="animate-spin" />
              ) : (
                <Send size={16} strokeWidth={2} />
              )}
            </motion.button>
          </div>
        </form>
      </div>

      {/* Mobile Floating Capsule */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-40 max-w-[600px] mx-auto">
        {/* Gradient Fade - Mobile */}
        <div className="fixed bottom-0 left-0 right-0 h-24 pointer-events-none -z-10 bg-gradient-to-t from-[var(--background)] to-transparent" />
        
        <form onSubmit={handleSubmit}>
          <div className="relative rounded-full border-2 border-[var(--border)] bg-[var(--surface)] shadow-xl">
            {/* Mode + Attach */}
            <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center gap-0.5">
              <button
                type="button"
                onClick={() => setShowModes(!showModes)}
                className="w-8 h-8 rounded-full hover:bg-[var(--surface-highlight)] flex items-center justify-center btn-press"
              >
                <ModeIcon size={14} strokeWidth={1.5} className="text-[var(--accent)]" />
              </button>
              {/* File Upload - Mobile */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-8 h-8 rounded-full hover:bg-[var(--surface-highlight)] flex items-center justify-center btn-press"
              >
                <Paperclip size={14} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
              </button>
            </div>

            {/* Mobile Mode Dropdown */}
            {showModes && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-full left-0 right-0 mb-2 p-2 rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-xl"
              >
                {modes.map((m) => {
                  const Icon = m.icon;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => { setMode(m.id); setShowModes(false); }}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                        mode === m.id ? 'bg-[var(--accent)]/10 text-[var(--accent)]' : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]'
                      }`}
                    >
                      <Icon size={18} strokeWidth={1.5} />
                      <div className="text-left">
                        <p className="text-sm font-medium">{m.label}</p>
                        <p className="text-xs text-[var(--text-secondary)]">{m.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </motion.div>
            )}

            <textarea
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              disabled={isLoading}
              rows={1}
              className="w-full py-3 pl-[4.5rem] pr-12 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm"
              style={{ minHeight: '48px', maxHeight: '48px' }}
            />

            <motion.button
              type="submit"
              disabled={!message.trim() || isLoading}
              whileTap={{ scale: 0.95 }}
              className={`absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                message.trim() && !isLoading
                  ? 'bg-[var(--text-primary)] text-[var(--background)]'
                  : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)]'
              }`}
            >
              {isLoading ? (
                <Loader2 size={16} strokeWidth={1.5} className="animate-spin" />
              ) : (
                <Send size={14} strokeWidth={2} />
              )}
            </motion.button>
          </div>
        </form>
      </div>
    </>
  );
}
