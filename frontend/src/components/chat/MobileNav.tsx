'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { Menu, X, Plus, Moon, Sun, Settings, LogOut, BarChart3 } from 'lucide-react';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt-backend.onrender.com'
  : 'http://localhost:8000';

interface ChatHistory {
  id: string;
  title: string;
  date: string;
}

export default function MobileNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const { user, token, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);

  // Fetch conversation history when user is logged in
  useEffect(() => {
    if (token) {
      fetchConversationHistory();
    } else {
      setChatHistory([]);
    }
  }, [token]);

  const fetchConversationHistory = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const conversations = await response.json();
        const formattedHistory = conversations.map((conv: any) => {
          const date = new Date(conv.created_at);
          const today = new Date();
          const yesterday = new Date(today);
          yesterday.setDate(yesterday.getDate() - 1);
          
          let dateStr = 'Older';
          if (date.toDateString() === today.toDateString()) {
            dateStr = 'Today';
          } else if (date.toDateString() === yesterday.toDateString()) {
            dateStr = 'Yesterday';
          }
          
          return {
            id: conv.id,
            title: conv.title || 'Untitled Chat',
            date: dateStr,
          };
        });
        setChatHistory(formattedHistory);
      }
    } catch (error) {
      console.error('Failed to fetch conversation history:', error);
    }
  };

  const handleSignOut = () => {
    logout();
    setIsOpen(false);
    router.push('/login');
  };

  return (
    <>
      {/* Mobile Menu Button - Top Left */}
      <button
        onClick={() => setIsOpen(true)}
        className="md:hidden fixed top-4 left-4 z-50 w-10 h-10 rounded-xl bg-[var(--surface)] border border-[var(--border)] flex items-center justify-center shadow-lg"
      >
        <Menu size={20} strokeWidth={1.5} className="text-[var(--text-primary)]" />
      </button>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="md:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            />
            
            {/* Sidebar */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="md:hidden fixed left-0 top-0 bottom-0 z-50 w-[85%] max-w-[320px] bg-[var(--surface)] border-r border-[var(--border)] flex flex-col"
            >
              <div className="p-4 flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <button
                    onClick={() => { setIsOpen(false); router.push('/'); }}
                    className="flex items-center gap-2"
                  >
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                      <span className="text-white text-sm font-bold">P</span>
                    </div>
                    <span className="font-semibold text-[var(--text-primary)]">PharmGPT</span>
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="w-8 h-8 rounded-lg bg-[var(--surface-highlight)] flex items-center justify-center"
                  >
                    <X size={16} className="text-[var(--text-secondary)]" />
                  </button>
                </div>

                {/* New Chat Button */}
                <button
                  onClick={() => { setIsOpen(false); router.push('/chat'); }}
                  className="w-full py-3 px-4 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium text-sm flex items-center justify-center gap-2 mb-6"
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
                    {chatHistory.length === 0 ? (
                      <p className="text-sm text-[var(--text-secondary)] px-2">Chat history will appear here</p>
                    ) : (
                      chatHistory.map((chat) => (
                        <button
                          key={chat.id}
                          onClick={() => setIsOpen(false)}
                          className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors"
                        >
                          <p className="text-sm text-[var(--text-primary)] truncate">{chat.title}</p>
                          <p className="text-xs text-[var(--text-secondary)] mt-0.5">{chat.date}</p>
                        </button>
                      ))
                    )}
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="pt-4 border-t border-[var(--border)] space-y-2">
                  <button
                    onClick={() => { setIsOpen(false); router.push('/workbench'); }}
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
                  {token && (
                    <button 
                      onClick={handleSignOut}
                      className="w-full p-3 rounded-xl text-left hover:bg-red-500/10 transition-colors flex items-center gap-3"
                    >
                      <LogOut size={20} strokeWidth={1.5} className="text-red-500" />
                      <span className="text-sm text-red-500">Sign Out</span>
                    </button>
                  )}
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
