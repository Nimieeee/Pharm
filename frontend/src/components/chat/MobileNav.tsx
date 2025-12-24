'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import {
  Menu, X, Plus, Moon, Sun, Settings, LogOut, BarChart3,
  Search, Image, FolderKanban, MessageSquare, ChevronRight,
  Sparkles
} from 'lucide-react';
import LongPressMenu, { useChatContextMenu } from './LongPressMenu';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? '' // Use relative path for production (proxied by Vercel rewrites)
  : 'http://localhost:8000';

interface ChatHistory {
  id: string;
  title: string;
  date: string;
}

interface MobileNavProps {
  onSelectConversation?: (id: string) => void;
  onNewChat?: () => void;
  onDeleteConversation?: (id: string) => void;
}

export default function MobileNav({ onSelectConversation, onNewChat, onDeleteConversation }: MobileNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const { user, token, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

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

  const handleDeleteChat = async (chatId: string) => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${chatId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setChatHistory(prev => prev.filter(c => c.id !== chatId));
        onDeleteConversation?.(chatId);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  // Filter chats based on search
  const filteredChats = chatHistory.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Navigation items
  const navItems = [
    { id: 'chat', label: 'New Chat', icon: MessageSquare, onClick: () => { onNewChat?.(); setIsOpen(false); router.push('/chat'); } },
    { id: 'workbench', label: 'Data Workbench', icon: BarChart3, onClick: () => { setIsOpen(false); router.push('/workbench'); } },
  ];

  return (
    <>
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
              className="md:hidden fixed inset-0 z-[99] bg-black/50 backdrop-blur-sm"
            />

            {/* Drawer - Slide from Left */}
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="md:hidden fixed left-0 top-0 bottom-0 z-[100] w-[85vw] max-w-[320px] bg-[var(--surface)] flex flex-col"
            >
              {/* Header with Search */}
              <div className="p-4 border-b border-[var(--border)]">
                <div className="flex items-center justify-between mb-4">
                  <button
                    onClick={() => { setIsOpen(false); router.push('/'); }}
                    className="flex items-center gap-2"
                  >
                    <div className="w-8 h-8 relative rounded-xl overflow-hidden">
                      <img
                        src="/PharmGPT.png"
                        alt="PharmGPT Logo"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <span className="font-serif font-medium text-[var(--text-primary)]">PharmGPT</span>
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="w-8 h-8 rounded-full bg-[var(--surface-highlight)] flex items-center justify-center"
                  >
                    <X size={16} className="text-[var(--text-secondary)]" />
                  </button>
                </div>

                {/* Search Bar - Rounded Pill */}
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search chats..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-full bg-[var(--surface-highlight)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20"
                  />
                </div>
              </div>

              {/* Navigation Items */}
              <div className="p-4 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={item.onClick}
                      className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-[var(--surface-highlight)] transition-colors"
                    >
                      <Icon size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                      <span className="text-sm font-medium text-[var(--text-primary)]">{item.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto px-4">
                <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 px-2">
                  Recent Chats
                </p>
                <div className="space-y-1">
                  {filteredChats.length === 0 ? (
                    <p className="text-sm text-[var(--text-secondary)] px-2">
                      {searchQuery ? 'No chats found' : 'Chat history will appear here'}
                    </p>
                  ) : (
                    filteredChats.map((chat) => (
                      <LongPressMenu
                        key={chat.id}
                        items={useChatContextMenu(
                          undefined,
                          undefined,
                          undefined,
                          () => handleDeleteChat(chat.id)
                        )}
                      >
                        <button
                          onClick={() => {
                            onSelectConversation?.(chat.id);
                            setIsOpen(false);
                          }}
                          className="w-full p-3 rounded-xl text-left hover:bg-[var(--surface-highlight)] transition-colors group"
                        >
                          <p className="text-sm text-[var(--text-primary)] truncate group-hover:text-[var(--accent)]">
                            {chat.title}
                          </p>
                          <p className="text-xs text-[var(--text-secondary)] mt-0.5">{chat.date}</p>
                        </button>
                      </LongPressMenu>
                    ))
                  )}
                </div>
              </div>

              {/* Footer - User Profile */}
              <div className="p-4 border-t border-[var(--border)]">
                {/* Theme Toggle */}
                <button
                  onClick={toggleTheme}
                  className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-[var(--surface-highlight)] transition-colors mb-2"
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

                {/* User Profile Row */}
                {user ? (
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--surface-highlight)]">
                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-full border-2 border-[var(--surface-highlight)] shadow-sm overflow-hidden bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`}
                          alt="Avatar"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-white text-sm font-medium">
                          {user.first_name?.[0] || user.email?.[0]?.toUpperCase() || 'U'}
                        </span>
                      )}
                    </div>
                    {/* Name */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                        {user.first_name ? `${user.first_name} ${user.last_name || ''}` : user.email}
                      </p>
                      <p className="text-xs text-[var(--text-secondary)] truncate">{user.email}</p>
                    </div>
                    {/* Settings / Sign Out */}
                    <button
                      onClick={handleSignOut}
                      className="w-8 h-8 rounded-full hover:bg-[var(--surface)] flex items-center justify-center transition-colors"
                    >
                      <LogOut size={16} className="text-[var(--text-secondary)]" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => { setIsOpen(false); router.push('/login'); }}
                    className="w-full p-3 rounded-xl bg-[var(--text-primary)] text-[var(--background)] text-sm font-medium"
                  >
                    Sign In
                  </button>
                )}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Export the toggle function for external use */}
      <MobileNavTrigger onOpen={() => setIsOpen(true)} />
    </>
  );
}

// Separate component to expose the trigger
function MobileNavTrigger({ onOpen }: { onOpen: () => void }) {
  // Store the onOpen function in a global context or use a ref
  useEffect(() => {
    (window as any).__openMobileNav = onOpen;
    return () => {
      delete (window as any).__openMobileNav;
    };
  }, [onOpen]);

  return null;
}

// Helper to open mobile nav from outside
export function openMobileNav() {
  (window as any).__openMobileNav?.();
}
