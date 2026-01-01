'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Trash2, Menu, Edit3, ChevronDown, Sparkles, MoreHorizontal } from 'lucide-react';
import { openMobileNav } from '@/components/chat/MobileNav';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput, { Mode } from '@/components/chat/ChatInput';
import DeepResearchUI from '@/components/chat/DeepResearchUI';
import { useChatContext } from '@/contexts/ChatContext';
import { useSidebar } from '@/contexts/SidebarContext';

import confetti from 'canvas-confetti';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, isLoadingConversation, isUploading, isDeleting, sendMessage, stopGeneration, uploadFiles, deepResearchProgress, deleteConversation, clearMessages, conversationId, selectConversation, cancelUpload, editMessage, deleteMessage } = useChatContext();
  const { sidebarOpen, setSidebarOpen } = useSidebar();
  const [hasInitialized, setHasInitialized] = useState(false);
  const [mode, setMode] = useState<Mode>('fast'); // Lifted mode state

  // Handle Confetti on first load after registration
  useEffect(() => {
    const shouldShow = localStorage.getItem('show_confetti');
    if (shouldShow === 'true') {
      const end = Date.now() + 5000;
      const colors = ['#6366f1', '#a855f7', '#ec4899'];

      (function frame() {
        confetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: colors
        });
        confetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: colors
        });

        if (Date.now() < end) {
          requestAnimationFrame(frame);
        }
      }());

      localStorage.removeItem('show_confetti');
    }
  }, []);

  // Save current conversation ID to localStorage
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem('currentConversationId', conversationId);
    }
  }, [conversationId]);

  // Restore conversation on page load/refresh
  useEffect(() => {
    const savedConversationId = localStorage.getItem('currentConversationId');
    if (savedConversationId && !conversationId && !hasInitialized) {
      selectConversation(savedConversationId);
      setHasInitialized(true);
    }
  }, [conversationId, hasInitialized, selectConversation]);

  useEffect(() => {
    if (initialQuery && !hasInitialized) {
      sendMessage(initialQuery, 'fast'); // Default to fast mode
      setHasInitialized(true);
    }
  }, [initialQuery, hasInitialized, sendMessage]);

  const handleNewChat = () => {
    localStorage.removeItem('currentConversationId');
    clearMessages();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Reset mode when conversation changes
  useEffect(() => {
    setMode('fast');
  }, [conversationId]);

  const handleSend = (message: string, selectedMode: Mode = mode) => {
    if (selectedMode !== mode) {
      setMode(selectedMode);
    }
    sendMessage(message, selectedMode);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-[var(--background)] transition-all duration-300 ease-in-out">
      {/* Floating Header Layer - Absolute Positioning for Pixel-Perfect Centering */}
      <div className="absolute top-0 left-0 w-full h-16 z-50 pointer-events-none px-4">
        {/* Sidebar Trigger - Always visible on mobile, hidden on desktop only when sidebar is open */}
        <button
          onClick={() => setSidebarOpen(true)}
          className={`absolute top-3 left-4 z-50 p-2.5 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--background)]/50 hover:text-[var(--text-primary)] transition-all backdrop-blur-sm pointer-events-auto md:hidden`}
        >
          <Menu size={24} strokeWidth={1.5} />
        </button>

        {/* PharmGPT Pill - Absolutely centered (pixel-perfect) */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/40 dark:bg-black/40 backdrop-blur-md border border-white/10 shadow-lg select-none whitespace-nowrap pointer-events-auto">
            <span className="text-xs font-medium text-[var(--text-primary)] tracking-tight">PharmGPT</span>
            <span className="text-[10px] text-[var(--text-secondary)] opacity-70">v2.0</span>
          </div>
        </div>

        {/* New Chat Button - Mobile only, absolute right */}
        <button
          onClick={handleNewChat}
          className="md:hidden absolute top-3 right-4 z-50 p-2.5 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--background)]/50 hover:text-[var(--text-primary)] transition-all backdrop-blur-sm pointer-events-auto"
        >
          <Edit3 size={24} strokeWidth={1.5} />
        </button>
      </div>

      {/* Messages Area - Scrollable */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-4 md:px-6 pt-24 pb-32 sm:pb-36 md:pb-44">
        <div className="max-w-3xl mx-auto">
          {isLoadingConversation ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-500 opacity-50" />
            </div>
          ) : messages.length === 0 ? (
            <EmptyState
              onSuggestionClick={(msg) => handleSend(msg, mode)}
              currentMode={mode}
            />
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((msg, index) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChatMessage
                    message={msg}
                    isStreaming={isLoading && index === messages.length - 1 && msg.role === 'assistant'}
                    onEdit={editMessage}
                    onDelete={deleteMessage}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {/* Deep Research Progress */}
          {deepResearchProgress && (
            <div className="mb-4">
              <DeepResearchUI
                isLoading={deepResearchProgress.type !== 'complete'}
                progressStep={deepResearchProgress.message || deepResearchProgress.status || 'Processing...'}
                progressPercent={deepResearchProgress.progress || 0}
                reportContent={deepResearchProgress.report || ''}
                sources={deepResearchProgress.citations?.map(c => ({
                  id: c.id,
                  title: c.title,
                  url: c.url,
                  snippet: c.snippet || '',
                  journal: c.journal,
                  year: c.year,
                  authors: c.authors,
                  source_type: c.source_type || c.source
                })) || []}
                error={deepResearchProgress.type === 'error' ? (deepResearchProgress.message || 'An error occurred') : undefined}
              />
            </div>
          )}

          {/* Loading indicator - minimal, no avatar */}
          {isLoading && !deepResearchProgress && (messages.length === 0 || messages[messages.length - 1]?.role !== 'assistant') && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="py-4"
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="text-xs text-[var(--text-secondary)] ml-2">Thinking...</span>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={handleSend}
        onStop={stopGeneration}
        onFileUpload={uploadFiles}
        onCancelUpload={cancelUpload}
        isLoading={isLoading}
        isUploading={isUploading}
        mode={mode}
        setMode={setMode}
      />
    </div>
  );
}

function EmptyState({ onSuggestionClick, currentMode }: { onSuggestionClick: (msg: string, mode?: Mode) => void, currentMode: Mode }) {
  const [suggestions, setSuggestions] = useState<{ text: string, mode: Mode }[]>([]);

  useEffect(() => {
    const suggestionPool = [
      // Clinical & Pharmacology
      { text: 'What are the common drug interactions with Warfarin?', mode: 'detailed' as Mode },
      { text: 'Explain the mechanism of action of SSRIs', mode: 'detailed' as Mode },
      { text: 'Compare ACE inhibitors vs ARBs in treating hypertension', mode: 'detailed' as Mode },
      { text: 'List potential side effects of GLP-1 agonists', mode: 'detailed' as Mode },
      { text: 'Analyze the structure-activity relationship of beta-lactams', mode: 'detailed' as Mode },

      // Research & Writing
      { text: 'Help me write a research manuscript introduction', mode: 'detailed' as Mode },
      { text: 'Draft an abstract for a study on mRNA vaccine stability', mode: 'detailed' as Mode },
      { text: 'Write a literature review on antibiotic resistance mechanisms', mode: 'detailed' as Mode },

      // Regulatory & Industry
      { text: 'Summarize the latest FDA guidelines for biosimilars', mode: 'detailed' as Mode },
      { text: 'What are phase III trial requirements for orphan drugs?', mode: 'detailed' as Mode },

      // Deep Research
      { text: 'Deep research: Current evidence for pembrolizumab in NSCLC', mode: 'deep_research' as Mode },
      { text: 'Deep research: Emerging CAR-T therapies for solid tumors', mode: 'deep_research' as Mode },
      { text: 'Deep research: Long-term outcomes of gene therapy in hemophilia', mode: 'deep_research' as Mode },
      { text: 'Deep research: AI applications in drug discovery 2024', mode: 'deep_research' as Mode },
    ];

    // Shuffle and pick 4
    const shuffled = [...suggestionPool].sort(() => 0.5 - Math.random());
    setSuggestions(shuffled.slice(0, 4));
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center py-12 md:py-16"
    >
      <div className="mb-8 relative flex justify-center">
        <img
          src="/PharmGPT.png"
          alt="PharmGPT"
          className="w-[120px] opacity-[0.05] dark:opacity-[0.08] pointer-events-none select-none grayscale"
        />
      </div>
      <h2 className="text-xl md:text-2xl font-serif font-medium text-[var(--text-primary)] mb-3">
        How can I help you today?
      </h2>
      <p className="text-[var(--text-secondary)] mb-8 max-w-md mx-auto text-sm md:text-base">
        Ask about drug interactions, research writing, or upload documents for analysis.
        <br />
        <span className="text-xs opacity-70 mt-2 block">Current Mode: {currentMode === 'deep_research' ? 'Deep Research' : currentMode === 'detailed' ? 'Detailed' : 'Fast'}</span>
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 max-w-xl mx-auto px-2 sm:px-4 min-h-[140px]">
        {suggestions.length > 0 ? (
          suggestions.map((suggestion, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i, duration: 0.3 }}
              onClick={() => onSuggestionClick(suggestion.text, suggestion.mode)}
              className="p-3 sm:p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-left text-xs sm:text-sm text-[var(--text-primary)] hover:border-[var(--accent)] hover:bg-[var(--surface-highlight)] transition-all h-full"
            >
              {suggestion.text}
            </motion.button>
          ))
        ) : (
          // Loading skeletons while shuffling (prevents layout shift)
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-[var(--surface-highlight)] animate-pulse" />
          ))
        )}
      </div>
    </motion.div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center">
        <Loader2 size={32} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
