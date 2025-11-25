'use client';

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Paperclip, ArrowRight, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
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
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    console.log('Dropped files:', files);
  };

  return (
    <>
      {/* Desktop Input - Static at bottom */}
      <div className="hidden md:block border-t border-[var(--border)] bg-[var(--background)] p-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div
            className={`relative rounded-2xl border transition-all ${
              isDragging 
                ? 'border-indigo-500 bg-indigo-500/5' 
                : 'border-[var(--border)] bg-[var(--surface)]'
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <div className="absolute left-4 bottom-3 flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx"
                multiple
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-9 h-9 rounded-xl bg-[var(--surface-highlight)] flex items-center justify-center hover:bg-[var(--border)] transition-colors btn-press"
              >
                <Paperclip size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
              </button>
            </div>

            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about pharmaceutical research..."
              disabled={isLoading}
              rows={1}
              className="w-full py-4 pl-16 pr-14 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm"
              style={{ minHeight: '56px', maxHeight: '200px' }}
            />

            <motion.button
              type="submit"
              disabled={!message.trim() || isLoading}
              whileTap={{ scale: 0.95 }}
              className={`absolute right-3 bottom-3 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                message.trim() && !isLoading
                  ? 'bg-[var(--text-primary)] text-[var(--background)]'
                  : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)]'
              }`}
            >
              {isLoading ? (
                <Loader2 size={16} strokeWidth={1.5} className="animate-spin" />
              ) : (
                <ArrowRight size={16} strokeWidth={1.5} />
              )}
            </motion.button>
          </div>

          <p className="text-xs text-[var(--text-secondary)] text-center mt-3">
            PharmGPT can make mistakes. Verify important pharmaceutical information.
          </p>
        </form>
      </div>

      {/* Mobile Floating Capsule Input */}
      <div className="md:hidden fixed bottom-8 left-4 right-4 z-50 max-w-[600px] mx-auto">
        <form onSubmit={handleSubmit}>
          <div
            className={`relative rounded-full border transition-all ${
              isDragging 
                ? 'border-indigo-500 bg-indigo-500/5' 
                : 'border-[rgba(0,0,0,0.08)] dark:border-[rgba(255,255,255,0.1)]'
            } bg-[rgba(var(--surface-rgb),0.85)] backdrop-blur-xl shadow-[0_8px_32px_-4px_rgba(0,0,0,0.12)]`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
              <input
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx"
                multiple
                onChange={(e) => console.log('Files:', e.target.files)}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-9 h-9 rounded-full bg-[var(--surface-highlight)] flex items-center justify-center hover:bg-[var(--border)] transition-colors btn-press"
              >
                <Paperclip size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
              </button>
            </div>

            <textarea
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              disabled={isLoading}
              rows={1}
              className="w-full py-3 pl-14 pr-14 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm rounded-full"
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
                <ArrowRight size={16} strokeWidth={1.5} />
              )}
            </motion.button>
          </div>
        </form>
      </div>
    </>
  );
}
