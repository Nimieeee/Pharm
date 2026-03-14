'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  Dna, FlaskConical, Box, BookOpen, 
  Layers, Search, ShieldCheck, Microscope,
  Menu, X, Sparkles
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

const HUBS = [
  { id: 'genetics', name: 'Genetics Hub', icon: Dna, path: '/genetics' },
  { id: 'lab', name: 'Molecular Lab', icon: FlaskConical, path: '/lab' },
  { id: 'studio', name: 'Creation Studio', icon: Box, path: '/studio' },
  { id: 'literature', name: 'Literature', icon: BookOpen, path: '/literature' },
];

const TOOLS = [
  { id: 'ddi', name: 'Drug Interactions', icon: Layers, path: '/ddi' },
  { id: 'gwas', name: 'Variant Lookup', icon: Search, path: '/genetics' },
  { id: 'admet', name: 'ADMET Profiler', icon: ShieldCheck, path: '/lab' },
  { id: 'docs', name: 'Documentation', icon: Microscope, path: '/docs' },
];

export const ResearchSidebar = () => {
  const pathname = usePathname();

  const SidebarLink = ({ item }: { item: typeof HUBS[0] }) => {
    const isActive = pathname === item.path;
    
    return (
      <Link 
        href={item.path}
        className={`group flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all duration-200 ${
          isActive 
            ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20 shadow-sm' 
            : 'text-foreground-muted hover:text-foreground hover:bg-surface-highlight'
        }`}
      >
        <div className={`p-1.5 rounded-lg transition-colors ${
          isActive ? 'bg-orange-500/20 text-orange-500' : 'bg-surface-highlight group-hover:bg-surface-hover'
        }`}>
          <item.icon size={18} strokeWidth={isActive ? 2.5 : 2} />
        </div>
        <span className={isActive ? 'font-medium' : ''}>{item.name}</span>
        {isActive && (
          <motion.div 
            layoutId="active-pill"
            className="ml-auto w-1 h-4 bg-orange-500 rounded-full"
          />
        )}
      </Link>
    );
  };

  return (
    <aside className="w-64 h-full flex flex-col bg-surface border-r border-border p-4 gap-8">
      {/* Brand */}
      <div className="flex items-center gap-3 px-2 mb-2">
        <div className="w-10 h-10 bg-atmospheric rounded-xl flex items-center justify-center border border-border shadow-soft p-2">
          <img src="/Benchside.png" alt="BS" className="w-full h-full object-contain" />
        </div>
        <div>
          <h1 className="font-serif font-bold text-foreground">Benchside</h1>
          <p className="text-[10px] text-foreground-muted tracking-widest uppercase font-medium">Research Hub</p>
        </div>
      </div>

      {/* Hubs Section */}
      <div className="flex flex-col gap-2">
        <p className="text-[10px] font-bold text-foreground-muted uppercase tracking-widest px-3 mb-2 flex items-center gap-2">
          <Sparkles size={10} className="text-orange-500" />
          Core Hubs
        </p>
        <div className="flex flex-col gap-1">
          {HUBS.map(hub => <SidebarLink key={hub.id} item={hub} />)}
        </div>
      </div>

      {/* Tools Section */}
      <div className="flex flex-col gap-2">
        <p className="text-[10px] font-bold text-foreground-muted uppercase tracking-widest px-3 mb-2">
          Research Tools
        </p>
        <div className="flex flex-col gap-1">
          {TOOLS.map(tool => <SidebarLink key={tool.id} item={tool} />)}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-border flex flex-col gap-4">
        <div className="flex items-center justify-between px-3">
          <span className="text-xs text-foreground-muted">System Theme</span>
          <ThemeToggle />
        </div>
        
        <Link 
          href="/"
          className="flex items-center gap-3 px-3 py-2 text-xs text-foreground-muted hover:text-orange-500 transition-colors"
        >
          <X size={14} />
          Back to Portal
        </Link>
      </div>
    </aside>
  );
};
