'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Trash2, GripVertical, ChevronDown, ChevronUp, Image, FileText, Save } from 'lucide-react';
import ThemeSelector from './ThemeSelector';

export interface Slide {
  slide_number: number;
  layout: 'title' | 'two_column' | 'bullets_only' | 'data_callout' | 'image_full';
  title: string;
  subtitle?: string;
  bullets: string[];
  speaker_notes?: string;
  image_prompt?: string | null;
  data?: { value: string; label: string } | null;
}

export interface SlideOutline {
  title: string;
  subtitle?: string;
  theme: string;
  slides: Slide[];
}

interface SlideOutlineEditorProps {
  outline: SlideOutline;
  onOutlineChange: (outline: SlideOutline) => void;
  onGenerate: (outline: SlideOutline) => void;
  onCancel: () => void;
}

export default function SlideOutlineEditor({
  outline,
  onOutlineChange,
  onGenerate,
  onCancel
}: SlideOutlineEditorProps) {
  const [expandedSlide, setExpandedSlide] = useState<number | null>(null);
  const [localOutline, setLocalOutline] = useState<SlideOutline>(outline);

  const updateSlide = (index: number, updates: Partial<Slide>) => {
    const newSlides = [...localOutline.slides];
    newSlides[index] = { ...newSlides[index], ...updates };
    const newOutline = { ...localOutline, slides: newSlides };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const addSlide = (afterIndex: number) => {
    const newSlide: Slide = {
      slide_number: afterIndex + 2,
      layout: 'bullets_only',
      title: 'New Slide',
      bullets: ['Point 1'],
      speaker_notes: '',
      image_prompt: null,
      data: null
    };
    const newSlides = [...localOutline.slides];
    newSlides.splice(afterIndex + 1, 0, newSlide);
    // Renumber
    newSlides.forEach((s, i) => s.slide_number = i + 1);
    const newOutline = { ...localOutline, slides: newSlides };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const deleteSlide = (index: number) => {
    if (localOutline.slides.length <= 2) return; // Keep at least title + 1 slide
    const newSlides = localOutline.slides.filter((_, i) => i !== index);
    newSlides.forEach((s, i) => s.slide_number = i + 1);
    const newOutline = { ...localOutline, slides: newSlides };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const moveSlide = (fromIndex: number, direction: 'up' | 'down') => {
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1;
    if (toIndex < 0 || toIndex >= localOutline.slides.length) return;
    
    const newSlides = [...localOutline.slides];
    const [moved] = newSlides.splice(fromIndex, 1);
    newSlides.splice(toIndex, 0, moved);
    newSlides.forEach((s, i) => s.slide_number = i + 1);
    const newOutline = { ...localOutline, slides: newSlides };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const getLayoutColor = (layout: string) => {
    switch (layout) {
      case 'title': return 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200';
      case 'two_column': return 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200';
      case 'data_callout': return 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200';
      case 'image_full': return 'bg-pink-100 dark:bg-pink-900/40 text-pink-800 dark:text-pink-200';
      default: return 'bg-slate-100 dark:bg-slate-900/40 text-slate-800 dark:text-slate-200';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header */}
      <div className="mb-4 p-4 bg-gradient-to-r from-amber-50 dark:from-amber-950/30 to-orange-50 dark:to-orange-950/30 border border-amber-200 dark:border-amber-800 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            <div>
              <input
                type="text"
                value={localOutline.title}
                onChange={(e) => {
                  const newOutline = { ...localOutline, title: e.target.value };
                  setLocalOutline(newOutline);
                  onOutlineChange(newOutline);
                }}
                className="text-lg font-semibold bg-transparent border-none focus:ring-2 focus:ring-amber-500 rounded px-2 py-1"
                placeholder="Presentation Title"
              />
              {localOutline.subtitle && (
                <input
                  type="text"
                  value={localOutline.subtitle}
                  onChange={(e) => {
                    const newOutline = { ...localOutline, subtitle: e.target.value };
                    setLocalOutline(newOutline);
                    onOutlineChange(newOutline);
                  }}
                  className="text-sm text-amber-700 dark:text-amber-300 bg-transparent border-none focus:ring-2 focus:ring-amber-500 rounded px-2 py-1 mt-1"
                  placeholder="Subtitle"
                />
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-200 font-medium">
              {localOutline.slides.length} slides
            </span>
          </div>
        </div>

        {/* Theme Selector */}
        <div className="mt-4 pt-4 border-t border-amber-200 dark:border-amber-800">
          <label className="text-xs text-amber-700 dark:text-amber-300 mb-2 block">Visual Theme</label>
          <ThemeSelector
            selectedTheme={localOutline.theme}
            onThemeChange={(newTheme) => {
              const newOutline = { ...localOutline, theme: newTheme };
              setLocalOutline(newOutline);
              onOutlineChange(newOutline);
            }}
          />
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center gap-3 mt-4 pt-4 border-t border-amber-200 dark:border-amber-800">
          <button
            onClick={() => onGenerate(localOutline)}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            Generate Slides
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Slide List */}
      <div className="space-y-3">
        {localOutline.slides.map((slide, index) => (
          <motion.div
            key={slide.slide_number}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.03 }}
            className={`p-4 rounded-xl border ${
              expandedSlide === index
                ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-700'
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Drag Handle */}
              <div className="flex flex-col gap-1 mt-1">
                <button
                  onClick={() => moveSlide(index, 'up')}
                  disabled={index === 0}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded disabled:opacity-30"
                >
                  <ChevronUp className="w-4 h-4" />
                </button>
                <GripVertical className="w-4 h-4 text-slate-400" />
                <button
                  onClick={() => moveSlide(index, 'down')}
                  disabled={index === localOutline.slides.length - 1}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded disabled:opacity-30"
                >
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>

              {/* Slide Number */}
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-200 flex items-center justify-center font-bold text-sm">
                {slide.slide_number}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <input
                    type="text"
                    value={slide.title}
                    onChange={(e) => updateSlide(index, { title: e.target.value })}
                    className="flex-1 font-semibold bg-transparent border-none focus:ring-2 focus:ring-amber-500 rounded px-2 py-1"
                  />
                  <span className={`text-xs px-2 py-1 rounded ml-2 ${getLayoutColor(slide.layout)}`}>
                    {slide.layout.replace('_', ' ')}
                  </span>
                </div>

                {/* Quick Stats */}
                <div className="flex items-center gap-4 text-xs text-slate-600 dark:text-slate-400 mb-2">
                  <span className="flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    {slide.bullets.length} bullets
                  </span>
                  {slide.image_prompt && (
                    <span className="flex items-center gap-1">
                      <Image className="w-3 h-3" />
                      Image planned
                    </span>
                  )}
                  {slide.speaker_notes && (
                    <span className="flex items-center gap-1">
                      Speaker notes
                    </span>
                  )}
                </div>

                {/* Expand/Collapse */}
                <button
                  onClick={() => setExpandedSlide(expandedSlide === index ? null : index)}
                  className="text-xs text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 flex items-center gap-1"
                >
                  {expandedSlide === index ? (
                    <>
                      <ChevronDown className="w-3 h-3" />
                      Hide details
                    </>
                  ) : (
                    <>
                      <ChevronUp className="w-3 h-3" />
                      Edit slide
                    </>
                  )}
                </button>

                {/* Expanded Editor */}
                {expandedSlide === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 pt-4 border-t border-amber-200 dark:border-amber-800 space-y-3"
                  >
                    {/* Layout Selector */}
                    <div>
                      <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Layout</label>
                      <select
                        value={slide.layout}
                        onChange={(e) => updateSlide(index, { layout: e.target.value as Slide['layout'] })}
                        className="w-full p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
                      >
                        <option value="title">Title Slide</option>
                        <option value="two_column">Two Column</option>
                        <option value="bullets_only">Bullets Only</option>
                        <option value="data_callout">Data Callout</option>
                        <option value="image_full">Image Full</option>
                      </select>
                    </div>

                    {/* Bullets Editor */}
                    <div>
                      <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Bullet Points</label>
                      <div className="space-y-2">
                        {slide.bullets.map((bullet, bi) => (
                          <div key={bi} className="flex items-center gap-2">
                            <input
                              type="text"
                              value={bullet}
                              onChange={(e) => {
                                const newBullets = [...slide.bullets];
                                newBullets[bi] = e.target.value;
                                updateSlide(index, { bullets: newBullets });
                              }}
                              className="flex-1 p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
                              placeholder={`Point ${bi + 1}`}
                            />
                            <button
                              onClick={() => {
                                const newBullets = slide.bullets.filter((_, i) => i !== bi);
                                updateSlide(index, { bullets: newBullets });
                              }}
                              className="p-2 hover:bg-red-100 dark:hover:bg-red-900/40 rounded text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => updateSlide(index, { bullets: [...slide.bullets, 'New point'] })}
                          className="w-full p-2 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-400 hover:border-amber-500 hover:text-amber-600 flex items-center justify-center gap-2 text-sm"
                        >
                          <Plus className="w-4 h-4" />
                          Add bullet
                        </button>
                      </div>
                    </div>

                    {/* Image Prompt */}
                    <div>
                      <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">
                        Image Prompt (optional)
                      </label>
                      <textarea
                        value={slide.image_prompt || ''}
                        onChange={(e) => updateSlide(index, { image_prompt: e.target.value || null })}
                        className="w-full p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
                        rows={2}
                        placeholder="Describe the AI-generated image for this slide..."
                      />
                    </div>

                    {/* Speaker Notes */}
                    <div>
                      <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">
                        Speaker Notes
                      </label>
                      <textarea
                        value={slide.speaker_notes || ''}
                        onChange={(e) => updateSlide(index, { speaker_notes: e.target.value })}
                        className="w-full p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
                        rows={2}
                        placeholder="What to say during this slide..."
                      />
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-2">
                      <button
                        onClick={() => addSlide(index)}
                        className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg text-sm flex items-center gap-1.5"
                      >
                        <Plus className="w-4 h-4" />
                        Add slide after
                      </button>
                      {localOutline.slides.length > 2 && (
                        <button
                          onClick={() => deleteSlide(index)}
                          className="px-3 py-1.5 bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 rounded-lg text-sm flex items-center gap-1.5"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete slide
                        </button>
                      )}
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Add Slide at End */}
      <button
        onClick={() => addSlide(localOutline.slides.length - 1)}
        className="w-full mt-4 p-4 border-2 border-dashed border-amber-300 dark:border-amber-700 rounded-xl text-amber-700 dark:text-amber-300 hover:border-amber-500 hover:text-amber-600 flex items-center justify-center gap-2 transition-colors"
      >
        <Plus className="w-5 h-5" />
        Add slide at end
      </button>
    </motion.div>
  );
}
