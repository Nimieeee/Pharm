"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Book, Code, Shield, Search, FileText, Image, MessageSquare } from 'lucide-react';

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-background text-foreground p-6 md:p-12">
            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">

                {/* Sidebar Navigation */}
                <div className="md:col-span-1 hidden md:block sticky top-24 self-start">
                    <nav className="space-y-1">
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 px-3">Documentation</h3>
                        <a href="#getting-started" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Getting Started</a>
                        <a href="#deep-research" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Deep Research</a>
                        <a href="#multimodal" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">Multimodal Analysis</a>
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
                                PharmGPT is designed to be intuitive for researchers and clinicians. This guide will help you get up and running quickly.
                            </p>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">1. Interface Overview</h3>
                            <p>The main interface consists of three key areas:</p>
                            <ul className="list-disc pl-5 space-y-2">
                                <li><strong>Chat Window:</strong> The central area where you interact with the AI.</li>
                                <li><strong>Sidebar:</strong> Access your chat history, pinned conversations, and settings.</li>
                            </ul>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">2. Chat Modes</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                                    <h4 className="font-bold text-blue-600 dark:text-blue-400 mb-2">Fast Mode</h4>
                                    <p className="text-sm">Optimized for speed. Use this for quick definitions, checking drug interactions, or simple fact retrieval. It uses a lightweight model to deliver near-instant responses.</p>
                                </div>
                                <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                                    <h4 className="font-bold text-purple-600 dark:text-purple-400 mb-2">Detailed Mode</h4>
                                    <p className="text-sm">Optimized for depth. Use this for complex explanations, learning new mechanisms, or when you need the AI to "think" through a problem step-by-step.</p>
                                </div>
                            </div>
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
                                Deep Research transforms PharmGPT from a chatbot into an autonomous research assistant. It is designed to handle complex queries that require synthesizing information from multiple scientific sources.
                            </p>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">How It Works</h3>
                            <div className="bg-surface-highlight p-6 rounded-xl border border-border space-y-4">
                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center font-bold text-purple-600">1</div>
                                    <div>
                                        <h4 className="font-semibold text-foreground">Planning</h4>
                                        <p className="text-sm mt-1">The AI analyzes your request and breaks it down into sub-questions. It decides which databases to search (e.g., PubMed for clinical data, Google Scholar for broader literature).</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center font-bold text-purple-600">2</div>
                                    <div>
                                        <h4 className="font-semibold text-foreground">Execution</h4>
                                        <p className="text-sm mt-1">It executes parallel search queries in real-time. It reads abstracts, snippets, and open-access full text to gather evidence.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center font-bold text-purple-600">3</div>
                                    <div>
                                        <h4 className="font-semibold text-foreground">Synthesis</h4>
                                        <p className="text-sm mt-1">The AI compiles the findings into a cohesive report. It resolves conflicting data and highlights consensus in the literature.</p>
                                    </div>
                                </div>
                            </div>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">Example Use Case</h3>
                            <div className="bg-gray-900 text-gray-300 p-4 rounded-lg font-mono text-sm">
                                "Conduct a literature review on the efficacy of GLP-1 receptor agonists in treating non-alcoholic steatohepatitis (NASH), focusing on trials published in the last 3 years."
                            </div>
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
                                PharmGPT includes a powerful <strong>Vision-to-Text Bridge</strong> that allows it to "see" and understand visual content. This is crucial for analyzing scientific papers, which often contain vital data in charts and figures.
                            </p>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">Supported Visuals</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="flex items-start gap-3 p-3 bg-surface rounded-lg border border-border">
                                    <span className="text-teal-500 text-xl">⚗️</span>
                                    <div>
                                        <strong className="block text-foreground">Chemical Structures</strong>
                                        <span className="text-sm">2D skeletal structures and 3D conformers.</span>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-3 bg-surface rounded-lg border border-border">
                                    <span className="text-teal-500 text-xl">📊</span>
                                    <div>
                                        <strong className="block text-foreground">Data Visualizations</strong>
                                        <span className="text-sm">Kaplan-Meier plots, forest plots, and bar charts.</span>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-3 bg-surface rounded-lg border border-border">
                                    <span className="text-teal-500 text-xl">🔬</span>
                                    <div>
                                        <strong className="block text-foreground">Microscopy</strong>
                                        <span className="text-sm">Histology slides and cell culture images.</span>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 p-3 bg-surface rounded-lg border border-border">
                                    <span className="text-teal-500 text-xl">📄</span>
                                    <div>
                                        <strong className="block text-foreground">Documents</strong>
                                        <span className="text-sm">Scanned PDFs, handwritten notes, and forms.</span>
                                    </div>
                                </div>
                            </div>

                            <h3 className="text-lg font-semibold mt-6 mb-3 text-foreground">Inside Documents</h3>
                            <p>
                                When you upload a <strong>PDF, Word, or PowerPoint</strong> file, our system automatically extracts every image found within the pages. These images are sent to our Vision AI, which generates a detailed textual description. This description is then embedded into the document's text index.
                            </p>
                            <p className="mt-2">
                                <strong>Why this matters:</strong> You can ask questions like <em>"What does the survival curve in Figure 2 show?"</em> and PharmGPT will be able to answer, even though the information was originally just pixels in an image.
                            </p>
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
                                We adhere to strict security protocols to ensure your research data remains confidential and protected.
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                                <div className="border border-gray-200 dark:border-gray-700 p-4 rounded-lg">
                                    <h4 className="font-bold mb-2">Anti-Jailbreak Protocol</h4>
                                    <p className="text-sm">
                                        A hardened system prompt and backend pre-filter prevent the AI from being manipulated into generating harmful or non-scientific content. We strictly enforce safety boundaries.
                                    </p>
                                </div>
                                <div className="border border-gray-200 dark:border-gray-700 p-4 rounded-lg">
                                    <h4 className="font-bold mb-2">Data Isolation</h4>
                                    <p className="text-sm">
                                        Your data is stored in an enterprise-grade database with strict access policies. Data is logically isolated per user, meaning no other user can access your documents or chat history.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>                  </div>
            </div>
        </div>
    );
}
