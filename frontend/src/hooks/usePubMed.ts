'use client';

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '@/config/api';

const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('sb-access-token') || localStorage.getItem('token');
  }
  return null;
};

export interface LiteratureArticle {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  journal: string;
  year: string;
  url: string;
  pdf_url?: string;
  pmid?: string;
  doi?: string;
  volume?: string;
  issue?: string;
  pages?: string;
  citation_count?: number;
  source: 'PubMed' | 'Semantic Scholar';
}

export interface LiteratureSearchResult {
  query: string;
  count: number;
  results: LiteratureArticle[];
  filters: {
    year_from: number | null;
    year_to: number | null;
  };
}

export function usePubMed() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (
    query: string,
    options?: {
      maxResults?: number;
      yearFrom?: number;
      yearTo?: number;
    }
  ): Promise<LiteratureSearchResult | null> => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        query,
        max_results: String(options?.maxResults || 20),
      });

      if (options?.yearFrom) {
        params.append('year_from', String(options.yearFrom));
      }
      if (options?.yearTo) {
        params.append('year_to', String(options.yearTo));
      }

      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/literature/search?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getArticle = useCallback(async (id: string, source: string): Promise<LiteratureArticle | null> => {
    // For now, search results include abstracts, so we can often find it in local state if we had one
    // But for a unified detail view, we can implement a specific endpoint if needed.
    // Given current backend, we just reuse the search-provided abstract.
    return null; 
  }, []);

  const getPDFLink = useCallback(async (pmid?: string, doi?: string): Promise<string | null> => {
    try {
      const token = getToken();
      const params = new URLSearchParams();
      if (pmid) params.append('pmid', pmid);
      if (doi) params.append('doi', doi);

      const response = await fetch(`${API_BASE_URL}/api/v1/literature/pdf/link?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      });

      if (!response.ok) return null;
      const data = await response.json();
      return data.pdf_url;
    } catch (err) {
      return null;
    }
  }, []);

  const downloadPDF = useCallback(async (pmid: string | undefined, doi: string | undefined, title: string) => {
    try {
      const token = getToken();
      const params = new URLSearchParams();
      if (pmid) params.append('pmid', pmid);
      if (doi) params.append('doi', doi);

      const response = await fetch(`${API_BASE_URL}/api/v1/literature/pdf/download?${params}`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      });

      if (!response.ok) throw new Error('Failed to download PDF');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download PDF');
    }
  }, []);

  return {
    search,
    getArticle,
    getPDFLink,
    downloadPDF,
    loading,
    error,
    clearError: () => setError(null),
  };
}
