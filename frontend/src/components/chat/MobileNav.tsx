'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu, X, Plus, MessageSquare, Calendar,
  Search, Moon, Sun, Settings, LogOut, User, Folder, MoreVertical, LogIn
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useTheme } from '@/lib/theme-context';
import { useTranslation } from '@/hooks/use-translation';

interface MobileNavProps {
  conversations: any[];
  currentConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string, e: React.MouseEvent) => void;
}

export default function MobileNav({
  conversations,
  currentConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation
}: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isOverflowOpen, setIsOverflowOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const signOut = logout;
  const { t } = useTranslation();

  const handleSignOut = () => {
    signOut();
    router.push('/login');
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const currentChat = conversations.find(c => c.id === currentConversationId);
  const headerTitle = currentChat ? currentChat.title : "Benchside";

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--border)] z-50 flex items-center justify-between px-4">
        <button
          onClick={() => setIsOpen(true)}
          className="w-10 h-10 -ml-2 flex items-center justify-center text-[var(--text-primary)]"
        >
          <Menu size={24} />
        </button>

        <div className="font-semibold text-lg text-[var(--text-primary)] truncate px-2 max-w-[200px]">
          {headerTitle}
        </div>

        <div className="relative">
          <button
            onClick={() => setIsOverflowOpen(!isOverflowOpen)}
            className="w-10 h-10 -mr-2 flex items-center justify-center text-[var(--text-primary)] transition-transform active:scale-95"
          >
            <MoreVertical size={24} />
          </button>

          <AnimatePresence>
            {isOverflowOpen && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setIsOverflowOpen(false)}
                  className="fixed inset-0 z-[60]"
                />
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-48 bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-xl z-[61] overflow-hidden flex flex-col"
                >
                  <button
                    onClick={() => {
                      toggleTheme();
                      setIsOverflowOpen(false);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
                    <span className="font-medium text-sm">
                      {theme === 'dark' ? t('dark_mode') : t('light_mode')}
                    </span>
                  </button>

                  <Link
                    href="/profile"
                    onClick={() => setIsOverflowOpen(false)}
                    className="w-full flex items-center gap-3 px-4 py-3 border-t border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <User size={16} />
                    <span className="font-medium text-sm">{t('profile')}</span>
                  </Link>

                  {user ? (
                    <button
                      onClick={() => {
                        handleSignOut();
                        setIsOverflowOpen(false);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 border-t border-[var(--border)] text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors text-left"
                    >
                      <LogOut size={16} />
                      <span className="font-medium text-sm">Sign Out</span>
                    </button>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setIsOverflowOpen(false)}
                      className="w-full flex items-center gap-3 px-4 py-3 border-t border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--surface-highlight)] transition-colors text-left"
                    >
                      <LogIn size={16} />
                      <span className="font-medium text-sm">{t('sign_in')}</span>
                    </Link>
                  )}
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="md:hidden fixed inset-0 bg-black/50 z-[60] backdrop-blur-sm"
            />

            {/* Menu Content */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="md:hidden fixed inset-y-0 left-0 w-[80%] max-w-[320px] bg-[var(--surface)] z-[61] shadow-2xl flex flex-col"
            >
              {/* Header */}
              <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center text-white font-bold text-sm">
                    {user?.first_name?.[0] || user?.email?.[0] || 'U'}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                      {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : user?.email || 'User'}
                    </span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">{user?.is_admin ? 'Admin' : 'User'}</span>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-8 h-8 flex items-center justify-center text-[var(--text-secondary)]"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Main Navigation */}
              <div className="p-4 space-y-2">
                <button
                  onClick={() => {
                    onNewChat();
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/20"
                >
                  <Plus size={18} />
                  <span className="font-medium text-sm">{t('new_chat')}</span>
                </button>

              </div>

              {/* Search */}
              <div className="px-4 pb-2">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                  <input
                    type="text"
                    placeholder="Search chats..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full h-9 pl-9 pr-4 rounded-lg bg-[var(--background)] border border-[var(--border)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)]"
                  />
                </div>
              </div>

              {/* Chat List */}
              <div className="flex-1 overflow-y-auto px-4 py-2">
                <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 px-2">
                  {t('recent_chats')}
                </p>

                <div className="space-y-1">
                  {filteredConversations.length > 0 ? (
                    filteredConversations.map(conv => (
                      <button
                        key={conv.id}
                        onClick={() => {
                          onSelectConversation(conv.id);
                          setIsOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${currentConversationId === conv.id
                          ? 'bg-[var(--surface-highlight)] text-[var(--text-primary)] font-medium'
                          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-highlight)]/50'
                          }`}
                      >
                        <MessageSquare size={16} className="shrink-0" />
                        <span className="truncate text-sm flex-1">{conv.title}</span>
                      </button>
                    ))
                  ) : (
                    <div className="p-8 text-center text-[var(--text-secondary)] flex flex-col items-center gap-3">
                      <Folder size={24} strokeWidth={1.5} className="opacity-50" />
                      <p className="text-sm">{t('no_chats_found')}</p>
                    </div>
                  )}
                </div>
              </div>

            </motion.div>
          </>
        )}
      </AnimatePresence >
    </>
  );
}
