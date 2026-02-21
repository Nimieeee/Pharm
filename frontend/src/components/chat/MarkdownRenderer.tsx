'use client';

import React, { useState, useRef, useCallback, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import { Copy, Check, Download, ExternalLink } from 'lucide-react';
import 'katex/dist/katex.min.css';
import { MermaidRenderer } from './MermaidRenderer';
import { useFeatureFlag } from '@/hooks/use-feature-flag';

interface MarkdownRendererProps {
  content: string;
  isAnimating?: boolean;
  className?: string;
  onCodeBlockCopy?: (code: string) => void;
}

// Custom UI Components
function ActionButton({ onClick, disabled, icon, successIcon, title, showSuccess }: any) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`p-1.5 rounded-lg transition-all duration-200 ${showSuccess
        ? 'bg-emerald-500/10 text-emerald-500'
        : 'hover:bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
        }`}
      title={title}
    >
      {showSuccess ? (successIcon || icon) : icon}
    </button>
  );
}

function InteractiveOverlay({ children, position = 'top-right', title, disabled }: any) {
  const posClasses = {
    'top-right': 'top-2 right-2',
    'bottom-right': 'bottom-2 right-2',
  }[position as string] || 'top-2 right-2';

  return (
    <div className={`absolute ${posClasses} z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1 bg-[var(--surface)]/80 backdrop-blur-sm p-1 rounded-lg border border-[var(--border)] shadow-sm`}>
      {title && <span className="text-xs px-2 py-1 text-[var(--text-secondary)] font-medium">{title}</span>}
      {children}
    </div>
  );
}

// Enhanced Code Block
function EnhancedCodeBlock({ children, className, isAnimating }: { children: React.ReactNode; className?: string; isAnimating?: boolean }) {
  const [copied, setCopied] = useState(false);
  const code = String(children);
  const language = className?.replace('language-', '') || '';

  const handleCopy = useCallback(async () => {
    if (isAnimating) return;
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code, isAnimating]);

  return (
    <div className="relative group my-4 rounded-xl border border-[var(--border)] bg-[var(--surface-highlight)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface)] border-b border-[var(--border)]">
        <span className="text-xs font-mono text-[var(--text-secondary)] uppercase">{language || 'text'}</span>
        <div className="flex items-center gap-1">
          <ActionButton
            onClick={handleCopy}
            disabled={isAnimating}
            icon={copied ? <Check size={14} /> : <Copy size={14} />}
            title="Copy code"
            showSuccess={copied}
          />
        </div>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code className="text-sm font-mono text-[var(--text-primary)] leading-relaxed">{code}</code>
      </pre>
    </div>
  );
}

// Enhanced Table with export options
function EnhancedTable({ children, isAnimating }: { children: React.ReactNode; isAnimating?: boolean }) {
  const [copied, setCopied] = useState(false);
  const tableRef = useRef<HTMLTableElement>(null);

  const copyForWord = useCallback(async () => {
    if (isAnimating || !tableRef.current) return;

    // Create a clone to manipulate styles without affecting the UI
    const clone = tableRef.current.cloneNode(true) as HTMLElement;

    // Inject inline styles for MS Word compatibility
    clone.style.borderCollapse = 'collapse';
    clone.style.width = '100%';
    clone.style.fontFamily = 'Arial, sans-serif';
    clone.style.fontSize = '12px'; // Standard Word table font size

    const ths = clone.querySelectorAll('th');
    ths.forEach(th => {
      th.style.border = '1px solid #000'; // Word prefers stark borders
      th.style.padding = '8px';
      th.style.backgroundColor = '#f0f0f0';
      th.style.fontWeight = 'bold';
      th.style.textAlign = 'left';
    });

    const tds = clone.querySelectorAll('td');
    tds.forEach(td => {
      td.style.border = '1px solid #000';
      td.style.padding = '8px';
      td.style.verticalAlign = 'top';
    });

    const htmlObj = new Blob([clone.outerHTML], { type: 'text/html' });
    const textObj = new Blob([clone.innerText], { type: 'text/plain' });

    const data = [new ClipboardItem({
      "text/html": htmlObj,
      "text/plain": textObj
    })];

    try {
      await navigator.clipboard.write(data);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy for Word:', err);
      // Fallback
      await navigator.clipboard.writeText(clone.outerHTML);
    }
  }, [isAnimating]);

  return (
    <div className="my-4 relative group">
      {/* Floating toolbar */}
      <div className="absolute -top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
        <div className="relative">
          <ActionButton
            onClick={copyForWord}
            disabled={isAnimating}
            icon={copied ? <Check size={14} /> : <Copy size={14} />}
            title="Copy"
            showSuccess={copied}
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
        <table ref={tableRef} className="w-full border-collapse text-sm">
          {children}
        </table>
      </div>
    </div>
  );
}

