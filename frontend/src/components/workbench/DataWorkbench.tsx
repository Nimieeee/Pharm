'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  Image as ImageIcon,
  BarChart3,
  FileText,
  Table,
  Download,
  Loader2,
  Sparkles,
  Palette,
  X,
  CheckCircle2,
  AlertCircle,
  Moon,
  Sun,
  ArrowLeft
} from 'lucide-react';
import { useTheme } from '@/lib/theme-context';
import { useRouter } from 'next/navigation';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? '' // Use relative path for production (proxied by Vercel)
  : 'http://localhost:8000';

// ============================================================================
// TYPES
// ============================================================================

interface StylePreset {
  id: string;
  name: string;
  description: string;
  preview_colors: string[];
}

interface AnalysisResult {
  status: string;
  image: string | null;
  statistics: Record<string, any> | null;
  analysis: string | null;
  style_config: Record<string, any> | null;
  code: string | null;
  error: string | null;
}

interface DataPreview {
  filename: string;
  rows: number;
  columns: string[];
  dtypes: Record<string, string>;
  sample: Record<string, any>[];
  numeric_columns: string[];
  categorical_columns: string[];
}

// ============================================================================
// PRESET STYLES
// ============================================================================

const PRESET_STYLES: StylePreset[] = [
  {
    id: 'nature',
    name: 'Nature Journal',
    description: 'Clean, minimal style',
    preview_colors: ['#1f77b4', '#7f7f7f', '#2ca02c']
  },
  {
    id: 'ft',
    name: 'Financial Times',
    description: 'Salmon pink background',
    preview_colors: ['#fff1e5', '#990f3d', '#0d7680']
  },
  {
    id: 'economist',
    name: 'The Economist',
    description: 'Red accent, clean',
    preview_colors: ['#e3120b', '#1a1a1a', '#ffffff']
  },
  {
    id: 'dark',
    name: 'Dark Mode',
    description: 'Dark with bright accents',
    preview_colors: ['#1a1a2e', '#00d4ff', '#ff6b6b']
  }
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DataWorkbench() {
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();

  // State
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [styleImage, setStyleImage] = useState<File | null>(null);
  const [styleDescription, setStyleDescription] = useState('');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [preview, setPreview] = useState<DataPreview | null>(null);
  const [activeTab, setActiveTab] = useState<'visualization' | 'analysis' | 'data'>('visualization');
  const [error, setError] = useState<string | null>(null);

  // Sheet Selection
  const [availableSheets, setAvailableSheets] = useState<string[]>([]);
  const [showSheetSelector, setShowSheetSelector] = useState(false);

  // File handlers
  const handleDataDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setDataFile(file);
      loadPreview(file);
    }
  }, []);

  const handleDataSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDataFile(file);
      loadPreview(file);
    }
  }, []);

  const handleStyleImageSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setStyleImage(file);
      setSelectedPreset(null);
    }
  }, []);

  const loadPreview = async (file: File, sheetName?: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    setIsPreviewLoading(true);
    setPreview(null);
    setError(null);

    const formData = new FormData();
    formData.append('data_file', file);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workbench/preview`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.status === 409) {
        const data = await response.json();
        if (data.type === 'multiple_sheets') {
          setAvailableSheets(data.sheets);
          setShowSheetSelector(true);
          setIsPreviewLoading(false);
          return;
        }
      }

      if (response.ok) {
        const data = await response.json();
        setPreview(data);
        setShowSheetSelector(false);
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to load preview');
      }
    } catch (err) {
      console.error('Preview failed:', err);
      setError('Network error loading preview');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleSheetSelect = (sheet: string) => {
    if (dataFile) {
      loadPreview(dataFile, sheet);
    }
  };

  const handleAnalyze = async () => {
    if (!dataFile) return;

    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please sign in to use the workbench');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('data_file', dataFile);

    if (styleImage) {
      formData.append('style_image', styleImage);
    }

    const finalStyleDesc = selectedPreset
      ? `Use ${PRESET_STYLES.find(s => s.id === selectedPreset)?.name} style`
      : styleDescription;

    if (finalStyleDesc) {
      formData.append('style_description', finalStyleDesc);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workbench/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed');
      }

      setResult(data);
      setActiveTab('visualization');
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadImage = () => {
    if (!result?.image) return;

    const link = document.createElement('a');
    link.href = `data:image/png;base64,${result.image}`;
    link.download = `${dataFile?.name || 'chart'}_visualization.png`;
    link.click();
  };

  return (
    <div className="min-h-screen bg-[var(--background)] p-4 md:p-8">
      {/* Sheet Selector Modal */}
      <AnimatePresence>
        {showSheetSelector && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[var(--surface)] p-6 rounded-2xl border border-[var(--border)] shadow-xl max-w-md w-full mx-4"
            >
              <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">Select a Sheet</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {availableSheets.map(sheet => (
                  <button
                    key={sheet}
                    onClick={() => handleSheetSelect(sheet)}
                    className="w-full text-left px-4 py-3 rounded-xl hover:bg-[var(--surface-highlight)] transition-colors text-[var(--text-primary)] border border-transparent hover:border-[var(--border)]"
                  >
                    {sheet}
                  </button>
                ))}
              </div>
              <button
                onClick={() => {
                  setShowSheetSelector(false);
                  setDataFile(null);
                }}
                className="mt-4 w-full py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                Cancel
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div className="max-w-7xl mx-auto">
        {/* Header with Theme Toggle */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => router.push('/chat')}
                className="p-2 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors"
              >
                <ArrowLeft size={18} className="text-[var(--text-secondary)]" />
              </button>
              <h1 className="text-2xl md:text-3xl font-serif font-medium text-[var(--text-primary)] flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <BarChart3 size={20} className="text-white" />
                </div>
                Data Analysis Workbench
              </h1>
            </div>
            <p className="text-[var(--text-secondary)] ml-14">
              Upload data, customize visualization style, and get AI-powered analysis
            </p>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-highlight)] transition-colors"
          >
            {theme === 'light' ? (
              <Moon size={20} className="text-[var(--text-secondary)]" />
            ) : (
              <Sun size={20} className="text-[var(--text-secondary)]" />
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ============================================================ */}
          {/* LEFT PANEL - Configuration */}
          {/* ============================================================ */}
          <div className="space-y-6">
            {/* Data Upload */}
            <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
              <h2 className="text-lg font-serif font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Upload size={20} className="text-[var(--accent)]" />
                Data Upload
              </h2>

              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDataDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${dataFile
                  ? 'border-emerald-500 bg-emerald-500/5'
                  : 'border-[var(--border)] hover:border-indigo-500/50'
                  }`}
              >
                {isPreviewLoading ? (
                  <div className="flex flex-col items-center justify-center py-4">
                    <Loader2 className="animate-spin text-indigo-500 mb-2" size={32} />
                    <p className="text-[var(--text-primary)] font-medium">Scanning document...</p>
                    <p className="text-xs text-[var(--text-secondary)]">Extracting tables and cleaning data</p>
                  </div>
                ) : dataFile ? (
                  <div className="flex items-center justify-center gap-3">
                    <CheckCircle2 className="text-emerald-500" size={24} />
                    <div className="text-left">
                      <p className="font-medium text-[var(--text-primary)]">{dataFile.name}</p>
                      <p className="text-sm text-[var(--text-secondary)]">
                        {(dataFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => { setDataFile(null); setPreview(null); }}
                      className="ml-4 p-1 hover:bg-[var(--surface-highlight)] rounded"
                    >
                      <X size={16} className="text-[var(--text-secondary)]" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="mx-auto text-[var(--text-secondary)] mb-3" size={32} />
                    <p className="text-[var(--text-primary)] font-medium">
                      Drop your data file here
                    </p>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      CSV, Excel, PDF, DOCX, JSON supported
                    </p>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls,.json,.tsv,.pdf,.docx,.doc"
                      onChange={handleDataSelect}
                      className="hidden"
                      id="data-upload"
                    />
                    <label
                      htmlFor="data-upload"
                      className="mt-4 inline-block px-4 py-2 bg-indigo-500 text-white rounded-lg cursor-pointer hover:bg-indigo-600 transition-colors"
                    >
                      Browse Files
                    </label>
                  </>
                )}
              </div>

              {/* Data Preview */}
              {preview && (
                <div className="mt-4 p-4 bg-[var(--surface-highlight)] rounded-xl border border-[var(--border)]">
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {preview.rows} rows × {preview.columns.length} columns
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {preview.columns.slice(0, 6).map(col => (
                      <span key={col} className="px-2 py-1 text-xs bg-[var(--surface)] border border-[var(--border)] rounded-full text-[var(--text-primary)]">{col}</span>
                    ))}
                    {preview.columns.length > 6 && (
                      <span className="px-2 py-1 text-xs text-[var(--text-secondary)]">
                        +{preview.columns.length - 6} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Style Configuration */}
            <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
              <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Palette size={20} className="text-violet-500" />
                Visualization Style
              </h2>

              {/* Preset Styles */}
              <div className="mb-4">
                <p className="text-sm text-[var(--text-secondary)] mb-3">Quick Presets</p>
                <div className="grid grid-cols-2 gap-2">
                  {PRESET_STYLES.map(style => (
                    <button
                      key={style.id}
                      onClick={() => {
                        setSelectedPreset(style.id);
                        setStyleImage(null);
                        setStyleDescription('');
                      }}
                      className={`p-3 rounded-xl border text-left transition-all ${selectedPreset === style.id
                        ? 'border-indigo-500 bg-indigo-500/10'
                        : 'border-[var(--border)] hover:border-indigo-500/50'
                        }`}
                    >
                      <div className="flex gap-1 mb-2">
                        {style.preview_colors.map((color, i) => (
                          <div
                            key={i}
                            className="w-4 h-4 rounded-full border border-[var(--border)]"
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">{style.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{style.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Style Description */}
              <div className="mb-4">
                <p className="text-sm text-[var(--text-secondary)] mb-2">Or describe your style</p>
                <input
                  type="text"
                  value={styleDescription}
                  onChange={(e) => {
                    setStyleDescription(e.target.value);
                    setSelectedPreset(null);
                  }}
                  placeholder="e.g., 'Use pastel colors with dark background'"
                  className="w-full px-4 py-3 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Clone from Image */}
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Clone style from image</p>
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleStyleImageSelect}
                    className="hidden"
                    id="style-upload"
                  />
                  <label
                    htmlFor="style-upload"
                    className="flex items-center gap-2 px-4 py-2 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-lg cursor-pointer hover:border-indigo-500/50 transition-colors"
                  >
                    <ImageIcon size={16} />
                    <span className="text-sm">Upload Reference</span>
                  </label>
                  {styleImage && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                      <CheckCircle2 size={14} className="text-emerald-500" />
                      <span className="text-sm text-emerald-600 dark:text-emerald-400">{styleImage.name}</span>
                      <button onClick={() => setStyleImage(null)}>
                        <X size={14} className="text-[var(--text-secondary)]" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Analyze Button */}
            <motion.button
              onClick={handleAnalyze}
              disabled={!dataFile || isAnalyzing}
              whileTap={{ scale: 0.98 }}
              className={`w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-3 transition-all shadow-lg ${dataFile && !isAnalyzing
                ? 'bg-gradient-to-r from-cyan-500 to-violet-500 hover:from-cyan-600 hover:to-violet-600 shadow-cyan-500/25'
                : 'bg-[var(--border)] cursor-not-allowed shadow-none'
                }`}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  Analyze & Visualize
                </>
              )}
            </motion.button>

            {/* Error Display */}
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}
          </div>

          {/* ============================================================ */}
          {/* RIGHT PANEL - Results */}
          {/* ============================================================ */}
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-[var(--border)]">
              {[
                { id: 'visualization', label: 'Visualization', icon: BarChart3 },
                { id: 'analysis', label: 'Analysis', icon: FileText },
                { id: 'data', label: 'Raw Data', icon: Table }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 py-3 px-4 flex items-center justify-center gap-2 text-sm font-medium transition-colors ${activeTab === tab.id
                    ? 'text-[var(--accent)] border-b-2 border-[var(--accent)] bg-[var(--accent)]/5'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                >
                  <tab.icon size={16} />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-6 min-h-[400px]">
              <AnimatePresence mode="wait">
                {/* Visualization Tab */}
                {activeTab === 'visualization' && (
                  <motion.div
                    key="viz"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {result?.image ? (
                      <div className="space-y-4">
                        <img
                          src={`data:image/png;base64,${result.image}`}
                          alt="Visualization"
                          className="w-full rounded-xl border border-[var(--border)]"
                        />
                        <button
                          onClick={downloadImage}
                          className="flex items-center gap-2 px-4 py-2 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-lg hover:border-indigo-500/50 transition-colors"
                        >
                          <Download size={16} />
                          Download PNG
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-64 text-[var(--text-secondary)]">
                        <BarChart3 size={48} className="mb-4 opacity-30" />
                        <p>Upload data and click Analyze to generate visualization</p>
                      </div>
                    )}
                  </motion.div>
                )}

                {/* Analysis Tab */}
                {activeTab === 'analysis' && (
                  <motion.div
                    key="analysis"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="prose prose-sm dark:prose-invert max-w-none"
                  >
                    {result?.analysis ? (
                      <div
                        className="text-[var(--text-primary)]"
                        dangerouslySetInnerHTML={{
                          __html: result.analysis
                            .replace(/^### /gm, '<h3>')
                            .replace(/^## /gm, '<h2>')
                            .replace(/^# /gm, '<h1>')
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.*?)\*/g, '<em>$1</em>')
                            .replace(/\n/g, '<br/>')
                        }}
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center h-64 text-[var(--text-secondary)]">
                        <FileText size={48} className="mb-4 opacity-30" />
                        <p>Analysis will appear here after processing</p>
                      </div>
                    )}
                  </motion.div>
                )}

                {/* Data Tab */}
                {activeTab === 'data' && (
                  <motion.div
                    key="data"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {preview ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-[var(--border)]">
                              {preview.columns.map(col => (
                                <th
                                  key={col}
                                  className="px-3 py-2 text-left font-medium text-[var(--text-primary)]"
                                >
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {preview.sample.map((row, i) => (
                              <tr key={i} className="border-b border-[var(--border)]">
                                {preview.columns.map(col => (
                                  <td
                                    key={col}
                                    className="px-3 py-2 text-[var(--text-secondary)]"
                                  >
                                    {String(row[col] ?? '')}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-64 text-[var(--text-secondary)]">
                        <Table size={48} className="mb-4 opacity-30" />
                        <p>Upload a data file to preview</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
