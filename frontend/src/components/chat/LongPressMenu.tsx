'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Share2, Edit3, Archive, Trash2 } from 'lucide-react';

interface MenuItem {
  id: string;
  label: string;
  icon: typeof Share2;
  onClick: () => void;
  destructive?: boolean;
}

interface LongPressMenuProps {
  children: ReactNode;
  items: MenuItem[];
  onLongPress?: () => void;
}

export default function LongPressMenu({ children, items, onLongPress }: LongPressMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    longPressTimer.current = setTimeout(() => {
      setPosition({ x: touch.clientX, y: touch.clientY });
      setIsOpen(true);
      onLongPress?.();
      // Haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    }, 500);
  };

  const handleTouchEnd = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  const handleTouchMove = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent | TouchEvent) => {
      if (isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  const handleItemClick = (item: MenuItem) => {
    setIsOpen(false);
    item.onClick();
  };

  return (
    <>
      <div
        ref={containerRef}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onTouchMove={handleTouchMove}
        onContextMenu={(e) => {
          e.preventDefault();
          setPosition({ x: e.clientX, y: e.clientY });
          setIsOpen(true);
        }}
      >
        {children}
      </div>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[100] bg-black/20 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Menu */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ type: 'spring', damping: 25, stiffness: 400 }}
              className="fixed z-[101] min-w-[180px] p-2 rounded-2xl bg-[var(--surface)] dark:bg-[#1E1E1E] border border-[var(--border)] shadow-2xl"
              style={{
                left: Math.min(position.x, window.innerWidth - 200),
                top: Math.min(position.y, window.innerHeight - (items.length * 48 + 16)),
              }}
            >
              {items.map((item, index) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                      item.destructive
                        ? 'text-red-500 hover:bg-red-500/10'
                        : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]'
                    }`}
                  >
                    <Icon size={18} strokeWidth={1.5} />
                    <span className="text-sm font-medium">{item.label}</span>
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

// Pre-built menu items for chat conversations
export function useChatContextMenu(
  onShare?: () => void,
  onRename?: () => void,
  onArchive?: () => void,
  onDelete?: () => void
): MenuItem[] {
  return [
    ...(onShare ? [{ id: 'share', label: 'Share', icon: Share2, onClick: onShare }] : []),
    ...(onRename ? [{ id: 'rename', label: 'Rename', icon: Edit3, onClick: onRename }] : []),
    ...(onArchive ? [{ id: 'archive', label: 'Archive', icon: Archive, onClick: onArchive }] : []),
    ...(onDelete ? [{ id: 'delete', label: 'Delete', icon: Trash2, onClick: onDelete, destructive: true }] : []),
  ];
}