// Enhanced Image with download
function EnhancedImage({ src, alt, isAnimating }: { src?: string; alt?: string; isAnimating?: boolean }) {
  const [downloaded, setDownloaded] = useState(false);

  const handleDownload = useCallback(async () => {
    if (!src || isAnimating) return;
    try {
      const response = await fetch(src);
      const blob = await response.blob();
      const ext = blob.type.split('/')[1] || 'png';
      const filename = alt ? `${alt.replace(/[^a-z0-9]/gi, '_')}.${ext}` : `image.${ext}`;

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);

      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 2000);
    } catch (error) {
      console.error('Failed to download image:', error);
    }
  }, [src, alt, isAnimating]);

  return (
    <div className="my-4 relative group inline-block">
      <img
        src={src}
        alt={alt || 'Image'}
        className="max-w-full h-auto rounded-xl border border-[var(--border)]"
      />
      <InteractiveOverlay position="bottom-right" disabled={isAnimating}>
        <ActionButton
          onClick={handleDownload}
          disabled={isAnimating}
          icon={<Download size={14} />}
          successIcon={<Check size={14} />}
          title="Download image"
          showSuccess={downloaded}
        />
      </InteractiveOverlay>
    </div>
  );
}


// Utility to fix incomplete markdown during streaming
function repairIncompleteMarkdown(content: string): string {
  let repaired = content;

  // Fix unclosed bold (**) - more sophisticated detection
  const boldMatches = repaired.match(/\*\*[^\*]*$/);
  if (boldMatches && boldMatches.length > 0) {
    // Check if we have an odd number of bold markers
    const boldCount = (repaired.match(/\*\*/g) || []).length;
    if (boldCount % 2 !== 0) {
      repaired += '**';
    }
  }

  // Fix unclosed code blocks (```) - handle language specifiers
  const codeBlockMatches = repaired.match(/```/g) || [];
  if (codeBlockMatches.length % 2 !== 0) {
    // Check if the last code block is unclosed
    const lastCodeBlockMatch = repaired.lastIndexOf('```');
    if (lastCodeBlockMatch !== -1 && lastCodeBlockMatch === repaired.length - 3) {
      // It's already a closing ``` at the end, don't add another
    } else {
      repaired += '\n```';
    }
  }

  // Fix unclosed inline code (`) - more sophisticated detection
  const backtickMatches = repaired.match(/`[^`]*$/);
  if (backtickMatches && backtickMatches.length > 0) {
    const backtickCount = (repaired.match(/`/g) || []).length;
    if (backtickCount % 2 !== 0) {
      repaired += '`';
    }
  }

  // Fix unclosed LaTeX ($$)
  const latexCount = (repaired.match(/\$\$/g) || []).length;
  if (latexCount % 2 !== 0) {
    repaired += '$$';
  }

  // Fix unclosed italic (*)
  const italicCount = (repaired.match(/\*(?!\*)[^\s][^\*]*$/g) || []).length;
  if (italicCount % 2 !== 0) {
    repaired += '*';
  }

  // Fix unclosed headers (#)
  const headerMatch = repaired.match(/#+(?!#)[^\n]*$/);
  if (headerMatch && !repaired.endsWith('\n')) {
    repaired += '\n\n';
  }

  // Fix unclosed lists (-, *, +)
  const listMatch = repaired.match(/^[\s]*(?:[-+*]|\d+\.)[\s]+[^\n]*$/);
  if (listMatch && !repaired.endsWith('\n')) {
    repaired += '\n';
  }

  // Fix unclosed blockquotes (>)
  const blockquoteMatches = repaired.match(/^>[^\n]*(?:\n>[^\n]*)*$/);
  if (blockquoteMatches && !repaired.endsWith('\n')) {
    repaired += '\n';
  }

  // Fix unclosed links [text](url
  const linkMatch = repaired.match(/\[[^\]]*\]\([^\)]*$/);
  if (linkMatch) {
    repaired += ')';
  }

  // Fix unclosed images ![alt](url
  const imageMatch = repaired.match(/!\[[^\]]*\]\([^\)]*$/);
  if (imageMatch) {
    repaired += ')';
  }

  return repaired;
}

