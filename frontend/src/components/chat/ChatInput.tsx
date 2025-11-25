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
    // Auto-resize
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
    <div className="bg-[var(--background)] p-4 pb-8 md:pb-4">
      {/* Floating Capsule Input */}
      <form onSubmit={handleSubmit} className="fixed md:relative bottom-8 md:bottom-auto left-4 md:left-auto right-4 md:right-auto max-w-[600px] md:max-w-3xl mx-auto">
        <div
          className={`relative rounded-full md:rounded-2xl border transition-all ${
            isDragging 
              ? 'border-indigo-500 bg-indigo-500/5' 
              : 'border-[rgba(0,0,0,0.08)] dark:border-[rgba(255,255,255,0.1)] bg-[rgba(var(--surface-rgb),0.85)] md:bg-[var(--surface)] md:border-[var(--border)]'
          } backdrop-blur-xl md:backdrop-blur-none shadow-[0_8px_32px_-4px_rgba(0,0,0,0.12)] md:shadow-none`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          {/* File Upload Button */}
          <div className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 md:top-auto md:translate-y-0 md:bottom-3 flex items-center gap-2">
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
              className="w-9 h-9 rounded-full md:rounded-xl bg-[var(--surface-highlight)] flex items-center justify-center hover:bg-[var(--border)] transition-colors btn-press"
            >
              <Paperclip size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
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
            className="w-full py-3 md:py-4 pl-14 md:pl-16 pr-14 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />

          {/* Send Button */}
          <motion.button
            type="submit"
            disabled={!message.trim() || isLoading}
            whileTap={{ scale: 0.95 }}
            className={`absolute right-2 md:right-3 top-1/2 -translate-y-1/2 md:top-auto md:translate-y-0 md:bottom-3 w-9 h-9 rounded-full md:rounded-xl flex items-center justify-center transition-all ${
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

        {/* Helper Text - Desktop only */}
        <p className="hidden md:block text-xs text-[var(--text-secondary)] text-center mt-3">
          PharmGPT can make mistakes. Verify important pharmaceutical information.
        </p>
      </form>
    </div>
  );
}
