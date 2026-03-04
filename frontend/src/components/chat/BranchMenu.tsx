import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Trash2, GitBranch } from 'lucide-react';
import { AssistantResponse } from '@/hooks/useChatState';
import { useTranslation } from '@/hooks/use-translation';

interface BranchMenuProps {
    branches: AssistantResponse[];
    activeBranchId: string;
    onSwitchBranch: (responseId: string) => void;
    onDeleteBranch: (responseId: string) => void;
}

function formatTime(isoString: string): string {
    try {
        return new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        }).format(new Date(isoString));
    } catch {
        return '';
    }
}

export default function BranchMenu({ branches, activeBranchId, onSwitchBranch, onDeleteBranch }: BranchMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const { t } = useTranslation();

    // Close on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    if (!branches || branches.length <= 1) {
        return null; // Don't show branch menu if only 1 branch exists
    }

    const activeIndex = branches.findIndex(b => b.id === activeBranchId);
    const activeLabel = activeIndex !== -1 ? branches[activeIndex].branch_label : 'A';

    return (
        <div className="relative inline-block text-left" ref={menuRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--border)] transition-colors border border-transparent hover:border-[var(--border)]"
                title="Switch response branch"
            >
                <GitBranch size={12} className="opacity-70" />
                <span>Branch {activeLabel}</span>
                <ChevronDown size={12} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute left-0 bottom-full mb-2 w-64 p-1.5 rounded-xl bg-[var(--surface)] border border-[var(--border)] shadow-xl z-50 transform origin-bottom-left animate-in fade-in slide-in-from-bottom-2 duration-200">
                    <div className="p-2 pb-1.5 mb-1.5 text-xs font-semibold text-[var(--text-secondary)] border-b border-[var(--border)]">
                        Response Versions
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                        {branches.map((branch, index) => {
                            const isActive = branch.id === activeBranchId;
                            // Extract a plain text preview (remove markdown links, bold, etc)
                            const plainText = branch.content.replace(/[#_*~`]/g, '').trim();
                            const preview = plainText.substring(0, 45) + (plainText.length > 45 ? '...' : '');

                            return (
                                <div
                                    key={branch.id}
                                    className={`group flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${isActive
                                            ? 'bg-orange-500/10 border border-orange-500/20'
                                            : 'hover:bg-[var(--surface-highlight)] border border-transparent'
                                        }`}
                                    onClick={() => {
                                        if (!isActive) {
                                            onSwitchBranch(branch.id);
                                            setIsOpen(false);
                                        }
                                    }}
                                >
                                    <div className={`mt-0.5 flex-shrink-0 w-4 flex justify-center ${isActive ? 'text-orange-500' : 'text-transparent'}`}>
                                        {isActive ? <Check size={14} strokeWidth={3} /> : <div className="w-1.5 h-1.5 rounded-full bg-[var(--text-secondary)] opacity-30 group-hover:opacity-100" />}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-center mb-0.5">
                                            <span className={`text-xs font-semibold ${isActive ? 'text-orange-500' : 'text-[var(--text-primary)]'}`}>
                                                Branch {branch.branch_label}
                                            </span>
                                            <span className="text-[10px] text-[var(--text-secondary)]">
                                                {formatTime(branch.created_at)}
                                            </span>
                                        </div>
                                        <p className="text-[10px] text-[var(--text-secondary)] line-clamp-2 leading-tight">
                                            {preview}
                                        </p>
                                    </div>

                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (confirm('Delete this response version?')) {
                                                onDeleteBranch(branch.id);
                                                if (isActive && branches.length === 1) {
                                                    setIsOpen(false);
                                                }
                                            }
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1.5 text-[var(--text-secondary)] hover:text-red-500 hover:bg-red-500/10 rounded-md transition-all self-center ml-1"
                                        title="Delete branch"
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