// Main Markdown Renderer Component - Memoized for performance
const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  isAnimating = false,
  className = '',
  mode = 'normal'
}: MarkdownRendererProps & { mode?: 'normal' | 'deep_research' | 'fast' }) {

  const mermaidEnabled = useFeatureFlag('mermaid-diagrams');

  // 1. Clean content from logs
  let displayContent = content
    .replace(/\{"timestamp":[^}]+\}/g, '')
    .replace(/\{"level":[^}]+\}/g, '')
    .trim();

  // 2. Repair incomplete markdown if animating
  if (isAnimating) {
    displayContent = repairIncompleteMarkdown(displayContent);
  }

  // 3. Preprocess LaTeX delimiters for KaTeX
  // Replace \[ ... \] with $$ ... $$
  displayContent = displayContent.replace(/\\\[([\s\S]*?)\\\]/g, '$$$1$$');
  // Replace \( ... \) with $ ... $
  displayContent = displayContent.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$');

  // 3. Deep Research specific handling
  const isDeepResearch = mode === 'deep_research';

  // Force Prose for Deep Research
  const finalClassName = isDeepResearch
    ? "prose prose-lg dark:prose-invert max-w-none"
    : `markdown-content ${className}`;

  // Strip code block wrappers for Deep Research
  if (isDeepResearch) {
    if (displayContent.startsWith('```markdown')) {
      displayContent = displayContent.slice(11);
    } else if (displayContent.startsWith('```')) {
      displayContent = displayContent.slice(3);
    }
    if (displayContent.endsWith('```')) {
      displayContent = displayContent.slice(0, -3);
    }
    displayContent = displayContent.trim();
  }

  return (
    <div className={finalClassName}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-serif font-semibold text-[var(--text-primary)] mt-6 mb-3 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-serif font-semibold text-[var(--text-primary)] mt-5 mb-2">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-serif font-semibold text-[var(--text-primary)] mt-4 mb-2">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold text-[var(--text-primary)] mt-3 mb-1">
              {children}
            </h4>
          ),

          // Paragraphs with proper spacing
          p: ({ children }) => (
            <p className="text-[var(--text-primary)] leading-7 mb-4">
              {children}
            </p>
          ),

          // Lists with proper styling
          ul: ({ children }) => (
            <ul className="list-disc pl-6 my-4 space-y-2 text-[var(--text-primary)]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-6 my-4 space-y-2 text-[var(--text-primary)]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-7">{children}</li>
          ),

          // Blockquote
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-[var(--accent)] pl-4 my-4 text-[var(--text-secondary)] italic bg-[var(--surface-highlight)] py-2 rounded-r-lg">
              {children}
            </blockquote>
          ),

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--accent)] hover:underline inline-flex items-center gap-1"
            >
              {children}
              <ExternalLink size={12} />
            </a>
          ),

          // Code - inline, block, and mermaid diagrams
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-[var(--surface-highlight)] rounded text-sm font-mono text-[var(--accent)]">
                  {children}
                </code>
              );
            }
            // Mermaid diagram rendering (admin-only via feature flag)
            const language = className?.replace('language-', '') || '';
            if (language === 'mermaid' && mermaidEnabled) {
              return <MermaidRenderer code={String(children).replace(/\n$/, '')} />;
            }
            return (
              <EnhancedCodeBlock className={className} isAnimating={isAnimating}>
                {String(children).replace(/\n$/, '')}
              </EnhancedCodeBlock>
            );
          },
          pre: ({ children }) => <>{children}</>,

          // Tables with interactive features - Enforce styling
          table: ({ children }) => (
            <EnhancedTable isAnimating={isAnimating}>
              {children}
            </EnhancedTable>
          ),
          thead: ({ children }) => (
            <thead className="bg-[var(--surface-highlight)] text-[var(--text-primary)]">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="bg-[var(--surface)]">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-[var(--border)] hover:bg-[var(--surface-highlight)]/50 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-4 py-3 text-left font-semibold text-[var(--text-primary)] border border-[var(--border)] bg-[var(--surface-highlight)] whitespace-nowrap">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-[var(--text-primary)] border border-[var(--border)] align-top">
              {children}
            </td>
          ),

          // Images with download
          img: ({ src, alt }) => (
            <EnhancedImage src={src} alt={alt} isAnimating={isAnimating} />
          ),

          // Horizontal rule
          hr: () => <hr className="my-6 border-[var(--border)]" />,

          // Text formatting
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          del: ({ children }) => <del className="line-through text-[var(--text-secondary)]">{children}</del>,
        }}
      >
        {displayContent}
      </ReactMarkdown>

      {/* Streaming cursor */}
      {isAnimating && (
        <span className="inline-block w-2 h-5 bg-[var(--accent)] animate-pulse ml-0.5 align-middle" />
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Strict Memoization
  // Only re-render if the content string has actually changed
  // OR if the 'isAnimating' status has changed.
  // OR if 'mode' has changed.
  return (
    prevProps.content === nextProps.content &&
    prevProps.isAnimating === nextProps.isAnimating &&
    prevProps.mode === nextProps.mode &&
    prevProps.className === nextProps.className
  );
});

export default MarkdownRenderer;

// Export utility function
export function cleanStreamContent(content: string): string {
  return content
    .replace(/\{"timestamp":[^}]+\}/g, '')
    .replace(/\{"level":[^}]+\}/g, '')
    .trim();
}
