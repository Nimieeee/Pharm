'use client';

import React, { useState, useCallback, useEffect, useRef, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkBreaks from 'remark-breaks';
import rehypeKatex from 'rehype-katex';
import {
  Copy, Check, Download, ExternalLink, Maximize2, X,
  FileCode, Table as TableIcon, Image as ImageIcon
} from 'lucide-react';

// Types
interface MarkdownRendererProps {
  content: string;
  isAnimating?: boolean;
  className?: string;
}

interface ActionButtonProps {
  onClick: () => void;
  disabled?: boolean;
  icon: React.ReactNode;
  successIcon?: React.ReactNode;
  title: string;
  showSuccess?: boolean;
}

// Action Button with hover effects
function ActionButton({ onClick, disabled, icon, successIcon, title, showSuccess }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        p-1.5 rounded-md backdrop-blur-md transition-all duration-200
        bg-white/80 dark:bg-[#1e1e1e]/80
        border border-[var(--border)]
        hover:bg-[var(--accent)] hover:text-white hover:scale-105
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        ${showSuccess ? 'bg-emerald-500 text-white' : ''}
      `}
    >
      {showSuccess && successIcon ? successIcon : icon}
    </button>
  );
}

// Interactive overlay wrapper
function InteractiveOverlay({
  children,
  position = 'top-right',
  disabled = false
}: {
  children: React.ReactNode;
  position?: 'top-right' | 'bottom-right';
  disabled?: boolean;
}) {
  const positionClasses = position === 'top-right'
    ? 'top-2 right-2'
    : 'bottom-2 right-2';

  return (
    <div className={`
      absolute ${positionClasses} flex gap-1 z-10
      opacity-0 group-hover:opacity-100 md:opacity-0 md:group-hover:opacity-100
      transition-opacity duration-200
      ${disabled ? 'pointer-events-none' : ''}
    `} style={{ opacity: typeof window !== 'undefined' && window.innerWidth < 768 ? 1 : undefined }}>
      {children}
    </div>
  );
}

// Code Block with enhanced features
function EnhancedCodeBlock({
  children,
  className,
  isAnimating
}: {
  children: string;
  className?: string;
  isAnimating?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const [isMermaid, setIsMermaid] = useState(false);
  const [mermaidSvg, setMermaidSvg] = useState<string>('');
  const [showFullscreen, setShowFullscreen] = useState(false);
  const mermaidRef = useRef<HTMLDivElement>(null);

  const language = className?.replace('language-', '') || '';
  const code = String(children).replace(/\n$/, '');

  // Detect and render Mermaid diagrams
  useEffect(() => {
    if (language === 'mermaid' && code) {
      setIsMermaid(true);
      import('mermaid').then((mermaid) => {
        mermaid.default.initialize({
          startOnLoad: false,
          theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default'
        });
        mermaid.default.render('mermaid-' + Math.random().toString(36).substr(2, 9), code)
          .then(({ svg }) => setMermaidSvg(svg))
          .catch(console.error);
      });
    }
  }, [language, code]);

  const handleCopy = useCallback(async () => {
    if (isAnimating) return;
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code, isAnimating]);

  const handleDownload = useCallback(() => {
    if (isAnimating) return;
    const ext = language || 'txt';
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [code, language, isAnimating]);

  const handleDownloadSvg = useCallback(() => {
    if (!mermaidSvg || isAnimating) return;
    const blob = new Blob([mermaidSvg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'diagram.svg';
    a.click();
    URL.revokeObjectURL(url);
  }, [mermaidSvg, isAnimating]);

  // Mermaid diagram rendering
  if (isMermaid && mermaidSvg) {
    return (
      <>
        <div className="my-4 relative group rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface-highlight)] border-b border-[var(--border)]">
            <span className="text-xs font-medium text-[var(--text-secondary)]">Mermaid Diagram</span>
          </div>
          <div
            ref={mermaidRef}
            className="p-4 overflow-auto flex justify-center"
            dangerouslySetInnerHTML={{ __html: mermaidSvg }}
          />
          <InteractiveOverlay disabled={isAnimating}>
            <ActionButton
              onClick={() => setShowFullscreen(true)}
              disabled={isAnimating}
              icon={<Maximize2 size={14} />}
              title="Fullscreen"
            />
            <ActionButton
              onClick={handleDownloadSvg}
              disabled={isAnimating}
              icon={<Download size={14} />}
              title="Download SVG"
            />
            <ActionButton
              onClick={handleCopy}
              disabled={isAnimating}
              icon={<Copy size={14} />}
              successIcon={<Check size={14} />}
              title="Copy source"
              showSuccess={copied}
            />
          </InteractiveOverlay>
        </div>

        {/* Fullscreen Modal */}
        {showFullscreen && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="relative bg-[var(--surface)] rounded-2xl max-w-[90vw] max-h-[90vh] overflow-auto p-6">
              <button
                onClick={() => setShowFullscreen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg bg-[var(--surface-highlight)] hover:bg-[var(--border)]"
              >
                <X size={20} />
              </button>
              <div dangerouslySetInnerHTML={{ __html: mermaidSvg }} />
            </div>
          </div>
        )}
      </>
    );
  }

  // Regular code block
  return (
    <div className="my-4 relative group rounded-xl border border-[var(--border)] bg-[var(--surface-highlight)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface)] border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <FileCode size={14} className="text-[var(--text-secondary)]" />
          <span className="text-xs font-medium text-[var(--text-secondary)]">{language || 'code'}</span>
        </div>
        <div className="flex gap-1">
          <ActionButton
            onClick={handleCopy}
            disabled={isAnimating}
            icon={<Copy size={14} />}
            successIcon={<Check size={14} />}
            title="Copy code"
            showSuccess={copied}
          />
          <ActionButton
            onClick={handleDownload}
            disabled={isAnimating}
            icon={<Download size={14} />}
            title={`Download as .${language || 'txt'}`}
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
  const [showMenu, setShowMenu] = useState(false);
  const tableRef = useRef<HTMLTableElement>(null);

  const getTableData = useCallback(() => {
    if (!tableRef.current) return { headers: [] as string[], rows: [] as string[][] };
    const headers: string[] = [];
    const rows: string[][] = [];

    const headerCells = tableRef.current.querySelectorAll('thead th');
    headerCells.forEach(cell => headers.push(cell.textContent || ''));

    const bodyRows = tableRef.current.querySelectorAll('tbody tr');
    bodyRows.forEach(row => {
      const rowData: string[] = [];
      row.querySelectorAll('td').forEach(cell => rowData.push(cell.textContent || ''));
      rows.push(rowData);
    });

    return { headers, rows };
  }, []);

  const copyAsCSV = useCallback(async () => {
    if (isAnimating) return;
    const { headers, rows } = getTableData();
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    await navigator.clipboard.writeText(csv);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    setShowMenu(false);
  }, [getTableData, isAnimating]);

  const copyAsTSV = useCallback(async () => {
    if (isAnimating) return;
    const { headers, rows } = getTableData();
    const tsv = [headers.join('\t'), ...rows.map(r => r.join('\t'))].join('\n');
    await navigator.clipboard.writeText(tsv);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    setShowMenu(false);
  }, [getTableData, isAnimating]);

  const copyAsHTML = useCallback(async () => {
    if (isAnimating || !tableRef.current) return;
    await navigator.clipboard.writeText(tableRef.current.outerHTML);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    setShowMenu(false);
  }, [isAnimating]);

  const downloadCSV = useCallback(() => {
    if (isAnimating) return;
    const { headers, rows } = getTableData();
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'table.csv';
    a.click();
    URL.revokeObjectURL(url);
    setShowMenu(false);
  }, [getTableData, isAnimating]);

  const downloadMarkdown = useCallback(() => {
    if (isAnimating) return;
    const { headers, rows } = getTableData();
    const separator = headers.map(() => '---').join(' | ');
    const md = [
      `| ${headers.join(' | ')} |`,
      `| ${separator} |`,
      ...rows.map(r => `| ${r.join(' | ')} |`)
    ].join('\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'table.md';
    a.click();
    URL.revokeObjectURL(url);
    setShowMenu(false);
  }, [getTableData, isAnimating]);

  return (
    <div className="my-4 relative group">
      {/* Floating toolbar */}
      <div className="absolute -top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
        <div className="relative">
          <ActionButton
            onClick={() => setShowMenu(!showMenu)}
            disabled={isAnimating}
            icon={copied ? <Check size={14} /> : <Copy size={14} />}
            title="Copy table"
            showSuccess={copied}
          />
          {showMenu && (
            <div className="absolute top-full right-0 mt-1 w-32 bg-[var(--surface)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden z-30">
              <button onClick={copyAsCSV} className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-highlight)]">Copy as CSV</button>
              <button onClick={copyAsTSV} className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-highlight)]">Copy as TSV</button>
              <button onClick={copyAsHTML} className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-highlight)]">Copy as HTML</button>
              <hr className="border-[var(--border)]" />
              <button onClick={downloadCSV} className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-highlight)]">Download CSV</button>
              <button onClick={downloadMarkdown} className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surface-highlight)]">Download MD</button>
            </div>
          )}
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


// Main Markdown Renderer Component - Memoized for performance
const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  isAnimating = false,
  className = ''
}: MarkdownRendererProps) {
  // Clean content from any leaked JSON logs
  const cleanContent = content
    .replace(/\{"timestamp":[^}]+\}/g, '')
    .replace(/\{"level":[^}]+\}/g, '')
    .trim();

  return (
    <div className={`markdown-content ${className}`}>
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

          // Code - inline and block
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-[var(--surface-highlight)] rounded text-sm font-mono text-[var(--accent)]">
                  {children}
                </code>
              );
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
        {cleanContent}
      </ReactMarkdown>

      {/* Streaming cursor */}
      {isAnimating && (
        <span className="inline-block w-2 h-5 bg-[var(--accent)] animate-pulse ml-0.5 align-middle" />
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for memoization
  // Only re-render if content changed or animation state changed
  if (prevProps.isAnimating !== nextProps.isAnimating) return false;
  if (prevProps.content !== nextProps.content) return false;
  if (prevProps.className !== nextProps.className) return false;
  return true;
});

export default MarkdownRenderer;

// Export utility function
export function cleanStreamContent(content: string): string {
  return content
    .replace(/\{"timestamp":[^}]+\}/g, '')
    .replace(/\{"level":[^}]+\}/g, '')
    .trim();
}
