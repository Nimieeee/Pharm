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
    // Process line-by-line for precision
    const lines = raw.split('\n');
    const cleaned = lines.map(line => {
        // Skip lines inside quoted labels (don't break label text)
        // We only fix structural syntax, not content inside ["..."]

        // --- FIX 1: Spaces inside node IDs ---
        // e.g. "F --> F 1[" → "F --> F1["  or  "-->|label| V[" → "-->|label| V["
        // Match: word boundary, then uppercase letter(s), space(s), digit(s), then bracket
        line = line.replace(/\b([A-Za-z]+)\s+(\d+)\s*(\[|\(|\{)/g, '$1$2$3');

        // --- FIX 2: Spaces between node ID and opening bracket ---
        // e.g. "AC [" → "AC[",  "AF [" → "AF["
        line = line.replace(/([A-Za-z0-9_]+)\s+(\[")/g, '$1$2');
        line = line.replace(/([A-Za-z0-9_]+)\s+(\[)/g, '$1$2');
        line = line.replace(/([A-Za-z0-9_]+)\s+(\()/g, '$1$2');
        line = line.replace(/([A-Za-z0-9_]+)\s+(\{)/g, '$1$2');
        line = line.replace(/([A-Za-z0-9_]+)\s+(\))/g, '$1$2');

        // --- FIX 3: Spaces after pipe closing in edge labels ---
        // e.g. "-->|Kidney| V[" → "-->|Kidney|V["
        line = line.replace(/\|\s+([A-Za-z0-9_]+)(\[|\(|\{)/g, '|$1$2');

        // --- FIX 4: Hallucinated arrow heads ---
        // e.g. "-->|Label|> B[" → "-->|Label| B["
        line = line.replace(/\|>/g, '|');
        line = line.replace(/->>/g, '-->');

        // --- FIX 5: Invalid arrow patterns ---
        // Fix multiple dashes or dots
        line = line.replace(/-+>/g, '-->');
        line = line.replace(/<-+/g, '<--');
        line = line.replace(/=\s*=/g, '==');
        line = line.replace(/\.\s*\./g, '..');

        // --- FIX 6: Style line fixes ---
        // 6a. Extra spaces between "style" and node ID: "style  B fill" → "style B fill"
        line = line.replace(/^(\s*style)\s{2,}([A-Za-z0-9_-]+)/g, '$1 $2');
        // 6b. Spaces inside hex color values: "fill:# f88" or "fill:#f 88" → "fill:#f88"
        line = line.replace(/(fill|stroke|color):#\s+([a-fA-F0-9])/g, '$1:#$2');
        line = line.replace(/(fill|stroke|color):#([a-fA-F0-9]+)\s+([a-fA-F0-9]+)/g, '$1:#$2$3');
        // 6c. Spaces around colon in style props: "fill: #fff" → "fill:#fff"
        line = line.replace(/(fill|stroke|color)\s*:\s+#/g, '$1:#');
        // 6d. Spaces around comma in style defs: "#fff, stroke" → "#fff,stroke"
        line = line.replace(/(fill|stroke|color):#[a-fA-F0-9]+,\s+(fill|stroke|color)/g,
            (match) => match.replace(', ', ','));

        // --- FIX 7: Invalid node ID characters (hyphens) ---
        // Replace hyphens in node IDs with underscores (but not in labels)
        line = line.replace(/(^|-->|--|<-->|<--|\.->|-.->)\s*([A-Za-z][A-Za-z0-9-]*)\s*(\[|\(|\{|\))/g,
            (match, prefix, id, bracket) => {
                return `${prefix}${id.replace(/-/g, '_')}${bracket}`;
            });

        return line;
    });

    return cleaned.join('\n').trim();
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
                    primaryBorderColor: '#6366f1',  // orange-500
                    lineColor: '#64748b',           // slate-500
                    secondaryColor: '#1e293b',      // slate-800
                    tertiaryColor: '#020617',       // slate-950 darker
                    edgeLabelBackground: '#0f172a',
                    nodeBorder: '#818cf8',          // orange-400
                    clusterBkg: '#020617',
                    clusterBorder: '#6366f1',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                } : {
                    background: 'transparent',
                    primaryColor: '#ffffff',
                    primaryTextColor: '#0f172a',
                    primaryBorderColor: '#4f46e5',  // orange-600
                    lineColor: '#475569',           // slate-600
                    secondaryColor: '#f8fafc',      // slate-50
                    tertiaryColor: '#f1f5f9',       // slate-100
                    edgeLabelBackground: '#ffffff',
                    nodeBorder: '#4338ca',          // orange-700
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


        // Parse SVG to get dimensions
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svg, "image/svg+xml");
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

            // Draw Benchside watermark at bottom right
            const wText = "BENCHSIDE";
            ctx.font = "800 12px sans-serif";
            const textMetrics = ctx.measureText(wText);
            const wWidth = 14 + 6 + textMetrics.width + 10;
            const wx = finalWidth - padding - wWidth + 20;
            const wy = finalHeight - padding + 15;

            ctx.globalAlpha = 0.4;
            const logoImg = new Image();
            logoImg.onload = () => {
                ctx.drawImage(logoImg, wx, wy - 11, 14, 14);

                ctx.globalAlpha = 0.5;
                ctx.fillStyle = "#888888";
                ctx.textBaseline = "middle";

                let currentX = wx + 20;
                for (let i = 0; i < wText.length; i++) {
                    ctx.fillText(wText[i], currentX, wy - 4);
                    currentX += ctx.measureText(wText[i]).width + 2;
                }
                ctx.globalAlpha = 1.0;

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
            logoImg.src = "/Benchside.png";
        };

        // Fix nested quotes and encoded characters in SVG string for Image src
        const encodedSvg = encodeURIComponent(svg)
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
