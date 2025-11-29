"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Book, Code, Layers, Shield, Search, FileText, Image, MessageSquare } from 'lucide-react';

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-6 md:p-12">
            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">

                {/* Sidebar Navigation */}
                <div className="md:col-span-1 hidden md:block sticky top-24 self-start">
                    <nav className="space-y-1">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 px-3">Documentation</h3>
                        <a href="#getting-started" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Getting Started</a>
                        <a href="#deep-research" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Deep Research</a>
                        <a href="#multimodal" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Multimodal Analysis</a>
                        <a href="#data-workbench" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Data Workbench</a>
                        <a href="#security" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Security & Privacy</a>
                    </nav>
                </div>

                {/* Main Content */}
                <div className="md:col-span-3 space-y-16">

                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <h1 className="text-4xl font-bold mb-4">PharmGPT Documentation</h1>
                        <p className="text-xl text-gray-600 dark:text-gray-400">
                            Comprehensive guide to using the advanced features of your AI research assistant.
                        </p>
                    </motion.div>

                    {/* Getting Started */}
                    <section id="getting-started" className="scroll-mt-24">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                <Book className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                            <h2 className="text-2xl font-bold">Getting Started</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                            <p>
                                PharmGPT is designed to be intuitive. Once you log in, you are presented with the main chat interface.
                                You can start by asking simple questions or uploading documents.
                            </p>
                            <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-900 dark:text-white">Chat Modes</h3>
                            <ul className="list-disc pl-5 space-y-2">
                                <li><strong>Fast Mode:</strong> Quick, concise answers. Best for definitions and simple facts.</li>
                                <li><strong>Detailed Mode:</strong> In-depth explanations with context. Good for learning new concepts.</li>
                                <li><strong>Deep Research Mode:</strong> Autonomous agentic workflow for complex queries (see below).</li>
                            </ul>
                        </div>
                    </section>

                    {/* Deep Research */}
                    <section id="deep-research" className="scroll-mt-24">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                                <Search className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                            </div>
                            <h2 className="text-2xl font-bold">Deep Research</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                            <p>
                                Deep Research is the flagship feature of PharmGPT. It transforms the AI from a chatbot into an autonomous researcher.
                            </p>
                            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg my-4 border-l-4 border-purple-500">
                                <strong>How it works:</strong>
                                <ol className="list-decimal pl-5 mt-2 space-y-1">
                                    <li><strong>Plan:</strong> The AI analyzes your query and creates a step-by-step research plan.</li>
                                    <li><strong>Search:</strong> It executes parallel searches across PubMed, Google Scholar, and the web.</li>
                                    <li><strong>Analyze:</strong> It reads abstracts and snippets to extract relevant findings.</li>
                                    <li><strong>Synthesize:</strong> It compiles the findings into a structured report with APA citations.</li>
                                </ol>
                            </div>
                            <p>
                                Use this mode for literature reviews, understanding complex mechanisms, or gathering data for a paper.
                            </p>
                        </div>
                    </section>

                    {/* Multimodal Analysis */}
                    <section id="multimodal" className="scroll-mt-24">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-teal-100 dark:bg-teal-900/30 rounded-lg">
                                <Image className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                            </div>
                            <h2 className="text-2xl font-bold">Multimodal Analysis</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                            <p>
                                PharmGPT can "see" and understand visual content. This is powered by the <strong>Vision-to-Text Bridge</strong>.
                            </p>
                            <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-900 dark:text-white">Supported Visuals</h3>
                            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                                <li className="flex items-start gap-2">
                                    <span className="text-teal-500">✓</span> Chemical Structures (2D/3D)
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-teal-500">✓</span> Clinical Trial Graphs & Charts
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-teal-500">✓</span> Histology Slides
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-teal-500">✓</span> Scanned Documents
                                </li>
                            </ul>
                            <p className="mt-4">
                                <strong>Inside Documents:</strong> When you upload a PDF, Word doc, or PowerPoint, the system automatically extracts images from the pages, analyzes them, and includes the description in the text index. This means you can search for "the graph on page 5" and get an answer.
                            </p>
                        </div>
                    </section>

                    {/* Data Workbench */}
                    <section id="data-workbench" className="scroll-mt-24">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                                <Layers className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                            </div>
                            <h2 className="text-2xl font-bold">Data Workbench</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                            <p>
                                The Data Workbench is your space for managing files and datasets.
                            </p>
                            <ul className="list-disc pl-5 space-y-2">
                                <li><strong>Upload:</strong> Drag and drop files (PDF, CSV, SDF, etc.).</li>
                                <li><strong>Preview:</strong> View file contents and metadata.</li>
                                <li><strong>Process:</strong> Automatically chunk and embed documents for RAG (Retrieval-Augmented Generation).</li>
                            </ul>
                        </div>
                    </section>

                    {/* Security */}
                    <section id="security" className="scroll-mt-24">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                                <Shield className="w-6 h-6 text-red-600 dark:text-red-400" />
                            </div>
                            <h2 className="text-2xl font-bold">Security & Privacy</h2>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-300">
                            <p>
                                We take security seriously. PharmGPT is built with multiple layers of protection.
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                                <div className="border border-gray-200 dark:border-gray-700 p-4 rounded-lg">
                                    <h4 className="font-bold mb-2">Anti-Jailbreak Protocol</h4>
                                    <p className="text-sm">
                                        A hardened system prompt and backend pre-filter prevent the AI from being manipulated into generating harmful or non-scientific content.
                                    </p>
                                </div>
                                <div className="border border-gray-200 dark:border-gray-700 p-4 rounded-lg">
                                    <h4 className="font-bold mb-2">Row Level Security (RLS)</h4>
                                    <p className="text-sm">
                                        Your data is stored in Supabase with strict RLS policies. Only your authenticated user account can access your documents and chat history.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                </div>
            </div>
        </div>
    );
}
