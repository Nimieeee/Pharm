'use client';

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';

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
    // Handle file drop
    const files = Array.from(e.dataTransfer.files);
    console.log('Dropped files:', files);
  };

  return (
    <div className="border-t border-[var(--border)] bg-[var(--background)] p-4 pb-8 md:pb-4">
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
          {/* File Upload Button */}
          <div className="absolute left-3 bottom-3 flex items-center gap-2">
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
              <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
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
            className="w-full py-4 pl-16 pr-14 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-sm"
            style={{ minHeight: '56px', maxHeight: '200px' }}
          />

          {/* Send Button */}
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
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            )}
          </motion.button>
        </div>

        {/* Helper Text */}
        <p className="text-xs text-[var(--text-secondary)] text-center mt-3">
          PharmGPT can make mistakes. Verify important pharmaceutical information.
        </p>
      </form>
    </div>
  );
}
