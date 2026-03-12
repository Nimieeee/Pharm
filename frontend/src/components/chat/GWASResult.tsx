'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dna, Globe, BookOpen, ExternalLink, AlertCircle, CheckCircle, Info } from 'lucide-react';

export interface GWASVariant {
  rsid: string;
  found: boolean;
  ensembl?: {
    chromosome: string;
    position: number;
    alleles: string[];
    most_severe_consequence?: string;
    minor_allele?: string;
    minor_allele_freq?: number;
  };
  gwas_associations?: Array<{
    trait: string;
    p_value?: number;
    p_value_formatted?: string;
    odds_ratio?: number;
    beta?: number;
    risk_allele?: string;
  }>;
  open_targets?: {
    genes: Array<{ symbol: string; biotype: string }>;
    cadd_score?: number;
  };
  clinvar?: {
    records: Array<{
      condition: string;
      clinical_significance: string;
      review_status: string;
      url: string;
    }>;
  };
  summary?: {
    chromosome?: string;
    position?: number;
    alleles: string[];
    genes: Array<{ symbol: string }>;
    trait_count: number;
    clinvar_records: number;
    most_severe_consequence?: string;
    cadd_score?: number;
  };
}

interface GWASResultProps {
  variant: GWASVariant;
}

export default function GWASResult({ variant }: GWASResultProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  if (!variant || !variant.found) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <Dna className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-sm">No data found for variant</p>
        {variant?.rsid && (
          <p className="text-xs mt-1 text-muted-foreground font-mono">
            {variant.rsid}
          </p>
        )}
      </div>
    );
  }

  const summary = (variant.summary || {}) as any;
  const hasGwasData = (variant.gwas_associations?.length || 0) > 0;
  const hasClinvarData = (variant.clinvar?.records?.length || 0) > 0;
  const hasGeneData = (summary.genes?.length || 0) > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header */}
      <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 dark:from-purple-950/30 to-blue-50 dark:to-blue-950/30 border border-purple-200 dark:border-purple-800 rounded-xl">
        <div className="flex items-center gap-3 mb-3">
          <Dna className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100">
            GWAS Variant Lookup
          </h3>
        </div>
        
        <div className="flex flex-wrap items-center gap-4">
          {/* Variant ID */}
          <div className="px-3 py-1.5 rounded-lg bg-white dark:bg-black/30 border border-purple-200 dark:border-purple-700">
            <span className="text-xs text-purple-600 dark:text-purple-400 font-mono">
              {variant.rsid}
            </span>
          </div>
          
          {/* Location */}
          {(summary as any).chromosome && (
            <div className="flex items-center gap-1.5 text-sm text-purple-800 dark:text-purple-200">
              <Globe className="w-4 h-4" />
              <span>Chr{(summary as any).chromosome}:{(summary as any).position?.toLocaleString()}</span>
            </div>
          )}

          {/* Alleles */}
          {(summary as any).alleles && (summary as any).alleles.length > 0 && (
            <div className="flex items-center gap-1.5 text-sm text-purple-800 dark:text-purple-200">
              <Dna className="w-4 h-4" />
              <span className="font-mono">{(summary as any).alleles.join(' / ')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        {/* Consequence */}
        {(summary as any).most_severe_consequence && (
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Consequence</p>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {summary.most_severe_consequence}
            </p>
          </div>
        )}
        
        {/* CADD Score */}
        {summary.cadd_score && (
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">CADD Score</p>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {summary.cadd_score}
              <span className="text-xs text-slate-500 ml-1">(higher = more deleterious)</span>
            </p>
          </div>
        )}
        
        {/* Trait Count */}
        {summary.trait_count !== undefined && (
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">GWAS Associations</p>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {summary.trait_count} trait{summary.trait_count !== 1 ? 's' : ''}
            </p>
          </div>
        )}
        
        {/* ClinVar Records */}
        {summary.clinvar_records !== undefined && (
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">ClinVar Records</p>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {summary.clinvar_records} record{summary.clinvar_records !== 1 ? 's' : ''}
            </p>
          </div>
        )}
      </div>

      {/* Genes Section */}
      {hasGeneData && (
        <div className="mb-4 p-4 rounded-xl border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-950/20">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            <h4 className="text-sm font-semibold text-purple-800 dark:text-purple-200">
              Nearby Genes
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {summary.genes?.map((gene: any, index: number) => (
              <span
                key={index}
                className="px-2.5 py-1 rounded-lg bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-200 text-sm font-medium"
              >
                {gene.symbol}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* GWAS Associations */}
      {hasGwasData && (
        <div className="mb-4 p-4 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
          <button
            onClick={() => setExpandedSection(expandedSection === 'gwas' ? null : 'gwas')}
            className="flex items-center justify-between w-full mb-3"
          >
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200">
                Trait Associations ({variant.gwas_associations?.length})
              </h4>
            </div>
            <span className="text-xs text-blue-600 dark:text-blue-400">
              {expandedSection === 'gwas' ? '▼' : '▶'}
            </span>
          </button>
          
          <AnimatePresence>
            {expandedSection === 'gwas' && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="space-y-2 mt-3">
                  {variant.gwas_associations?.slice(0, 10).map((assoc, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg bg-white dark:bg-black/30 border border-blue-100 dark:border-blue-900"
                    >
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                        {assoc.trait}
                      </p>
                      <div className="flex flex-wrap gap-3 text-xs text-blue-700 dark:text-blue-300">
                        {assoc.p_value_formatted && (
                          <span className="font-mono">P = {assoc.p_value_formatted}</span>
                        )}
                        {assoc.odds_ratio && (
                          <span>OR: {assoc.odds_ratio}</span>
                        )}
                        {assoc.beta && (
                          <span>β: {assoc.beta}</span>
                        )}
                        {assoc.risk_allele && (
                          <span className="font-mono">Risk allele: {assoc.risk_allele}</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {(variant.gwas_associations?.length || 0) > 10 && (
                    <p className="text-xs text-blue-600 dark:text-blue-400 text-center mt-2">
                      ...and {variant.gwas_associations!.length - 10} more associations
                    </p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* ClinVar Section */}
      {hasClinvarData && (
        <div className="mb-4 p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
            <h4 className="text-sm font-semibold text-red-800 dark:text-red-200">
              Clinical Significance (ClinVar)
            </h4>
          </div>
          <div className="space-y-2">
            {variant.clinvar?.records.slice(0, 5).map((record, index) => (
              <div
                key={index}
                className="p-3 rounded-lg bg-white dark:bg-black/30 border border-red-100 dark:border-red-900"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900 dark:text-red-100 mb-1">
                      {record.condition}
                    </p>
                    <div className="flex flex-wrap gap-2 text-xs">
                      <span className={`px-2 py-0.5 rounded ${
                        record.clinical_significance?.includes('Pathogenic') 
                          ? 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                          : record.clinical_significance?.includes('Benign')
                          ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300'
                          : 'bg-slate-100 dark:bg-slate-900/50 text-slate-800 dark:text-slate-300'
                      }`}>
                        {record.clinical_significance || 'Unknown'}
                      </span>
                      <span className="text-slate-600 dark:text-slate-400">
                        {record.review_status}
                      </span>
                    </div>
                  </div>
                  {record.url && (
                    <a
                      href={record.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Sources Footer */}
      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Data sources: Ensembl, GWAS Catalog, Open Targets, ClinVar
        </p>
        <div className="flex items-center gap-2">
          <a
            href={`https://www.ensembl.org/Homo_sapiens/Variation/Explore?v=${variant.rsid}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-200 flex items-center gap-1"
          >
            Ensembl
            <ExternalLink className="w-3 h-3" />
          </a>
          <a
            href={`https://www.ebi.ac.uk/gwas/variants/${variant.rsid}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 flex items-center gap-1"
          >
            GWAS Catalog
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </motion.div>
  );
}
