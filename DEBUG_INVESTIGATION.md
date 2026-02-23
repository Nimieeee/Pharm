# Systematic Debug Investigation: UI Not Updating During Document Upload Streaming

## ROOT CAUSE IDENTIFIED ✅

**The Bug**: `currentConvIdRef.current` was NOT being set for existing conversations, only for new ones.

**Why it only happened with documents**:
1. First message (without document) creates NEW conversation → `currentConvIdRef.current` IS set
2. Second message (with document) uses EXISTING conversation → `currentConvIdRef.current` NOT set (remains from previous)
3. But when you upload document and send immediately, conversation already exists from upload
4. So `currentConvIdRef.current` is `null`
5. `isCurrentConv()` returns `false`
6. ALL `updateMessage` calls are skipped
7. Content never appears in UI

**The Code**:
```typescript
if (!streamConversationId) {
    // Create new conversation
    currentConvIdRef.current = convData.id;  // ← Set here
} else {
    moveConversationToTop(streamConversationId);  // ← BUG: NOT set here!
}
```

**The Fix**:
```typescript
} else {
    currentConvIdRef.current = streamConversationId;  // ← FIXED!
    moveConversationToTop(streamConversationId);
}
```

## Evidence from Logs

```
⚠️ Not current conversation when adding assistant message
⚠️ [1] Not current conversation (current: null, target: a258bc11-0bf7-4ff3-8eda-db4b67c28c1c), skipping update
```

Every single update was skipped because `currentConvIdRef.current === null`.

## Why Systematic Debugging Worked

1. Added comprehensive logging at every boundary
2. Logs revealed `convMatch: false` on every update
3. Traced back to `isCurrentConv()` check
4. Found `currentConvIdRef.current` was `null`
5. Searched codebase for where it's set
6. Found it's only set for NEW conversations, not existing ones
7. Fixed by setting it for existing conversations too

## File Changed
- `frontend/src/hooks/useChatStreaming.ts` - Line 147
