'use client';

import { useState } from 'react';
import ChatSidebar from '@/components/chat/ChatSidebar';
import MobileNav from '@/components/chat/MobileNav';
import { SidebarContext } from '@/contexts/SidebarContext';
import { ChatProvider, useChatContext } from '@/contexts/ChatContext';

function ChatLayoutInner({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { selectConversation, clearMessages, conversationId } = useChatContext();

  const handleSelectConversation = (id: string) => {
    selectConversation(id);
  };

  const handleNewChat = () => {
    clearMessages();
  };

  const handleDeleteConversation = (id: string) => {
    // If the deleted conversation is the current one, clear messages
    if (id === conversationId) {
      clearMessages();
    }
  };

  return (
    <SidebarContext.Provider value={{ sidebarOpen, setSidebarOpen }}>
      <div className="h-screen flex bg-[var(--background)]">
        {/* Sidebar - Overlay on mobile, fixed on desktop */}
        <ChatSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />

        {/* Mobile Navigation - Legacy, can be removed if not needed */}
        <MobileNav
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
        />

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
}

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <ChatProvider>
      <ChatLayoutInner>{children}</ChatLayoutInner>
    </ChatProvider>
  );
}
