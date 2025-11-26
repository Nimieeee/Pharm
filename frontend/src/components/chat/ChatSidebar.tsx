'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { ChevronsLeft, ChevronsRight, Plus, Moon, Sun, Settings, BarChart3 } from 'lucide-react';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

interface ChatHistory {
  id: string;
  title: string;
  date: string;
}

export default function ChatSidebar({ isOpen, onToggle }: ChatSidebarProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [chatHistory] = useState<ChatHistory[]>([
    { id: '1', title: 'Warfarin drug interactions', date: 'Today' },
    { id: '2', title: 'SSRI mechanism analysis', date: 'Today' },
    { id: '3', title: 'Clinical trial summary', date: 'Yesterday' },
    { id: '4', title: 'Metformin pharmacokinetics', date: 'Yesterday' },
  ]);

  return (
    <>
      {/* Desktop Sidebar */}
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
            className="hidden md:flex flex-col h-full border-r border-[var(--border)] bg-[var(--surface)] overflow-hidden"
          >
            <div className="p-4 flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={() => router.push('/')}
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                    <span className="text-white text-sm font-bold">P</span>
                  </div>
                  <span className="font-semibold text-[var(--text-primary)]">PharmGPT</span>
                </button>
                <button
                  onClick={onToggle}
                  className="w-8 h-8 rounded-lg bg-[var(--surface-highlight)] flex items-center justify-center hover:bg-[var(--border)] transition-colors btn-press"
                >
                  <ChevronsLeft size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                </button>
              </div>

              {/* New Chat Button */}
              <button
                onClick={() => router.push('/chat')}
                className="w-full py-3 px-4 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium text-sm flex items-center justify-center gap-2 btn-press hover:opacity-90 transition-all mb-6"
              >
                <Plus size={16} strokeWidth={1.5} />
                New Chat
              </button>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto">
                <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 px-2">
                  Recent Chats
                </p>
                <div className="space-y-1">
                  {chatHistory.map((chat, i) => (
                    <motion.button
                      key={chat.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors group"
                    >
                      <p className="text-sm text-[var(--text-primary)] truncate group-hover:text-indigo-500 transition-colors">
                        {chat.title}
                      </p>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                        {chat.date}
                      </p>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="pt-4 border-t border-[var(--border)] space-y-2">
                <button
                  onClick={() => router.push('/workbench')}
                  className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3"
                >
                  <BarChart3 size={20} strokeWidth={1.5} className="text-indigo-500" />
                  <span className="text-sm text-[var(--text-primary)]">Data Workbench</span>
                </button>
                <button
                  onClick={toggleTheme}
                  className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3"
                >
                  {theme === 'light' ? (
                    <Moon size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                  ) : (
                    <Sun size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                  )}
                  <span className="text-sm text-[var(--text-primary)]">
                    {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                  </span>
                </button>
                <button className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3">
                  <Settings size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                  <span className="text-sm text-[var(--text-primary)]">Settings</span>
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Collapsed Toggle Button - positioned in header area, left side */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="hidden md:flex fixed left-4 top-4 z-40 w-10 h-10 rounded-xl bg-[var(--surface)] border border-[var(--border)] items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors btn-press shadow-lg"
        >
          <ChevronsRight size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
        </button>
      )}
    </>
  );
}
