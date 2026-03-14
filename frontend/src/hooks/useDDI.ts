'use client';

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '@/config/api';

const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

export interface DDIInteraction {
  drug_a: string;
  drug_b: string;
  interaction_found: boolean;
  severity?: string;
  mechanism?: string;
  clinical_significance?: string;
  evidence_level?: string;
  description?: string;
  source?: string;
}

export interface PolypharmacyResult {
  drugs: string[];
  count: number;
  interactions: DDIInteraction[];
  summary: {
    major: number;
    moderate: number;
    minor: number;
  };
}

export function useDDI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkInteraction = useCallback(async (
    drugA: string,
    drugB: string
  ): Promise<DDIInteraction | null> => {
    if (!drugA.trim() || !drugB.trim()) {
      setError('Please enter both drug names');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/ddi/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        credentials: 'include',
        body: JSON.stringify({
          drug_a: drugA,
          drug_b: drugB,
        }),
      });

      if (!response.ok) {
        throw new Error(`DDI check failed: ${response.statusText}`);
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

  const checkPolypharmacy = useCallback(async (
    drugs: string[]
  ): Promise<PolypharmacyResult | null> => {
    if (drugs.length < 2) {
      setError('Please enter at least 2 drugs');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/ddi/polypharmacy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        credentials: 'include',
        body: JSON.stringify({ drugs }),
      });

      if (!response.ok) {
        throw new Error(`Polypharmacy check failed: ${response.statusText}`);
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
    checkInteraction,
    checkPolypharmacy,
    loading,
    error,
    clearError: () => setError(null),
  };
}

// Common drug presets for quick testing
export const DRUG_PRESETS = [
  { name: 'Warfarin + Aspirin', drugs: ['Warfarin', 'Aspirin'] },
  { name: 'Simvastatin + Ketoconazole', drugs: ['Simvastatin', 'Ketoconazole'] },
  { name: 'Methotrexate + NSAIDs', drugs: ['Methotrexate', 'Ibuprofen'] },
  { name: 'ACE Inhibitors + Potassium', drugs: ['Lisinopril', 'Potassium'] },
  { name: 'SSRI + Tramadol', drugs: ['Fluoxetine', 'Tramadol'] },
  { name: 'Metformin + Contrast', drugs: ['Metformin', 'Iohexol'] },
];
