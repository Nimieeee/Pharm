'use client';

import { useState, useEffect } from 'react';
import { Search, Calendar, FileText, ExternalLink, Copy, BookOpen } from 'lucide-react';
import HubLayout from '@/components/shared/HubLayout';
import { LoadingAnimation } from '@/components/shared/LoadingAnimation';
import { usePubMed, LiteratureArticle } from '@/hooks/usePubMed';

const EXAMPLE_QUERIES = [
  'SGLT2 inhibitors diabetes',
  'CAR-T therapy lymphoma',
  'GLP-1 agonists weight loss',
  'PD-1 checkpoint inhibitors',
  'Crispr gene editing',
];

export default function LiteratureDashboard() {
  const { search, loading, error, clearError } = usePubMed();
  
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LiteratureArticle[]>([]);
  const [resultCount, setResultCount] = useState(0);
  const [yearFrom, setYearFrom] = useState<number | ''>('');
  const [yearTo, setYearTo] = useState<number | ''>('');
  const [maxResults, setMaxResults] = useState(20);
  const [expandedAbstract, setExpandedAbstract] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Random example on mount
  const [exampleQuery, setExampleQuery] = useState('');
  useEffect(() => {
    setExampleQuery(EXAMPLE_QUERIES[Math.floor(Math.random() * EXAMPLE_QUERIES.length)]);
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    const result = await search(query, {
      maxResults: maxResults,
      yearFrom: yearFrom || undefined,
      yearTo: yearTo || undefined,
    });

    if (result) {
      setResults(result.results);
      setResultCount(result.count);
      setHasSearched(true);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const copyCitation = (article: LiteratureArticle) => {
    const authorsArr = Array.isArray(article.authors) ? article.authors : [];
    const authors = authorsArr.slice(0, 3).join(', ') + (authorsArr.length > 3 ? ' et al.' : '');
    const citation = `${authors} (${article.year}). ${article.title}. ${article.journal}. ${article.volume || ''}${article.issue ? `(${article.issue})` : ''}:${article.pages || ''}. DOI: ${article.doi || 'N/A'}`;
    navigator.clipboard.writeText(citation);
  };

  return (
    <HubLayout
      title="Literature Search"
      subtitle="Search PubMed biomedical literature"
      icon={Search}
      accentColor="teal"
    >
      <div className="max-w-5xl mx-auto">
        {/* Search Box */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 mb-6">
          {/* Search Input - Mobile Responsive */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={exampleQuery || "Search PubMed..."}
              className="flex-1 w-full px-4 py-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-teal-600 hover:bg-teal-700 disabled:bg-slate-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shrink-0 sm:w-auto w-full"
            >
              {loading ? <Search className="w-5 h-5 animate-pulse" /> : <Search className="w-5 h-5" />}
              Search
            </button>
          </div>

          {/* Filters - Mobile Responsive */}
          <div className="flex flex-wrap gap-3 sm:gap-4 items-center">
            <div className="flex items-center gap-2 flex-wrap">
              <Calendar className="w-4 h-4 text-[var(--text-muted)] shrink-0" />
              <span className="text-sm text-[var(--text-muted)] shrink-0">Year:</span>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="From"
                  min={1900}
                  max={2030}
                  className="w-16 sm:w-20 px-2 sm:px-3 py-1.5 text-sm rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[var(--text-muted)]">-</span>
                <input
                  type="number"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value ? parseInt(e.target.value) : '')}
                  placeholder="To"
                  min={1900}
                  max={2030}
                  className="w-16 sm:w-20 px-2 sm:px-3 py-1.5 text-sm rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <FileText className="w-4 h-4 text-[var(--text-muted)] shrink-0" />
              <span className="text-sm text-[var(--text-muted)] shrink-0">Results:</span>
              <select
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value))}
                className="px-2 sm:px-3 py-1.5 text-sm rounded-lg bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-teal-500 shrink-0"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-600 dark:text-red-400">{error}</p>
            <button onClick={clearError} className="text-sm text-red-500 underline mt-2">Dismiss</button>
          </div>
        )}

        {/* Results */}
        {hasSearched && (
          <div className="mb-4">
            <p className="text-[var(--text-muted)]">
              Found <span className="font-semibold text-[var(--text-primary)]">{resultCount}</span> articles
              {(yearFrom || yearTo) && (
                <span className="ml-2">
                  ({yearFrom || '1900'} - {yearTo || new Date().getFullYear()})
                </span>
              )}
            </p>
          </div>
        )}

        {/* Articles */}
        <div className="space-y-4">
          {loading && (
            <div className="py-20">
              <LoadingAnimation label="Searching 30M+ biomedical records from PubMed..." />
            </div>
          )}
          
          {!loading && results.map((article) => (
            <div
              key={article.pmid}
              className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 hover:border-teal-500/50 transition-colors"
            >
              <div className="flex gap-4">
                <div className="flex-1">
                  <a
                    href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-lg font-semibold text-[var(--text-primary)] hover:text-teal-600 transition-colors flex items-start gap-2"
                  >
                    {article.title}
                    <ExternalLink className="w-4 h-4 mt-1 flex-shrink-0" />
                  </a>
                  
                  <p className="text-sm text-[var(--text-muted)] mt-1">
                    {Array.isArray(article.authors) ? (
                      <>
                        {article.authors.slice(0, 3).join(', ')}
                        {article.authors.length > 3 && ' et al.'}
                      </>
                    ) : (
                      'Unknown Author'
                    )}
                  </p>
                  
                  <p className="text-sm text-[var(--text-secondary)] mt-1">
                    <span className="font-medium">{article.journal}</span>
                    {article.volume && <span> {article.volume}</span>}
                    {article.issue && <span>({article.issue})</span>}
                    {article.pages && <span>:{article.pages}</span>}
                    {article.year && <span> ({article.year})</span>}
                    {article.doi && (
                      <a
                        href={`https://doi.org/${article.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-teal-600 hover:underline"
                      >
                        DOI: {article.doi}
                      </a>
                    )}
                  </p>

                  {/* Abstract */}
                  {article.abstract && (
                    <div className="mt-3">
                      {expandedAbstract === article.id ? (
                        <div>
                          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                            {article.abstract}
                          </p>
                          <button
                            onClick={() => setExpandedAbstract(null)}
                            className="text-sm text-teal-600 mt-2"
                          >
                            Show less
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setExpandedAbstract(article.id || null)}
                          className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1"
                        >
                          <BookOpen className="w-4 h-4" />
                          Show abstract
                        </button>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => copyCitation(article)}
                    className="p-2 rounded-lg bg-[var(--background)] border border-[var(--border)] hover:border-teal-500/50 transition-colors text-[var(--text-muted)] hover:text-teal-600"
                    title="Copy citation"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {hasSearched && results.length === 0 && !loading && (
            <div className="text-center py-12 text-[var(--text-muted)]">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No articles found. Try a different search query.</p>
            </div>
          )}
        </div>

        {/* Source Attribution */}
        {hasSearched && results.length > 0 && (
          <p className="text-center text-xs text-[var(--text-muted)] mt-8">
            Source: PubMed via NCBI E-utilities
          </p>
        )}
      </div>
    </HubLayout>
  );
}
