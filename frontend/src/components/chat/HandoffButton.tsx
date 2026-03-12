'use client';

import React from 'react';
import { ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';

interface HandoffButtonProps {
  type: 'lab' | 'genetics' | 'studio';
  data: {
    smiles?: string;
    rsid?: string;
    docId?: string;
  };
  label?: string;
}

export default function HandoffButton({ type, data, label }: HandoffButtonProps) {
  const getHandoffUrl = () => {
    switch (type) {
      case 'lab':
        return data.smiles ? `/lab?smiles=${encodeURIComponent(data.smiles)}` : '/lab';
      case 'genetics':
        return data.rsid ? `/genetics?rsid=${encodeURIComponent(data.rsid)}` : '/genetics';
      case 'studio':
        return data.docId ? `/studio?doc=${encodeURIComponent(data.docId)}` : '/studio';
      default:
        return '/';
    }
  };

  const getLabel = () => {
    if (label) return label;
    switch (type) {
      case 'lab':
        return 'Open in Lab';
      case 'genetics':
        return 'View in Genetics';
      case 'studio':
        return 'Edit in Studio';
      default:
        return 'Open';
    }
  };

  const handleClick = () => {
    window.open(getHandoffUrl(), '_blank');
  };

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={handleClick}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors"
    >
      {getLabel()}
      <ExternalLink className="w-3 h-3" />
    </motion.button>
  );
}
