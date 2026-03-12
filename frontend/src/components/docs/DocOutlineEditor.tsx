'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, ChevronDown, ChevronUp, FileText, Save, FileType } from 'lucide-react';

export interface DocSection {
  heading: string;
  key_points: string[];
  subsections?: DocSection[];
}

export interface DocOutline {
  title: string;
  subtitle?: string;
  doc_type: string;
  sections: DocSection[];
}

interface DocOutlineEditorProps {
  outline: DocOutline;
  onOutlineChange: (outline: DocOutline) => void;
  onGenerate: (outline: DocOutline) => void;
  onCancel: () => void;
}

const DOC_TYPES = [
  { id: 'report', name: 'Report', description: 'Executive summary with findings' },
  { id: 'manuscript', name: 'Manuscript', description: 'Academic paper format (IMRAD)' },
  { id: 'whitepaper', name: 'Whitepaper', description: 'Technical proposal document' },
  { id: 'case_report', name: 'Case Report', description: 'Clinical case presentation' }
];

export default function DocOutlineEditor({
  outline,
  onOutlineChange,
  onGenerate,
  onCancel
}: DocOutlineEditorProps) {
  const [expandedSection, setExpandedSection] = useState<number | null>(null);
  const [localOutline, setLocalOutline] = useState<DocOutline>(outline);

  const updateSection = (index: number, updates: Partial<DocSection>) => {
    const newSections = [...localOutline.sections];
    newSections[index] = { ...newSections[index], ...updates };
    const newOutline = { ...localOutline, sections: newSections };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const addSection = (afterIndex: number) => {
    const newSection: DocSection = {
      heading: 'New Section',
      key_points: ['Point 1']
    };
    const newSections = [...localOutline.sections];
    newSections.splice(afterIndex + 1, 0, newSection);
    const newOutline = { ...localOutline, sections: newSections };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const deleteSection = (index: number) => {
    if (localOutline.sections.length <= 1) return;
    const newSections = localOutline.sections.filter((_, i) => i !== index);
    const newOutline = { ...localOutline, sections: newSections };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  const moveSection = (fromIndex: number, direction: 'up' | 'down') => {
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1;
    if (toIndex < 0 || toIndex >= localOutline.sections.length) return;
    
    const newSections = [...localOutline.sections];
    const [moved] = newSections.splice(fromIndex, 1);
    newSections.splice(toIndex, 0, moved);
    const newOutline = { ...localOutline, sections: newSections };
    setLocalOutline(newOutline);
    onOutlineChange(newOutline);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-4"
    >
      {/* Header */}
      <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 dark:from-blue-950/30 to-indigo-50 dark:to-indigo-950/30 border border-blue-200 dark:border-blue-800 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <FileType className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div>
              <input
                type="text"
                value={localOutline.title}
                onChange={(e) => {
                  const newOutline = { ...localOutline, title: e.target.value };
                  setLocalOutline(newOutline);
                  onOutlineChange(newOutline);
                }}
                className="text-lg font-semibold bg-transparent border-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                placeholder="Document Title"
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
                  className="text-sm text-blue-700 dark:text-blue-300 bg-transparent border-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1 mt-1"
                  placeholder="Subtitle"
                />
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 font-medium">
              {localOutline.sections.length} sections
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 font-medium capitalize">
              {localOutline.doc_type}
            </span>
          </div>
        </div>
        
        {/* Document Type Selector */}
        <div className="mb-4">
          <label className="text-xs font-medium text-blue-700 dark:text-blue-300 mb-2 block">
            Document Type
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {DOC_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => {
                  const newOutline = { ...localOutline, doc_type: type.id };
                  setLocalOutline(newOutline);
                  onOutlineChange(newOutline);
                }}
                className={`p-2 rounded-lg border text-left transition-colors ${
                  localOutline.doc_type === type.id
                    ? 'bg-blue-100 dark:bg-blue-900/40 border-blue-300 dark:border-blue-700'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-blue-300'
                }`}
              >
                <p className="text-sm font-medium">{type.name}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{type.description}</p>
              </button>
            ))}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center gap-3 mt-4 pt-4 border-t border-blue-200 dark:border-blue-800">
          <button
            onClick={() => onGenerate(localOutline)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            Generate Document
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Section List */}
      <div className="space-y-3">
        {localOutline.sections.map((section, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.03 }}
            className={`p-4 rounded-xl border ${
              expandedSection === index
                ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-300 dark:border-blue-700'
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Move Controls */}
              <div className="flex flex-col gap-1 mt-1">
                <button
                  onClick={() => moveSection(index, 'up')}
                  disabled={index === 0}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded disabled:opacity-30"
                >
                  <ChevronUp className="w-4 h-4" />
                </button>
                <FileText className="w-4 h-4 text-slate-400" />
                <button
                  onClick={() => moveSection(index, 'down')}
                  disabled={index === localOutline.sections.length - 1}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded disabled:opacity-30"
                >
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>

              {/* Section Number */}
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 flex items-center justify-center font-bold text-sm">
                {index + 1}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <input
                    type="text"
                    value={section.heading}
                    onChange={(e) => updateSection(index, { heading: e.target.value })}
                    className="flex-1 font-semibold bg-transparent border-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                  />
                </div>

                {/* Quick Stats */}
                <div className="flex items-center gap-4 text-xs text-slate-600 dark:text-slate-400 mb-2">
                  <span className="flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    {section.key_points.length} key points
                  </span>
                  {section.subsections && section.subsections.length > 0 && (
                    <span className="flex items-center gap-1">
                      {section.subsections.length} subsections
                    </span>
                  )}
                </div>

                {/* Expand/Collapse */}
                <button
                  onClick={() => setExpandedSection(expandedSection === index ? null : index)}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1"
                >
                  {expandedSection === index ? (
                    <>
                      <ChevronDown className="w-3 h-3" />
                      Hide details
                    </>
                  ) : (
                    <>
                      <ChevronUp className="w-3 h-3" />
                      Edit section
                    </>
                  )}
                </button>

                {/* Expanded Editor */}
                {expandedSection === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800 space-y-3"
                  >
                    {/* Key Points Editor */}
                    <div>
                      <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">
                        Key Points
                      </label>
                      <div className="space-y-2">
                        {section.key_points.map((point, pi) => (
                          <div key={pi} className="flex items-center gap-2">
                            <input
                              type="text"
                              value={point}
                              onChange={(e) => {
                                const newPoints = [...section.key_points];
                                newPoints[pi] = e.target.value;
                                updateSection(index, { key_points: newPoints });
                              }}
                              className="flex-1 p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm"
                              placeholder={`Point ${pi + 1}`}
                            />
                            <button
                              onClick={() => {
                                const newPoints = section.key_points.filter((_, i) => i !== pi);
                                updateSection(index, { key_points: newPoints });
                              }}
                              className="p-2 hover:bg-red-100 dark:hover:bg-red-900/40 rounded text-red-600"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => updateSection(index, { key_points: [...section.key_points, 'New point'] })}
                          className="w-full p-2 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-400 hover:border-blue-500 hover:text-blue-600 flex items-center justify-center gap-2 text-sm"
                        >
                          <Plus className="w-4 h-4" />
                          Add key point
                        </button>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-2">
                      <button
                        onClick={() => addSection(index)}
                        className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg text-sm flex items-center gap-1.5"
                      >
                        <Plus className="w-4 h-4" />
                        Add section after
                      </button>
                      {localOutline.sections.length > 1 && (
                        <button
                          onClick={() => deleteSection(index)}
                          className="px-3 py-1.5 bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 rounded-lg text-sm flex items-center gap-1.5"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete section
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

      {/* Add Section at End */}
      <button
        onClick={() => addSection(localOutline.sections.length - 1)}
        className="w-full mt-4 p-4 border-2 border-dashed border-blue-300 dark:border-blue-700 rounded-xl text-blue-700 dark:text-blue-300 hover:border-blue-500 hover:text-blue-600 flex items-center justify-center gap-2 transition-colors"
      >
        <Plus className="w-5 h-5" />
        Add section at end
      </button>
    </motion.div>
  );
}
