'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { User, Sparkles, Copy, Check, RefreshCw, ExternalLink } from 'lucide-react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Array<{ id: number; title: string; url: string }>;
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onRegenerate?: () => void;
}

// ============================================================================
// MARKDOWN PARSER - Handles streaming/incomplete markdown gracefully
// ============================================================================

function parseMarkdown(text: string): React.ReactNode[] {
  const elements: React.ReactNode[] = [];
  const lines = text.split('\n');
  let inCodeBlock = false;
  let codeBlockLang = '';
  let codeBlockContent: string[] = [];
  let listItems: string[] = [];
  let listType: 'ul' | 'ol' | null = null;

  const flushList = () => {
    if (listItems.length > 0 && listType) {
      const ListTag = listType === 'ol' ? 'ol' : 'ul';
      elements.push(
        <ListTag key={`list-${elements.length}`} className={`my-3 pl-6 space-y-1 ${listType === 'ol' ? 'list-decimal' : 'list-disc'}`}>
          {listItems.map((item, i) => (
            <li key={i} className="text-[var(--text-primary)]">{parseInline(item)}</li>
          ))}
        </ListTag>
      );
      listItems = [];
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block handling
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        flushList();
        inCodeBlock = true;
        codeBlockLang = line.slice(3).trim();
        codeBlockContent = [];
      } else {
        elements.push(
          <CodeBlock 
            key={`code-${elements.length}`} 
            code={codeBlockContent.join('\n')} 
            language={codeBlockLang} 
          />
        );
        inCodeBlock = false;
        codeBlockLang = '';
        codeBlockContent = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Headers
    if (line.startsWith('# ')) {
      flushList();
      elements.push(<h1 key={`h1-${i}`} className="text-xl font-bold text-[var(--text-primary)] mt-6 mb-3">{parseInline(line.slice(2))}</h1>);
      continue;
    }
    if (line.startsWith('## ')) {
      flushList();
      elements.push(<h2 key={`h2-${i}`} className="text-lg font-semibold text-[var(--text-primary)] mt-5 mb-2">{parseInline(line.slice(3))}</h2>);
      continue;
    }
    if (line.startsWith('### ')) {
      flushList();
      elements.push(<h3 key={`h3-${i}`} className="text-base font-semibold text-[var(--text-primary)] mt-4 mb-2">{parseInline(line.slice(4))}</h3>);
      continue;
    }

    // Horizontal rule
    if (line.match(/^[-*_]{3,}$/)) {
      flushList();
      elements.push(<hr key={`hr-${i}`} className="my-4 border-[var(--border)]" />);
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote key={`bq-${i}`} className="border-l-4 border-indigo-500 pl-4 my-3 text-[var(--text-secondary)] italic">
          {parseInline(line.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered list
    if (line.match(/^[-*+]\s/)) {
      if (listType !== 'ul') {
        flushList();
        listType = 'ul';
      }
      listItems.push(line.slice(2));
      continue;
    }

    // Ordered list
    if (line.match(/^\d+\.\s/)) {
      if (listType !== 'ol') {
        flushList();
        listType = 'ol';
      }
      listItems.push(line.replace(/^\d+\.\s/, ''));
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      flushList();
      continue;
    }

    // Regular paragraph
    flushList();
    elements.push(
      <p key={`p-${i}`} className="text-[var(--text-primary)] leading-relaxed my-2">
        {parseInline(line)}
      </p>
    );
  }

  // Handle unclosed code block (streaming)
  if (inCodeBlock && codeBlockContent.length > 0) {
    elements.push(
      <CodeBlock 
        key={`code-${elements.length}`} 
        code={codeBlockContent.join('\n')} 
        language={codeBlockLang}
        isStreaming={true}
      />
    );
  }

  flushList();
  return elements;
}

// Parse inline markdown (bold, italic, code, links, citations)
function parseInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Citation [1], [2], etc.
    const citationMatch = remaining.match(/^\[(\d+)\]/);
    if (citationMatch) {
      parts.push(
        <sup key={key++} className="text-indigo-500 font-medium cursor-pointer hover:underline">
          [{citationMatch[1]}]
        </sup>
      );
      remaining = remaining.slice(citationMatch[0].length);
      continue;
    }

    // Bold **text**
    const boldMatch = remaining.match(/^\*\*(.+?)\*\*/);
    if (boldMatch) {
      parts.push(<strong key={key++} className="font-semibold">{boldMatch[1]}</strong>);
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // Italic *text*
    const italicMatch = remaining.match(/^\*(.+?)\*/);
    if (italicMatch) {
      parts.push(<em key={key++} className="italic">{italicMatch[1]}</em>);
      remaining = remaining.slice(italicMatch[0].length);
      continue;
    }

    // Inline code `code`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      parts.push(
        <code key={key++} className="px-1.5 py-0.5 bg-[var(--surface-highlight)] rounded text-sm font-mono text-indigo-600 dark:text-indigo-400">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // Links [text](url)
    const linkMatch = remaining.match(/^\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      parts.push(
        <a 
          key={key++} 
          href={linkMatch[2]} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-indigo-500 hover:underline inline-flex items-center gap-1"
        >
          {linkMatch[1]}
          <ExternalLink size={12} />
        </a>
      );
      remaining = remaining.slice(linkMatch[0].length);
      continue;
    }

    // Regular character
    parts.push(remaining[0]);
    remaining = remaining.slice(1);
  }

  return parts;
}


// ============================================================================
// CODE BLOCK COMPONENT
// ============================================================================

function CodeBlock({ code, language, isStreaming }: { code: string; language: string; isStreaming?: boolean }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-[var(--border)] bg-[var(--surface-highlight)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface)] border-b border-[var(--border)]">
        <span className="text-xs font-medium text-[var(--text-secondary)]">
          {language || 'code'}
          {isStreaming && <span className="ml-2 text-indigo-500">● streaming</span>}
        </span>
        <button
          onClick={handleCopy}
          disabled={isStreaming}
          className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors disabled:opacity-50"
          title="Copy code"
        >
          {copied ? (
            <Check size={14} className="text-emerald-500" />
          ) : (
            <Copy size={14} className="text-[var(--text-secondary)]" />
          )}
        </button>
      </div>
      {/* Code */}
      <pre className="p-4 overflow-x-auto">
        <code className="text-sm font-mono text-[var(--text-primary)]">{code}</code>
      </pre>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ChatMessage({ message, isStreaming, onRegenerate }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const parsedContent = useMemo(() => {
    if (isUser) return null;
    return parseMarkdown(message.content);
  }, [message.content, isUser]);

  return (
    <div className={`flex gap-4 py-6 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center shadow-lg ${
        isUser 
          ? 'bg-[var(--surface-highlight)]' 
          : 'bg-gradient-to-br from-cyan-500 to-violet-500'
      }`}>
        {isUser ? (
          <User size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
        ) : (
          <Sparkles size={16} strokeWidth={1.5} className="text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block rounded-2xl ${
          isUser 
            ? 'bg-[var(--text-primary)] text-[var(--background)] rounded-tr-md p-4' 
            : 'bg-[var(--glass-surface)] backdrop-blur-md border border-[var(--glass-border)] rounded-tl-md p-4'
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="text-sm prose-sm max-w-none">
              {parsedContent}
              
              {/* Streaming indicator */}
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-indigo-500 animate-pulse ml-1" />
              )}
            </div>
          )}
        </div>

        {/* Message Actions (for assistant messages) */}
        {!isUser && !isStreaming && (
          <div className="flex items-center gap-2 mt-2 px-1">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group"
              title="Copy message"
            >
              {copied ? (
                <Check size={14} className="text-emerald-500" />
              ) : (
                <Copy size={14} className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
              )}
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors group"
                title="Regenerate response"
              >
                <RefreshCw size={14} className="text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]" />
              </button>
            )}
            <span className="text-xs text-[var(--text-secondary)] ml-2">
              {formatTime(message.timestamp)}
            </span>
          </div>
        )}

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 p-3 bg-[var(--surface-highlight)] rounded-xl">
            <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">References</p>
            <div className="space-y-1">
              {message.citations.map((citation) => (
                <a
                  key={citation.id}
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-xs text-indigo-500 hover:underline"
                >
                  <span className="font-medium">[{citation.id}]</span>
                  <span className="truncate">{citation.title}</span>
                  <ExternalLink size={10} />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp for user messages */}
        {isUser && (
          <p className="text-xs text-[var(--text-secondary)] mt-2 px-1">
            {formatTime(message.timestamp)}
          </p>
        )}
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}
