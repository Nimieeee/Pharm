'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

interface UploadZoneProps {
  onFileUpload: (file: File) => void;
  isLoading: boolean;
  acceptedFormats?: string;
  label?: string;
}

export default function UploadZone({ 
  onFileUpload, 
  isLoading, 
  acceptedFormats = ".txt", 
  label = "Upload genomic data" 
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFileUpload(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileUpload(file);
  };

  return (
    <div className="relative">
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={`
          relative cursor-pointer overflow-hidden
          p-12 border-2 border-dashed rounded-3xl transition-all duration-300
          flex flex-col items-center justify-center text-center
          ${isDragging 
            ? 'border-purple-500 bg-purple-500/10 scale-[1.02]' 
            : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'}
          ${isLoading ? 'pointer-events-none' : ''}
        `}
      >
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="relative">
                <Loader2 className="w-12 h-12 text-purple-500 animate-spin" />
                <div className="absolute inset-0 blur-xl bg-purple-500/50 animate-pulse" />
              </div>
              <div>
                <p className="text-lg font-bold text-white">Analyzing DNA</p>
                <p className="text-sm text-slate-400">Processing millions of variants...</p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 flex items-center justify-center mx-auto mb-4 border border-purple-500/30">
                <Upload className="w-8 h-8 text-purple-400" />
              </div>
              
              <div>
                <p className="text-xl font-bold text-white mb-1">{label}</p>
                <p className="text-sm text-slate-400">
                  Drop your 23andMe or AncestryDNA raw data file here
                </p>
              </div>

              <div className="flex items-center justify-center gap-6 pt-6">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <CheckCircle className="w-4 h-4 text-green-500/50" />
                  Supports .txt files
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <ShieldCheck className="w-4 h-4 text-blue-500/50" />
                  100% Client-side privacy
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={acceptedFormats}
          className="hidden"
        />
      </motion.div>

      {/* Subtle Bottom Information */}
      <div className="mt-4 flex items-center justify-between px-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold flex items-center gap-1.5">
          <AlertCircle className="w-3 h-3" />
          No data is stored on our servers
        </p>
        <div className="flex gap-2">
          {['23andMe', 'AncestryDNA'].map(brand => (
            <span key={brand} className="text-[9px] px-2 py-0.5 rounded bg-white/5 border border-white/5 text-slate-500 font-mono">
              {brand}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
