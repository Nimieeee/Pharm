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
 *  - Syntax auto-correction for AI generated spaces
 */

function cleanMermaidSyntax(raw: string): string {
    return raw
        // Fix spaces between node ID and the opening bracket/parentheses e.g. A ["Text"] -> A["Text"]
        .replace(/([A-Za-z0-9_]+)\s+\[/g, '$1[')
        .replace(/([A-Za-z0-9_]+)\s+\(/g, '$1(')
        .replace(/([A-Za-z0-9_]+)\s+\{/g, '$1{')
        .replace(/([A-Za-z0-9_]+)\s+\>/g, '$1>')
        .trim();
}

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
                theme: 'base',
                themeVariables: isDark ? {
                    background: 'transparent',
                    primaryColor: '#1e293b',
                    primaryTextColor: '#f8fafc',
                    primaryBorderColor: '#3b82f6',
                    lineColor: '#94a3b8',
                    secondaryColor: '#334155',
                    tertiaryColor: '#0f172a',
                    edgeLabelBackground: '#1e293b',
                    nodeBorder: '#3b82f6',
                    clusterBkg: '#0f172a',
                    clusterBorder: '#3b82f6',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                } : {
                    background: 'transparent',
                    primaryColor: '#ffffff',
                    primaryTextColor: '#0f172a',
                    primaryBorderColor: '#2563eb',
                    lineColor: '#64748b',
                    secondaryColor: '#f8fafc',
                    tertiaryColor: '#e2e8f0',
                    edgeLabelBackground: '#ffffff',
                    nodeBorder: '#2563eb',
                    clusterBkg: '#f1f5f9',
                    clusterBorder: '#2563eb',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                },
                securityLevel: 'loose',
                fontFamily: 'inherit',
            });

            const cleanedCode = cleanMermaidSyntax(code);
            const { svg: renderedSvg } = await mermaid.render(idRef.current, cleanedCode);
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

        // Inject watermark into the SVG native code before download
        let svgWithWatermark = svg;
        const watermarkNode = `
            <g transform="translate(100%, 100%)">
               <text x="-15" y="-15" text-anchor="end" fill="#888888" opacity="0.6" font-size="14px" font-weight="900" font-family="sans-serif" letter-spacing="2px">BENCHSIDE</text>
            </g>`;
        svgWithWatermark = svg.replace(/<\/svg>$/, `${watermarkNode}</svg>`);

        const blob = new Blob([svgWithWatermark], { type: 'image/svg+xml' });
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
            <div className="relative p-6 px-8 pb-10 flex justify-center overflow-x-auto min-h-[140px] w-full">
                <div
                    ref={containerRef}
                    className="flex justify-center w-full [&_svg]:w-full [&_svg]:max-w-4xl [&_svg]:h-auto transition-all"
                    dangerouslySetInnerHTML={{ __html: svg }}
                />

                {/* Benchside Watermark */}
                <div className="absolute bottom-2 right-3 flex items-center gap-1.5 pointer-events-none select-none opacity-40">
                    <img src="/Benchside.png" alt="Benchside" className="w-[14px] h-[14px] object-contain" />
                    <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-secondary)]">Benchside</span>
                </div>
            </div>
        </div>
    );
}
