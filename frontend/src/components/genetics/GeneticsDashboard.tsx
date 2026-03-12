'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Dna, Upload, Search, FileText, AlertCircle, CheckCircle, Loader2, Pill, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setError('');
    setIsLoading(true);

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE_URL}/api/v1/chat/pharmgx/report`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
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
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const response = await fetch(`${API_BASE_URL}/api/v1/chat/gwas/lookup/${rsid.trim()}`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
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
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Dna className="w-8 h-8 text-purple-600" />
          <h1 className="text-2xl font-bold">Genetics Hub</h1>
        </div>
        <p className="text-muted-foreground">
          Pharmacogenomics and GWAS variant analysis
        </p>
      </motion.div>

      {/* Tab Selector */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => {
            setActiveTab('pharmgx');
            setError('');
          }}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
            activeTab === 'pharmgx'
              ? 'bg-purple-600 text-white'
              : 'bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700'
          }`}
        >
          <Pill className="w-4 h-4" />
          PharmGx Report
        </button>
        <button
          onClick={() => {
            setActiveTab('gwas');
            setError('');
          }}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
            activeTab === 'gwas'
              ? 'bg-purple-600 text-white'
              : 'bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          GWAS Lookup
        </button>
      </div>

      {/* PharmGx Tab */}
      {activeTab === 'pharmgx' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-6"
        >
          {/* Upload Section */}
          <div className="p-6 bg-card border border-border rounded-xl">
            <h2 className="text-lg font-semibold mb-4">Upload Genetic Data</h2>
            <div className="flex items-start gap-4 mb-4">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-2">
                  23andMe or AncestryDNA Raw Data
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    accept=".txt"
                    onChange={handleFileUpload}
                    className="flex-1 text-sm"
                  />
                  {file && (
                    <span className="text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      {file.name}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Supported formats: 23andMe raw data, AncestryDNA raw data
                </p>
              </div>
              {isLoading && (
                <div className="flex items-center gap-2 text-purple-600">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Analyzing...</span>
                </div>
              )}
            </div>
          </div>

          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20"
            >
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-300">Analysis Error</p>
                  <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Report */}
          {pharmgxResult && <PharmGxReport report={pharmgxResult} />}
        </motion.div>
      )}

      {/* GWAS Tab */}
      {activeTab === 'gwas' && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-6"
        >
          {/* Search Section */}
          <div className="p-6 bg-card border border-border rounded-xl">
            <h2 className="text-lg font-semibold mb-4">GWAS Variant Lookup</h2>
            <form onSubmit={handleGWASSearch}>
              <div className="flex gap-3 mb-4">
                <input
                  type="text"
                  value={rsid}
                  onChange={(e) => setRsid(e.target.value)}
                  placeholder="Enter rsID (e.g., rs7903146)"
                  className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded-lg flex items-center gap-2 transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      Lookup
                    </>
                  )}
                </button>
              </div>

              {/* Example Variants */}
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-muted-foreground self-center">Try:</span>
                {exampleVariants.map((variant) => (
                  <button
                    key={variant.rsid}
                    type="button"
                    onClick={() => setRsid(variant.rsid)}
                    className="text-xs px-3 py-1.5 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-900/60 transition-colors"
                    title={variant.trait}
                  >
                    {variant.rsid} ({variant.gene})
                  </button>
                ))}
              </div>
            </form>
          </div>

          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20"
            >
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-300">Lookup Error</p>
                  <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Result */}
          {gwasResult && <GWASResult variant={gwasResult} />}
        </motion.div>
      )}
    </div>
  );
}
