'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Dna, FlaskConical, Box, BookOpen, ArrowRight } from 'lucide-react';
import Link from 'next/link';

const HUBS = [
  {
    id: 'genetics',
    name: 'Genetics Hub',
    desc: 'Map patient genomics to drug response patterns. Integrated GWAS lookup and variant clinical significance analysis.',
    icon: Dna,
    color: 'purple',
    path: '/genetics',
    tags: ['Pharmacogenomics', 'Variant Mapping', 'Clinical Traits']
  },
  {
    id: 'lab',
    name: 'Molecular Lab',
    desc: 'Predict 119+ ADMET properties with Chemprop v2. Batch process SMILES and SDF files with AI-driven safety scoring.',
    icon: FlaskConical,
    color: 'amber',
    path: '/lab',
    tags: ['ADMET', 'Toxicity', 'Lead Optimization']
  },
  {
    id: 'studio',
    name: 'Creation Studio',
    desc: 'Transform complex research data into boardroom-ready presentations. Automated manuscript generation in docx format.',
    icon: Box,
    color: 'teal',
    path: '/studio',
    tags: ['Reporting', 'Presentation', 'Publication']
  },
  {
    id: 'literature',
    name: 'Literature Engine',
    desc: 'Deep semantic search across 35M+ papers. Real-time citation extraction and automated knowledge synthesis.',
    icon: BookOpen,
    color: 'blue',
    path: '/literature',
    tags: ['Deep Search', 'LLM Synthesis', 'Full-Text Access']
  }
];

export const HubsGrid = () => {
  return (
    <section className="py-24 bg-surface/50 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16">
          <h2 className="text-3xl md:text-5xl font-serif font-bold text-foreground mb-4">
            Unified Research Ecosystem
          </h2>
          <p className="text-foreground-muted text-lg max-w-2xl">
            A cohesive suite of intelligence hubs designed to accelerate every phase of pharmacological development.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {HUBS.map((hub, idx) => (
            <Link key={hub.id} href={hub.path}>
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -8 }}
                className="group p-8 rounded-[2rem] bg-surface-highlight border border-border hover:border-foreground/10 transition-all duration-500 cursor-pointer h-full flex flex-col hover:shadow-2xl hover:shadow-foreground/5"
              >
                <div className="flex items-start justify-between mb-8">
                  <div className={`p-4 rounded-2xl bg-${hub.color}-500/10 text-${hub.id === 'genetics' ? 'purple-500' : hub.id === 'lab' ? 'amber-500' : hub.id === 'studio' ? 'teal-500' : 'blue-500'} border border-${hub.id === 'genetics' ? 'purple-500' : hub.id === 'lab' ? 'amber-500' : hub.id === 'studio' ? 'teal-500' : 'blue-500'}/20`}>
                    <hub.icon size={32} />
                  </div>
                  <div className="p-2 rounded-full border border-border group-hover:bg-foreground group-hover:text-background transition-all">
                    <ArrowRight size={20} />
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-2xl font-serif font-bold text-foreground">{hub.name}</h3>
                  <p className="text-foreground-muted leading-relaxed">
                    {hub.desc}
                  </p>
                  
                  <div className="flex flex-wrap gap-2 pt-4">
                    {hub.tags.map(tag => (
                      <span key={tag} className="text-[10px] uppercase font-bold tracking-widest px-2 py-1 rounded-md bg-surface border border-border text-foreground-muted/70">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};
