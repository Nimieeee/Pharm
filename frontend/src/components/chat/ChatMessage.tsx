'use client';

import { useState } from 'react';
import { Copy, Check, RefreshCw, ExternalLink, FileText } from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Array<{ id: number; title: string; url: string }>;
  attachments?: Array<{ name: string; size: string; type: string }>;
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onRegenerate?: () => void;
}

export default function ChatMessage({ message, isStreaming, onRegenerate }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ============================================
  // USER MESSAGE - Stacked Layout (Attachments Top)
  // ============================================
  if (isUser) {
    return (
      <div className="flex flex-col items-end gap-2 mb-4 py-3 sm:py-4">
        {/* 1. Attachment Cards (Rendered OUTSIDE the bubble) */}
        {message.attachments?.map((file, index) => (
          <div
            key={index}
            className="flex items-center gap-3 p-2.5 bg-white dark:bg-card border border-[var(--border-subtle)] rounded-xl shadow-sm w-fit min-w-[200px] max-w-xs"
          >
            {/* Icon Box */}
            <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center text-slate-600 dark:text-slate-300">
              <FileText size={20} />
            </div>
            {/* File Info */}
            <div className="flex flex-col overflow-hidden">
              <span className="text-sm font-medium truncate">{file.name}</span>
              <span className="text-xs text-muted-foreground">{file.size}</span>
            </div>
          </div>
        ))}

        {/* 2. The Text Bubble */}
        {message.content && (
          <div className="max-w-[85%] bg-[var(--surface-highlight)] text-[var(--text-primary)] rounded-2xl rounded-tr-sm px-5 py-3 shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
        )}

        {/* 3. Action Row (Footer) - Optional, can be added if needed, currently just timestamp */}
        <p className="text-[10px] sm:text-xs text-[var(--text-secondary)] mt-0.5 text-right px-1">
          {formatTime(message.timestamp)}
        </p>
      </div>
    );
  }

  // ============================================
  // AI MESSAGE - Editorial/Document Style
  // NO bubble, NO avatar, NO background, NO card
  // Full width, clean article appearance
  // ============================================
  // Strip markdown code block wrappers if present (Deep Research fix)
  const cleanContent = (content: string) => {
    if (!content) return '';
    let cleaned = content;
    // Remove starting ```markdown or ```
    if (cleaned.startsWith('```markdown')) {
      cleaned = cleaned.slice(11);
    } else if (cleaned.startsWith('```')) {
      cleaned = cleaned.slice(3);
    }
    // Remove ending ```
    if (cleaned.endsWith('```')) {
      cleaned = cleaned.slice(0, -3);
    }
    return cleaned.trim();
  };

  const displayContent = cleanContent(message.content);

  return (
    <article className="py-5 sm:py-6 w-full">
      {/* AI Response - Editorial style, transparent background */}
      <div className="text-[var(--text-primary)] leading-relaxed w-full">
        <MarkdownRenderer
          content={displayContent}
          isAnimating={isStreaming}
          className="markdown-content w-full"
        />
      </div>

      {/* Action Buttons - Only show when not streaming */}
      {!isStreaming && (
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[var(--border)]/50">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group"
            title="Copy message"
          >
            {copied ? (
              <Check size={14} strokeWidth={1.5} className="text-emerald-500" />
            ) : (
              <Copy size={14} strokeWidth={1.5} className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
            )}
          </button>
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group"
              title="Regenerate response"
            >
              <RefreshCw size={14} strokeWidth={1.5} className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
            </button>
          )}
          <span className="text-xs text-[var(--text-secondary)] ml-auto">
            {formatTime(message.timestamp)}
          </span>
        </div>
      )}

      {/* Citations */}
      {message.citations && message.citations.length > 0 && (
        <div className="mt-4 p-3 bg-[var(--surface-highlight)] rounded-xl">
          <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">References</p>
          <div className="space-y-1">
            {message.citations.map((citation) => (
              <a
                key={citation.id}
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs text-[var(--accent)] hover:underline"
              >
                <span className="font-medium">[{citation.id}]</span>
                <span className="truncate">{citation.title}</span>
                <ExternalLink size={10} strokeWidth={1.5} className="flex-shrink-0" />
              </a>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}
