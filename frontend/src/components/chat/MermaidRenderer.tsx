'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Download, Check, RefreshCw, ZoomIn, ZoomOut, Maximize, Image as ImageIcon, FileCode2 } from 'lucide-react';
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { motion, AnimatePresence } from 'framer-motion';

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
    // 1) Remove markdown backticks if present (e.g., ```mermaid ... ```)
    let cleanedText = raw.replace(/^```mermaid\n?/im, '').replace(/```$/im, '');

    // 2) Initial trim & line split
    let lines = cleanedText.trim().split('\n');
    const cleanedLines: string[] = [];

    // Process line-by-line for precision
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (!line) continue;

        // Skip pure comments
        if (line.startsWith('%%')) {
            cleanedLines.push(line);
            continue;
        }

        // --- HEURISTIC 1: Fix graph direction declarations ---
        // Sometimes AI outputs "graphTD" instead of "graph TD"
        if (/^(graph|flowchart)([A-Za-z]+)$/i.test(line)) {
            line = line.replace(/^(graph|flowchart)([A-Za-z]+)$/i, '$1 $2');
        }

        // --- HEURISTIC 2: Spaces inside simple node IDs ---
        // "F --> F 1[" → "F --> F1["
        line = line.replace(/\b([A-Za-z]+)\s+(\d+)\s*(\[|\(|\{)/g, '$1$2$3');

        // --- HEURISTIC 3: Remove spaces between node ID and opening bracket ---
        // "Node1 [" → "Node1["
        line = line.replace(/([A-Za-z0-9_]+)\s+(\[|\(|\{)/g, '$1$2');

        // --- HEURISTIC 4: Fix spaces after pipe in edge labels ---
        // "-->|Label| V[" → "-->|Label|V["
        line = line.replace(/\|\s+([A-Za-z0-9_]+)($|\[|\(|\{)/g, '|$1$2');

        // --- HEURISTIC 5: Clean invalid arrow syntax (Hallucinations) ---
        // "|>" → "|" ; "->>" → "-->" ; "-+>" → "-->" ; "<-+" → "<--"
        line = line.replace(/\|>/g, '|');
        line = line.replace(/->>/g, '-->');
        line = line.replace(/-+>/g, '-->');
        line = line.replace(/<-+/g, '<--');
        line = line.replace(/=\s*=/g, '==');
        line = line.replace(/\.\s*\./g, '..');

        // --- HEURISTIC 6: Fix unclosed/trailing labels or edges ---
        // Removes stray trailing characters that break parsing
        if (line.endsWith('|')) line = line.slice(0, -1);
        if (line.endsWith('-->')) line = line.replace(/-->$/, '');

        // --- HEURISTIC 7: Subgraph concatenation error ---
        // AI sometimes outputs "subgraph Name [Label] \n" or "subgraph Name A --> B" on one line
        // If line contains 'subgraph' but also has arrow relations, break them up
        if (/^subgraph\b/.test(line) && /-->/.test(line)) {
            const parts = line.split(/(?=[A-Za-z0-9_]+\s*-->)/);
            if (parts.length > 1) {
                cleanedLines.push(parts[0].trim());
                cleanedLines.push(...parts.slice(1).map(p => p.trim()));
                continue; // Skip the rest of loop for this line
            }
        }

        // --- HEURISTIC 8: Escape characters inside node text (Labels) ---
        // Node labels with quotes 'Node["Has "Quotes""]' fail. Need to convert inner double quotes to single or remove
        const labelRegex = /(\[|\(|\{)(".*?)"(\]|\)|\})/g;
        line = line.replace(labelRegex, (match, open, content, close) => {
            // content includes the opening quote. Let's capture the inner part.
            // If the format is ["Some text"], content is '"Some text'.
            // More robust label extractor:
            return match; // fallback
        });
        // Simpler string replace for quote collision:
        // Match `["` or `("` ... `"]` or `")`
        line = line.replace(/(\[|\()"(.*?)"(\]|\))/g, (match, open, innerText, close) => {
            // Replace inner double quotes with single quotes to avoid breaking Mermaid syntax
            const sanitizedText = innerText.replace(/"/g, "'");
            return `${open}"${sanitizedText}"${close}`;
        });

        // --- HEURISTIC 9: Fix CSS styling syntax errors ---
        // "style  B fill" → "style B fill"
        line = line.replace(/^(\s*style)\s{2,}([A-Za-z0-9_-]+)/g, '$1 $2');

        // --- FIX 7: Invalid node ID characters (hyphens) ---
        // Replace hyphens in node IDs with underscores (but not in labels)
        line = line.replace(/(^|-->|--|<-->|<--|\.->|-.->)\s*([A-Za-z][A-Za-z0-9-]*)\s*(\[|\(|\{|\))/g,
            (match, prefix, id, bracket) => {
                return `${prefix}${id.replace(/-/g, '_')}${bracket}`;
            });

        // --- HEURISTIC 13: Handle weird character encodings ---
        line = line.replace(/&amp;/g, '&');
        line = line.replace(/&lt;/g, '<');
        line = line.replace(/&gt;/g, '>');

        cleanedLines.push(line);
    }

    // --- HEURISTIC 14: Ensure balanced subgraphs ---
    const text = cleanedLines.join('\n');
    const subgraphCount = (text.match(/^subgraph\b/gm) || []).length;
    const endCount = (text.match(/^end\b/gm) || []).length;

    // If missing ends, append them
    for (let i = 0; i < (subgraphCount - endCount); i++) {
        cleanedLines.push('end');
    }

    // --- HEURISTIC 15: Fallback syntax check ---
    if (cleanedLines.length > 0 && !cleanedLines[0].match(/^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|journey|gitGraph|mindmap|timeline)/i)) {
        // Assume it's a flowchart if no type is declared
        cleanedLines.unshift('flowchart TD');
    }

    return cleanedLines.join('\n').trim();
}

export function MermaidRenderer({ code }: { code: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [downloaded, setDownloaded] = useState<'svg' | 'png' | null>(null);
    const idRef = useRef(`mermaid-${Math.random().toString(36).slice(2, 9)}`);
    const [tooltip, setTooltip] = useState<{ x: number, y: number, text: string } | null>(null);

    // Attach click events for Node Tooltips
    useEffect(() => {
        if (!svg || !containerRef.current) return;

        const svgElement = containerRef.current.querySelector('svg');
        if (!svgElement) return;

        const handleNodeClick = (e: MouseEvent) => {
            const target = e.target as Element;
            const node = target.closest('.node');
            if (node) {
                const label = node.querySelector('.label')?.textContent || node.getAttribute('id') || '';
                setTooltip({ x: e.clientX, y: e.clientY - 40, text: label.trim() });
                setTimeout(() => setTooltip(null), 2500);
            } else {
                setTooltip(null);
            }
        };

        svgElement.addEventListener('click', handleNodeClick);
        return () => svgElement.removeEventListener('click', handleNodeClick);
    }, [svg]);

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
                    primaryBorderColor: '#f97316',  // orange-500
                    lineColor: '#64748b',           // slate-500
                    secondaryColor: '#1e293b',      // slate-800
                    tertiaryColor: '#020617',       // slate-950 darker
                    edgeLabelBackground: '#0f172a',
                    nodeBorder: '#fb923c',          // orange-400
                    clusterBkg: '#020617',
                    clusterBorder: '#f97316',
                    fontSize: '16px',
                    fontFamily: 'inherit',
                } : {
                    background: 'transparent',
                    primaryColor: '#ffffff',
                    primaryTextColor: '#0f172a',
                    primaryBorderColor: '#ea580c',  // orange-600
                    lineColor: '#475569',           // slate-600
                    secondaryColor: '#f8fafc',      // slate-50
                    tertiaryColor: '#f1f5f9',       // slate-100
                    edgeLabelBackground: '#ffffff',
                    nodeBorder: '#c2410c',          // orange-700
                    clusterBkg: '#f8fafc',
                    clusterBorder: '#ea580c',
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

    const handleDownloadSvg = useCallback(() => {
        if (!svg) return;
        const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'diagram.svg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setDownloaded('svg');
        setTimeout(() => setDownloaded(null), 2000);
    }, [svg]);

    const handleDownloadPng = useCallback(() => {
        if (!svg) return;

        const img = new Image();

        img.onload = () => {
            const canvas = document.createElement('canvas');

            // Get dimensions
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svg, "image/svg+xml");
            const svgElement = svgDoc.documentElement;

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

            const padding = 40;
            const finalWidth = width + (padding * 2);
            const finalHeight = height + (padding * 2);

            canvas.width = finalWidth;
            canvas.height = finalHeight;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            // Fill background based on theme
            const isDark = document.documentElement.classList.contains('dark');
            ctx.fillStyle = isDark ? '#020617' : '#ffffff';
            ctx.fillRect(0, 0, finalWidth, finalHeight);

            // Draw SVG
            ctx.drawImage(img, padding, padding, width, height);

            // Draw Watermark
            const wText = "BENCHSIDE";
            ctx.font = "800 18px sans-serif";
            const textMetrics = ctx.measureText(wText);
            const wWidth = 22 + 8 + textMetrics.width + 10;
            const wx = finalWidth - padding - wWidth + 20;
            const wy = finalHeight - padding + 15;

            ctx.globalAlpha = 0.4;
            const logoImg = new Image();
            logoImg.onload = () => {
                ctx.drawImage(logoImg, wx, wy - 16, 22, 22);
                ctx.globalAlpha = 0.5;
                ctx.fillStyle = "#888888";
                ctx.textBaseline = "middle";

                let currentX = wx + 20;
                for (let i = 0; i < wText.length; i++) {
                    ctx.fillText(wText[i], currentX, wy - 4);
                    currentX += ctx.measureText(wText[i]).width + 2;
                }
                ctx.globalAlpha = 1.0;

                // Export to PNG
                const pngUrl = canvas.toDataURL('image/png');
                const a = document.createElement('a');
                a.href = pngUrl;
                a.download = 'diagram.png';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                setDownloaded('png');
                setTimeout(() => setDownloaded(null), 2000);
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
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={handleDownloadSvg}
                        className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-1.5"
                        title="Download SVG"
                    >
                        {downloaded === 'svg' ? <Check size={14} className="text-emerald-500" /> : <FileCode2 size={14} />}
                        <span className="text-[10px] uppercase font-bold">SVG</span>
                    </button>
                    <button
                        onClick={handleDownloadPng}
                        className="p-1.5 rounded-lg hover:bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-1.5"
                        title="Download PNG"
                    >
                        {downloaded === 'png' ? <Check size={14} className="text-emerald-500" /> : <ImageIcon size={14} />}
                        <span className="text-[10px] uppercase font-bold">PNG</span>
                    </button>
                </div>
            </div>
            <div className="relative flex justify-center overflow-hidden min-h-[300px] w-full bg-[var(--background)]">
                <TransformWrapper
                    initialScale={1}
                    minScale={0.2}
                    maxScale={4}
                    centerOnInit
                    wheel={{ step: 0.1 }}
                >
                    {({ zoomIn, zoomOut, resetTransform }: any) => (
                        <>
                            <div className="absolute top-4 right-4 z-[40] flex flex-col gap-1 bg-[var(--surface)]/80 backdrop-blur-md border border-[var(--border)] rounded-lg p-1 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={() => zoomIn()} className="p-1.5 hover:bg-[var(--surface-highlight)] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"><ZoomIn size={14} /></button>
                                <button onClick={() => zoomOut()} className="p-1.5 hover:bg-[var(--surface-highlight)] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"><ZoomOut size={14} /></button>
                                <button onClick={() => resetTransform()} className="p-1.5 hover:bg-[var(--surface-highlight)] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"><Maximize size={14} /></button>
                            </div>

                            <TransformComponent wrapperStyle={{ width: "100%", height: "100%", cursor: "grab" }} contentStyle={{ width: "100%", height: "100%", display: "flex", justifyContent: "center", alignItems: "center", padding: "40px" }}>
                                <div
                                    ref={containerRef}
                                    className="flex justify-center w-full [&_svg]:max-w-none"
                                    dangerouslySetInnerHTML={{ __html: svg }}
                                />
                            </TransformComponent>
                        </>
                    )}
                </TransformWrapper>

                {/* Tooltip */}
                <AnimatePresence>
                    {tooltip && (
                        <motion.div
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="fixed z-[60] px-3 py-1.5 bg-[var(--foreground)] text-[var(--background)] text-xs font-medium rounded-md shadow-xl pointer-events-none transform -translate-x-1/2 -translate-y-full"
                            style={{ left: tooltip.x, top: tooltip.y }}
                        >
                            {tooltip.text}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Benchside Watermark */}
                <div className="absolute bottom-2 right-3 flex items-center gap-1.5 pointer-events-none select-none opacity-40 z-10">
                    <img src="/Benchside.png" alt="Benchside" className="w-[14px] h-[14px] object-contain" />
                    <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-secondary)]">Benchside</span>
                </div>
            </div>
        </div>
    );
}
