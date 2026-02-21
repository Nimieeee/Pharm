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
                    primaryColor: '#0f172a',        // slate-950
                    primaryTextColor: '#f8fafc',
                    primaryBorderColor: '#6366f1',  // indigo-500
                    lineColor: '#64748b',           // slate-500
                    secondaryColor: '#1e293b',      // slate-800
                    tertiaryColor: '#020617',       // slate-950 darker
                    edgeLabelBackground: '#0f172a',
                    nodeBorder: '#818cf8',          // indigo-400
                    clusterBkg: '#020617',
                    clusterBorder: '#6366f1',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                } : {
                    background: 'transparent',
                    primaryColor: '#ffffff',
                    primaryTextColor: '#0f172a',
                    primaryBorderColor: '#4f46e5',  // indigo-600
                    lineColor: '#475569',           // slate-600
                    secondaryColor: '#f8fafc',      // slate-50
                    tertiaryColor: '#f1f5f9',       // slate-100
                    edgeLabelBackground: '#ffffff',
                    nodeBorder: '#4338ca',          // indigo-700
                    clusterBkg: '#f8fafc',
                    clusterBorder: '#4f46e5',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                },
                flowchart: { htmlLabels: false },
                sequence: { showSequenceNumbers: true },
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

        // Base64 encoded Benchside logo
        const benchsideLogoB64 = "data:image/png;base64,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7fNq9+1P/T5d625/B/9gP0Tvw90/Hmr/51kP/d1+zv+e//c92P34N8P91kP/HnufvR/0h15rffAfvcf+6nffgXfg7f7v//Xh/aD30r+/u/+h97t/tN/tXvzDvgM/3/vQv+E//s09oH9wXw/x2A/Xfrt37Qf3b92Peu+1n/I/8T5//wveB7bvn/896D124N71P/n6fv2nfn8/+1+r3/h/D7+/B9x3+hHw+/Gf6452f//D//j34E+1W++386Tf9/fR+/U18L7w++15/3/u3W/vB/uT9tTjfeje29lX987H7j+/u9817E17N7rXtvf+rN6J3T3s9/k7+AftN/P23ffv9xO0vTj1/W/3B22X+63920M/8v35u233AflN/ff333t3u794P72fbD3tPuxerX//qD/oR+6h/1n0l/2L/w/eU/ee/O9/d/D+u3v1vun5gG/P/9vXQ//5n3rPeo897B7/iHvdX8/25H/Yf/H22/2312//HvcL8A68/w2N7sM17sVz1wfePfv/BvyN5+/g/bYPej/E/3u9/Uv/4f/fHnL/8//cO/CP2/37R9wv4A/H/tC+t96R312/RfvIf+H6+309/kI0hBCEEAQhBEEIQhCEEAQhCEEQQhCEEAQhCIIQhCAIQQhBEIIgrCH+H+JvTfI/gX95AAAAAElFTkSuQmCC";

        const watermarkNode = `
                <g class="benchside-watermark" transform="translate(10, 20)">
                    <image href="${benchsideLogoB64}" x="0" y="0" width="14" height="14" opacity="0.4" />
                    <text x="20" y="11" text-anchor="start" fill="#888888" opacity="0.6" font-size="12px" font-weight="800" font-family="sans-serif" letter-spacing="2px">BENCHSIDE</text>
                </g>`;
        const svgWithWatermark = svg.replace(/<\/svg>$/, `${watermarkNode}</svg>`);

        // Parse SVG to get dimensions
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgWithWatermark, "image/svg+xml");
        const svgElement = svgDoc.documentElement;

        // Force explicit width/height to avoid cutoff in canvas
        let width = parseInt(svgElement.getAttribute('width') || '0', 10);
        let height = parseInt(svgElement.getAttribute('height') || '0', 10);

        if (!width || !height) {
            const viewBox = svgElement.getAttribute('viewBox');
            if (viewBox) {
                const parts = viewBox.split(/[ ,]+/);
                width = parseInt(parts[2], 10);
                height = parseInt(parts[3], 10);
            } else {
                const rect = containerRef.current?.getBoundingClientRect();
                width = rect?.width || 800;
                height = rect?.height || 600;
            }
        }

        // Add padding
        const padding = 40;
        const finalWidth = width + (padding * 2);
        const finalHeight = height + (padding * 2);

        // Create canvas for JPEG conversion
        const canvas = document.createElement('canvas');
        canvas.width = finalWidth;
        canvas.height = finalHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Fill background
        const isDark = document.documentElement.classList.contains('dark');
        ctx.fillStyle = isDark ? '#020617' : '#ffffff';
        ctx.fillRect(0, 0, finalWidth, finalHeight);

        const img = new Image();
        img.onload = () => {
            // Draw SVG onto canvas with padding
            ctx.drawImage(img, padding, padding, width, height);

            // Export to JPEG
            const jpegUrl = canvas.toDataURL('image/jpeg', 0.95);
            const a = document.createElement('a');
            a.href = jpegUrl;
            a.download = 'diagram.jpg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            URL.revokeObjectURL(url);
            setDownloaded(true);
            setTimeout(() => setDownloaded(false), 2000);
        };

        // Fix nested quotes and encoded characters in SVG string for Image src
        const encodedSvg = encodeURIComponent(svgWithWatermark)
            .replace(/'/g, '%27')
            .replace(/"/g, '%22');
        const url = `data:image/svg+xml;charset=utf-8,${encodedSvg}`;
        img.src = url;
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
