import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '@/components/chat/ChatMessage';

export type Mode = 'fast' | 'detailed' | 'deep_research';

export interface DeepResearchProgress {
    type: string;
    status?: string;
    message?: string;
    progress?: number;
    plan_overview?: string;
    steps?: Array<{ id: number; topic: string; source: string }>;
    count?: number;
    report?: string;
    citations?: Array<{
        id: number;
        title: string;
        url: string;
        source: string;
        source_type?: string;
        authors?: string;
        year?: string;
        journal?: string;
        doi?: string;
        snippet?: string;
    }>;
}

// Global LRU cache store
const MAX_CACHED_CONVERSATIONS = 20;
const conversationMessages = new Map<string, Message[]>();

export function cacheSet(key: string, value: Message[]) {
    conversationMessages.delete(key);
    conversationMessages.set(key, value);
    while (conversationMessages.size > MAX_CACHED_CONVERSATIONS) {
        const oldest = conversationMessages.keys().next().value;
        if (oldest) conversationMessages.delete(oldest);
    }
}

export function cacheGet(key: string): Message[] | undefined {
    return conversationMessages.get(key);
}

export function clearMessageCache() {
    conversationMessages.clear();
}

export function useChatState() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingConversation, setIsLoadingConversation] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [deepResearchProgress, setDeepResearchProgress] = useState<DeepResearchProgress | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<Array<{ name: string; size: string; type: string }>>([]);

    // Branch navigation maps
    const [branchMap, setBranchMap] = useState<Record<string, { branchIndex: number; branchCount: number; siblingIds: string[] }>>({});

    // Refs for stable callbacks and async tracking
    const currentConvIdRef = useRef<string | null>(null);
    const uploadAbortRef = useRef<AbortController | null>(null);
    const lastUpdateRef = useRef<number>(0);
    const isSendingRef = useRef(false);
    const modeRef = useRef<Mode>('detailed');

    // Cache syncer
    useEffect(() => {
        if (conversationId && messages.length > 0) {
            cacheSet(conversationId, messages);
        }
    }, [messages, conversationId]);

    const clearMessages = useCallback(() => {
        setMessages([]);
        setConversationId(null);
        currentConvIdRef.current = null;
        setDeepResearchProgress(null);
        if (typeof window !== 'undefined') {
            localStorage.removeItem('streamConversationId');
            localStorage.removeItem('currentConversationId');
        }
    }, []);

    return {
        // State
        messages,
        setMessages,
        isLoading,
        setIsLoading,
        isLoadingConversation,
        setIsLoadingConversation,
        isUploading,
        setIsUploading,
        conversationId,
        setConversationId,
        deepResearchProgress,
        setDeepResearchProgress,
        isDeleting,
        setIsDeleting,
        uploadedFiles,
        setUploadedFiles,
        branchMap,
        setBranchMap,

        // Refs
        currentConvIdRef,
        uploadAbortRef,
        lastUpdateRef,
        isSendingRef,
        modeRef,

        // Utilities
        clearMessages
    };
}
