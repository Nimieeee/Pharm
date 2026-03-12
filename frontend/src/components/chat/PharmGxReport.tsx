'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dna, AlertTriangle, AlertCircle, CheckCircle, Pill, FileWarning, ShieldAlert, Info } from 'lucide-react';

export interface GeneResult {
  gene: string;
  snps_tested: string[];
  alleles: string[];
  phenotype: string;
  drug_impact: string[];
}

export interface DrugRecommendation {
  drug: string;
  genes: string[];
  phenotypes: string[];
  guidance: string;
  recommendation: string;
}

export interface PharmGxReport {
  success: boolean;
  patient_id: string;
  filename: string;
  generated_at: string;
  genes_analyzed: number;
  gene_results: GeneResult[];
  drug_recommendations: DrugRecommendation[];
  summary: {
    poor_metabolizer_count: number;
    intermediate_count: number;
    normal_count: number;
    high_risk_drugs: number;
  };
  error?: string;
}

interface PharmGxReportProps {
  report: PharmGxReport;
}

export default function PharmGxReport({ report }: PharmGxReportProps) {
  const [expandedGene, setExpandedGene] = useState<string | null>(null);
  const [expandedDrug, setExpandedDrug] = useState<string | null>(null);

  if (!report.success) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-30 text-red-500" />
        <p className="text-sm font-medium">Could not analyze genetic data</p>
        <p className="text-xs mt-1 text-muted-foreground">{report.error}</p>
        <p className="text-xs mt-2 text-muted-foreground">
          Supported formats: 23andMe, AncestryDNA raw data
        </p>
      </div>
    );
  }

  const summary = report.summary || {};
  const hasHighRisk = (summary.high_risk_drugs || 0) > 0;

  const getPhenotypeColor = (phenotype: string) => {
    if (phenotype.includes("Poor") || phenotype.includes("CONTRAINDICATED")) {
      return "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800";
    }
    if (phenotype.includes("Intermediate") || phenotype.includes("High risk")) {
      return "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800";
    }
    return "bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800";
  };

  const getPhenotypeIcon = (phenotype: string) => {
    if (phenotype.includes("Poor") || phenotype.includes("CONTRAINDICATED")) {
      return <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />;
    }
    if (phenotype.includes("Intermediate") || phenotype.includes("High risk")) {
      return <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />;
    }
    return <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header */}
      <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 dark:from-blue-950/30 to-purple-50 dark:to-purple-950/30 border border-blue-200 dark:border-blue-800 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Dna className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              Pharmacogenomic Report
            </h3>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 font-medium">
            {report.genes_analyzed} Genes
          </span>
        </div>
        
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2 text-blue-800 dark:text-blue-200">
            <FileWarning className="w-4 h-4" />
            <span>Patient ID: <span className="font-mono">{report.patient_id}</span></span>
          </div>
          <div className="flex items-center gap-2 text-blue-800 dark:text-blue-200">
            <Info className="w-4 h-4" />
            <span>Generated: {new Date(report.generated_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className={`p-3 rounded-xl border ${hasHighRisk ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800' : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800'}`}>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className={`w-4 h-4 ${hasHighRisk ? 'text-red-600' : 'text-slate-500'}`} />
            <span className="text-xs text-slate-600 dark:text-slate-400">High Risk Drugs</span>
          </div>
          <p className={`text-xl font-bold ${hasHighRisk ? 'text-red-700 dark:text-red-300' : 'text-slate-800 dark:text-slate-200'}`}>
            {summary.high_risk_drugs || 0}
          </p>
        </div>
        
        <div className="p-3 rounded-xl border bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-xs text-slate-600 dark:text-slate-400">Poor Metabolizer</span>
          </div>
          <p className="text-xl font-bold text-red-700 dark:text-red-300">
            {summary.poor_metabolizer_count || 0}
          </p>
        </div>
        
        <div className="p-3 rounded-xl border bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <span className="text-xs text-slate-600 dark:text-slate-400">Intermediate</span>
          </div>
          <p className="text-xl font-bold text-amber-700 dark:text-amber-300">
            {summary.intermediate_count || 0}
          </p>
        </div>
        
        <div className="p-3 rounded-xl border bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="text-xs text-slate-600 dark:text-slate-400">Normal</span>
          </div>
          <p className="text-xl font-bold text-green-700 dark:text-green-300">
            {summary.normal_count || 0}
          </p>
        </div>
      </div>

      {/* Gene Analysis Section */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
          <Dna className="w-4 h-4" />
          Gene Analysis
        </h4>
        
        <div className="space-y-2">
          {report.gene_results.map((gene, index) => (
            <motion.div
              key={gene.gene}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`p-3 rounded-xl border ${getPhenotypeColor(gene.phenotype)}`}
            >
              <button
                onClick={() => setExpandedGene(expandedGene === gene.gene ? null : gene.gene)}
                className="flex items-center justify-between w-full"
              >
                <div className="flex items-center gap-3">
                  {getPhenotypeIcon(gene.phenotype)}
                  <div className="text-left">
                    <p className="text-sm font-semibold">{gene.gene}</p>
                    <p className="text-xs opacity-80">{gene.phenotype}</p>
                  </div>
                </div>
                <span className="text-xs opacity-60">
                  {expandedGene === gene.gene ? '▼' : '▶'}
                </span>
              </button>
              
              <AnimatePresence>
                {expandedGene === gene.gene && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden mt-3 pt-3 border-t border-current border-opacity-20"
                  >
                    <div className="text-xs space-y-2">
                      <div>
                        <span className="opacity-70">SNPs tested:</span>{' '}
                        <span className="font-mono">{gene.snps_tested.join(', ')}</span>
                      </div>
                      <div>
                        <span className="opacity-70">Alleles:</span>{' '}
                        <span>{gene.alleles.join(', ')}</span>
                      </div>
                      {gene.drug_impact.length > 0 && (
                        <div>
                          <span className="opacity-70">Affects:</span>{' '}
                          <span className="font-medium">{gene.drug_impact.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Drug Recommendations Section */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
          <Pill className="w-4 h-4" />
          Drug Recommendations
        </h4>
        
        <div className="space-y-3">
          {report.drug_recommendations.map((drug, index) => {
            const isContraindicated = drug.guidance.includes("CONTRAINDICATED");
            const isAvoid = drug.guidance.includes("Avoid");
            
            return (
              <motion.article
                key={drug.drug}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`p-4 rounded-xl border ${
                  isContraindicated 
                    ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800' 
                    : isAvoid
                    ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800'
                    : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {isContraindicated ? (
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    ) : isAvoid ? (
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    )}
                    <h5 className="text-sm font-semibold capitalize">{drug.drug}</h5>
                  </div>
                  <button
                    onClick={() => setExpandedDrug(expandedDrug === drug.drug ? null : drug.drug)}
                    className="text-xs opacity-60 hover:opacity-100"
                  >
                    {expandedDrug === drug.drug ? '▼' : '▶'}
                  </button>
                </div>
                
                <p className={`text-sm mb-2 ${
                  isContraindicated ? 'text-red-800 dark:text-red-200' : 
                  isAvoid ? 'text-amber-800 dark:text-amber-200' : 
                  'text-slate-800 dark:text-slate-200'
                }`}>
                  {drug.guidance}
                </p>
                
                <div className="flex flex-wrap gap-2 text-xs opacity-70">
                  {drug.genes.map((gene, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-white/50 dark:bg-black/20">
                      {gene}
                    </span>
                  ))}
                </div>
                
                <AnimatePresence>
                  {expandedDrug === drug.drug && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden mt-3 pt-3 border-t border-current border-opacity-20"
                    >
                      <div className="text-xs space-y-2">
                        <div>
                          <span className="opacity-70">Phenotypes:</span>
                          <ul className="mt-1 space-y-0.5">
                            {drug.phenotypes.map((p, i) => (
                              <li key={i}>• {p}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="pt-2">
                          <span className="opacity-70">Recommendation:</span>{' '}
                          <span className="font-medium">{drug.recommendation}</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.article>
            );
          })}
        </div>
      </div>

      {/* Medical Disclaimer */}
      <div className="mt-6 p-4 rounded-xl border-2 border-red-200 dark:border-red-800 bg-red-50/70 dark:bg-red-950/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-800 dark:text-red-300 mb-2">
              Medical Disclaimer
            </p>
            <p className="text-xs text-red-700 dark:text-red-400 leading-relaxed">
              This report is for <strong>educational and research purposes only</strong> and does not constitute medical advice. 
              Pharmacogenomic test results should be interpreted by qualified healthcare professionals in the context of 
              complete medical history, current medications, and clinical presentation. 
              <strong> Do not make any changes to medications without consulting your healthcare provider.</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Data Source Attribution */}
      <p className="mt-4 text-xs text-center text-slate-500 dark:text-slate-400">
        Data based on CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines. 
        Gene-drug associations curated from PharmGKB.
      </p>
    </motion.div>
  );
}
