import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '@/components/chat/ChatMessage';

export type Mode = 'fast' | 'detailed' | 'deep_research';

export interface AssistantResponse {
    id: string;
    user_message_id: string;
    branch_label: string;
    content: string;
    model_used?: string;
    token_count?: number;
    metadata?: Record<string, any>;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

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

// Cache write throttle constants
const CACHE_WRITE_DELAY = 1000; // Increased from 500ms to 1000ms to reduce overhead during streaming

export function cacheSet(key: string, value: Message[]) {
    conversationMessages.delete(key);
    conversationMessages.set(key, value);
    while (conversationMessages.size > MAX_CACHED_CONVERSATIONS) {
        const oldest = conversationMessages.keys().next().value;
        if (oldest) conversationMessages.delete(oldest);
    }
}

export function cacheSetThrottled(key: string, value: Message[]) {
    // Immediate update to the Map
    conversationMessages.delete(key);
    conversationMessages.set(key, value);
    while (conversationMessages.size > MAX_CACHED_CONVERSATIONS) {
        const oldest = conversationMessages.keys().next().value;
        if (oldest) conversationMessages.delete(oldest);
    }
    // Throttled persistence is handled in useChatState via debounced effect
}

export function cacheGet(key: string): Message[] | undefined {
    return conversationMessages.get(key);
}

export function clearMessageCache() {
    conversationMessages.clear();
}

// Generate stable client-side ID that won't change on server response
let clientIdCounter = 0;
export function generateStableClientId(): string {
    const timestamp = Date.now();
    const counter = clientIdCounter++;
    return `client_${timestamp}_${counter}`;
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

    // NEW Independent Branching State
    // Original messages array now only contains user messages (and optimistic assistant messages temporarily)
    const [branchData, setBranchData] = useState<Map<string, AssistantResponse[]>>(new Map());
    const [activeBranches, setActiveBranches] = useState<Map<string, string>>(new Map());

    // Refs for stable callbacks and async tracking
    const currentConvIdRef = useRef<string | null>(null);
    const uploadAbortRef = useRef<AbortController | null>(null);
    const lastUpdateRef = useRef<number>(0);
    const isSendingRef = useRef<Set<string>>(new Set<string>());
    const modeRef = useRef<Mode>('detailed');

    // ID mapping: client ID -> server ID (for stable React keys)
    const idMappingRef = useRef<Map<string, string>>(new Map());

    // Debounced cache sync - prevents excessive writes during streaming
    const lastCacheSyncRef = useRef<number>(0);
    const cacheTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        if (conversationId && messages.length > 0) {
            // Clear any pending timeout
            if (cacheTimeoutRef.current) {
                clearTimeout(cacheTimeoutRef.current);
            }

            // Only sync to cache after 1 second of no updates
            cacheTimeoutRef.current = setTimeout(() => {
                cacheSet(conversationId, messages);
                lastCacheSyncRef.current = Date.now();
            }, CACHE_WRITE_DELAY);
        }

        return () => {
            if (cacheTimeoutRef.current) {
                clearTimeout(cacheTimeoutRef.current);
            }
        };
    }, [messages, conversationId]);

    // Final sync on unmount
    useEffect(() => {
        return () => {
            if (conversationId && messages.length > 0) {
                cacheSet(conversationId, messages);
            }
        };
    }, []);

    const clearMessages = useCallback(() => {
        setMessages([]);
        setBranchData(new Map());
        setActiveBranches(new Map());
        setConversationId(null);
        currentConvIdRef.current = null;
        setDeepResearchProgress(null);
        setIsLoading(false);  // FIX: Reset isLoading state
        idMappingRef.current.clear();  // Clear ID mappings
        if (typeof window !== 'undefined') {
            localStorage.removeItem('streamConversationId');
            localStorage.removeItem('currentConversationId');
        }
    }, []);

    // Map client ID to server ID (stable key)
    const mapMessageId = useCallback((clientId: string, serverId: string) => {
        idMappingRef.current.set(clientId, serverId);
    }, []);

    // Get stable key for React (prefers server ID if available, falls back to client ID)
    const getStableKey = useCallback((id: string): string => {
        return idMappingRef.current.get(id) || id;
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

        // Branch State
        branchData,
        setBranchData,
        activeBranches,
        setActiveBranches,

        // Refs
        currentConvIdRef,
        uploadAbortRef,
        lastUpdateRef,
        isSendingRef,
        modeRef,

        // ID Mapping for stable keys
        mapMessageId,
        getStableKey,

        // Utilities
        clearMessages
    };
}
