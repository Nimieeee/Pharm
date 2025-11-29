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
  onEdit?: (messageId: string, newContent: string) => void;
  onDelete?: (messageId: string) => void;
}

export default function ChatMessage({ message, isStreaming, onRegenerate, onEdit, onDelete }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (editContent.trim() && onEdit) {
      onEdit(message.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditContent(message.content);
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (confirm('Delete this message?') && onDelete) {
      onDelete(message.id);
    }
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
            className="flex items-center gap-3 p-3 bg-card border border-border rounded-xl shadow-sm hover:shadow-md transition-shadow w-fit min-w-[220px] max-w-[280px]"
          >
            {/* Icon Box - Theme aware primary color */}
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center text-primary-foreground flex-shrink-0">
              <FileText size={20} strokeWidth={2} />
            </div>
            {/* File Info */}
            <div className="flex flex-col overflow-hidden flex-1 min-w-0">
              <span className="text-sm font-medium text-card-foreground truncate">{file.name}</span>
              <span className="text-xs text-muted-foreground">{file.size}</span>
            </div>
          </div>
        ))}

        {/* 2. Text Bubble */}
        {isEditing ? (
          <div className="bg-[var(--surface)] px-4 py-3 rounded-2xl shadow-sm border border-border max-w-fit min-w-[200px]">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full min-h-[60px] bg-transparent border-none outline-none text-sm resize-none text-foreground"
              autoFocus
            />
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleSaveEdit}
                className="px-3 py-1 bg-primary text-primary-foreground rounded-lg text-xs hover:opacity-90 transition-opacity"
              >
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-3 py-1 bg-surface-highlight text-foreground rounded-lg text-xs hover:opacity-90 transition-opacity"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="max-w-[85%] bg-[var(--surface-highlight)] text-[var(--text-primary)] rounded-2xl rounded-tr-sm px-5 py-3 shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
        )}

        {/* 3. Action Row (Copy/Edit/Delete) */}
        <div className="flex items-center gap-2 mt-1">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors"
            title="Copy message"
          >
            {copied ? (
              <Check size={14} strokeWidth={1.5} className="text-emerald-500" />
            ) : (
              <Copy size={14} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
            )}
          </button>
          <button
            onClick={handleEdit}
            disabled={!onEdit}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Edit message"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-secondary)]"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" /><path d="m15 5 4 4" /></svg>
          </button>
          <button
            onClick={handleDelete}
            disabled={!onDelete}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete message"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-secondary)]"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
          </button>
          <span className="text-[10px] sm:text-xs text-[var(--text-secondary)] ml-auto">
            {formatTime(message.timestamp)}
          </span>
        </div>
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
