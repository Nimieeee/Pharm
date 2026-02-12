'use client';

import { useState, useRef } from 'react';
import { Copy, Check, RefreshCw, ExternalLink, FileText } from 'lucide-react';
import { motion } from 'framer-motion';
import MarkdownRenderer from './MarkdownRenderer';
import { useTranslation } from '@/hooks/use-translation';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  translations?: Record<string, string>;  // Pre-generated translations {lang_code: content}
  citations?: Array<{
    id: number;
    title: string;
    url: string;
    authors?: string;
    year?: string;
    journal?: string;
    source?: string;
    doi?: string;
    volume?: string;
    issue?: string;
    pages?: string;
  }>;
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
  const { t, language } = useTranslation();
  const contentRef = useRef<HTMLDivElement>(null);

  const animationProps = {
    initial: { opacity: 0, y: 15 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: "easeOut" }
  };

  const handleCopy = async () => {
    if (!contentRef.current) {
      // Fallback for user messages or if ref is missing
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      return;
    }

    try {
      // Create a blob with the rendered HTML content
      // We clone it to add inline styles for Word if needed, but the rendered output usually suffices 
      // if it's copied as text/html.
      const htmlContent = contentRef.current.outerHTML;
      const textContent = contentRef.current.innerText; // Get visual text, not raw markdown

      const htmlBlob = new Blob([htmlContent], { type: 'text/html' });
      const textBlob = new Blob([textContent], { type: 'text/plain' });

      const data = [new ClipboardItem({
        'text/html': htmlBlob,
        'text/plain': textBlob
      })];

      await navigator.clipboard.write(data);
    } catch (e) {
      console.warn('Rich copy failed, falling back to text', e);
      await navigator.clipboard.writeText(message.content);
    }

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
    if (confirm(t('delete_confirm')) && onDelete) {
      onDelete(message.id);
    }
  };

  // ============================================
  // USER MESSAGE - Stacked Layout (Attachments Top)
  // ============================================
  if (isUser) {
    return (
      <motion.div
        {...animationProps}
        className="flex flex-col items-end gap-2 mb-4 py-3 sm:py-4"
      >
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
                {t('save')}
              </button>
              <button
                onClick={handleCancelEdit}
                className="px-3 py-1 bg-surface-highlight text-foreground rounded-lg text-xs hover:opacity-90 transition-opacity"
              >
                {t('cancel')}
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
            title={t('copy')}
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
            title={t('edit')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-secondary)]"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" /><path d="m15 5 4 4" /></svg>
          </button>
          <button
            onClick={handleDelete}
            disabled={!onDelete}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-secondary)]"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
          </button>
          <span className="text-[10px] sm:text-xs text-[var(--text-secondary)] ml-auto">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </motion.div>
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

  // Get displayed content - use translation if available, fallback to original
  const translatedContent = message.translations?.[language] || message.content;
  const displayContent = cleanContent(translatedContent);

  return (
    <motion.article
      {...animationProps}
      className="py-5 sm:py-6 w-full pl-2 sm:pl-0"
    >
      {/* AI Response - Editorial style, transparent background */}
      <div
        ref={contentRef}
        className="text-[var(--text-primary)] leading-relaxed w-full"
      >
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
            title={t('copy')}
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
              title={t('regenerate')}
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
        <div className="mt-4 p-4 bg-[var(--surface-highlight)] rounded-xl border border-border">
          <p className="text-xs font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <FileText size={14} />
            {t('references')} ({message.citations.length})
          </p>
          <div className="space-y-2.5">
            {message.citations.map((citation) => {
              // Helper to format authors to APA style (Last, F. M.)
              const formatAuthors = (authorStr: string) => {
                if (!authorStr) return '';
                // Remove "et al." for processing if present in the source string
                const cleanStr = authorStr.replace(/ et al\.?/i, '');
                const authors = cleanStr.split(/,\s*|\s+and\s+/).map(a => a.trim()).filter(a => a);

                // If authors are already in "Last, F." format, just join them with & for the last one
                if (authors.some(a => a.includes('.'))) {
                  if (authors.length > 1) {
                    const lastAuthor = authors.pop();
                    return `${authors.join(', ')}, & ${lastAuthor}`;
                  }
                  return authors[0];
                }

                // Convert "First Last" to "Last, F."
                const formattedList = authors.map(name => {
                  const parts = name.split(' ');
                  if (parts.length < 2) return name;
                  const last = parts[parts.length - 1];
                  const initials = parts.slice(0, -1).map(p => p[0] + '.').join(' ');
                  return `${last}, ${initials}`;
                });

                if (formattedList.length > 1) {
                  const lastAuthor = formattedList.pop();
                  return `${formattedList.join(', ')}, & ${lastAuthor}`;
                }
                return formattedList[0] || '';
              };

              const formattedAuthors = citation.authors ? formatAuthors(citation.authors) : '';
              const hasYear = citation.year && citation.year.trim();

              // Get domain for web sources if no journal
              let sourceName = citation.journal || citation.source || 'Web';
              if ((sourceName === 'Web' || !sourceName) && citation.url) {
                try {
                  const urlObj = new URL(citation.url);
                  sourceName = urlObj.hostname.replace('www.', '');
                } catch (e) {
                  sourceName = 'Web';
                }
              }

              return (
                <div key={citation.id} className="text-xs mb-3">
                  <div className="flex items-start gap-2">
                    <span className="font-bold text-[var(--accent)] flex-shrink-0 mt-0.5">[{citation.id}]</span>
                    <div className="flex-1 min-w-0 break-words">
                      <p className="text-[var(--text-secondary)] leading-relaxed">
                        {formattedAuthors && <span className="font-medium text-[var(--text-primary)]">{formattedAuthors} </span>}
                        {hasYear && <span>({citation.year}). </span>}
                        <a
                          href={citation.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[var(--text-primary)] hover:text-[var(--accent)] transition-colors font-medium"
                        >
                          {citation.title}.
                        </a>{' '}
                        <span className="italic">{sourceName}</span>
                        {citation.volume && <span>, {citation.volume}</span>}
                        {citation.issue && <span>({citation.issue})</span>}
                        {citation.pages && <span>, {citation.pages}</span>}
                        .
                        {citation.doi && (
                          <span className="block mt-0.5 text-[var(--accent)] opacity-80 hover:opacity-100">
                            doi:{citation.doi.replace('doi:', '')}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </motion.article>
  );
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

// Optimization: Memoize ChatMessage to prevent re-renders of history
// Only re-render if:
// 1. Message ID changes (obviously)
// 2. Content length changes significantly (or is streaming status changes)
// 3. Translations change
// 4. Copied/Editing state changes (handled internally)
export const MemoizedChatMessage = React.memo(ChatMessage, (prev, next) => {
  // Always update if it's the specific message being streamed
  if (prev.isStreaming !== next.isStreaming) return false;
  if (next.isStreaming) return false; // Always re-render steaming message (controlled by batching upstream)

  // Compare content and other props
  return (
    prev.message.content === next.message.content &&
    prev.message.id === next.message.id &&
    prev.message.translations === next.message.translations
  );
});

import React from 'react';
