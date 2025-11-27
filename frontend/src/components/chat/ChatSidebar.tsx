import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import * as RadixPopover from '@radix-ui/react-popover';
import {
  ChevronsLeft, ChevronsRight, Plus, Moon, Sun, Settings, BarChart3, LogOut, X,
  MoreHorizontal, Pin, Pencil, Copy, Archive, Share2, Download, Trash2
} from 'lucide-react';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt-backend.onrender.com'
  : 'http://localhost:8000';

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onSelectConversation?: (id: string) => void;
  onNewChat?: () => void;
}

interface ChatHistory {
  id: string;
  title: string;
  date: string; // Used for display date string in old logic, now we use created_at for grouping
  created_at: string;
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-md mx-4 p-6 rounded-2xl bg-surface border border-border shadow-xl"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-serif font-medium text-foreground">Settings</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-surface-highlight flex items-center justify-center hover:bg-surface-hover transition-colors"
          >
            <X size={16} className="text-foreground-muted" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Account Info */}
          <div className="p-4 rounded-xl bg-surface-highlight">
            <p className="text-xs font-medium text-foreground-muted uppercase tracking-wider mb-2">Account</p>
            <p className="text-sm text-foreground">{user?.email || 'Not signed in'}</p>
            {user?.first_name && (
              <p className="text-xs text-foreground-muted mt-1">{user.first_name} {user.last_name}</p>
            )}
          </div>

          {/* Theme Toggle */}
          <div className="p-4 rounded-xl bg-surface-highlight flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Theme</p>
              <p className="text-xs text-foreground-muted">{theme === 'light' ? 'Light mode' : 'Dark mode'}</p>
            </div>
            <button
              onClick={toggleTheme}
              className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center hover:bg-surface-hover transition-colors"
            >
              {theme === 'light' ? (
                <Moon size={18} className="text-foreground-muted" />
              ) : (
                <Sun size={18} className="text-foreground-muted" />
              )}
            </button>
          </div>

          {/* App Info */}
          <div className="p-4 rounded-xl bg-surface-highlight">
            <p className="text-xs font-medium text-foreground-muted uppercase tracking-wider mb-2">About</p>
            <p className="text-sm text-foreground">PharmGPT v1.0</p>
            <p className="text-xs text-foreground-muted mt-1">AI-Powered Pharmaceutical Research Assistant</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 py-3 rounded-xl bg-foreground text-background font-medium text-sm hover:opacity-90 transition-opacity"
        >
          Done
        </button>
      </motion.div>
    </div>
  );
}

// Helper to categorize dates
const getRelativeDateCategory = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays <= 1 && now.getDate() === date.getDate()) return 'Today';
  if (diffDays <= 2) return 'Yesterday';
  if (diffDays <= 7) return 'Previous 7 Days';
  if (diffDays <= 30) return 'Previous 30 Days';

  return date.toLocaleString('default', { month: 'long' });
};

