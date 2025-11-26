'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { ChevronsLeft, ChevronsRight, Plus, Moon, Sun, Settings, BarChart3, LogOut, X } from 'lucide-react';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt-backend.onrender.com'
  : 'http://localhost:8000';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onSelectConversation?: (id: string) => void;
}

interface ChatHistory {
  id: string;
  title: string;
  date: string;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-md mx-4 p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-xl"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-serif font-medium text-[var(--text-primary)]">Settings</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[var(--surface-highlight)] flex items-center justify-center hover:bg-[var(--border)] transition-colors"
          >
            <X size={16} className="text-[var(--text-secondary)]" />
          </button>
        </div>
        
        <div className="space-y-4">
          {/* Account Info */}
          <div className="p-4 rounded-xl bg-[var(--surface-highlight)]">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2">Account</p>
            <p className="text-sm text-[var(--text-primary)]">{user?.email || 'Not signed in'}</p>
            {user?.first_name && (
              <p className="text-xs text-[var(--text-secondary)] mt-1">{user.first_name} {user.last_name}</p>
            )}
          </div>
          
          {/* Theme Toggle */}
          <div className="p-4 rounded-xl bg-[var(--surface-highlight)] flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">Theme</p>
              <p className="text-xs text-[var(--text-secondary)]">{theme === 'light' ? 'Light mode' : 'Dark mode'}</p>
            </div>
            <button
              onClick={toggleTheme}
              className="w-10 h-10 rounded-xl bg-[var(--surface)] flex items-center justify-center hover:bg-[var(--border)] transition-colors"
            >
              {theme === 'light' ? (
                <Moon size={18} className="text-[var(--text-secondary)]" />
              ) : (
                <Sun size={18} className="text-[var(--text-secondary)]" />
              )}
            </button>
          </div>
          
          {/* App Info */}
          <div className="p-4 rounded-xl bg-[var(--surface-highlight)]">
            <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-2">About</p>
            <p className="text-sm text-[var(--text-primary)]">PharmGPT v1.0</p>
            <p className="text-xs text-[var(--text-secondary)] mt-1">AI-Powered Pharmaceutical Research Assistant</p>
          </div>
        </div>
        
        <button
          onClick={onClose}
          className="w-full mt-6 py-3 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium text-sm hover:opacity-90 transition-opacity"
        >
          Done
        </button>
      </motion.div>
    </div>
  );
}

export default function ChatSidebar({ isOpen, onToggle, onSelectConversation }: ChatSidebarProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, token, logout } = useAuth();
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

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
    
    setIsLoadingHistory(true);
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
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSignOut = () => {
    logout();
    router.push('/login');
  };

  const handleSelectConversation = (id: string) => {
    if (onSelectConversation) {
      onSelectConversation(id);
    }
  };

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
                  <span className="font-serif font-medium text-[var(--text-primary)]">PharmGPT</span>
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
                  {isLoadingHistory ? (
                    <p className="text-sm text-[var(--text-secondary)] px-2">Loading...</p>
                  ) : chatHistory.length === 0 ? (
                    <p className="text-sm text-[var(--text-secondary)] px-2">Chat history will appear here</p>
                  ) : (
                    chatHistory.map((chat, i) => (
                      <motion.button
                        key={chat.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => handleSelectConversation(chat.id)}
                        className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors group"
                      >
                        <p className="text-sm text-[var(--text-primary)] truncate group-hover:text-[var(--accent)] transition-colors">
                          {chat.title}
                        </p>
                        <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                          {chat.date}
                        </p>
                      </motion.button>
                    ))
                  )}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="pt-4 border-t border-[var(--border)] space-y-2">
                <button
                  onClick={() => router.push('/workbench')}
                  className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3"
                >
                  <BarChart3 size={20} strokeWidth={1.5} className="text-[var(--accent)]" />
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
                <button 
                  onClick={() => setShowSettings(true)}
                  className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3"
                >
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

      {/* Settings Modal */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </>
  );
}
