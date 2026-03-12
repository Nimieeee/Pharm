'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, AlertCircle, Info, CheckCircle, ShieldAlert } from 'lucide-react';

export interface DDIInteraction {
  drug_a: string;
  drug_b: string;
  severity: 'Major' | 'Moderate' | 'Minor' | 'None' | 'Unknown';
  description: string;
  mechanism?: string;
  clinical_significance: string;
  evidence_level?: string;
  alternatives?: string[];
  interaction_found?: boolean;
  pair?: string;
}

interface DDIResultProps {
  interactions: DDIInteraction[];
  drugs?: string[];
}

export default function DDIResult({ interactions, drugs }: DDIResultProps) {
  if (!interactions || interactions.length === 0) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30 text-emerald-500" />
        <p className="text-sm">No drug interactions found</p>
        {drugs && drugs.length > 0 && (
          <p className="text-xs mt-1 text-muted-foreground">
            Checked: {drugs.join(', ')}
          </p>
        )}
      </div>
    );
  }

  // Count by severity
  const majorCount = interactions.filter(i => i.severity === 'Major').length;
  const moderateCount = interactions.filter(i => i.severity === 'Moderate').length;
  const minorCount = interactions.filter(i => i.severity === 'Minor').length;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Major':
        return 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800';
      case 'Moderate':
        return 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800';
      case 'Minor':
        return 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800';
      default:
        return 'bg-slate-50 dark:bg-slate-950/30 border-slate-200 dark:border-slate-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'Major':
        return <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'Moderate':
        return <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />;
      case 'Minor':
        return <Info className="w-5 h-5 text-green-600 dark:text-green-400" />;
      default:
        return <Info className="w-5 h-5 text-slate-600 dark:text-slate-400" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'Major':
        return 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300';
      case 'Moderate':
        return 'bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-300';
      case 'Minor':
        return 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300';
      default:
        return 'bg-slate-100 dark:bg-slate-900/50 text-slate-800 dark:text-slate-300';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header Summary */}
      <div className="mb-4 p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl">
        <div className="flex items-center gap-2 mb-2">
          <ShieldAlert className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Drug Interaction Check
          </h3>
        </div>
        
        <div className="flex flex-wrap gap-3 mt-3">
          {majorCount > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-100 dark:bg-red-900/40">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium text-red-800 dark:text-red-300">
                {majorCount} Major
              </span>
            </div>
          )}
          {moderateCount > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/40">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span className="text-sm font-medium text-amber-800 dark:text-amber-300">
                {moderateCount} Moderate
              </span>
            </div>
          )}
          {minorCount > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/40">
              <Info className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-800 dark:text-green-300">
                {minorCount} Minor
              </span>
            </div>
          )}
          {interactions.length === 0 && (
            <span className="text-sm text-slate-600 dark:text-slate-400">
              No significant interactions found
            </span>
          )}
        </div>
      </div>

      {/* Interaction Cards */}
      <div className="space-y-3">
        {interactions.map((interaction, index) => (
          <motion.article
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`p-4 border rounded-xl ${getSeverityColor(interaction.severity)}`}
          >
            {/* Drug Pair Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                {getSeverityIcon(interaction.severity)}
                <div>
                  <h4 className="text-sm font-semibold">
                    {interaction.pair || `${interaction.drug_a} + ${interaction.drug_b}`}
                  </h4>
                  <span className={`text-xs px-2 py-0.5 rounded ${getSeverityBadge(interaction.severity)}`}>
                    {interaction.severity} Interaction
                  </span>
                </div>
              </div>
            </div>

            {/* Description */}
            {interaction.description && (
              <p className="text-sm mb-2 opacity-90">
                {interaction.description}
              </p>
            )}

            {/* Mechanism */}
            {interaction.mechanism && (
              <div className="mb-2">
                <p className="text-xs font-medium opacity-70 mb-1">Mechanism:</p>
                <p className="text-sm opacity-80">{interaction.mechanism}</p>
              </div>
            )}

            {/* Clinical Significance */}
            {interaction.clinical_significance && (
              <div className="mb-2 p-2 rounded bg-white/50 dark:bg-black/20">
                <p className="text-xs font-medium opacity-70 mb-1">Clinical Significance:</p>
                <p className="text-sm">{interaction.clinical_significance}</p>
              </div>
            )}

            {/* Evidence Level */}
            {interaction.evidence_level && (
              <p className="text-xs opacity-60">
                Evidence: {interaction.evidence_level}
              </p>
            )}

            {/* Alternatives */}
            {interaction.alternatives && interaction.alternatives.length > 0 && (
              <div className="mt-3 pt-3 border-t border-current border-opacity-20">
                <p className="text-xs font-medium opacity-70 mb-2">Recommendations:</p>
                <ul className="text-sm space-y-1 opacity-80">
                  {interaction.alternatives.map((alt, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-xs mt-1">•</span>
                      <span>{alt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.article>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="mt-4 p-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-red-800 dark:text-red-300 mb-1">
              Medical Disclaimer
            </p>
            <p className="text-xs text-red-700 dark:text-red-400">
              This information is for educational purposes only and does not constitute medical advice. 
              Always consult a qualified healthcare professional before making any changes to medications. 
              Drug interactions can vary based on individual patient factors.
            </p>
          </div>
        </div>
      </div>

      {/* Source Attribution */}
      <p className="mt-3 text-xs text-center text-muted-foreground">
        Source: NLM RxNorm® and RxNav® APIs
      </p>
    </motion.div>
  );
}