export default function ChatSidebar({ isOpen, onToggle, onSelectConversation, onNewChat }: ChatSidebarProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, token, logout } = useAuth();
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  // Fetch conversation history when user is logged in
  useEffect(() => {
    if (token) {
      fetchConversationHistory();
    } else {
      setChatHistory([]);
    }
  }, [token]);

  // Listen for active conversation changes from localStorage
  useEffect(() => {
    const checkActiveChat = () => {
      const current = localStorage.getItem('currentConversationId');
      setActiveChatId(current);
    };

    checkActiveChat();
    window.addEventListener('storage', checkActiveChat);
    // Also poll/check periodically or on route change if needed, 
    // but for now we'll rely on parent updates or manual checks
    const interval = setInterval(checkActiveChat, 1000);

    return () => {
      window.removeEventListener('storage', checkActiveChat);
      clearInterval(interval);
    };
  }, []);

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
        const formattedHistory = conversations.map((conv: any) => ({
          id: conv.id,
          title: conv.title || 'Untitled Chat',
          date: new Date(conv.created_at).toLocaleDateString(),
          created_at: conv.created_at
        }));
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
    setActiveChatId(id);
    if (onSelectConversation) {
      onSelectConversation(id);
    }
  };

  // Group chats by category
  const groupedChats = chatHistory.reduce((acc, chat) => {
    const category = getRelativeDateCategory(chat.created_at);
    if (!acc[category]) acc[category] = [];
    acc[category].push(chat);
    return acc;
  }, {} as Record<string, ChatHistory[]>);

  // Order of categories
  const categoryOrder = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days'];
  const sortedCategories = Object.keys(groupedChats).sort((a, b) => {
    const indexA = categoryOrder.indexOf(a);
    const indexB = categoryOrder.indexOf(b);
    if (indexA !== -1 && indexB !== -1) return indexA - indexB;
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;
    return 0; // Keep other months as they appear (or sort alphabetically if needed)
  });

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
            className="hidden md:flex flex-col h-full border-r border-border bg-surface overflow-hidden"
          >
            <div className="p-4 flex flex-col h-full">
              {/* Header Area - Vertical Stack */}
              <div className="flex flex-col gap-4 mb-2">
                {/* Row 1: Logo and Toggle */}
                <div className="flex items-center justify-between h-12 px-1">
                  <button
                    onClick={() => router.push('/')}
                    className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                  >
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                      <span className="text-white text-sm font-bold">P</span>
                    </div>
                    <span className="font-serif font-medium text-foreground text-lg">PharmGPT</span>
                  </button>
                  <button
                    onClick={onToggle}
                    className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-surface-highlight transition-colors text-foreground-muted"
                  >
                    <ChevronsLeft size={20} strokeWidth={1.5} />
                  </button>
                </div>

                {/* Row 2: New Chat Button */}
                <button
                  onClick={() => {
                    onNewChat?.();
                    router.push('/chat');
                    setActiveChatId(null);
                  }}
                  className="w-full h-10 px-4 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-medium text-sm flex items-center gap-2 hover:opacity-90 transition-all"
                >
                  <Plus size={18} strokeWidth={2} />
                  New Chat
                </button>

                {/* Row 3: Search Bar */}
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search chats..."
                    className="w-full h-9 pl-9 pr-4 rounded-md bg-secondary/50 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
                  </div>
                </div>
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {isLoadingHistory ? (
                  <p className="text-sm text-foreground-muted px-2">Loading...</p>
                ) : chatHistory.length === 0 ? (
                  <p className="text-sm text-foreground-muted px-2">Chat history will appear here</p>
                ) : (
                  sortedCategories.map((category) => (
                    <div key={category} className="mb-6">
                      <p className="text-xs font-medium text-foreground-muted px-3 py-2 mb-1">
                        {category}
                      </p>
                      <div className="space-y-1">
                        {groupedChats[category].map((chat) => {
                          const isActive = activeChatId === chat.id;
                          return (
                            <div key={chat.id} className="group relative">
                              <button
                                onClick={() => handleSelectConversation(chat.id)}
                                className={`w-full flex items-center justify-between p-2 pl-3 pr-2 rounded-md text-sm transition-colors h-9 ${isActive
                                  ? 'bg-[var(--surface-highlight)] text-foreground'
                                  : 'text-foreground/80 hover:bg-[var(--surface-highlight)]/50'
                                  }`}
                              >
                                <span className="truncate flex-1 text-left">{chat.title}</span>

                                {/* Context Menu Trigger */}
                                <RadixPopover.Root>
                                  <RadixPopover.Trigger asChild>
                                    <div
                                      role="button"
                                      tabIndex={0}
                                      className={`p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10 ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                                        } transition-opacity`}
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <MoreHorizontal size={14} className="text-foreground-muted" />
                                    </div>
                                  </RadixPopover.Trigger>
                                  <RadixPopover.Portal>
                                    <RadixPopover.Content
                                      className="z-[100] w-[200px] rounded-xl border border-border bg-background shadow-2xl p-1 animate-in fade-in zoom-in-95 duration-200"
                                      sideOffset={5}
                                      align="end"
                                    >
                                      <div className="flex flex-col gap-0.5">
                                        {[
                                          { icon: Pin, label: 'Pin' },
                                          { icon: Pencil, label: 'Rename' },
                                          { icon: Copy, label: 'Clone' },
                                          { icon: Archive, label: 'Archive' },
                                          { icon: Share2, label: 'Share' },
                                          { icon: Download, label: 'Download' },
                                        ].map((item) => (
                                          <button
                                            key={item.label}
                                            className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                                          >
                                            <item.icon size={14} className="text-foreground-muted" />
                                            {item.label}
                                          </button>
                                        ))}

                                        <button
                                          className="flex items-center gap-2 px-2 py-1.5 text-sm text-red-500 rounded-md hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors text-left"
                                        >
                                          <Trash2 size={14} />
                                          Delete
                                        </button>
                                      </div>

                                      {/* Tags Footer */}
                                      <div className="h-px bg-border my-1" />
                                      <div className="px-2 py-1.5 flex items-center gap-2">
                                        <span className="px-2 py-0.5 rounded-full bg-[var(--surface-highlight)] text-[10px] font-medium text-foreground-muted border border-border">
                                          General
                                        </span>
                                        <button className="w-5 h-5 rounded-full border border-dashed border-foreground-muted flex items-center justify-center hover:border-foreground transition-colors">
                                          <Plus size={10} className="text-foreground-muted" />
                                        </button>
                                      </div>
                                    </RadixPopover.Content>
                                  </RadixPopover.Portal>
                                </RadixPopover.Root>
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Footer Actions */}
              <div className="pt-4 border-t border-border space-y-2">
                <button
                  onClick={() => router.push('/workbench')}
                  className="w-full p-3 rounded-xl text-left hover:bg-surface-hover transition-colors flex items-center gap-3"
                >
                  <BarChart3 size={20} strokeWidth={1.5} className="text-[var(--accent)]" />
                  <span className="text-sm text-foreground">Data Workbench</span>
                </button>
                <button
                  onClick={toggleTheme}
                  className="w-full p-3 rounded-xl text-left hover:bg-surface-hover transition-colors flex items-center gap-3"
                >
                  {theme === 'light' ? (
                    <Moon size={20} strokeWidth={1.5} className="text-foreground-muted" />
                  ) : (
                    <Sun size={20} strokeWidth={1.5} className="text-foreground-muted" />
                  )}
                  <span className="text-sm text-foreground">
                    {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                  </span>
                </button>
                <button
                  onClick={() => setShowSettings(true)}
                  className="w-full p-3 rounded-xl text-left hover:bg-surface-hover transition-colors flex items-center gap-3"
                >
                  <Settings size={20} strokeWidth={1.5} className="text-foreground-muted" />
                  <span className="text-sm text-foreground">Settings</span>
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
          className="hidden md:flex fixed left-4 top-4 z-40 w-10 h-10 rounded-xl bg-surface border border-border items-center justify-center hover:bg-surface-hover transition-colors btn-press shadow-lg"
        >
          <ChevronsRight size={16} strokeWidth={1.5} className="text-foreground-muted" />
        </button>
      )}

      {/* Settings Modal */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </>
  );
}
