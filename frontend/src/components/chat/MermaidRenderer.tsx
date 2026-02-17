'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Download, Check, RefreshCw } from 'lucide-react';

/**
 * MermaidRenderer
 * 
 * Renders Mermaid diagram syntax into interactive SVG diagrams.
 * Uses dynamic import to avoid SSR issues with mermaid.
 * 
 * Features:
 *  - Auto-renders mermaid syntax
 *  - Download as SVG
 *  - Error handling + fallback to code block
 *  - Theme-aware (adapts to dark/light mode)
 */
export function MermaidRenderer({ code }: { code: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [downloaded, setDownloaded] = useState(false);
    const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2, 9)}`);

    const renderDiagram = useCallback(async () => {
        try {
            setError(null);
            const mermaid = (await import('mermaid')).default;

            // Detect theme
            const isDark = document.documentElement.classList.contains('dark');

            mermaid.initialize({
                startOnLoad: false,
                theme: isDark ? 'dark' : 'default',
                securityLevel: 'loose',
                fontFamily: 'inherit',
            });

            const { svg: renderedSvg } = await mermaid.render(idRef.current, code.trim());
            setSvg(renderedSvg);
        } catch (err: any) {
            console.error('Mermaid render error:', err);
            setError(err?.message || 'Failed to render diagram');
        }
    }, [code]);

    useEffect(() => {
        // Debounce rendering to avoid parsing errors while streaming
        const timeoutId = setTimeout(() => {
            renderDiagram();
        }, 1500);

        return () => clearTimeout(timeoutId);
    }, [renderDiagram]);

    const handleDownload = useCallback(() => {
        if (!svg) return;
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'diagram.svg';
        a.click();
        URL.revokeObjectURL(url);
        setDownloaded(true);
        setTimeout(() => setDownloaded(false), 2000);
    }, [svg]);

    // Error state: show the raw code + error message
    if (error) {
        return (
            <div className="my-4 rounded-xl border border-red-500/30 bg-red-500/5 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2 bg-red-500/10 border-b border-red-500/20">
                    <span className="text-xs font-mono text-red-400">MERMAID (render error)</span>
                    <button
                        onClick={renderDiagram}
                        className="p-1.5 rounded-lg hover:bg-red-500/20 text-red-400 transition-colors"
                        title="Retry render"
                    >
                        <RefreshCw size={14} />
                    </button>
                </div>
                <pre className="p-4 overflow-x-auto">
                    <code className="text-sm font-mono text-[var(--text-primary)] leading-relaxed">{code}</code>
                </pre>
                <div className="px-4 py-2 text-xs text-red-400 border-t border-red-500/20">
                    {error}
                </div>
            </div>
        );
    }

    // Success state: show the rendered SVG
    return (
        <div className="my-4 relative group rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface-highlight)] border-b border-[var(--border)]">
                <span className="text-xs font-mono text-[var(--text-secondary)] uppercase">diagram</span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={handleDownload}
                        className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                        title="Download SVG"
                    >
                        {downloaded ? <Check size={14} className="text-emerald-500" /> : <Download size={14} />}
                    </button>
                </div>
            </div>
            <div
                ref={containerRef}
                className="p-4 flex justify-center overflow-x-auto [&_svg]:max-w-full"
                dangerouslySetInnerHTML={{ __html: svg }}
            />
        </div>
    );
}
