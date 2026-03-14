'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Database, Zap, Globe, ShieldCheck } from 'lucide-react';

const STATS = [
  { 
    label: 'Compounds Profiled', 
    value: '1.2M+', 
    desc: 'Deep molecular insights',
    icon: Database,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10'
  },
  { 
    label: 'Variant Associations', 
    value: '450K+', 
    desc: 'GWAS cataloged traits',
    icon: Zap,
    color: 'text-purple-500',
    bg: 'bg-purple-500/10'
  },
  { 
    label: 'Research Citations', 
    value: '35M+', 
    desc: 'Real-time PubMed sync',
    icon: Globe,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10'
  },
  { 
    label: 'Accuracy Rate', 
    value: '99.4%', 
    desc: 'Validated ADMET logic',
    icon: ShieldCheck,
    color: 'text-teal-500',
    bg: 'bg-teal-500/10'
  }
];

export const StatsShowcase = () => {
  return (
    <div className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {STATS.map((stat, idx) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className="relative group p-8 rounded-3xl bg-surface border border-border hover:border-border-hover transition-all duration-500 overflow-hidden shadow-soft"
            >
              {/* Background Glow */}
              <div className={`absolute -right-4 -bottom-4 w-32 h-32 ${stat.bg} blur-3xl rounded-full group-hover:scale-150 transition-transform duration-700 opacity-50`} />
              
              <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center mb-6 border border-white/5`}>
                <stat.icon size={24} strokeWidth={2} />
              </div>
              
              <div className="relative">
                <h3 className="text-4xl font-serif font-bold text-foreground mb-2 tracking-tight">
                  {stat.value}
                </h3>
                <p className="text-sm font-bold text-foreground-muted uppercase tracking-widest mb-1">
                  {stat.label}
                </p>
                <p className="text-xs text-foreground-muted/60">
                  {stat.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
