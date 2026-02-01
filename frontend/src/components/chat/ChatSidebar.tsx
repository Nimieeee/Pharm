import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { useAuth } from '@/lib/auth-context';
import { useConversations, clearSWRCache } from '@/hooks/useSWRChat';
import { useStreamingConversations } from '@/hooks/useStreamingState';
import { useTranslation } from '@/hooks/use-translation';
import * as RadixPopover from '@radix-ui/react-popover';
import {
  ChevronsLeft, ChevronsRight, Plus, Moon, Sun, Settings, LogOut, X,
  MoreHorizontal, Pin, Pencil, Copy, Archive, Share2, Download, Trash2, Book, HelpCircle, Loader2, User, ShieldAlert
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { API_BASE_URL } from '@/config/api';


interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onSelectConversation?: (id: string) => void;
  onNewChat?: () => void;
  currentChatId?: string | null;
}

interface ChatHistory {
  id: string;
  title: string;
  date: string;
  created_at: string;
  is_pinned?: boolean;
  is_archived?: boolean;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const { t } = useTranslation();

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
          <h2 className="text-lg font-serif font-medium text-foreground">{t('settings')}</h2>
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
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-foreground-muted uppercase tracking-wider">{t('account')}</p>
              <button
                onClick={() => { onClose(); router.push('/profile'); }}
                className="text-xs font-medium text-indigo-500 hover:text-indigo-600 transition-colors"
                role="link"
              >
                {t('manage_profile')}
              </button>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-medium text-lg overflow-hidden shrink-0">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`}
                    alt={user.first_name || 'User'}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{user?.first_name ? `${user.first_name} ${user.last_name || ''}` : 'User'}</p>
                <p className="text-xs text-foreground-muted truncate max-w-[200px]">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Help & Support (Moved from Sidebar) */}
          <div className="p-4 rounded-xl bg-surface-highlight space-y-2">
            <p className="text-xs font-medium text-foreground-muted uppercase tracking-wider mb-2">{t('help_support')}</p>
            <button
              onClick={() => { onClose(); router.push('/support'); }}
              className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-surface transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <HelpCircle size={18} className="text-blue-500" />
                <span className="text-sm text-foreground">{t('help_center')}</span>
              </div>
              <ChevronsRight size={14} className="text-foreground-muted" />
            </button>
            <button
              onClick={() => { onClose(); router.push('/docs'); }}
              className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-surface transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <Book size={18} className="text-indigo-500" />
                <span className="text-sm text-foreground">{t('documentation')}</span>
              </div>
              <ChevronsRight size={14} className="text-foreground-muted" />
            </button>
          </div>

          {/* App Info */}
          <div className="p-4 rounded-xl bg-surface-highlight">
            <p className="text-xs font-medium text-foreground-muted uppercase tracking-wider mb-2">{t('about')}</p>
            <div className="flex justify-between items-center">
              <p className="text-sm text-foreground">PharmGPT</p>
              <span className="text-xs bg-surface px-2 py-1 rounded-md text-foreground-muted font-mono">v2.0.0</span>
            </div>
            <p className="text-xs text-foreground-muted mt-2">AI-Powered Pharmacological Research Assistant</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 py-3 rounded-xl bg-foreground text-background font-medium text-sm hover:opacity-90 transition-opacity"
        >
          {t('done')}
        </button>
      </motion.div>
    </div>
  );
}

// Helper to categorize dates
const getRelativeDateCategory = (dateString: string, t: (key: string) => string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays <= 1 && now.getDate() === date.getDate()) return t('today');
  if (diffDays <= 2) return t('yesterday');
  if (diffDays <= 7) return t('previous_7_days');
  if (diffDays <= 30) return t('previous_30_days');

  return date.toLocaleString('default', { month: 'long' });
};

