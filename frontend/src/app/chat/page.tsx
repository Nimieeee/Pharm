'use client';

import { useState, useRef, useEffect, Suspense, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Trash2, Menu, Edit3, ChevronDown, Sparkles, MoreHorizontal, PanelLeft } from 'lucide-react';

import { MemoizedChatMessage } from '@/components/chat/ChatMessage';
import { MemoizedChatInput, Mode } from '@/components/chat/ChatInput';
import DeepResearchUI from '@/components/chat/DeepResearchUI';
import { useChatContext } from '@/contexts/ChatContext';
import { useSidebar } from '@/contexts/SidebarContext';
import { useTranslation } from '@/hooks/use-translation';
import StreamingLogo from '@/components/chat/StreamingLogo';
import { isConversationStreaming } from '@/hooks/useStreamingState';

import confetti from 'canvas-confetti';
import { getSuggestionPool } from '@/config/suggestionPrompts';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, isConversationLoading, isLoadingConversation, isUploading, isDeleting, sendMessage, stopGeneration, uploadFiles, deepResearchProgress, deleteConversation, clearMessages, conversationId, selectConversation, cancelUpload, removeFile, regenerateMessage, deleteMessage, branchData, activeBranches, regenerateResponse, switchBranch, deleteBranch, editMessage } = useChatContext();
  const { sidebarOpen, setSidebarOpen } = useSidebar();
  const { t, language } = useTranslation();
  const [hasInitialized, setHasInitialized] = useState(false);
  const [mode, setMode] = useState<Mode>('fast'); // Lifted mode state
  const renderCountRef = useRef(0);

  // DEBUG: Monitor messages state changes
  useEffect(() => {
    renderCountRef.current++;
    console.log(`🎨 [RENDER #${renderCountRef.current}] ChatContent rendered, messages.length: ${messages.length}`);
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      console.log(`🎨 [RENDER #${renderCountRef.current}] Last message: role=${lastMsg.role}, id=${lastMsg.id.substring(0, 8)}, contentLen=${lastMsg.content.length}`);
    }
  }, [messages]);

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

  // Smart Auto-Scroll Implementation
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isUserAtBottom, setIsUserAtBottom] = useState(true);
  const isAutoScrolling = useRef(false);

  const scrollToBottom = useCallback((behavior: 'auto' | 'smooth' = 'smooth') => {
    if (messagesEndRef.current) {
      isAutoScrolling.current = true;
      messagesEndRef.current.scrollIntoView({ behavior });
      // Reset auto-scroll flag after a short delay
      setTimeout(() => { isAutoScrolling.current = false; }, 100);
    }
  }, []);

  // Check if user is at bottom of chat
  const checkIsAtBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return true;

    const threshold = 150; // pixels from bottom
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;

    return scrollHeight - scrollTop - clientHeight < threshold;
  }, []);

  // Handle scroll events
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      // Only update if not caused by our own auto-scroll
      if (!isAutoScrolling.current) {
        const atBottom = checkIsAtBottom();
        setIsUserAtBottom(atBottom);
      }
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [checkIsAtBottom]);

  // Combined effect for new messages AND streaming content
  useEffect(() => {
    if (isUserAtBottom && messages.length > 0) {
      scrollToBottom('auto');
    }
  }, [messages, isUserAtBottom, scrollToBottom]);

  // Reset mode when conversation changes
  useEffect(() => {
    setMode('fast');
  }, [conversationId]);

  const handleSend = (message: string, selectedMode: Mode = mode) => {
    if (selectedMode !== mode) {
      setMode(selectedMode);
    }
    sendMessage(message, selectedMode, language);
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
          <PanelLeft size={24} strokeWidth={1.5} />
        </button>

        {/* Benchside Pill - Absolutely centered (pixel-perfect) */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface/80 backdrop-blur-md border border-[var(--border)] shadow-lg select-none whitespace-nowrap pointer-events-auto">
            <span className="text-xs font-medium text-[var(--text-primary)] tracking-tight">Benchside</span>
            <span className="text-[10px] text-[var(--text-secondary)] opacity-70">v1.0</span>
          </div>
        </div>

        {/* New Chat Button - Mobile only, absolute right */}
        <button
          onClick={handleNewChat}
          className="md:hidden absolute top-3 right-4 z-50 p-2.5 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--background)]/50 hover:text-[var(--text-primary)] transition-all backdrop-blur-sm pointer-events-auto"
        >
          <Edit3 size={24} strokeWidth={1.5} />
        </button>

        {/* Export removed per user request */}
      </div>

      {/* Messages Area - Scrollable */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-2 sm:px-4 md:px-6 pt-24 pb-32 sm:pb-36 md:pb-44"
        onClick={(e) => {
          // Refocus input when user clicks the empty chat background
          if (e.target === e.currentTarget) {
            const textarea = document.querySelector<HTMLTextAreaElement>('textarea[autofocus]')
              || document.querySelector<HTMLInputElement>('.chat-input-field');
            textarea?.focus();
          }
        }}
      >
        <div className="max-w-3xl mx-auto">
          {isLoadingConversation ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-orange-500 opacity-50" />
            </div>
          ) : messages.length === 0 ? (
            <EmptyState
              onSuggestionClick={(msg) => handleSend(msg, mode)}
              currentMode={mode}
            />
          ) : (
            messages.map((msg, index) => {
              if (msg.role !== 'user') {
                return (
                  <div key={msg.id}>
                    <MemoizedChatMessage
                      message={msg}
                      isStreaming={isLoading && index === messages.length - 1}
                      onDelete={deleteMessage}
                    />
                  </div>
                );
              }

              const userMsg = msg;
              const branches = branchData.get(userMsg.id) || [];
              const activeBranchId = activeBranches.get(userMsg.id);
              const activeResponse = activeBranchId
                ? branches.find(b => b.id === activeBranchId)
                : branches[branches.length - 1];

              return (
                <div key={userMsg.id}>
                  <MemoizedChatMessage
                    message={userMsg}
                    isStreaming={false}
                    onEdit={editMessage}
                    onDelete={deleteMessage}
                  />
                  {activeResponse && (
                    <MemoizedChatMessage
                      message={{
                        id: activeResponse.id,
                        role: 'assistant',
                        content: activeResponse.content,
                        timestamp: new Date(activeResponse.created_at),
                        mode: activeResponse.metadata?.mode,
                        translations: activeResponse.metadata?.translations,
                        citations: activeResponse.metadata?.citations
                      }}
                      isStreaming={isLoading && index === messages.length - 1}
                      onRegenerate={() => regenerateResponse(userMsg.id)}
                      onDelete={() => deleteBranch(activeResponse.id)}
                      branches={branches}
                      activeBranchId={activeResponse.id}
                      onSwitchBranch={(newBranchId) => switchBranch(userMsg.id, newBranchId)}
                      onDeleteBranch={deleteBranch}
                    />
                  )}
                </div>
              );
            })
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
          {/* Show "Thinking..." ONLY when:
              1. isLoading is true AND
              2. No assistant message exists yet (waiting for stream to start)
              Once assistant message is added, hide this and wait for content to stream */}
          <AnimatePresence>
            {!deepResearchProgress && isLoading && (
              messages.length === 0 ||
              (() => {
                const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
                return !lastUserMsg || !branchData.get(lastUserMsg.id)?.length;
              })()
            ) && (
                <motion.div
                  key="thinking-indicator"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0, transition: { duration: 0.15 } }}
                  className="py-4 min-h-[3rem]"
                >
                  <div className="flex items-center gap-2 text-slate-500">
                    <StreamingLogo className="w-5 h-5 opacity-80" />
                    <span className="text-xs text-[var(--text-secondary)]">{t('thinking')}</span>
                  </div>
                </motion.div>
              )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <MemoizedChatInput
        onSend={(content, mode) => {
          // Update mode implementation
          setMode(mode);
          sendMessage(content, mode, language);
        }}
        onStop={stopGeneration}
        onFileUpload={uploadFiles}
        onCancelUpload={cancelUpload}
        onRemoveFile={removeFile}
        isLoading={conversationId ? isConversationStreaming(conversationId) : false}
        isUploading={isUploading}
        mode={mode}
        setMode={setMode}
      />
    </div>
  );
}



function EmptyState({ onSuggestionClick, currentMode }: { onSuggestionClick: (msg: string, mode?: Mode) => void, currentMode: Mode }) {
  const [suggestions, setSuggestions] = useState<{ text: string, mode: Mode }[]>([]);
  const { t, language } = useTranslation();

  useEffect(() => {
    // Efficiently select 4 random, unique suggestions from the large pool
    const pool = getSuggestionPool(language as any);
    const poolSize = pool.length;
    const selectedIndices = new Set<number>();

    while (selectedIndices.size < 4 && selectedIndices.size < poolSize) {
      const randomIndex = Math.floor(Math.random() * poolSize);
      selectedIndices.add(randomIndex);
    }

    const randomSuggestions = Array.from(selectedIndices).map(index => pool[index]);
    setSuggestions(randomSuggestions);
  }, [language]);

  const getModeLabel = (m: Mode) => {
    switch (m) {
      case 'deep_research': return t('mode_research');
      case 'detailed': return t('mode_detailed');
      default: return t('mode_fast');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center py-12 md:py-16"
    >
      <div className="mb-8 relative flex justify-center">
        <img
          src="/Benchside.png"
          alt="Benchside"
          className="w-[120px] opacity-[0.05] dark:opacity-[0.08] pointer-events-none select-none grayscale"
        />
      </div>
      <h2 className="text-xl md:text-2xl font-serif font-medium text-[var(--text-primary)] mb-3">
        {t('how_can_i_help')}
      </h2>
      <p className="text-[var(--text-secondary)] mb-8 max-w-md mx-auto text-sm md:text-base">
        {t('empty_state_desc')}
        <br />
        <span className="text-xs opacity-70 mt-2 block">{t('current_mode')}: {getModeLabel(currentMode)}</span>
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 max-w-xl mx-auto px-2 sm:px-4 min-h-[140px]">
        {suggestions.length > 0 ? (
          suggestions.map((suggestion, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i, duration: 0.3 }}
              onClick={() => onSuggestionClick(suggestion.text, currentMode)}
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
