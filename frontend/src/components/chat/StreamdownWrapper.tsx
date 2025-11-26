'use client';

import { useEffect, useState, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

interface StreamdownWrapperProps {
  children: string;
  isAnimating?: boolean;
  className?: string;
}

// Fallback component for SSR and loading states
function MarkdownFallback({ children, isAnimating }: { children: string; isAnimating?: boolean }) {
  return (
    <div className="whitespace-pre-wrap">
      {children}
      {isAnimating && (
        <span className="inline-block w-2 h-4 bg-[var(--accent)] animate-pulse ml-1" />
      )}
    </div>
  );
}

export default function StreamdownWrapper({ children, isAnimating, className }: StreamdownWrapperProps) {
  const [mounted, setMounted] = useState(false);
  const [StreamdownComp, setStreamdownComp] = useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    setMounted(true);
    
    // Only import on client side after mount
    let cancelled = false;
    
    import('streamdown')
      .then((mod) => {
        if (!cancelled) {
          setStreamdownComp(() => mod.Streamdown);
        }
      })
      .catch((err) => {
        console.error('Failed to load Streamdown:', err);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // During SSR or before mount, show fallback
  if (!mounted || !StreamdownComp) {
    return (
      <div className={className}>
        <MarkdownFallback isAnimating={isAnimating}>{children}</MarkdownFallback>
      </div>
    );
  }

  // Client-side with Streamdown loaded
  return (
    <StreamdownComp
      isAnimating={isAnimating}
      className={className}
      controls={{
        table: true,
        code: true,
        mermaid: {
          download: true,
          copy: true,
          fullscreen: true,
          panZoom: true,
        }
      }}
      mermaid={{
        config: {
          theme: 'base',
          themeVariables: {
            fontSize: '14px',
          },
        }
      }}
    >
      {children}
    </StreamdownComp>
  );
}
