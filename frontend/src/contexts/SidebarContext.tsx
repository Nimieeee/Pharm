'use client';

import { createContext, useContext } from 'react';

interface SidebarContextType {
  sidebarOpen: boolean;
}

export const SidebarContext = createContext<SidebarContextType>({ sidebarOpen: true });
export const useSidebar = () => useContext(SidebarContext);
