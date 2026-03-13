'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image as ImageIcon, Download, Maximize2, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '@/config/api';

interface MoleculePreviewProps {
  smiles: string;
}

export default function MoleculePreview({ smiles }: MoleculePreviewProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!smiles || typeof smiles !== 'string') {
      setSvg(null);
      setError(null);
      return;
    }

    const fetchSvg = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Ensure SMILES is properly trimmed and encoded
        const trimmedSmiles = smiles.trim();
        if (!trimmedSmiles) {
          setError('Empty SMILES string');
          setIsLoading(false);
          return;
        }

        const encodedSmiles = encodeURIComponent(trimmedSmiles);
        const response = await fetch(`${API_BASE_URL}/api/v1/admet/svg?smiles=${encodedSmiles}`);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to load molecule structure: ${response.status} - ${errorText}`);
        }

        const data = await response.text();
        setSvg(data);
      } catch (err: any) {
        setError(err.message);
        console.error('Molecule preview error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSvg();
  }, [smiles]);

  const handleDownload = () => {
    if (!svg) return;
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `molecule_${smiles.slice(0, 10)}.svg`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-slate-400" />
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Molecular Structure
          </h3>
        </div>
        
        {svg && (
          <button 
            onClick={handleDownload}
            className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
            title="Download SVG"
          >
            <Download className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex-1 flex items-center justify-center min-h-[250px] relative rounded-xl bg-black/20 border border-white/5 overflow-hidden">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3"
            >
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <span className="text-xs text-slate-500">Rendering structure...</span>
            </motion.div>
          ) : error ? (
            <motion.div 
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="px-4 text-center"
            >
              <p className="text-xs text-red-500 mb-1">Failed to render structure</p>
              <p className="text-[10px] text-slate-600 font-mono">{smiles}</p>
            </motion.div>
          ) : svg ? (
            <motion.div 
              key="svg"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full h-full flex items-center justify-center p-8 invert dark:invert-0 brightness-110"
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          ) : (
            <div className="flex flex-col items-center gap-2 opacity-20">
              <ImageIcon className="w-12 h-12" />
              <span className="text-xs">No molecule active</span>
            </div>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-black/20 border border-white/5">
        <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">SMILES string</p>
        <p className="text-xs font-mono text-blue-400 truncate">{smiles || 'N/A'}</p>
      </div>
    </div>
  );
}
