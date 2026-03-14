'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTheme } from '@/lib/theme-context';
import { 
  Dna, FlaskConical, Box, BookOpen, 
  Layers, Search, ShieldCheck, Microscope,
  Menu, X, Sparkles, ChevronDown, Sun, Moon
} from 'lucide-react';

const NAVIGATION = [
  { 
    title: 'SCIENTIFIC HUB', 
    items: [
      { id: 'genetics', name: 'Genetics Hub', icon: Dna, path: '/genetics' },
      { id: 'lab', name: 'Molecular Lab', icon: FlaskConical, path: '/lab' },
      { id: 'studio', name: 'Creation Studio', icon: Box, path: '/studio' },
      { id: 'literature', name: 'Literature Engine', icon: BookOpen, path: '/literature' },
      { id: 'ddi', name: 'Interaction Checker', icon: Layers, path: '/ddi' },
    ]
  }
];

export const ResearchSidebar = ({
  isCollapsed,
  onToggle
}: {
  isCollapsed?: boolean;
  onToggle?: () => void;
}) => {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  const SidebarLink = ({ item }: { item: typeof NAVIGATION[0]['items'][0] }) => {
    const isActive = pathname === item.path;
    
    return (
      <Link 
        href={item.path}
        title={isCollapsed ? item.name : undefined}
        className={`group flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-200 ${
          isActive 
            ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20 shadow-sm' 
            : 'text-foreground-muted hover:text-foreground hover:bg-surface-highlight'
        }`}
      >
        <div className={`p-1.5 rounded-lg transition-colors shrink-0 ${
          isActive ? 'bg-orange-500/20 text-orange-500' : 'bg-surface-highlight group-hover:bg-surface-hover'
        }`}>
          <item.icon size={18} strokeWidth={isActive ? 2.5 : 2} />
        </div>
        {!isCollapsed && <span className={isActive ? 'font-medium' : ''}>{item.name}</span>}
        {isActive && !isCollapsed && (
          <motion.div 
            layoutId="active-pill"
            className="ml-auto w-1 h-4 bg-orange-500 rounded-full"
          />
        )}
      </Link>
    );
  };

  return (
    <aside className={`h-full flex flex-col bg-surface border-r border-border p-4 gap-8 transition-all duration-300 ${isCollapsed ? 'w-20' : 'w-64'}`}>
      {/* Brand & Toggle */}
      <div className="flex items-center gap-3 px-2 mb-2 relative">
        <div className="w-10 h-10 bg-atmospheric rounded-xl flex items-center justify-center border border-border shadow-soft p-2 shrink-0">
          <img src="/Benchside.png" alt="BS" className="w-full h-full object-contain" />
        </div>
        {!isCollapsed && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h1 className="font-serif font-bold text-foreground">Benchside</h1>
            <p className="text-[10px] text-foreground-muted tracking-widest uppercase font-medium">Research Hub</p>
          </motion.div>
        )}
        
        {onToggle && (
          <button 
            onClick={onToggle}
            className={`absolute -right-7 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-border border border-border flex items-center justify-center text-foreground-muted hover:text-foreground transition-all z-10 ${isCollapsed ? 'rotate-180' : ''}`}
          >
            <ChevronDown size={12} className="-rotate-90" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex flex-col gap-6 overflow-y-auto no-scrollbar">
        {NAVIGATION.map((section) => (
          <div key={section.title} className="flex flex-col gap-2">
            {!isCollapsed && (
              <p className="text-[10px] font-bold text-foreground-muted uppercase tracking-widest px-3 mb-1 flex items-center gap-2">
                {section.title === 'Scientific Hubs' && <Sparkles size={10} className="text-orange-500" />}
                {section.title}
              </p>
            )}
            <div className="flex flex-col gap-1">
              {section.items.map(item => <SidebarLink key={item.id} item={item} />)}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-border flex flex-col gap-4">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-200 text-foreground-muted hover:text-foreground hover:bg-surface-highlight`}
          title={isCollapsed ? (theme === 'dark' ? 'Light mode' : 'Dark mode') : undefined}
        >
          <div className="p-1.5 rounded-lg bg-surface-highlight shrink-0">
            {theme === 'dark' ? (
              <Sun size={18} strokeWidth={2} />
            ) : (
              <Moon size={18} strokeWidth={2} />
            )}
          </div>
          {!isCollapsed && <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>}
        </button>

        {!isCollapsed && (
          <Link
            href="/"
            className="flex items-center gap-3 px-3 py-2 text-xs text-foreground-muted hover:text-orange-500 transition-colors"
          >
            <X size={14} />
            Back to Portal
          </Link>
        )}
        {isCollapsed && (
          <Link href="/" title="Back to Portal" className="flex justify-center p-2 text-foreground-muted hover:text-orange-500">
            <X size={18} />
          </Link>
        )}
      </div>
    </aside>
  );
};
