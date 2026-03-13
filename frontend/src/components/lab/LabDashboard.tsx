'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FlaskConical, Download, Share2, Search, AlertCircle, CheckCircle, Loader2, Clipboard, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/config/api';
import { getRandomDrugs, DrugSuggestion } from '@/constants/drugPool';
import { useTheme } from '@/lib/theme-context';

// Shared & New Components
import HubLayout from '../shared/HubLayout';
import SkeletonLoader from '../shared/SkeletonLoader';
import ADMETPropertyCard, { ADMETProperty } from './ADMETPropertyCard';
import MoleculePreview from './MoleculePreview';
import StreamingLogo from '../chat/StreamingLogo';

interface ADMETResult {
  success: boolean;
  smiles: string;
  report: string;
  include_svg: boolean;
}

interface ParsedReport {
  categories: {
    '吸收 (Absorption)'?: ADMETProperty[];
    '分布 (Distribution)'?: ADMETProperty[];
    '代谢 (Metabolism)'?: ADMETProperty[];
    '排泄 (Excretion)'?: ADMETProperty[];
    '毒性 (Toxicity)'?: ADMETProperty[];
    [key: string]: ADMETProperty[] | undefined;
  };
  summary: string[];
}

export default function LabDashboard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  const [smiles, setSmiles] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ADMETResult | null>(null);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState<DrugSuggestion[]>([]);

  // Load random drug suggestions on mount
  useEffect(() => {
    setSuggestions(getRandomDrugs(4));
  }, []);

  const handleRefreshSuggestions = () => {
    setSuggestions(getRandomDrugs(4));
  };

  // Parse the markdown report into structured data
  const parsedData = useMemo(() => {
    if (!result?.report) return null;

    const data: ParsedReport = { categories: {}, summary: [] };
    let currentCategory = '';
    
    const lines = result.report.split('\n');
    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed) return;

      if (trimmed.startsWith('## ') || trimmed.startsWith('### ')) {
        const catName = trimmed.replace(/^#+\s+/, '');
        if (catName.match(/吸收|分布|代谢|排泄|毒性|Absorption|Distribution|Metabolism|Excretion|Toxicity/)) {
          currentCategory = catName;
          data.categories[currentCategory] = [];
        } else {
          data.summary.push(trimmed);
        }
      } else if (trimmed.startsWith('- **') && currentCategory) {
        const match = trimmed.match(/- \*\*(.+?)\*\*: (.+)/);
        if (match) {
          const name = match[1];
          const valueStr = match[2];
          
          let status: any = 'neutral';
          if (valueStr.includes('✅') || valueStr.toLowerCase().includes('good') || valueStr.toLowerCase().includes('high')) status = 'success';
          if (valueStr.includes('⚠️') || valueStr.toLowerCase().includes('moderate') || valueStr.toLowerCase().includes('warning')) status = 'warning';
          if (valueStr.includes('❌') || valueStr.toLowerCase().includes('poor') || valueStr.toLowerCase().includes('low') || valueStr.toLowerCase().includes('toxic')) status = 'danger';

          data.categories[currentCategory]?.push({
            name,
            value: valueStr.replace(/[✅⚠️❌]/g, '').trim(),
            status
          });
        }
      } else if (!currentCategory && trimmed.length > 0) {
        data.summary.push(trimmed);
      }
    });

    return data;
  }, [result]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (!smiles.trim()) {
      toast.error('Please enter a SMILES string');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('sb-access-token') : null;

      const response = await fetch(`${API_BASE_URL}/api/v1/admet/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          smiles: smiles.trim(),
          include_svg: true,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Analysis failed');
      }

      const data = await response.json();
      setResult(data);
      toast.success('ADMET analysis complete');
    } catch (err: any) {
      setError(err.message);
      toast.error(`Analysis failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('sb-access-token') : null;
      const response = await fetch(`${API_BASE_URL}/api/v1/admet/export?smiles=${encodeURIComponent(smiles)}`, {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `admet_${smiles.slice(0, 15)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('CSV exported');
    } catch (err: any) {
      toast.error(`Export failed: ${err.message}`);
    }
  };

  return (
    <HubLayout 
      title="Molecular Lab" 
      subtitle="Predict drug absorption, distribution, metabolism, excretion, and toxicity"
      icon={FlaskConical}
      accentColor="amber"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Input and Molecule Preview */}
        <div className="lg:col-span-4 space-y-6">
          <section className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Upload className="w-3.5 h-3.5" />
              Molecule Input
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  value={smiles}
                  onChange={(e) => setSmiles(e.target.value)}
                  placeholder="Enter SMILES structure..."
                  className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/10 text-white placeholder:text-slate-600 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 outline-none transition-all pr-12"
                />
                <button 
                  type="submit"
                  disabled={isLoading}
                  className="absolute right-2 top-2 p-2 rounded-lg bg-amber-500 text-black hover:bg-amber-400 disabled:opacity-50 transition-colors"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                </button>
              </div>

              <div className="flex flex-wrap gap-2">
                {suggestions.map((mol) => (
                  <button
                    key={mol.name}
                    type="button"
                    onClick={() => { setSmiles(mol.smiles); }}
                    className="text-[10px] px-2.5 py-1.25 rounded-full bg-white/5 border border-white/5 text-slate-400 hover:bg-white/10 hover:text-white transition-all"
                  >
                    {mol.name}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={handleRefreshSuggestions}
                  className="text-[10px] px-2.5 py-1.25 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 hover:bg-amber-500/30 hover:text-amber-300 transition-all"
                >
                  ↻ More
                </button>
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button 
                  type="button"
                  onClick={async () => {
                    const text = await navigator.clipboard.readText();
                    if (text) { setSmiles(text); toast.info('SMILES pasted from clipboard'); }
                  }}
                  className="flex-1 flex items-center justify-center gap-2 p-2.5 rounded-xl bg-white/5 border border-white/5 text-xs text-slate-400 hover:bg-white/10 hover:text-white transition-all"
                >
                  <Clipboard className="w-3.5 h-3.5" />
                  Paste
                </button>
                <button 
                  type="button"
                  className="flex-1 flex items-center justify-center gap-2 p-2.5 rounded-xl bg-white/5 border border-white/5 text-xs text-slate-400 hover:bg-white/10 hover:text-white transition-all"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Upload
                </button>
              </div>
            </form>
          </section>

          <MoleculePreview smiles={smiles} />
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center py-20 opacity-80 select-none"
              >
                <StreamingLogo className="w-24 h-24 mb-6" />
                <h3 className="text-xl font-medium text-amber-500 animate-pulse">Analyzing Molecule...</h3>
                <p className="text-sm max-w-xs text-center mt-2 text-slate-400">Processing structural features across 119 ADMET endpoints</p>
              </motion.div>
            ) : error ? (
              <motion.div 
                key="error"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-8 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-md text-center"
              >
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold text-red-400 mb-2">Analysis Failed</h3>
                <p className="text-sm text-red-500/70 max-w-md mx-auto">{error}</p>
                <button 
                  onClick={() => handleSubmit()}
                  className="mt-6 px-6 py-2 rounded-xl bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-all text-sm font-medium"
                >
                  Retry Analysis
                </button>
              </motion.div>
            ) : result ? (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                {/* Result Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-green-500/20 text-green-500">
                      <CheckCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>ADMET Profile Complete</h2>
                      <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Computational predictions based on structural features</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={handleExportCSV}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium transition-all"
                    >
                      <Download className="w-4 h-4" />
                      CSV
                    </button>
                    <button 
                      onClick={() => { navigator.clipboard.writeText(result.report); toast.success('Report copied'); }}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-sm font-medium transition-all"
                    >
                      <Share2 className="w-4 h-4" />
                      Share
                    </button>
                  </div>
                </div>

                {/* Property Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {parsedData && Object.entries(parsedData.categories).map(([name, props], i) => (
                    <ADMETPropertyCard 
                      key={name}
                      category={name}
                      properties={props || []}
                      icon={FlaskConical}
                    />
                  ))}
                </div>

                {/* Insights / Summary */}
                {parsedData && parsedData.summary.length > 0 && (
                  <section className="p-6 rounded-2xl bg-amber-500/5 border border-amber-500/10 backdrop-blur-md">
                    <h3 className="text-sm font-semibold text-amber-500 uppercase tracking-wider mb-4">Key Insights</h3>
                    <div className="space-y-3">
                      {parsedData.summary.map((line, i) => (
                        <p key={i} className="text-sm text-slate-300 leading-relaxed">
                          {line.replace(/^#+\s+/, '')}
                        </p>
                      ))}
                    </div>
                  </section>
                )}
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center py-20 opacity-30 select-none"
              >
                <FlaskConical className="w-24 h-24 mb-6" />
                <h3 className="text-xl font-medium">Ready for Analysis</h3>
                <p className="text-sm max-w-xs text-center mt-2">Enter a SMILES string on the left to begin predicting pharmacological properties</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </HubLayout>
  );
}
