'use client';

import { useState, createContext, useContext } from 'react';
import ChatSidebar from '@/components/chat/ChatSidebar';

// Context to share sidebar state with child components
interface SidebarContextType {
  sidebarOpen: boolean;
}

export const SidebarContext = createContext<SidebarContextType>({ sidebarOpen: true });
export const useSidebar = () => useContext(SidebarContext);

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <SidebarContext.Provider value={{ sidebarOpen }}>
      <div className="h-screen flex bg-[var(--background)]">
        {/* Desktop Sidebar - Hidden on mobile */}
        <div className="hidden md:block">
          <ChatSidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
        </div>
        
        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
}