export default function ChatSidebar({ isOpen, onToggle, onSelectConversation, onNewChat, currentChatId }: ChatSidebarProps) {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, token, logout } = useAuth();
  const { t } = useTranslation();
  const [showArchived, setShowArchived] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [openPopoverId, setOpenPopoverId] = useState<string | null>(null);

  // SWR for conversation list - no token param needed (uses localStorage internally)
  const { conversations, isLoading: isLoadingHistory, isError, mutate: mutateConversations } = useConversations();

  // Track which conversations are currently streaming
  const streamingConversations = useStreamingConversations();


  // Transform to ChatHistory format
  const chatHistory = useMemo(() =>
    conversations.map((conv: any) => ({
      id: conv.id,
      title: conv.title || 'Untitled Chat',
      date: new Date(conv.created_at).toLocaleDateString(),
      created_at: conv.created_at,
      is_pinned: conv.is_pinned,
      is_archived: conv.is_archived
    })), [conversations]
  );

  // Clear cache on unmount or logout if needed
  useEffect(() => {
    if (!user) {
      // Clear sensitive data when no user
      mutateConversations([], false);
    }
  }, [user, mutateConversations]);

  // Listen for active conversation changes from localStorage
  useEffect(() => {
    const checkActiveChat = () => {
      const current = localStorage.getItem('currentConversationId');
      setActiveChatId(current);
    };

    checkActiveChat();

    // Only listen to storage events from other tabs
    window.addEventListener('storage', checkActiveChat);

    return () => {
      window.removeEventListener('storage', checkActiveChat);
    };
  }, []);

  // Refresh conversations (called after create/delete)
  const fetchConversationHistory = () => {
    mutateConversations();
  };

  const handleSignOut = async () => {
    try {
      // 1. Clear SWR cache explicitly
      const { clearSWRCache } = await import('@/hooks/useSWRChat');
      clearSWRCache();

      // 2. Perform logout
      await logout();
    } catch (error) {
      console.error('Logout failed', error);
    }
    router.push('/login');
  };

  const handleSelectConversation = (id: string) => {
    setActiveChatId(id);
    if (onSelectConversation) {
      onSelectConversation(id);
    }
  };

  // Actions - using SWR optimistic updates
  const handlePin = async (id: string, currentPinned: boolean) => {
    // Optimistic update
    mutateConversations(
      (current: any[] | undefined) => current?.map((c: any) => c.id === id ? { ...c, is_pinned: !currentPinned } : c) || [],
      false
    );
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${id}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_pinned: !currentPinned })
      });
      if (!response.ok) {
        throw new Error(`Failed to ${currentPinned ? 'unpin' : 'pin'} conversation`);
      }
    } catch (error) {
      console.error('Pin error:', error);
      alert(error instanceof Error ? error.message : 'Failed to update conversation');
      mutateConversations(); // Revalidate on error
    }
  };

  const handleArchive = async (id: string, currentArchived: boolean) => {
    mutateConversations(
      (current: any[] | undefined) => current?.map((c: any) => c.id === id ? { ...c, is_archived: !currentArchived } : c) || [],
      false
    );
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${id}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_archived: !currentArchived })
      });
      if (!response.ok) {
        throw new Error('Failed to archive conversation');
      }
    } catch (error) {
      console.error('Archive error:', error);
      alert(error instanceof Error ? error.message : 'Failed to archive conversation');
      mutateConversations(); // Revalidate on error
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this chat?')) return;

    mutateConversations(
      (current: any[] | undefined) => current?.filter((c: any) => c.id !== id) || [],
      false
    );

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        let errorMessage = 'Failed to delete conversation';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If json parse fails, use default message
        }
        throw new Error(errorMessage);
      }
      if (activeChatId === id) {
        onNewChat?.();
        router.push('/chat');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete conversation');
      mutateConversations(); // Revalidate on error
    }
  };

  const handleClone = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${id}/clone`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        throw new Error('Failed to clone conversation');
      }
      const newChat = await response.json();
      mutateConversations(); // Refresh list
      onSelectConversation?.(newChat.id);
    } catch (error) {
      console.error('Clone error:', error);
      alert(error instanceof Error ? error.message : 'Failed to clone conversation');
    }
  };

  const handleRename = async (id: string) => {
    if (!editTitle.trim()) return;

    mutateConversations(
      (current: any[] | undefined) => current?.map((c: any) => c.id === id ? { ...c, title: editTitle } : c) || [],
      false
    );
    setEditingId(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${id}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editTitle })
      });
      if (!response.ok) {
        throw new Error('Failed to rename conversation');
      }
    } catch (error) {
      console.error('Rename error:', error);
      alert(error instanceof Error ? error.message : 'Failed to rename conversation');
      mutateConversations(); // Revalidate on error
    }
  };

  const handleDownload = async (chat: ChatHistory) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${chat.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to download conversation');
      }

      const fullChat = await response.json();
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(fullChat, null, 2));
      const downloadAnchorNode = document.createElement('a');
      downloadAnchorNode.setAttribute("href", dataStr);
      downloadAnchorNode.setAttribute("download", `${chat.title.replace(/[^a-z0-9]/gi, '_')}.json`);
      document.body.appendChild(downloadAnchorNode);
      downloadAnchorNode.click();
      downloadAnchorNode.remove();
    } catch (error) {
      console.error('Download error:', error);
      alert(error instanceof Error ? error.message : 'Failed to download conversation');
    }
  };

  // Group chats
  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return chatHistory;
    return chatHistory.filter((chat: ChatHistory) =>
      chat.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [chatHistory, searchQuery]);

  const pinnedChats = filteredHistory.filter((c: ChatHistory) => c.is_pinned && !c.is_archived);
  const unpinnedChats = filteredHistory.filter((c: ChatHistory) => !c.is_pinned && !c.is_archived);

  const groupedChats = unpinnedChats.reduce((acc: Record<string, ChatHistory[]>, chat: ChatHistory) => {
    const category = getRelativeDateCategory(chat.created_at, t);
    if (!acc[category]) acc[category] = [];
    acc[category].push(chat);
    return acc;
  }, {} as Record<string, ChatHistory[]>);

  const categoryOrder = [t('today'), t('yesterday'), t('previous_7_days'), t('previous_30_days')];
  const sortedCategories = Object.keys(groupedChats).sort((a, b) => {
    const indexA = categoryOrder.indexOf(a);
    const indexB = categoryOrder.indexOf(b);
    if (indexA !== -1 && indexB !== -1) return indexA - indexB;
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;
    return 0;
  });

  const renderChatItem = (chat: ChatHistory) => {
    // Prefer external currentChatId if provided, otherwise fallback to local state
    const effectiveActiveId = currentChatId !== undefined ? currentChatId : activeChatId;
    const isActive = effectiveActiveId === chat.id;
    const isEditing = editingId === chat.id;
    const isStreaming = streamingConversations.has(chat.id);

    return (
      <div key={chat.id} className="group relative">
        <div
          className={`w-full flex items-center justify-between p-2 pl-3 pr-2 rounded-md text-sm transition-colors h-9 ${isActive
            ? 'bg-[var(--surface-highlight)] text-foreground'
            : 'text-foreground/80 hover:bg-[var(--surface-highlight)]/50'
            }`}
        >
          {/* Streaming indicator */}
          {isStreaming && (
            <Loader2 size={14} className="mr-2 animate-spin text-indigo-500 flex-shrink-0" />
          )}

          {isEditing ? (
            <input
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onBlur={() => handleRename(chat.id)}
              onKeyDown={(e) => e.key === 'Enter' && handleRename(chat.id)}
              className="flex-1 bg-transparent border-none outline-none text-sm"
            />
          ) : (
            <button
              className="flex-1 text-left truncate"
              onClick={() => handleSelectConversation(chat.id)}
            >
              {chat.title}
            </button>
          )}

          {/* Context Menu - 3 dots button */}
          <RadixPopover.Root open={openPopoverId === chat.id} onOpenChange={(open) => setOpenPopoverId(open ? chat.id : null)}>
            <RadixPopover.Trigger asChild>
              <div
                role="button"
                tabIndex={0}
                className={`p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10 transition-opacity
                  ${isActive || openPopoverId === chat.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}
                `}
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
                side="bottom"
              >
                <div className="flex flex-col gap-0.5">
                  <button
                    onClick={() => { handlePin(chat.id, !!chat.is_pinned); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <Pin size={14} className="text-foreground-muted" />
                    {chat.is_pinned ? t('unpin') : t('pin')}
                  </button>
                  <button
                    onClick={() => { setEditingId(chat.id); setEditTitle(chat.title); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <Pencil size={14} className="text-foreground-muted" />
                    {t('rename')}
                  </button>
                  <button
                    onClick={() => { handleClone(chat.id); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <Copy size={14} className="text-foreground-muted" />
                    {t('clone')}
                  </button>
                  <button
                    onClick={() => { handleArchive(chat.id, !!chat.is_archived); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <Archive size={14} className="text-foreground-muted" />
                    {t('archive')}
                  </button>
                  <button
                    onClick={() => { handleDownload(chat); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-foreground rounded-md hover:bg-[var(--surface-highlight)] transition-colors text-left"
                  >
                    <Download size={14} className="text-foreground-muted" />
                    {t('download')}
                  </button>
                  <button
                    onClick={() => { handleDelete(chat.id); setOpenPopoverId(null); }}
                    className="flex items-center gap-2 px-2 py-1.5 text-sm text-red-500 rounded-md hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors text-left"
                  >
                    <Trash2 size={14} />
                    {t('delete')}
                  </button>
                </div>
              </RadixPopover.Content>
            </RadixPopover.Portal>
          </RadixPopover.Root>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="md:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-[90]"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.aside
            initial={{ width: 0, x: -20, opacity: 0 }}
            animate={{ width: 280, x: 0, opacity: 1 }}
            exit={{ width: 0, x: -20, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
            className="fixed md:relative z-[100] md:z-0 h-full border-r border-border bg-surface overflow-hidden shadow-2xl md:shadow-none will-change-transform whitespace-nowrap"
          >
            <div className="w-[280px] h-full flex flex-col p-4">
              {/* Header Area */}
              <div className="flex flex-col gap-4 mb-2">
                <div className="flex items-center justify-between h-12 px-1">
                  <div className="flex items-center gap-2">
                    {/* Mobile Toggle */}
                    <button
                      onClick={onToggle}
                      className="md:hidden w-8 h-8 rounded-lg flex items-center justify-center hover:bg-surface-highlight transition-colors text-foreground-muted"
                    >
                      <ChevronsLeft size={20} strokeWidth={1.5} />
                    </button>

                    <button
                      onClick={() => router.push('/')}
                      className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                    >
                      <div className="w-8 h-8 relative rounded-xl overflow-hidden">
                        <img
                          src="/PharmGPT.png"
                          alt="PharmGPT Logo"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <span className="font-serif font-medium text-foreground text-lg">PharmGPT</span>
                    </button>
                  </div>

                  <button
                    onClick={onToggle}
                    className="hidden md:flex w-8 h-8 rounded-lg items-center justify-center hover:bg-surface-highlight transition-colors text-foreground-muted"
                  >
                    <ChevronsLeft size={20} strokeWidth={1.5} />
                  </button>
                </div>

                <button
                  onClick={() => {
                    onNewChat?.();
                    router.push('/chat');
                    setActiveChatId(null);
                  }}
                  className="w-full h-10 px-4 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-medium text-sm flex items-center gap-2 hover:opacity-90 transition-all"
                >
                  <Plus size={18} strokeWidth={2} />
                  {t('new_chat')}
                </button>

                <div className="relative">
                  <input
                    type="text"
                    placeholder={t('search_chats')}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full h-9 pl-9 pr-4 rounded-lg bg-[var(--surface-highlight)] dark:bg-zinc-800/50 border border-[var(--border)] text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/50 transition-all"
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-foreground-muted"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
                  </div>
                </div>
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                {isLoadingHistory && chatHistory.length === 0 ? (
                  // Skeleton loader for fresh logins - feels faster than "Loading..."
                  <div className="space-y-2 px-2">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="animate-pulse">
                        <div className="h-10 bg-[var(--surface-highlight)] rounded-lg" />
                      </div>
                    ))}
                  </div>
                ) : isError ? (
                  <div className="flex flex-col items-center justify-center py-6 px-2 text-center text-foreground-muted space-y-2">
                    <p className="text-sm">{t('could_not_load')}</p>
                    <button
                      onClick={() => mutateConversations()}
                      className="text-xs px-3 py-1.5 bg-indigo-500/10 text-indigo-500 rounded-md hover:bg-indigo-500/20 transition-colors"
                    >
                      {t('retry')}
                    </button>
                  </div>
                ) : chatHistory.length === 0 ? (
                  <p className="text-sm text-foreground-muted px-2">{t('no_chats')}</p>
                ) : (
                  <>
                    {/* Pinned Chats */}
                    {pinnedChats.length > 0 && (
                      <div className="mb-6">
                        <p className="text-xs font-medium text-foreground-muted px-3 py-2 mb-1 flex items-center gap-1">
                          <Pin size={10} /> {t('pinned')}
                        </p>
                        <div className="space-y-1">
                          {pinnedChats.map(renderChatItem)}
                        </div>
                      </div>
                    )}

                    {/* Recent Chats */}
                    {sortedCategories.map((category) => (
                      <div key={category} className="mb-6">
                        <p className="text-xs font-medium text-foreground-muted px-3 py-2 mb-1">
                          {category}
                        </p>
                        <div className="space-y-1">
                          {groupedChats[category].map(renderChatItem)}
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>

              {/* Footer Actions */}
              <div className="pt-4 border-t border-border space-y-2">

                {/* @ts-ignore */}
                {user?.is_admin && (
                  <button
                    onClick={() => router.push('/admin')}
                    className="w-full p-3 rounded-xl text-left hover:bg-surface-hover transition-colors flex items-center gap-3 bg-red-500/10 text-red-500"
                  >
                    <ShieldAlert size={20} strokeWidth={1.5} />
                    <span className="text-sm font-medium">{t('admin_panel')}</span>
                  </button>
                )}


                {/* Theme Toggle Row */}
                <div className="flex items-center justify-between px-3 py-2">
                  <span className="text-sm text-foreground-muted">{t('theme')}</span>
                  <ThemeToggle />
                </div>

                <button
                  onClick={() => setShowSettings(true)}
                  className="w-full p-3 rounded-xl text-left hover:bg-surface-hover transition-colors flex items-center gap-3"
                >
                  <Settings size={20} strokeWidth={1.5} className="text-foreground-muted" />
                  <span className="text-sm text-foreground">{t('settings')}</span>
                </button>

                {token && (
                  <button
                    onClick={handleSignOut}
                    className="w-full p-3 rounded-xl text-left hover:bg-red-500/10 transition-colors flex items-center gap-3"
                  >
                    <LogOut size={20} strokeWidth={1.5} className="text-red-500" />
                    <span className="text-sm text-red-500">{t('sign_out')}</span>
                  </button>
                )}

                {/* Signature */}
                <div className="pt-4 pb-2 text-center">
                  <p className="text-[10px] tracking-[0.2em] text-muted-foreground/40 font-bold uppercase">
                    PharmGPT
                  </p>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Collapsed Toggle Button */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="hidden md:flex fixed left-4 top-4 z-40 w-10 h-10 rounded-xl bg-surface border border-border items-center justify-center hover:bg-surface-hover transition-colors btn-press shadow-lg"
        >
          <ChevronsRight size={16} strokeWidth={1.5} className="text-foreground-muted" />
        </button>
      )}

      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </>
  );
}
