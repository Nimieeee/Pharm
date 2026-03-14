'use client';

import React from 'react';
import { motion } from 'framer-motion';
import StatusBadge, { StatusType } from '../shared/StatusBadge';

export interface ADMETProperty {
  name: string;
  key: string;
  value: any;
  status: 'success' | 'warning' | 'danger' | 'neutral';
  interpretation: string;
  unit?: string;
}

interface ADMETPropertyCardProps {
  category: string;
  properties: ADMETProperty[];
  icon: React.ElementType;
}

export default function ADMETPropertyCard({ category, properties, icon: Icon }: ADMETPropertyCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="p-5 rounded-2xl bg-[var(--surface)] border border-[var(--border)] backdrop-blur-md flex flex-col h-full hover:border-[var(--border-hover)] transition-all group"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500/20 transition-colors">
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-primary)]">
          {category}
        </h3>
      </div>

      <div className="space-y-4 flex-1">
        {properties.map((prop, i) => (
          <div key={i} className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm font-medium text-[var(--text-secondary)]">
                {prop.name}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-medium text-[var(--text-primary)]">
                  {prop.value}{prop.unit}
                </span>
                <StatusBadge status={prop.status} label={prop.status} showLabel={false} className="capitalize" />
              </div>
            </div>
            {prop.interpretation && (
              <p className="text-[10px] text-[var(--text-muted)] italic leading-tight">
                {prop.interpretation}
              </p>
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}
