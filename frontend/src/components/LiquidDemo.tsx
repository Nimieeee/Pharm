'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  LiquidGlassContainer, 
  RefractiveCard, 
  LiquidButton, 
  GlassDivider,
  GlassBadge 
} from '@/components/ui/LiquidGlass';
import { 
  BarChart3, 
  Upload, 
  Sparkles, 
  TrendingUp, 
  FileSpreadsheet,
  Loader2 
} from 'lucide-react';

export default function LiquidDemo() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleStartAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 3000);
  };

  return (
    <LiquidGlassContainer className="flex items-center justify-center p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
        className="w-full max-w-4xl"
      >
        <RefractiveCard className="p-6 md:p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center">
                <BarChart3 size={20} className="text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                  Data Analysis Workbench
                </h2>
                <p className="text-sm text-[var(--text-secondary)]">
                  AI-Powered Scientific Analysis
                </p>
              </div>
            </div>
            <GlassBadge variant="success">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
              Ready
            </GlassBadge>
          </div>

          <GlassDivider className="mb-6" />

          {/* Upload Area */}
          <div className="mb-6">
            <div className="border-2 border-dashed border-[var(--glass-border)] rounded-xl p-8 text-center hover:border-cyan-500/50 transition-colors cursor-pointer">
              <Upload size={32} className="mx-auto mb-3 text-[var(--text-secondary)]" />
              <p className="text-sm font-medium text-[var(--text-primary)] mb-1">
                Drop your data files here
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                CSV, Excel, or JSON files up to 10MB
              </p>
            </div>
          </div>

          {/* Mock Data Preview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <RefractiveCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <FileSpreadsheet size={16} className="text-cyan-500" />
                <span className="text-xs font-medium text-[var(--text-secondary)]">Dataset</span>
              </div>
              <p className="text-2xl font-bold text-[var(--text-primary)]">1,247</p>
              <p className="text-xs text-[var(--text-secondary)]">rows loaded</p>
            </RefractiveCard>

            <RefractiveCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-violet-500" />
                <span className="text-xs font-medium text-[var(--text-secondary)]">Correlation</span>
              </div>
              <p className="text-2xl font-bold text-[var(--text-primary)]">0.847</p>
              <p className="text-xs text-[var(--text-secondary)]">R² value</p>
            </RefractiveCard>

            <RefractiveCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-amber-500" />
                <span className="text-xs font-medium text-[var(--text-secondary)]">P-Value</span>
              </div>
              <p className="text-2xl font-bold text-[var(--text-primary)]">&lt;0.001</p>
              <p className="text-xs text-emerald-500">Significant</p>
            </RefractiveCard>
          </div>

          <GlassDivider className="mb-6" />

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <LiquidButton 
              variant="primary" 
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 size={16} className="inline mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={16} className="inline mr-2" />
                  Start Analysis
                </>
              )}
            </LiquidButton>
            
            <LiquidButton variant="secondary">
              Clone Style
            </LiquidButton>
          </div>
        </RefractiveCard>

        {/* Footer Note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-xs text-[var(--text-secondary)] mt-4"
        >
          Powered by Mistral Large & Pixtral Vision
        </motion.p>
      </motion.div>
    </LiquidGlassContainer>
  );
}
