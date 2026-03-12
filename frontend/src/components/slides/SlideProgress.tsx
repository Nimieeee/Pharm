'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Loader2, Image as ImageIcon, FileText, Package } from 'lucide-react';

interface SlideProgressProps {
  currentStep: 'content' | 'images' | 'assembly' | 'complete';
  currentSlide: number;
  totalSlides: number;
  totalImages: number;
  message: string;
  onDownload?: () => void;
}

export default function SlideProgress({
  currentStep,
  currentSlide,
  totalSlides,
  totalImages,
  message,
  onDownload
}: SlideProgressProps) {
  const getStepStatus = (step: string) => {
    const steps = ['content', 'images', 'assembly', 'complete'];
    const currentIndex = steps.indexOf(currentStep);
    const stepIndex = steps.indexOf(step);
    
    if (step === 'complete') return currentStep === 'complete' ? 'active' : 'pending';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  const StepIndicator = ({ step, icon: Icon, label }: { step: string; icon: any; label: string }) => {
    const status = getStepStatus(step);
    
    return (
      <div className="flex flex-col items-center gap-2">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
          status === 'completed' ? 'bg-emerald-500 text-white' :
          status === 'active' ? 'bg-amber-500 text-white animate-pulse' :
          'bg-slate-200 dark:bg-slate-800 text-slate-400'
        }`}>
          {status === 'completed' ? (
            <CheckCircle className="w-6 h-6" />
          ) : (
            <Icon className="w-6 h-6" />
          )}
        </div>
        <span className={`text-xs font-medium ${
          status === 'completed' ? 'text-emerald-600 dark:text-emerald-400' :
          status === 'active' ? 'text-amber-600 dark:text-amber-400' :
          'text-slate-500'
        }`}>
          {label}
        </span>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4 p-8"
    >
      {/* Centered Loading Animation */}
      {currentStep !== 'complete' && (
        <div className="text-center mb-8">
          <div className="relative inline-block mb-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-20 h-20 border-4 border-amber-200 dark:border-amber-900/40 border-t-amber-500 rounded-full"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
            </div>
          </div>
          
          <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
            {currentStep === 'content' && 'Writing slides...'}
            {currentStep === 'images' && 'Generating images...'}
            {currentStep === 'assembly' && 'Assembling presentation...'}
          </h3>
          
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {message}
          </p>
        </div>
      )}

      {/* Progress Bar */}
      {currentStep !== 'complete' && (
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-2">
            <span>Progress</span>
            <span>{currentSlide} / {totalSlides} slides</span>
          </div>
          <div className="h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(currentSlide / totalSlides) * 100}%` }}
              transition={{ duration: 0.3 }}
              className="h-full bg-gradient-to-r from-amber-500 to-orange-500"
            />
          </div>
        </div>
      )}

      {/* Step Indicators */}
      <div className="flex items-center justify-center gap-8 mb-8">
        <StepIndicator
          step="content"
          icon={FileText}
          label="Content"
        />
        <div className={`w-12 h-0.5 ${
          getStepStatus('images') !== 'pending' ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-800'
        }`} />
        <StepIndicator
          step="images"
          icon={ImageIcon}
          label="Images"
        />
        <div className={`w-12 h-0.5 ${
          getStepStatus('assembly') !== 'pending' ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-800'
        }`} />
        <StepIndicator
          step="assembly"
          icon={Package}
          label="Assembly"
        />
      </div>

      {/* Completion State */}
      {currentStep === 'complete' && onDownload && (
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-emerald-500 flex items-center justify-center">
            <CheckCircle className="w-12 h-12 text-white" />
          </div>
          
          <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mb-2">
            Presentation Ready!
          </h3>
          
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
            {totalSlides} slides generated successfully
            {totalImages > 0 && ` with ${totalImages} AI-generated images`}
          </p>
          
          <button
            onClick={onDownload}
            className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-medium flex items-center gap-2 mx-auto transition-colors"
          >
            <Package className="w-5 h-5" />
            Download PowerPoint
          </button>
        </motion.div>
      )}

      {/* Detailed Status */}
      {currentStep !== 'complete' && (
        <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-xl">
          <div className="flex items-start gap-3">
            <Loader2 className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5 animate-spin" />
            <div>
              <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                {currentStep === 'content' && `Writing slide ${currentSlide} of ${totalSlides}...`}
                {currentStep === 'images' && `Generating image ${currentSlide} of ${totalImages}...`}
                {currentStep === 'assembly' && 'Finalizing presentation...'}
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                {message}
              </p>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
