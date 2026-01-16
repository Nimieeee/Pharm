'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    Upload,
    Loader2,
    Download,
    FlaskConical,
    ChevronDown,
    ChevronRight,
    Copy,
    Check,
    ArrowLeft,
    RefreshCw
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/theme-context';
import { API_BASE_URL } from '@/config/api';

// =============================================================================
// TYPES
// =============================================================================

interface LabReportTemplate {
    id: string;
    name: string;
    description: string;
}

interface LabReportSections {
    introduction: string | null;
    materials_methods: string | null;
    results: string | null;
    discussion: string | null;
    conclusion: string | null;
}

interface LabReportResult {
    status: string;
    title: string;
    sections: LabReportSections;
    references: Array<{ text: string }>;
    full_report: string;
    error: string | null;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LabReportUI() {
    const { theme } = useTheme();
    const router = useRouter();

    // State
    const [experimentType, setExperimentType] = useState('');
    const [customType, setCustomType] = useState('');
    const [instructions, setInstructions] = useState('');
    const [dataFile, setDataFile] = useState<File | null>(null);
    const [methodologyFile, setMethodologyFile] = useState<File | null>(null);
    const [dataImage, setDataImage] = useState<File | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState<LabReportResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['introduction', 'results']));
    const [copied, setCopied] = useState(false);
    const [templates, setTemplates] = useState<LabReportTemplate[]>([]);

    // Fetch templates on mount
    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch(`${API_BASE_URL}/api/v1/lab-report/templates`, {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                });
                if (response.ok) {
                    const data = await response.json();
                    setTemplates(data.templates);
                }
            } catch (err) {
                console.error('Failed to fetch templates:', err);
            }
        };
        fetchTemplates();
    }, []);

    const handleGenerate = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setError('Please sign in to generate lab reports');
            return;
        }

        const finalExperimentType = experimentType === 'custom' ? customType : experimentType;
        if (!finalExperimentType) {
            setError('Please select or enter an experiment type');
            return;
        }

        setIsGenerating(true);
        setError(null);
        setResult(null);

        try {
            const formData = new FormData();
            formData.append('experiment_type', finalExperimentType);
            formData.append('conversation_id', crypto.randomUUID()); // New conversation for lab report

            if (instructions) {
                formData.append('instructions', instructions);
            }
            if (dataFile) {
                formData.append('data_file', dataFile);
            }
            if (methodologyFile) {
                formData.append('methodology_file', methodologyFile);
            }
            if (dataImage) {
                formData.append('data_image', dataImage);
            }

            const response = await fetch(`${API_BASE_URL}/api/v1/lab-report/generate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Generation failed');
            }

            setResult(data);
            // Expand all sections by default when report is generated
            setExpandedSections(new Set(['introduction', 'materials_methods', 'results', 'discussion', 'conclusion', 'references']));
        } catch (err: any) {
            setError(err.message || 'Generation failed');
        } finally {
            setIsGenerating(false);
        }
    };

    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    const copyToClipboard = async () => {
        if (result?.full_report) {
            await navigator.clipboard.writeText(result.full_report);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const downloadReport = () => {
        if (!result?.full_report) return;
        const blob = new Blob([result.full_report], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${result.title?.replace(/[^a-zA-Z0-9]/g, '_') || 'lab_report'}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const renderSection = (key: string, title: string, content: string | null) => {
        if (!content) return null;

        const isExpanded = expandedSections.has(key);

        return (
            <div key={key} className="border border-[var(--border)] rounded-xl overflow-hidden">
                <button
                    onClick={() => toggleSection(key)}
                    className="w-full px-4 py-3 flex items-center justify-between bg-[var(--surface-highlight)] hover:bg-[var(--surface)] transition-colors"
                >
                    <span className="font-medium text-[var(--text-primary)]">{title}</span>
                    {isExpanded ? (
                        <ChevronDown size={18} className="text-[var(--text-secondary)]" />
                    ) : (
                        <ChevronRight size={18} className="text-[var(--text-secondary)]" />
                    )}
                </button>
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div
                                className="p-4 prose prose-sm dark:prose-invert max-w-none text-[var(--text-primary)]"
                                dangerouslySetInnerHTML={{
                                    __html: content
                                        .replace(/\n/g, '<br/>')
                                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                                        .replace(/\$([^$]+)\$/g, '<code class="font-mono bg-[var(--surface-highlight)] px-1 rounded">$1</code>')
                                }}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-[var(--background)] p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
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
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                                    <FlaskConical size={20} className="text-white" />
                                </div>
                                Lab Report Generator
                            </h1>
                        </div>
                        <p className="text-[var(--text-secondary)] ml-14">
                            Generate structured lab reports from your experimental data
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left Panel - Input */}
                    <div className="space-y-6">
                        {/* Experiment Type */}
                        <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
                            <h2 className="text-lg font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <FlaskConical size={20} className="text-emerald-500" />
                                Experiment Type
                            </h2>

                            <div className="grid grid-cols-2 gap-2">
                                {templates.map(template => (
                                    <button
                                        key={template.id}
                                        onClick={() => setExperimentType(template.id)}
                                        className={`p-3 text-left rounded-xl border transition-all ${experimentType === template.id
                                                ? 'border-emerald-500 bg-emerald-500/10'
                                                : 'border-[var(--border)] hover:border-emerald-500/50'
                                            }`}
                                    >
                                        <p className="text-sm font-medium text-[var(--text-primary)]">{template.name}</p>
                                        <p className="text-xs text-[var(--text-secondary)] mt-1">{template.description}</p>
                                    </button>
                                ))}
                            </div>

                            {experimentType === 'custom' && (
                                <input
                                    type="text"
                                    value={customType}
                                    onChange={(e) => setCustomType(e.target.value)}
                                    placeholder="Enter experiment type..."
                                    className="mt-4 w-full px-4 py-3 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-emerald-500"
                                />
                            )}
                        </div>

                        {/* Data Upload */}
                        <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
                            <h2 className="text-lg font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <Upload size={20} className="text-blue-500" />
                                Data Sources
                            </h2>

                            <div className="space-y-4">
                                {/* Data File */}
                                <div>
                                    <label className="text-sm text-[var(--text-secondary)] block mb-2">
                                        Data File (CSV, Excel)
                                    </label>
                                    <input
                                        type="file"
                                        accept=".csv,.xlsx,.xls"
                                        onChange={(e) => setDataFile(e.target.files?.[0] || null)}
                                        className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-500/10 file:text-emerald-600 dark:file:text-emerald-400 hover:file:bg-emerald-500/20"
                                    />
                                    {dataFile && (
                                        <p className="text-xs text-emerald-500 mt-1">✓ {dataFile.name}</p>
                                    )}
                                </div>

                                {/* Methodology File */}
                                <div>
                                    <label className="text-sm text-[var(--text-secondary)] block mb-2">
                                        Methodology Document (PDF, DOCX)
                                    </label>
                                    <input
                                        type="file"
                                        accept=".pdf,.docx,.doc"
                                        onChange={(e) => setMethodologyFile(e.target.files?.[0] || null)}
                                        className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-500/10 file:text-blue-600 dark:file:text-blue-400 hover:file:bg-blue-500/20"
                                    />
                                    {methodologyFile && (
                                        <p className="text-xs text-blue-500 mt-1">✓ {methodologyFile.name}</p>
                                    )}
                                </div>

                                {/* Data Image */}
                                <div>
                                    <label className="text-sm text-[var(--text-secondary)] block mb-2">
                                        Image of Data Table (optional)
                                    </label>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={(e) => setDataImage(e.target.files?.[0] || null)}
                                        className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-purple-500/10 file:text-purple-600 dark:file:text-purple-400 hover:file:bg-purple-500/20"
                                    />
                                    {dataImage && (
                                        <p className="text-xs text-purple-500 mt-1">✓ {dataImage.name}</p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Additional Instructions */}
                        <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
                            <h2 className="text-lg font-medium text-[var(--text-primary)] mb-4 flex items-center gap-2">
                                <FileText size={20} className="text-violet-500" />
                                Additional Instructions
                            </h2>
                            <textarea
                                value={instructions}
                                onChange={(e) => setInstructions(e.target.value)}
                                placeholder="Any specific requirements for your lab report..."
                                rows={3}
                                className="w-full px-4 py-3 bg-[var(--surface-highlight)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-violet-500 resize-none"
                            />
                        </div>

                        {/* Generate Button */}
                        <motion.button
                            onClick={handleGenerate}
                            disabled={!experimentType || isGenerating}
                            whileTap={{ scale: 0.98 }}
                            className={`w-full py-4 rounded-xl font-semibold text-white flex items-center justify-center gap-3 transition-all shadow-lg ${experimentType && !isGenerating
                                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-emerald-500/25'
                                    : 'bg-[var(--border)] cursor-not-allowed shadow-none'
                                }`}
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="animate-spin" size={20} />
                                    Generating Report...
                                </>
                            ) : (
                                <>
                                    <FlaskConical size={20} />
                                    Generate Lab Report
                                </>
                            )}
                        </motion.button>

                        {/* Error Display */}
                        {error && (
                            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
                                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* Right Panel - Result */}
                    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl overflow-hidden">
                        {/* Header */}
                        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
                            <div className="flex items-center gap-2">
                                <FileText size={20} className="text-[var(--accent)]" />
                                <h3 className="font-medium text-[var(--text-primary)]">Generated Report</h3>
                            </div>
                            {result && (
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={copyToClipboard}
                                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-[var(--surface-highlight)] border border-[var(--border)] rounded-lg hover:border-[var(--accent)]/50 transition-colors"
                                    >
                                        {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                        {copied ? 'Copied!' : 'Copy'}
                                    </button>
                                    <button
                                        onClick={downloadReport}
                                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-[var(--surface-highlight)] border border-[var(--border)] rounded-lg hover:border-[var(--accent)]/50 transition-colors"
                                    >
                                        <Download size={14} />
                                        Download
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Content */}
                        <div className="p-6 max-h-[calc(100vh-300px)] overflow-y-auto">
                            {result ? (
                                <div className="space-y-4">
                                    {/* Title */}
                                    <h2 className="text-xl font-serif font-medium text-[var(--text-primary)] mb-6">
                                        {result.title}
                                    </h2>

                                    {/* Sections */}
                                    {renderSection('introduction', '1. Introduction', result.sections.introduction)}
                                    {renderSection('materials_methods', '2. Materials and Methods', result.sections.materials_methods)}
                                    {renderSection('results', '3. Results', result.sections.results)}
                                    {renderSection('discussion', '4. Discussion', result.sections.discussion)}
                                    {renderSection('conclusion', '5. Conclusion', result.sections.conclusion)}

                                    {/* References */}
                                    {result.references.length > 0 && (
                                        <div className="border border-[var(--border)] rounded-xl overflow-hidden">
                                            <button
                                                onClick={() => toggleSection('references')}
                                                className="w-full px-4 py-3 flex items-center justify-between bg-[var(--surface-highlight)] hover:bg-[var(--surface)] transition-colors"
                                            >
                                                <span className="font-medium text-[var(--text-primary)]">6. References</span>
                                                {expandedSections.has('references') ? (
                                                    <ChevronDown size={18} className="text-[var(--text-secondary)]" />
                                                ) : (
                                                    <ChevronRight size={18} className="text-[var(--text-secondary)]" />
                                                )}
                                            </button>
                                            <AnimatePresence>
                                                {expandedSections.has('references') && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: 'auto', opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        className="overflow-hidden"
                                                    >
                                                        <div className="p-4 space-y-2">
                                                            {result.references.map((ref, i) => (
                                                                <p key={i} className="text-sm text-[var(--text-secondary)]">
                                                                    {i + 1}. {ref.text}
                                                                </p>
                                                            ))}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-64 text-[var(--text-secondary)]">
                                    <FlaskConical size={48} className="mb-4 opacity-30" />
                                    <p className="text-center">Select experiment type and upload data to generate a report</p>
                                    <p className="text-xs mt-2 opacity-60">Supports data files, images, and methodology documents</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
