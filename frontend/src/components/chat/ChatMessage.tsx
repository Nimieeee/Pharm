'use client';

import { useState, useRef } from 'react';
import { Copy, Check, RefreshCw, ExternalLink, FileText, ChevronLeft, ChevronRight, Download, FileDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import MarkdownRenderer from './MarkdownRenderer';
import { useTranslation } from '@/hooks/use-translation';
import { toast } from 'sonner';
import CitationPanel from './CitationPanel';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: string;      // The generation mode used for this message
  // Branching is now handled via separate props for assistant messages
  translations?: Record<string, string>;
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

import BranchMenu from './BranchMenu';
import { AssistantResponse } from '@/hooks/useChatState';
import { useChatContext } from '@/contexts/ChatContext';

interface ChatMessageProps {
  message: Message | { id: string; role: 'assistant'; content: string; timestamp: Date; mode?: string; translations?: Record<string, string>; citations?: any[] };
  isStreaming?: boolean;
  onRegenerate?: () => void;
  onEdit?: (messageId: string, newContent: string) => void;
  onDelete?: (messageId: string) => void;

  // Independent Branching Props
  branches?: AssistantResponse[];
  activeBranchId?: string;
  onSwitchBranch?: (responseId: string) => void;
  onDeleteBranch?: (responseId: string) => void;
}

export default function ChatMessage({
  message, isStreaming, onRegenerate, onEdit, onDelete,
  branches, activeBranchId, onSwitchBranch, onDeleteBranch
}: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const { t, language } = useTranslation();
  const contentRef = useRef<HTMLDivElement>(null);
  const { conversationId: contextConversationId } = useChatContext();
  
  // Use context conversationId with fallback to localStorage or URL
  const conversationId = contextConversationId || (
    typeof window !== 'undefined' 
      ? localStorage.getItem('last_conversation_id') || window.location.pathname.split('/').pop()
      : null
  );

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

  const handleExport = async (style: 'plain' | 'report' | 'manuscript') => {
    const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!conversationId || !UUID_REGEX.test(conversationId)) {
      toast.error('Please open a conversation first to export');
      return;
    }

    setIsExporting(true);
    setShowExportMenu(false);

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('token')
        : null;

      const response = await fetch(
        `/api/v1/export/${conversationId}/manuscript?style=${style}`,
        {
          method: 'GET',
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `benchside_${style}_${conversationId.slice(0, 8)}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`${style === 'manuscript' ? 'Manuscript' : style === 'report' ? 'Report' : 'Document'} downloaded`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
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
    // Use regex to safely strip outer ```markdown or ``` if the ENTIRE block is wrapped
    let cleaned = content;
    const match = cleaned.match(/^```(?:markdown)?\s*\n([\s\S]*?)```$/i);
    if (match && match[1]) {
      cleaned = match[1];
    }
    return cleaned.trim();
  };

  // Get displayed content - use translation if available, fallback to original
  const translatedContent = message.translations?.[language] || message.content;
  const displayContent = cleanContent(translatedContent);

  return (
    <motion.article
      {...animationProps}
      className="py-5 sm:py-6 w-full pl-2 sm:pl-0 min-h-[3rem]"
    >
      {/* AI Response - Editorial style, transparent background */}
      <div
        ref={contentRef}
        className="text-[var(--text-primary)] leading-relaxed w-full min-h-[2rem]"
      >
        <MarkdownRenderer
          content={displayContent}
          isAnimating={isStreaming}
          className={`markdown-content w-full ${isStreaming ? 'streaming-text' : ''}`}
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

          {/* Export Menu - Only for assistant messages */}
          {!isUser && (
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group"
                title="Export conversation"
              >
                <Download size={14} strokeWidth={1.5} className={`text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] ${isExporting ? 'animate-spin' : ''}`} />
              </button>

              <AnimatePresence>
                {showExportMenu && (
                  <>
                    {/* Backdrop to close menu */}
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowExportMenu(false)}
                    />

                    {/* Menu dropdown */}
                    <motion.div
                      initial={{ opacity: 0, y: -8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute left-0 bottom-full mb-2 z-20 min-w-[180px] bg-[var(--surface)]/95 backdrop-blur-md border border-[var(--border)] rounded-xl shadow-lg overflow-hidden"
                    >
                      <div className="py-1">
                        <button
                          onClick={() => handleExport('plain')}
                          disabled={isExporting}
                          className="w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3 disabled:opacity-50"
                        >
                          <FileText size={14} className="text-[var(--text-secondary)]" />
                          <span className="text-[var(--text-primary)]">Export as Chat</span>
                        </button>
                        <button
                          onClick={() => handleExport('report')}
                          disabled={isExporting}
                          className="w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3 disabled:opacity-50"
                        >
                          <FileDown size={14} className="text-[var(--text-secondary)]" />
                          <span className="text-[var(--text-primary)]">Export as Report</span>
                        </button>
                        <button
                          onClick={() => handleExport('manuscript')}
                          disabled={isExporting}
                          className="w-full px-4 py-2.5 text-left text-sm hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3 disabled:opacity-50"
                        >
                          <FileDown size={14} className="text-[var(--text-secondary)]" />
                          <span className="text-[var(--text-primary)]">Export as Manuscript</span>
                        </button>
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          )}

          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group mr-2"
              title={t('regenerate')}
            >
              <RefreshCw size={14} strokeWidth={1.5} className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
            </button>
          )}

          {branches && branches.length > 1 && onSwitchBranch && onDeleteBranch && activeBranchId && (
            <BranchMenu
              branches={branches}
              activeBranchId={activeBranchId}
              onSwitchBranch={onSwitchBranch}
              onDeleteBranch={onDeleteBranch}
            />
          )}

          {branches && branches.length > 1 && onSwitchBranch && activeBranchId && (
            <div className="flex items-center gap-0.5 ml-1">
              <button
                onClick={() => {
                  const idx = branches.findIndex(b => b.id === activeBranchId);
                  if (idx > 0) onSwitchBranch(branches[idx - 1].id);
                }}
                disabled={branches.findIndex(b => b.id === activeBranchId) <= 0}
                className="p-1 rounded hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-30"
                title="Previous branch"
              >
                <ChevronLeft size={14} className="text-[var(--text-secondary)]" />
              </button>
              <span className="text-[10px] text-[var(--text-secondary)] font-medium min-w-[24px] text-center">
                {branches.findIndex(b => b.id === activeBranchId) + 1}/{branches.length}
              </span>
              <button
                onClick={() => {
                  const idx = branches.findIndex(b => b.id === activeBranchId);
                  if (idx < branches.length - 1) onSwitchBranch(branches[idx + 1].id);
                }}
                disabled={branches.findIndex(b => b.id === activeBranchId) >= branches.length - 1}
                className="p-1 rounded hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-30"
                title="Next branch"
              >
                <ChevronRight size={14} className="text-[var(--text-secondary)]" />
              </button>
            </div>
          )}

          <span className="text-xs text-[var(--text-secondary)] ml-auto">
            {formatTime(message.timestamp)}
          </span>
        </div>
      )}

      {/* Citations Panel */}
      {!isUser && message.citations && message.citations.length > 0 && (
        <CitationPanel citations={message.citations} />
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
// 2. Content changes (when edited)
// 3. Streaming status changes
// 4. onEdit callback changes (critical for edit functionality)
export const MemoizedChatMessage = React.memo(ChatMessage, (prev, next) => {
  // Always update if it's the specific message being streamed
  if (prev.isStreaming !== next.isStreaming) return false;
  if (next.isStreaming) return false; // Always re-render streaming message

  // CRITICAL: Must update if onEdit callback changes
  if (prev.onEdit !== next.onEdit) return false;

  // Compare content - if content changed, MUST re-render
  if (prev.message.content !== next.message.content) return false;

  // For other props, skip re-render if unchanged
  return (
    prev.message.id === next.message.id &&
    prev.message.translations === next.message.translations &&
    prev.activeBranchId === next.activeBranchId &&
    prev.branches?.length === next.branches?.length
  );
});

import React from 'react';
