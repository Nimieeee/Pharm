'use client';

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '@/config/api';

const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

export interface PubMedArticle {
  pmid: string;
  title: string;
  authors: string[];
  journal: string;
  year: string;
  volume?: string;
  issue?: string;
  pages?: string;
  doi?: string;
  abstract?: string;
}

export interface PubMedSearchResult {
  query: string;
  count: number;
  results: PubMedArticle[];
  filters: {
    year_from: number | null;
    year_to: number | null;
  };
}

export interface PubMedArticleDetail extends PubMedArticle {
  abstract: string;
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
  ): Promise<PubMedSearchResult | null> => {
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
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/pubmed/search?${params}`, {
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

  const getArticle = useCallback(async (pmid: string): Promise<PubMedArticleDetail | null> => {
    setLoading(true);
    setError(null);

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/pubmed/article/${pmid}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch article: ${response.statusText}`);
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

  return {
    search,
    getArticle,
    loading,
    error,
    clearError: () => setError(null),
  };
}
