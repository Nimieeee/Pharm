'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dna, Upload, Search, FileText, AlertCircle, CheckCircle, Loader2, Pill, TrendingUp, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';

// Shared & New Components
import HubLayout from '../shared/HubLayout';
import SkeletonLoader from '../shared/SkeletonLoader';
import UploadZone from './UploadZone';
import PharmGxReport, { PharmGxReport as PharmGxReportType } from '../chat/PharmGxReport';
import GWASResult, { GWASVariant } from '../chat/GWASResult';

import { API_BASE_URL } from '@/config/api';

export default function GeneticsDashboard() {
  const [activeTab, setActiveTab] = useState<'pharmgx' | 'gwas'>('pharmgx');
  const [file, setFile] = useState<File | null>(null);
  const [rsid, setRsid] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pharmgxResult, setPharmgxResult] = useState<PharmGxReportType | null>(null);
  const [gwasResult, setGWASResult] = useState<GWASVariant | null>(null);
  const [error, setError] = useState('');

  const handleFileUpload = async (selectedFile: File) => {
    setFile(selectedFile);
    setError('');
    setIsLoading(true);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('sb-access-token') : null;
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE_URL}/api/v1/chat/pharmgx/report`, {
        method: 'POST',
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Analysis failed');
      }

      const data = await response.json();
      setPharmgxResult(data);
      toast.success('Pharmacogenomic report generated');
    } catch (err: any) {
      setError(err.message);
      toast.error(`Analysis failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGWASSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rsid.trim()) {
      toast.error('Please enter an rsID');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('sb-access-token') : null;
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/gwas/lookup/${rsid.trim()}`, {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Lookup failed');
      }

      const data = await response.json();
      setGWASResult(data);
      toast.success('GWAS lookup complete');
    } catch (err: any) {
      setError(err.message);
      toast.error(`Lookup failed: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const exampleVariants = [
    { rsid: 'rs7903146', gene: 'TCF7L2', trait: 'Type 2 Diabetes' },
    { rsid: 'rs4244285', gene: 'CYP2C19', trait: 'Clopidogrel Response' },
    { rsid: 'rs1799853', gene: 'CYP2C9', trait: 'Warfarin Sensitivity' },
    { rsid: 'rs4149056', gene: 'SLCO1B1', trait: 'Statin Myopathy' },
  ];

  return (
    <HubLayout 
      title="Genetics Hub" 
      subtitle="Analyze personal genomic data and variant associations"
      icon={Dna}
      accentColor="purple"
    >
      <div className="space-y-8">
        {/* Hub Navigation / Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-2xl bg-white/5 border border-white/10 w-fit">
          <button
            onClick={() => setActiveTab('pharmgx')}
            className={`
              px-6 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2
              ${activeTab === 'pharmgx' 
                ? 'bg-purple-500 text-black shadow-lg shadow-purple-500/20' 
                : 'text-slate-400 hover:text-white hover:bg-white/5'}
            `}
          >
            <Pill className="w-4 h-4" />
            PharmGx Report
          </button>
          <button
            onClick={() => setActiveTab('gwas')}
            className={`
              px-6 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2
              ${activeTab === 'gwas' 
                ? 'bg-purple-500 text-black shadow-lg shadow-purple-500/20' 
                : 'text-slate-400 hover:text-white hover:bg-white/5'}
            `}
          >
            <TrendingUp className="w-4 h-4" />
            GWAS Lookup
          </button>
        </div>

        <section className="min-h-[400px]">
          <AnimatePresence mode="wait">
            {activeTab === 'pharmgx' ? (
              <motion.div
                key="pharmgx"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="space-y-8"
              >
                {!pharmgxResult && !isLoading ? (
                  <UploadZone 
                    onFileUpload={handleFileUpload} 
                    isLoading={isLoading} 
                    label="Upload Raw Genetic Data"
                  />
                ) : (
                  <div className="space-y-6">
                    {isLoading && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <SkeletonLoader count={4} variant="card" />
                      </div>
                    )}
                    {pharmgxResult && (
                      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center justify-between mb-6">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-full bg-purple-500/20 text-purple-400">
                              <ShieldCheck className="w-5 h-5" />
                            </div>
                            <div>
                              <h3 className="text-lg font-bold text-white">Analysis Result</h3>
                              <p className="text-xs text-slate-400 font-mono">{file?.name}</p>
                            </div>
                          </div>
                          <button 
                            onClick={() => { setPharmgxResult(null); setFile(null); }}
                            className="text-xs text-slate-500 hover:text-white transition-colors"
                          >
                            Upload Different File
                          </button>
                        </div>
                        <PharmGxReport report={pharmgxResult} />
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="gwas"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="space-y-8"
              >
                <section className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md max-w-2xl mx-auto text-center">
                  <h3 className="text-xl font-bold text-white mb-2">Variant Lookup</h3>
                  <p className="text-sm text-slate-400 mb-8">Enter an rsID to explore trait associations and clinical info</p>
                  
                  <form onSubmit={handleGWASSearch} className="space-y-6">
                    <div className="relative group">
                      <input
                        type="text"
                        value={rsid}
                        onChange={(e) => setRsid(e.target.value)}
                        placeholder="e.g., rs7903146"
                        className="w-full px-6 py-4 rounded-2xl bg-black/40 border border-white/10 text-white text-center text-lg placeholder:text-slate-600 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 outline-none transition-all"
                      />
                      <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-600 group-focus-within:text-purple-500 transition-colors" />
                    </div>

                    <div className="flex flex-wrap justify-center gap-2">
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold self-center mr-2">Quick Access:</span>
                      {exampleVariants.map((variant) => (
                        <button
                          key={variant.rsid}
                          type="button"
                          onClick={() => setRsid(variant.rsid)}
                          className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/5 text-slate-400 hover:bg-white/10 hover:text-white transition-all"
                          title={variant.trait}
                        >
                          {variant.rsid}
                        </button>
                      ))}
                    </div>

                    <button 
                      type="submit" 
                      disabled={isLoading || !rsid.trim()}
                      className="w-full py-4 rounded-2xl bg-purple-500 text-black font-bold hover:bg-purple-400 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                    >
                      {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                      Search Database
                    </button>
                  </form>
                </section>

                <AnimatePresence mode="wait">
                  {isLoading ? (
                    <motion.div 
                      key="loading"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="max-w-2xl mx-auto space-y-4 py-8"
                    >
                      <SkeletonLoader count={3} variant="list" />
                    </motion.div>
                  ) : gwasResult ? (
                    <motion.div 
                      key="result"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="max-w-4xl mx-auto"
                    >
                      <GWASResult variant={gwasResult} />
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Error States */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 backdrop-blur-md flex items-start gap-4"
          >
            <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-bold text-red-400">Analysis Error</h3>
              <p className="text-sm text-red-500/70">{error}</p>
            </div>
          </motion.div>
        )}
      </div>
    </HubLayout>
  );
}
