'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, ExternalLink } from 'lucide-react';

interface StreamdownWrapperProps {
  children: string;
  isAnimating?: boolean;
  className?: string;
}

// Code block with copy button
function CodeBlock({ children, className }: { children: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  const language = className?.replace('language-', '') || '';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-[var(--border)] bg-[var(--surface-highlight)]">
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface)] border-b border-[var(--border)]">
        <span className="text-xs font-medium text-[var(--text-secondary)]">{language || 'code'}</span>
        <button onClick={handleCopy} className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] transition-colors">
          {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} className="text-[var(--text-secondary)]" />}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code className="text-sm font-mono text-[var(--text-primary)]">{children}</code>
      </pre>
    </div>
  );
}

// Fallback markdown renderer using react-markdown
function MarkdownFallback({ children, isAnimating, className }: StreamdownWrapperProps) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-xl font-serif font-semibold text-[var(--text-primary)] mt-6 mb-3 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-serif font-semibold text-[var(--text-primary)] mt-5 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-serif font-semibold text-[var(--text-primary)] mt-4 mb-2">{children}</h3>,
          p: ({ children }) => <p className="text-[var(--text-primary)] leading-relaxed my-2">{children}</p>,
          ul: ({ children }) => <ul className="my-3 pl-5 space-y-1.5 list-disc text-[var(--text-primary)]">{children}</ul>,
          ol: ({ children }) => <ol className="my-3 pl-5 space-y-1.5 list-decimal text-[var(--text-primary)]">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          blockquote: ({ children }) => <blockquote className="border-l-2 border-[var(--accent)] pl-4 my-3 text-[var(--text-secondary)] italic">{children}</blockquote>,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline inline-flex items-center gap-1">
              {children}<ExternalLink size={12} />
            </a>
          ),
          code: ({ className, children }) => {
            const isInline = !className;
            if (isInline) {
              return <code className="px-1.5 py-0.5 bg-[var(--surface-highlight)] rounded text-sm font-mono text-[var(--accent)]">{children}</code>;
            }
            return <CodeBlock className={className}>{String(children).replace(/\n$/, '')}</CodeBlock>;
          },
          pre: ({ children }) => <>{children}</>,
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-[var(--surface-highlight)]">{children}</thead>,
          th: ({ children }) => <th className="px-3 py-2 text-left font-semibold border-b border-[var(--border)]">{children}</th>,
          td: ({ children }) => <td className="px-3 py-2 border-b border-[var(--border)]">{children}</td>,
          hr: () => <hr className="my-6 border-[var(--border)]" />,
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
        }}
      >
        {children}
      </ReactMarkdown>
      {isAnimating && <span className="inline-block w-2 h-4 bg-[var(--accent)] animate-pulse ml-1" />}
    </div>
  );
}

export default function StreamdownWrapper({ children, isAnimating, className }: StreamdownWrapperProps) {
  const [mounted, setMounted] = useState(false);
  const [StreamdownComp, setStreamdownComp] = useState<React.ComponentType<any> | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    setMounted(true);
    let cancelled = false;
    
    import('streamdown')
      .then((mod) => {
        if (!cancelled && mod.Streamdown) {
          setStreamdownComp(() => mod.Streamdown);
        }
      })
      .catch((err) => {
        console.error('Failed to load Streamdown, using fallback:', err);
        if (!cancelled) {
          setLoadError(true);
        }
      });

    return () => { cancelled = true; };
  }, []);

  // Use fallback if not mounted, error loading, or streamdown not available
  if (!mounted || loadError || !StreamdownComp) {
    return <MarkdownFallback isAnimating={isAnimating} className={className}>{children}</MarkdownFallback>;
  }

  // Try to render with Streamdown, fallback on error
  try {
    return (
      <StreamdownComp
        isAnimating={isAnimating}
        className={className}
        controls={{ table: true, code: true, mermaid: { download: true, copy: true, fullscreen: true, panZoom: true } }}
        mermaid={{ config: { theme: 'base', themeVariables: { fontSize: '14px' } } }}
      >
        {children}
      </StreamdownComp>
    );
  } catch (err) {
    console.error('Streamdown render error:', err);
    return <MarkdownFallback isAnimating={isAnimating} className={className}>{children}</MarkdownFallback>;
  }
}
