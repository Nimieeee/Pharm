'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Search, FlaskConical, ShieldCheck, Microscope, ArrowRight } from 'lucide-react';

const STAGES = [
  {
    id: 'discovery',
    name: 'Drug Discovery',
    desc: 'Target identification and validation using genomics.',
    icon: Search,
    active: true
  },
  {
    id: 'preclinical',
    name: 'Preclinical Lab',
    desc: 'ADMET profiling and lead optimization.',
    icon: FlaskConical,
    active: true
  },
  {
    id: 'clinical',
    name: 'Clinical Trials',
    desc: 'Evidence synthesis and trial mapping.',
    icon: ShieldCheck,
    active: false
  },
  {
    id: 'regulatory',
    name: 'Regulatory Studio',
    desc: 'Automated dossier and manuscript creation.',
    icon: Microscope,
    active: false
  }
];

export const PipelineShowcase = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-3xl md:text-5xl font-serif font-bold text-foreground">
            Digital Pipeline Acceleration
          </h2>
          <p className="text-foreground-muted text-lg max-w-2xl mx-auto">
            From molecular discovery to regulatory documentation—Benchside powers the entire development lifecycle.
          </p>
        </div>

        <div className="relative">
          {/* Connector Line */}
          <div className="absolute top-1/2 left-0 w-full h-1 bg-border -translate-y-1/2 hidden lg:block" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 relative">
            {STAGES.map((stage, idx) => (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.15 }}
                className="relative flex flex-col items-center text-center group"
              >
                {/* Stage Icon Circle */}
                <div className={`
                  w-20 h-20 rounded-full flex items-center justify-center mb-6 relative z-10 
                  border-4 border-surface shadow-2xl transition-all duration-500
                  ${stage.active 
                    ? 'bg-orange-500 text-black shadow-orange-500/20' 
                    : 'bg-surface-highlight text-foreground-muted grayscale'}
                `}>
                  <stage.icon size={32} />
                  {stage.active && (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="absolute inset-0 bg-orange-500 rounded-full -z-10 blur-lg"
                    />
                  )}
                </div>

                <h3 className="text-xl font-bold text-foreground mb-2">{stage.name}</h3>
                <p className="text-sm text-foreground-muted max-w-[200px] leading-relaxed">
                  {stage.desc}
                </p>

                {/* Mobile/Tablet Arrow */}
                {idx < STAGES.length - 1 && (
                  <div className="mt-6 text-foreground-muted lg:hidden rotate-90 md:rotate-0">
                    <ArrowRight size={24} />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
