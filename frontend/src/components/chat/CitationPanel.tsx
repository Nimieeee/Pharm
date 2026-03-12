'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronDown, Copy, Download, ExternalLink, Check } from 'lucide-react';
import { toast } from 'sonner';

export interface Citation {
  id: number;
  title: string;
  url: string;
  authors?: string;
  year?: string;
  journal?: string;
  source?: string;
  doi?: string;
  volume?: string;
  issue?: string;
  pages?: string;
  pmid?: string;
}

interface CitationPanelProps {
  citations: Citation[];
  onExportBib?: () => void;
}

export default function CitationPanel({ citations, onExportBib }: CitationPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const handleCopyAPA = (citation: Citation) => {
    const apa = formatAPA(citation);
    navigator.clipboard.writeText(apa);
    setCopiedId(citation.id);
    toast.success('Citation copied (APA)');
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCopyBibTeX = (citation: Citation) => {
    const bibtex = formatBibTeX(citation);
    navigator.clipboard.writeText(bibtex);
    setCopiedId(citation.id);
    toast.success('Citation copied (BibTeX)');
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownloadAllBib = () => {
    const bibContent = citations.map(c => formatBibTeX(c)).join('\n\n');
    const blob = new Blob([bibContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'references.bib';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('BibTeX file downloaded');
  };

  const formatAPA = (citation: Citation) => {
    const authors = citation.authors || 'Unknown author';
    const year = citation.year || 'n.d.';
    const title = citation.title;
    const journal = citation.journal || citation.source || '';
    
    let apa = `${authors} (${year}). ${title}.`;
    if (journal) {
      apa += ` ${journal}.`;
    }
    if (citation.doi) {
      apa += ` https://doi.org/${citation.doi}`;
    }
    return apa;
  };

  const formatBibTeX = (citation: Citation) => {
    const key = `ref${citation.id}`;
    let bibtex = `@article{${key},\n`;
    
    if (citation.authors) {
      bibtex += `  author={${citation.authors}},\n`;
    }
    if (citation.title) {
      bibtex += `  title={${citation.title}},\n`;
    }
    if (citation.journal) {
      bibtex += `  journal={${citation.journal}},\n`;
    }
    if (citation.year) {
      bibtex += `  year={${citation.year}},\n`;
    }
    if (citation.volume) {
      bibtex += `  volume={${citation.volume}},\n`;
    }
    if (citation.doi) {
      bibtex += `  doi={${citation.doi}},\n`;
    }
    if (citation.url) {
      bibtex += `  url={${citation.url}},\n`;
    }
    
    bibtex += '}';
    return bibtex;
  };

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="border-t border-amber-200/30 mt-4 pt-4"
    >
      {/* Collapsible Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs font-medium text-amber-600 dark:text-amber-500 hover:text-amber-700 dark:hover:text-amber-400 transition-colors"
      >
        <BookOpen className="w-3.5 h-3.5" />
        <span>{citations.length} Reference{citations.length > 1 ? 's' : ''}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {/* Citation Cards */}
            <div className="mt-3 space-y-3">
              {citations.map((citation) => (
                <div
                  key={citation.id}
                  className="p-3 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/30 dark:border-amber-800/30 rounded-lg"
                >
                  {/* Title */}
                  <div className="flex items-start gap-2 mb-2">
                    <span className="text-xs font-bold text-amber-700 dark:text-amber-500 flex-shrink-0 mt-0.5">
                      [{citation.id}]
                    </span>
                    <div className="flex-1 min-w-0">
                      {citation.url ? (
                        <a
                          href={citation.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-amber-900 dark:text-amber-200 hover:text-amber-700 dark:hover:text-amber-100 transition-colors flex items-center gap-1"
                        >
                          {citation.title}
                          <ExternalLink className="w-3 h-3 flex-shrink-0" />
                        </a>
                      ) : (
                        <p className="text-xs font-medium text-amber-900 dark:text-amber-200">
                          {citation.title}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Authors */}
                  {citation.authors && (
                    <p className="text-xs text-amber-800 dark:text-amber-300 mb-1 pl-6">
                      {citation.authors}
                    </p>
                  )}

                  {/* Journal/Year */}
                  {(citation.journal || citation.year) && (
                    <p className="text-xs text-amber-700 dark:text-amber-400 pl-6 mb-2">
                      {citation.journal && <span className="italic">{citation.journal}</span>}
                      {citation.year && <span>. {citation.year}</span>}
                      {citation.volume && <span>;{citation.volume}</span>}
                    </p>
                  )}

                  {/* DOI */}
                  {citation.doi && (
                    <p className="text-xs text-amber-600 dark:text-amber-500 pl-6 mb-2">
                      doi:{citation.doi}
                    </p>
                  )}

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pl-6 mt-2">
                    <button
                      onClick={() => handleCopyAPA(citation)}
                      className="text-xs px-2 py-1 rounded bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-800/60 transition-colors flex items-center gap-1"
                    >
                      {copiedId === citation.id ? (
                        <Check className="w-3 h-3" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      APA
                    </button>
                    <button
                      onClick={() => handleCopyBibTeX(citation)}
                      className="text-xs px-2 py-1 rounded bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-800/60 transition-colors flex items-center gap-1"
                    >
                      {copiedId === citation.id ? (
                        <Check className="w-3 h-3" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      BibTeX
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Bulk Actions */}
            <div className="mt-3 flex items-center gap-2">
              <button
                onClick={handleDownloadAllBib}
                className="text-xs px-3 py-1.5 rounded-lg bg-amber-600 text-white hover:bg-amber-700 transition-colors flex items-center gap-1.5"
              >
                <Download className="w-3 h-3" />
                Download .bib
              </button>
              <span className="text-xs text-amber-600 dark:text-amber-500">
                {citations.length} citation{citations.length > 1 ? 's' : ''}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
