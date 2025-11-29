"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, HelpCircle, Search, FileText, Image, Database, Zap } from 'lucide-react';

interface FAQItem {
    question: string;
    answer: React.ReactNode;
    category: 'general' | 'features' | 'technical' | 'privacy';
}

const faqs: FAQItem[] = [
    {
        category: 'general',
        question: "What is PharmGPT?",
        answer: "PharmGPT is an advanced AI-powered pharmaceutical research assistant. It combines state-of-the-art Large Language Models (LLMs) with deep research capabilities, real-time web search, and multimodal document analysis to help researchers, students, and professionals navigate complex biomedical data."
    },
    {
        category: 'features',
        question: "What are Fast and Detailed modes?",
        answer: "We offer two core chat modes to suit your needs. 'Fast Mode' is optimized for speed, providing quick, concise answers for definitions or simple facts. 'Detailed Mode' provides in-depth explanations, context, and broader analysis, making it ideal for learning complex concepts or exploring nuances."
    },
    {
        category: 'features',
        question: "What is 'Deep Research' mode?",
        answer: "Deep Research mode is an autonomous agentic workflow. Instead of just answering a question, PharmGPT creates a research plan, queries multiple academic databases (PubMed, Google Scholar), analyzes the findings, and synthesizes a comprehensive, cited report. It's like having a research assistant write a literature review for you."
    },
    {
        category: 'features',
        question: "Can I upload images?",
        answer: "Yes! PharmGPT is multimodal. You can upload images of chemical structures, clinical trial graphs, or scanned documents. Our advanced Vision AI analyzes the image in detail and allows the system to 'see' and reason about the visual content alongside text."
    },
    {
        category: 'features',
        question: "What file types are supported?",
        answer: (
            <ul className="list-disc list-inside space-y-1">
                <li><strong>Documents:</strong> PDF, DOCX, PPTX, TXT, MD</li>
                <li><strong>Data:</strong> CSV, XLSX (Excel)</li>
                <li><strong>Chemistry:</strong> SDF, MOL (Molecular structures)</li>
                <li><strong>Images:</strong> PNG, JPG, JPEG, WEBP</li>
            </ul>
        )
    },
    {
        category: 'technical',
        question: "How does the citation system work?",
        answer: "We strictly adhere to APA 7th Edition standards. When Deep Research finds sources, it extracts metadata (Author, Year, Journal, DOI) and formats both in-text citations (e.g., 'Smith et al., 2023') and a full reference list at the end of the response."
    },
    {
        category: 'technical',
        question: "Does it search the real-time web?",
        answer: "Yes. We integrate with leading general web search engines and specialized academic databases to access real-time information. This ensures you get the most up-to-date scientific data, clinical trial results, and news, rather than relying solely on the AI's training data."
    },
    {
        category: 'privacy',
        question: "Is my data secure?",
        answer: "Absolutely. Your conversations and uploaded documents are stored in a secure, enterprise-grade database with strict access controls. Only you can access your data. We do not use your private data to train our public models."
    }
];

export default function FAQPage() {
    const [openIndex, setOpenIndex] = React.useState<number | null>(0);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-6 md:p-12">
            <div className="max-w-4xl mx-auto">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <div className="inline-flex items-center justify-center p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
                        <HelpCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h1 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-teal-500">
                        Frequently Asked Questions
                    </h1>
                    <p className="text-lg text-gray-600 dark:text-gray-400">
                        Everything you need to know about PharmGPT's capabilities and workflows.
                    </p>
                </motion.div>

                <div className="space-y-4">
                    {faqs.map((faq, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
                        >
                            <button
                                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                                className="w-full flex items-center justify-between p-6 text-left focus:outline-none"
                            >
                                <span className="text-lg font-semibold">{faq.question}</span>
                                {openIndex === index ? (
                                    <ChevronUp className="w-5 h-5 text-blue-500" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                )}
                            </button>

                            {openIndex === index && (
                                <div className="px-6 pb-6 text-gray-600 dark:text-gray-300 leading-relaxed border-t border-gray-100 dark:border-gray-700 pt-4">
                                    {faq.answer}
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>

                <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
                        <Database className="w-8 h-8 text-blue-600 mb-3" />
                        <h3 className="font-semibold mb-2">Deep Research</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Autonomous multi-step research across PubMed & Google Scholar.</p>
                    </div>
                    <div className="p-6 bg-teal-50 dark:bg-teal-900/20 rounded-xl border border-teal-100 dark:border-teal-800">
                        <Image className="w-8 h-8 text-teal-600 mb-3" />
                        <h3 className="font-semibold mb-2">Multimodal Analysis</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Upload images, PDFs, and slides. The AI sees what you see.</p>
                    </div>
                    <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-100 dark:border-purple-800">
                        <Zap className="w-8 h-8 text-purple-600 mb-3" />
                        <h3 className="font-semibold mb-2">Real-time Data</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Live web search integration ensures answers are never outdated.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
