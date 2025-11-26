'use client';

import { useEffect, useState } from 'react';

interface StreamdownWrapperProps {
  children: string;
  isAnimating?: boolean;
  className?: string;
}

// This component only renders Streamdown on the client side
export default function StreamdownWrapper({ children, isAnimating, className }: StreamdownWrapperProps) {
  const [StreamdownComponent, setStreamdownComponent] = useState<React.ComponentType<any> | null>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Dynamically import Streamdown only on client
    import('streamdown').then((mod) => {
      setStreamdownComponent(() => mod.Streamdown);
    }).catch((err) => {
      console.error('Failed to load Streamdown:', err);
    });
  }, []);

  // Show loading state or plain text during SSR/loading
  if (!isClient || !StreamdownComponent) {
    return (
      <div className={className}>
        <div className="whitespace-pre-wrap">{children}</div>
        {isAnimating && (
          <span className="inline-block w-2 h-4 bg-[var(--accent)] animate-pulse ml-1" />
        )}
      </div>
    );
  }

  return (
    <StreamdownComponent
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
    </StreamdownComponent>
  );
}
