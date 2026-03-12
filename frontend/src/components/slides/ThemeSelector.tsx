'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, Palette } from 'lucide-react';

export interface Theme {
  id: string;
  name: string;
  colors: string[];
  description: string;
}

const THEMES: Theme[] = [
  {
    id: 'ocean_gradient',
    name: 'Ocean Gradient',
    colors: ['#065A82', '#1C7293', '#F8FBFD'],
    description: 'Professional blue gradient for corporate presentations'
  },
  {
    id: 'forest_moss',
    name: 'Forest & Moss',
    colors: ['#2C5F2D', '#97BC62', '#F5F5F0'],
    description: 'Natural green tones for environmental topics'
  },
  {
    id: 'coral_energy',
    name: 'Coral Energy',
    colors: ['#2F3C7E', '#F96167', '#FFF9F5'],
    description: 'Bold and energetic for dynamic presentations'
  },
  {
    id: 'teal_trust',
    name: 'Teal Trust',
    colors: ['#028090', '#00A896', '#F0FAFA'],
    description: 'Trustworthy teal for healthcare and finance'
  },
  {
    id: 'charcoal_minimal',
    name: 'Charcoal Minimal',
    colors: ['#212121', '#36454F', '#F8F8F8'],
    description: 'Minimalist monochrome for modern design'
  },
  {
    id: 'berry_cream',
    name: 'Berry Cream',
    colors: ['#6B2737', '#D63384', '#FFF5F7'],
    description: 'Elegant berry tones for creative pitches'
  },
  {
    id: 'sage_calm',
    name: 'Sage Calm',
    colors: ['#556B2F', '#8FBC8F', '#F5F5F0'],
    description: 'Calming sage for wellness and mindfulness'
  },
  {
    id: 'cherry_bold',
    name: 'Cherry Bold',
    colors: ['#8B0000', '#DC143C', '#FFFAFA'],
    description: 'Bold red for impactful statements'
  },
  {
    id: 'midnight_executive',
    name: 'Midnight Executive',
    colors: ['#1A1A2E', '#16213E', '#F8F9FA'],
    description: 'Executive dark theme for leadership presentations'
  },
  {
    id: 'warm_terracotta',
    name: 'Warm Terracotta',
    colors: ['#E2725B', '#CC5500', '#FFF8F0'],
    description: 'Warm earth tones for authentic storytelling'
  }
];

interface ThemeSelectorProps {
  selectedTheme: string;
  onThemeChange: (themeId: string) => void;
}

export default function ThemeSelector({ selectedTheme, onThemeChange }: ThemeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  const selectedThemeData = THEMES.find(t => t.id === selectedTheme) || THEMES[0];

  return (
    <div className="relative">
      {/* Selector Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-amber-500 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex overflow-hidden border border-slate-200 dark:border-slate-700">
            {selectedThemeData.colors.map((color, i) => (
              <div
                key={i}
                style={{ backgroundColor: color }}
                className="flex-1"
              />
            ))}
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {selectedThemeData.name}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {selectedThemeData.description}
            </p>
          </div>
        </div>
        <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Menu */}
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 max-h-96 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg z-20"
            >
              <div className="p-2">
                <div className="flex items-center gap-2 px-3 py-2 mb-2 border-b border-slate-200 dark:border-slate-800">
                  <Palette className="w-4 h-4 text-slate-400" />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Choose Theme
                  </span>
                </div>
                
                {THEMES.map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => {
                      onThemeChange(theme.id);
                      setIsOpen(false);
                    }}
                    className={`w-full p-3 rounded-lg flex items-center gap-3 transition-colors ${
                      selectedTheme === theme.id
                        ? 'bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800 border border-transparent'
                    }`}
                  >
                    {/* Color Preview */}
                    <div className="w-10 h-10 rounded-lg flex overflow-hidden border border-slate-200 dark:border-slate-700 flex-shrink-0">
                      {theme.colors.map((color, i) => (
                        <div
                          key={i}
                          style={{ backgroundColor: color }}
                          className="flex-1"
                        />
                      ))}
                    </div>
                    
                    {/* Info */}
                    <div className="flex-1 text-left min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                        {theme.name}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {theme.description}
                      </p>
                    </div>
                    
                    {/* Checkmark */}
                    {selectedTheme === theme.id && (
                      <Check className="w-5 h-5 text-amber-600 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
