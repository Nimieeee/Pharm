'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FlaskConical, Download, Share2, Search, AlertCircle, CheckCircle, Loader2, Clipboard, Upload, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/config/api';
import { getRandomDrugs, DrugSuggestion } from '@/constants/drugPool';

// Shared & New Components
import HubLayout from '../shared/HubLayout';
import SkeletonLoader from '../shared/SkeletonLoader';
import { LoadingAnimation } from '../shared/LoadingAnimation';
import ADMETPropertyCard from './ADMETPropertyCard';
import MoleculePreview from './MoleculePreview';
import StreamingLogo from '../chat/StreamingLogo';

interface ADMETProperty {
  name: string;
  key: string;
  value: any;
  status: 'success' | 'warning' | 'danger' | 'neutral';
  interpretation: string;
  unit?: string;
}

interface ADMETCategory {
  name: string;
  properties: ADMETProperty[];
}

interface ADMETResult {
  success: boolean;
  smiles?: string;
  categories: ADMETCategory[];
  ai_interpretation: string;
  report_markdown: string;
  molecule_name?: string;
  error?: string;
}

interface BatchADMETResponse {
  total_submitted: number;
  capped_at: number;
  results: ADMETResult[];
}

export default function LabDashboard() {
  const [smiles, setSmiles] = useState('');
  const [batchSmiles, setBatchSmiles] = useState('');
  const [inputType, setInputType] = useState<'single' | 'batch' | 'sdf'>('single');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ADMETResult | null>(null);
  const [batchResults, setBatchResults] = useState<ADMETResult[]>([]);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState<DrugSuggestion[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load random drug suggestions on mount
  useEffect(() => {
    setSuggestions(getRandomDrugs(4));
  }, []);

  const handleRefreshSuggestions = () => {
    setSuggestions(getRandomDrugs(4));
  };

  // No longer parsing markdown, using structured JSON

  const handleAnalyze = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (inputType === 'single') {
      if (!smiles.trim()) {
        toast.error('Please enter a SMILES string');
        return;
      }
      await analyzeSingle();
    } else if (inputType === 'batch') {
      if (!batchSmiles.trim()) {
        toast.error('Please enter list of SMILES');
        return;
      }
      await analyzeBatch();
    } else if (inputType === 'sdf') {
      if (!selectedFile) {
        toast.error('Please select an SDF file');
        return;
      }
      await analyzeSDF();
    }
  };

  const analyzeSingle = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);
    setBatchResults([]);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/v1/admet/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ smiles: smiles.trim(), include_svg: true }),
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

  const analyzeBatch = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);
    setBatchResults([]);

    const smilesList = batchSmiles.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
    if (smilesList.length === 0) {
      setIsLoading(false);
      toast.error('No valid SMILES found');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/v1/admet/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ smiles_list: smilesList }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Batch analysis failed');
      }

      const data: BatchADMETResponse = await response.json();
      setBatchResults(data.results);
      toast.success(`Batch analysis complete: ${data.results.length} compounds processed`);
    } catch (err: any) {
      setError(err.message);
      toast.error(`Batch analysis failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeSDF = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError('');
    setResult(null);
    setBatchResults([]);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE_URL}/api/v1/admet/batch`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'SDF analysis failed');
      }

      const data: BatchADMETResponse = await response.json();
      setBatchResults(data.results);
      toast.success(`SDF analysis complete: ${data.results.length} compounds processed`);
    } catch (err: any) {
      setError(err.message);
      toast.error(`SDF analysis failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.sdf')) {
        toast.error('Please upload an .sdf file');
        return;
      }
      setSelectedFile(file);
      setInputType('sdf');
    }
  };

  const handleExportBatchCSV = async () => {
    if (batchResults.length === 0) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/v1/admet/export/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ results: batchResults }),
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
          <section className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex items-center gap-2">
                <Upload className="w-3.5 h-3.5" />
                Molecule Input
              </h3>
              <div className="flex bg-[var(--surface-highlight)] rounded-lg p-1">
                {(['single', 'batch', 'sdf'] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setInputType(type)}
                    className={`px-2 py-1 text-[10px] font-medium rounded-md transition-all ${
                      inputType === type 
                        ? 'bg-amber-500 text-white shadow-sm' 
                        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    {type === 'single' ? 'Single' : type === 'batch' ? 'Batch' : 'SDF'}
                  </button>
                ))}
              </div>
            </div>
            
            <form onSubmit={handleAnalyze} className="space-y-4">
              {inputType === 'single' ? (
                <div className="relative">
                  <input
                    type="text"
                    value={smiles}
                    onChange={(e) => setSmiles(e.target.value)}
                    placeholder="Enter SMILES structure..."
                    className="w-full px-4 py-3 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 outline-none transition-all pr-12"
                  />
                  <button 
                    type="submit"
                    disabled={isLoading}
                    className="absolute right-2 top-2 p-2 rounded-lg bg-amber-500 text-white hover:bg-amber-400 disabled:opacity-50 transition-colors"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  </button>
                </div>
              ) : inputType === 'batch' ? (
                <div className="space-y-2">
                  <textarea
                    value={batchSmiles}
                    onChange={(e) => setBatchSmiles(e.target.value)}
                    placeholder="Enter SMILES list (one per line or comma-separated)..."
                    className="w-full h-32 px-4 py-3 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 outline-none transition-all resize-none font-mono text-xs"
                  />
                  <button 
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-10 rounded-xl bg-amber-500 text-white font-medium hover:bg-amber-400 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                    Analyze Batch
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div 
                    onClick={() => document.getElementById('sdf-upload')?.click()}
                    className={`w-full h-32 border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer transition-all ${
                      selectedFile ? 'border-amber-500 bg-amber-500/5' : 'border-[var(--border)] hover:border-amber-500/50 hover:bg-amber-500/5'
                    }`}
                  >
                    <Upload className={`w-8 h-8 ${selectedFile ? 'text-amber-500' : 'text-[var(--text-secondary)]'}`} />
                    <span className="text-xs font-medium text-[var(--text-secondary)]">
                      {selectedFile ? selectedFile.name : 'Click to select .SDF file'}
                    </span>
                    <input 
                      id="sdf-upload" 
                      type="file" 
                      accept=".sdf" 
                      onChange={handleFileChange} 
                      className="hidden" 
                    />
                  </div>
                  <button 
                    type="submit"
                    disabled={isLoading || !selectedFile}
                    className="w-full h-10 rounded-xl bg-amber-500 text-white font-medium hover:bg-amber-400 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                    Analyze SDF
                  </button>
                </div>
              )}

              {inputType === 'single' && (
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((mol) => (
                    <button
                      key={mol.name}
                      type="button"
                      onClick={() => { setSmiles(mol.smiles); }}
                      className="text-[10px] px-2.5 py-1.25 rounded-full bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all"
                    >
                      {mol.name}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={handleRefreshSuggestions}
                    className="text-[10px] px-2.5 py-1.25 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-600 hover:bg-amber-500/30 hover:text-amber-700 transition-all"
                  >
                    ↻ More
                  </button>
                </div>
              )}

              <div className="pt-2 flex items-center gap-2">
                <button 
                  type="button"
                  onClick={async () => {
                    try {
                      const text = await navigator.clipboard.readText();
                      if (text) { 
                        if (inputType === 'single') setSmiles(text); 
                        else setBatchSmiles(text);
                        toast.info('Pasted from clipboard'); 
                      }
                    } catch (err) {
                      toast.error('Could not read clipboard');
                    }
                  }}
                  className="flex-1 flex items-center justify-center gap-2 p-2.5 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all"
                >
                  <Clipboard className="w-3.5 h-3.5" />
                  Paste
                </button>
              </div>
            </form>
          </section>

          {inputType === 'single' && <MoleculePreview smiles={smiles} />}
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <LoadingAnimation label="Calculating ADMET predictions across 119 endpoints..." />
            ) : error ? (
              <motion.div
                key="error"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-8 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-md text-center"
              >
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold text-red-600 mb-2">Analysis Failed</h3>
                <p className="text-sm text-red-600/70 max-w-md mx-auto">{error}</p>
                <button
                  onClick={() => handleAnalyze()}
                  className="mt-6 px-6 py-2 rounded-xl bg-red-500/20 text-red-600 hover:bg-red-500/30 transition-all text-sm font-medium"
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
                      <h2 className="text-xl font-bold text-[var(--text-primary)]">ADMET Profile Complete</h2>
                      <p className="text-sm text-[var(--text-secondary)] truncate max-w-md">Predictions for {result.smiles}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => { 
                        const blob = new Blob([result.report_markdown], { type: 'text/markdown' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `admet_report.md`;
                        a.click();
                        window.URL.revokeObjectURL(url);
                      }}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] hover:bg-[var(--surface-hover)] text-sm font-medium transition-all"
                    >
                      <Download className="w-4 h-4" />
                      Markdown
                    </button>
                    <button
                      onClick={() => { navigator.clipboard.writeText(result.report_markdown); toast.success('Report copied'); }}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] hover:bg-[var(--surface-hover)] text-sm font-medium transition-all"
                    >
                      <Share2 className="w-4 h-4" />
                      Copy
                    </button>
                  </div>
                </div>

                {/* AI Interpretation */}
                {result.ai_interpretation && (
                  <section className="p-6 rounded-2xl bg-gradient-to-r from-amber-500/10 to-blue-500/10 border border-amber-500/20 backdrop-blur-md">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="w-5 h-5 text-amber-500" />
                      <h3 className="text-sm font-semibold text-amber-600 uppercase tracking-wider">Medicinal Chemistry Insights</h3>
                    </div>
                    <p className="text-base text-[var(--text-primary)] leading-relaxed">
                      {result.ai_interpretation}
                    </p>
                  </section>
                )}

                {/* Property Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.categories.map((cat) => (
                    <ADMETPropertyCard 
                      key={cat.name}
                      category={cat.name}
                      properties={cat.properties}
                      icon={FlaskConical}
                    />
                  ))}
                </div>
              </motion.div>
            ) : batchResults.length > 0 ? (
              <motion.div 
                key="batch-results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-[var(--text-primary)]">Batch Results ({batchResults.length})</h2>
                  <button
                    onClick={handleExportBatchCSV}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 text-white hover:bg-amber-400 text-sm font-medium transition-all shadow-md"
                  >
                    <Download className="w-4 h-4" />
                    Download CSV
                  </button>
                </div>

                <div className="space-y-4">
                  {batchResults.map((res, idx) => (
                    <details key={idx} className="group rounded-2xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
                      <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-[var(--surface-highlight)] transition-all">
                        <div className="flex items-center gap-4">
                          <span className="w-6 h-6 rounded-full bg-[var(--surface-highlight)] flex items-center justify-center text-[10px] font-bold text-[var(--text-secondary)]">
                            {idx + 1}
                          </span>
                          <span className="font-mono text-xs text-[var(--text-secondary)] truncate max-w-[200px] md:max-w-md">
                            {res.smiles || res.molecule_name || 'Unknown Compound'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          {res.success ? (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-500 font-medium">Success</span>
                          ) : (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 font-medium">Failed</span>
                          )}
                          <svg className="w-4 h-4 text-[var(--text-secondary)] group-open:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      </summary>
                      <div className="p-4 border-t border-[var(--border)] bg-[var(--background)]">
                        {res.success ? (
                          <div className="space-y-6">
                            <div className="max-w-sm mx-auto">
                              <MoleculePreview smiles={res.smiles || ''} />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {res.categories.map((cat) => (
                                <ADMETPropertyCard 
                                  key={cat.name}
                                  category={cat.name}
                                  properties={cat.properties}
                                  icon={FlaskConical}
                                />
                              ))}
                            </div>
                            {res.ai_interpretation && (
                              <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10">
                                <h4 className="text-xs font-bold text-amber-600 uppercase mb-2">AI Insights</h4>
                                <p className="text-sm text-[var(--text-primary)]">{res.ai_interpretation}</p>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="p-4 flex items-center gap-3 bg-red-500/5 text-red-500 rounded-xl border border-red-500/10">
                            <AlertCircle className="w-4 h-4" />
                            <p className="text-sm">{res.error || 'Unknown error during analysis'}</p>
                          </div>
                        )}
                      </div>
                    </details>
                  ))}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center py-20 opacity-30 select-none"
              >
                <FlaskConical className="w-24 h-24 mb-6" />
                <h3 className="text-xl font-medium text-[var(--text-primary)]">Ready for Analysis</h3>
                <p className="text-sm max-w-xs text-center mt-2 text-[var(--text-secondary)]">
                  {inputType === 'single' 
                    ? 'Enter a SMILES string on the left to begin predicting pharmacological properties' 
                    : inputType === 'batch'
                    ? 'Paste your SMILES list and click Analyze Batch'
                    : 'Upload an .SDF file and click Analyze SDF'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </HubLayout>
  );
}
