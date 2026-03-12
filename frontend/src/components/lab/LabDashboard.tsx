'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FlaskConical, Download, Share2, Search, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface ADMETResult {
  success: boolean;
  smiles: string;
  report: string;
  include_svg: boolean;
}

export default function LabDashboard() {
  const [smiles, setSmiles] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ADMETResult | null>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!smiles.trim()) {
      toast.error('Please enter a SMILES string');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const response = await fetch('/api/v1/admet/analyze', {
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
      const token = typeof window !== 'undefined'
        ? localStorage.getItem('sb-access-token')
        : null;

      const response = await fetch(
        `/api/v1/admet/export?smiles=${encodeURIComponent(smiles)}`,
        {
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `admet_${smiles.slice(0, 20)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('CSV exported');
    } catch (err: any) {
      toast.error(`Export failed: ${err.message}`);
    }
  };

  const exampleMolecules = [
    { name: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O' },
    { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C' },
    { name: 'Penicillin', smiles: 'CC1(C(N2C(S1)C(C2=O)=O)C(=O)O)S' },
    { name: 'Diazepam', smiles: 'CN1C(=O)CN=C(C2=C1C=CC=C2)C3=CC=CC=C3Cl' },
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
          <FlaskConical className="w-8 h-8 text-amber-600" />
          <h1 className="text-2xl font-bold">ADMET Lab</h1>
        </div>
        <p className="text-muted-foreground">
          Predict absorption, distribution, metabolism, excretion, and toxicity properties
        </p>
      </motion.div>

      {/* Input Form */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8 p-6 bg-card border border-border rounded-xl"
      >
        <form onSubmit={handleSubmit}>
          <label className="block text-sm font-medium mb-2">
            SMILES String
          </label>
          <div className="flex gap-3 mb-4">
            <input
              type="text"
              value={smiles}
              onChange={(e) => setSmiles(e.target.value)}
              placeholder="Enter SMILES (e.g., CC(=O)Oc1ccccc1C(=O)O)"
              className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white rounded-lg flex items-center gap-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Analyze
                </>
              )}
            </button>
          </div>

          {/* Example Molecules */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground self-center">Try:</span>
            {exampleMolecules.map((mol) => (
              <button
                key={mol.name}
                type="button"
                onClick={() => setSmiles(mol.smiles)}
                className="text-xs px-3 py-1.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors"
              >
                {mol.name}
              </button>
            ))}
          </div>
        </form>
      </motion.div>

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-8 p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20"
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

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Action Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-medium">Analysis Complete</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleExportCSV}
                className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg flex items-center gap-2 text-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result.report);
                  toast.success('Report copied to clipboard');
                }}
                className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg flex items-center gap-2 text-sm transition-colors"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
            </div>
          </div>

          {/* Report Content */}
          <div className="p-6 bg-card border border-border rounded-xl">
            <div className="prose dark:prose-invert max-w-none">
              {result.report.split('\n').map((line, i) => {
                if (line.startsWith('## ')) {
                  return <h2 key={i} className="text-xl font-bold mt-6 mb-3">{line.slice(3)}</h2>;
                }
                if (line.startsWith('### ')) {
                  return <h3 key={i} className="text-lg font-semibold mt-4 mb-2">{line.slice(4)}</h3>;
                }
                if (line.startsWith('- **')) {
                  const match = line.match(/- \*\*(.+?)\*\*: (.+)/);
                  if (match) {
                    return (
                      <li key={i} className="ml-4">
                        <strong>{match[1]}</strong>: {match[2]}
                      </li>
                    );
                  }
                }
                if (line.startsWith('⚠️')) {
                  return (
                    <div key={i} className="my-2 p-2 rounded bg-amber-50 dark:bg-amber-950/20 text-amber-800 dark:text-amber-200">
                      {line}
                    </div>
                  );
                }
                return <p key={i} className="my-2">{line}</p>;
              })}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
