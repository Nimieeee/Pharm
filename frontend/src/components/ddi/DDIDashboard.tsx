'use client';

import { useState } from 'react';
import { AlertTriangle, Pill, Plus, X, Info, Loader2 } from 'lucide-react';
import { useDDI, DDIInteraction, DRUG_PRESETS } from '@/hooks/useDDI';
import HubLayout from '@/components/shared/HubLayout';
import { LoadingAnimation } from '@/components/shared/LoadingAnimation';

type Mode = 'single' | 'poly';

export default function DDIDashboard() {
  const { checkInteraction, checkPolypharmacy, loading, error, clearError } = useDDI();
  
  const [mode, setMode] = useState<Mode>('single');
  const [drugA, setDrugA] = useState('');
  const [drugB, setDrugB] = useState('');
  const [drugs, setDrugs] = useState<string[]>(['', '']);
  const [result, setResult] = useState<DDIInteraction | null>(null);
  const [polyResult, setPolyResult] = useState<any>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSingleCheck = async () => {
    const res = await checkInteraction(drugA, drugB);
    if (res) {
      setResult(res);
      setPolyResult(null);
      setHasSearched(true);
    }
  };

  const handlePolyCheck = async () => {
    const validDrugs = drugs.filter(d => d.trim());
    const res = await checkPolypharmacy(validDrugs);
    if (res) {
      setPolyResult(res);
      setResult(null);
      setHasSearched(true);
    }
  };

  const addDrug = () => {
    if (drugs.length < 10) {
      setDrugs([...drugs, '']);
    }
  };

  const removeDrug = (index: number) => {
    if (drugs.length > 2) {
      setDrugs(drugs.filter((_, i) => i !== index));
    }
  };

  const updateDrug = (index: number, value: string) => {
    const newDrugs = [...drugs];
    newDrugs[index] = value;
    setDrugs(newDrugs);
  };

  const loadPreset = (preset: typeof DRUG_PRESETS[0]) => {
    setMode('single');
    setDrugA(preset.drugs[0]);
    setDrugB(preset.drugs[1]);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'major': return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400 border-red-200 dark:border-red-800';
      case 'moderate': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400 border-amber-200 dark:border-amber-800';
      case 'minor': return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400 border-green-200 dark:border-green-800';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700';
    }
  };

  const getSeverityIcon = (severity: string) => {
    if (severity?.toLowerCase() === 'major') return '❌';
    if (severity?.toLowerCase() === 'moderate') return '⚠️';
    if (severity?.toLowerCase() === 'minor') return 'ℹ️';
    return '';
  };

  return (
    <HubLayout
      title="Drug Interaction Checker"
      subtitle="Check drug-drug interactions"
      icon={AlertTriangle}
      accentColor="red"
    >
      <div className="max-w-4xl mx-auto">
        {/* Mode Selector */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 mb-6">
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => { setMode('single'); setHasSearched(false); setResult(null); setPolyResult(null); }}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                mode === 'single'
                  ? 'bg-red-600 text-white'
                  : 'bg-[var(--background)] border border-[var(--border)] text-[var(--text-muted)] hover:border-red-500'
              }`}
            >
              Single Pair
            </button>
            <button
              onClick={() => { setMode('poly'); setHasSearched(false); setResult(null); setPolyResult(null); }}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                mode === 'poly'
                  ? 'bg-red-600 text-white'
                  : 'bg-[var(--background)] border border-[var(--border)] text-[var(--text-muted)] hover:border-red-500'
              }`}
            >
              Polypharmacy (3+ drugs)
            </button>
          </div>

          {/* Drug Presets */}
          <div className="mb-4">
            <p className="text-xs text-[var(--text-muted)] mb-2">Quick presets:</p>
            <div className="flex flex-wrap gap-2">
              {DRUG_PRESETS.slice(0, 3).map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => loadPreset(preset)}
                  className="text-xs px-3 py-1 rounded-full bg-[var(--background)] border border-[var(--border)] text-[var(--text-muted)] hover:border-red-500 hover:text-red-500 transition-colors"
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Drug Inputs */}
          {mode === 'single' ? (
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={drugA}
                onChange={(e) => setDrugA(e.target.value)}
                placeholder="Drug A (e.g., Warfarin)"
                className="flex-1 px-4 py-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <input
                type="text"
                value={drugB}
                onChange={(e) => setDrugB(e.target.value)}
                placeholder="Drug B (e.g., Aspirin)"
                className="flex-1 px-4 py-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <button
                onClick={handleSingleCheck}
                disabled={loading || !drugA.trim() || !drugB.trim()}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors w-full sm:w-auto"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Pill className="w-5 h-5" />}
                Check
              </button>
            </div>
          ) : (
            <div>
              <div className="space-y-2 mb-4">
                {drugs.map((drug, idx) => (
                  <div key={idx} className="flex gap-2">
                    <input
                      type="text"
                      value={drug}
                      onChange={(e) => updateDrug(idx, e.target.value)}
                      placeholder={`Drug ${idx + 1}`}
                      className="flex-1 px-4 py-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                    {drugs.length > 2 && (
                      <button
                        onClick={() => removeDrug(idx)}
                        className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-muted)] hover:text-red-500 hover:border-red-500 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={addDrug}
                  disabled={drugs.length >= 10}
                  className="px-4 py-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-muted)] hover:border-red-500 hover:text-red-500 transition-colors flex items-center justify-center gap-2 w-full sm:w-auto"
                >
                  <Plus className="w-4 h-4" /> Add Drug
                </button>
                <button
                  onClick={handlePolyCheck}
                  disabled={loading || drugs.filter(d => d.trim()).length < 2}
                  className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors w-full"
                >
                  {loading ? <Pill className="w-5 h-5 animate-pulse" /> : <Pill className="w-5 h-5" />}
                  Check All Interactions
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-600 dark:text-red-400">{error}</p>
            <button onClick={clearError} className="text-sm text-red-500 underline mt-2">Dismiss</button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="py-20">
            <LoadingAnimation label="Cross-referencing RxNorm databases for potential drug-drug interactions..." />
          </div>
        )}

        {/* Single Result */}
        {!loading && result && (
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">{getSeverityIcon(result.severity || '')}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSeverityColor(result.severity || 'Unknown')}`}>
                {result.severity || 'Unknown'} INTERACTION
              </span>
            </div>

            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              {result.drug_a} + {result.drug_b}
            </h3>

            {result.interaction_found ? (
              <div className="space-y-4">
                {result.mechanism && (
                  <div>
                    <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Mechanism</h4>
                    <p className="text-[var(--text-primary)]">{result.mechanism}</p>
                  </div>
                )}
                {result.description && (
                  <div>
                    <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Description</h4>
                    <p className="text-[var(--text-primary)]">{result.description}</p>
                  </div>
                )}
                {result.clinical_significance && (
                  <div>
                    <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Clinical Significance</h4>
                    <p className="text-[var(--text-primary)]">{result.clinical_significance}</p>
                  </div>
                )}
                {result.evidence_level && (
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-[var(--text-muted)]">Evidence Level:</h4>
                    <span className="text-sm">{result.evidence_level}</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[var(--text-muted)]">{result.description || 'No interaction data found for these drugs.'}</p>
            )}

            {result.source && (
              <p className="text-xs text-[var(--text-muted)] mt-4">Source: {result.source}</p>
            )}
          </div>
        )}

        {/* Polypharmacy Results */}
        {!loading && polyResult && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-[var(--text-primary)]">Interaction Summary</h3>
                <div className="flex gap-3 text-sm">
                  <span className="px-3 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400">
                    {polyResult.summary.major} Major
                  </span>
                  <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400">
                    {polyResult.summary.moderate} Moderate
                  </span>
                  <span className="px-3 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400">
                    {polyResult.summary.minor} Minor
                  </span>
                </div>
              </div>
            </div>

            {/* Interactions */}
            {polyResult.interactions.map((interaction: DDIInteraction, idx: number) => (
              <div
                key={idx}
                className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-lg">{getSeverityIcon(interaction.severity || '')}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(interaction.severity || 'Unknown')}`}>
                    {interaction.severity || 'Unknown'}
                  </span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {interaction.drug_a} + {interaction.drug_b}
                  </span>
                </div>
                {interaction.description && (
                  <p className="text-sm text-[var(--text-secondary)]">{interaction.description}</p>
                )}
              </div>
            ))}

            {polyResult.interactions.length === 0 && (
              <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6 text-center">
                <Info className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <p className="text-[var(--text-primary)]">No interactions found among these drugs.</p>
              </div>
            )}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-[var(--text-muted)] text-center mt-8">
          Source: NLM RxNorm/RxNav APIs. This is for informational purposes only and should not replace clinical judgment.
        </p>
      </div>
    </HubLayout>
  );
}
