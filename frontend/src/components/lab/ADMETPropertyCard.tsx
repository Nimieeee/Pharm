'use client';

import React from 'react';
import { motion } from 'framer-motion';
import StatusBadge, { StatusType } from '../shared/StatusBadge';
import { useTheme } from '@/lib/theme-context';

export interface ADMETProperty {
  name: string;
  value: string | number;
  status: StatusType;
  unit?: string;
}

interface ADMETPropertyCardProps {
  category: string;
  properties: ADMETProperty[];
  icon: React.ElementType;
}

export default function ADMETPropertyCard({ category, properties, icon: Icon }: ADMETPropertyCardProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex flex-col h-full hover:border-white/20 transition-all group"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20 transition-colors">
          <Icon className="w-5 h-5" />
        </div>
        <h3 className={`text-sm font-semibold uppercase tracking-wider ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
          {category}
        </h3>
      </div>

      <div className="space-y-4 flex-1">
        {properties.map((prop, i) => (
          <div key={i} className="flex items-center justify-between gap-4">
            <span className={`text-sm font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              {prop.name}
            </span>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-mono font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
                {prop.value}{prop.unit}
              </span>
              <StatusBadge status={prop.status} label={prop.status} className="capitalize" />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
