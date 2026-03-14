'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ExternalLink, BookOpen, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';

export interface PubMedArticle {
  pmid: string;
  title: string;
  authors: string[];
  journal: string;
  year: string;
  doi?: string;
  url: string;
  abstract_preview?: string;
  has_abstract?: boolean;
  volume?: string;
  issue?: string;
  pages?: string;
  pubdate?: string;
}

interface PubMedResultsProps {
  results: PubMedArticle[];
  query?: string;
  onCite?: (article: PubMedArticle) => void;
}

export default function PubMedResults({ results, query, onCite }: PubMedResultsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedPmid, setCopiedPmid] = useState<string | null>(null);

  const handleCopyAPA = (article: PubMedArticle) => {
    const apa = formatAPA(article);
    navigator.clipboard.writeText(apa);
    setCopiedPmid(article.pmid);
    toast.success('Citation copied (APA)');
    setTimeout(() => setCopiedPmid(null), 2000);
  };

  const formatAPA = (article: PubMedArticle) => {
    const authors = article.authors || [];
    const authorsStr = authors.length > 1 
      ? `${authors[0]} et al.` 
      : (authors[0] || 'Unknown author');
    const year = article.year || 'n.d.';
    const title = article.title;
    const journal = article.journal || '';
    
    let apa = `${authorsStr} (${year}). ${title}.`;
    if (journal) {
      apa += ` ${journal}.`;
    }
    if (article.doi) {
      apa += ` https://doi.org/${article.doi}`;
    }
    return apa;
  };

  if (!results || results.length === 0) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-sm">No PubMed articles found</p>
        {query && (
          <p className="text-xs mt-1 text-muted-foreground">
            Try: "{query}"
          </p>
        )}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-amber-200/30">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-amber-600" />
          <h3 className="text-sm font-semibold text-amber-700 dark:text-amber-500">
            PubMed Search Results
          </h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400">
            {results.length} articles
          </span>
        </div>
      </div>

      {/* Article Cards */}
      <div className="space-y-3">
        {results.map((article, index) => (
          <motion.article
            key={article.pmid}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/30 dark:border-amber-800/30 rounded-xl hover:border-amber-300/50 transition-colors"
          >
            {/* Title */}
            <div className="flex items-start gap-3 mb-2">
              <span className="text-xs font-bold text-amber-600 flex-shrink-0 mt-0.5">
                {index + 1}.
              </span>
              <div className="flex-1 min-w-0">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold text-amber-900 dark:text-amber-100 hover:text-amber-700 dark:hover:text-amber-200 transition-colors flex items-center gap-1.5"
                >
                  {article.title}
                  <ExternalLink className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                </a>
              </div>
            </div>

            {/* Authors */}
            {Array.isArray(article.authors) && article.authors.length > 0 ? (
              <p className="text-xs text-amber-800 dark:text-amber-300 mb-1.5 pl-6">
                {article.authors.length > 3
                  ? `${article.authors.slice(0, 3).join(', ')} et al.`
                  : article.authors.join(', ')}
              </p>
            ) : typeof article.authors === 'string' ? (
              <p className="text-xs text-amber-800 dark:text-amber-300 mb-1.5 pl-6">
                {article.authors}
              </p>
            ) : null}

            {/* Journal Info */}
            <div className="pl-6 flex flex-wrap items-center gap-2 text-xs text-amber-700 dark:text-amber-400">
              {article.journal && (
                <span className="italic">{article.journal}</span>
              )}
              {article.year && (
                <span>· {article.year}</span>
              )}
              {article.volume && (
                <span>Vol. {article.volume}</span>
              )}
              {article.doi && (
                <span className="text-amber-600 dark:text-amber-500">
                  doi:{article.doi}
                </span>
              )}
            </div>

            {/* Abstract Preview */}
            {article.abstract_preview && (
              <div className="mt-3 pl-6">
                <button
                  onClick={() => setExpandedId(expandedId === article.pmid ? null : article.pmid)}
                  className="text-xs text-amber-600 dark:text-amber-500 hover:text-amber-700 dark:hover:text-amber-400 flex items-center gap-1 transition-colors"
                >
                  {expandedId === article.pmid ? (
                    <>
                      <ChevronUp className="w-3 h-3" />
                      Hide abstract
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3" />
                      Show abstract
                    </>
                  )}
                </button>

                <AnimatePresence>
                  {expandedId === article.pmid && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <p className="text-xs text-amber-800 dark:text-amber-300 mt-2 leading-relaxed">
                        {article.abstract_preview}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-3 pl-6 flex items-center gap-2">
              <button
                onClick={() => handleCopyAPA(article)}
                className="text-xs px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-800/60 transition-colors flex items-center gap-1.5"
              >
                {copiedPmid === article.pmid ? (
                  <Check className="w-3 h-3" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
                Copy APA
              </button>
              {onCite && (
                <button
                  onClick={() => onCite(article)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-amber-600 text-white hover:bg-amber-700 transition-colors"
                >
                  Cite
                </button>
              )}
            </div>
          </motion.article>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-amber-200/30 flex items-center justify-between">
        <p className="text-xs text-amber-600 dark:text-amber-500">
          Source: PubMed® via NCBI E-utilities
        </p>
        <a
          href={`https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(query || '')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-amber-700 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-200 flex items-center gap-1 transition-colors"
        >
          View on PubMed
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </motion.div>
  );
}
