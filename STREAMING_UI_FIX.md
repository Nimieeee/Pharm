# Streaming UI Update Fix - React State Race Condition

## Problem
The AI streaming was working correctly (backend sent all chunks, frontend received them), but the UI wasn't updating until the page was refreshed. The console logs showed:
- ✅ Stream complete! Total chunks: 810
- ✅ 6064 chars received
- ✅ [DONE] signal received
- ✅ onDone handler called

But the message content remained empty in the UI.

## Root Cause
React state race condition between ID updates and content updates:

1. Frontend creates assistant message with temp ID (e.g., `"1771801095701"`)
2. Message is added to React state
3. Backend sends meta with real ID (e.g., `"5a850984-b902-4a56-acb0-d130f049b498"`)
4. Code updates `assistantMessage.id` to real ID
5. Code updates message in state by mapping old ID → new ID
6. Content chunks arrive and call `updateMessage()`
7. `updateMessage` tries to find message by ID in state
8. **PROBLEM**: Due to React's async state batching, the ID update might not be in the state yet
9. Message not found → state update fails → UI doesn't re-render

## Solution
Changed from ID-based lookups to position-based tracking:

### Before (ID-based)
```typescript
const updateMessage = (fullContent: string) => {
    setMessages((prev) => {
        const targetId = assistantMessage.id; // Could be old or new ID
        const exists = prev.some(m => m.id === targetId);
        if (exists) {
            return prev.map(m => m.id === targetId ? { ...m, content: fullContent } : m);
        }
        // Fallback logic that often failed
    });
};
```

### After (Position-based)
```typescript
let messagePosition = -1; // Track position in array

const updateMessage = (fullContent: string) => {
    setMessages((prev) => {
        // Use cached position for direct access
        if (messagePosition >= 0 && messagePosition < prev.length) {
            const msg = prev[messagePosition];
            if (msg.role === 'assistant') {
                const updated = [...prev];
                updated[messagePosition] = { ...msg, content: fullContent };
                return updated;
            }
        }
        // Fallback to ID-based lookup if needed
    });
};

// Cache position when adding message
setMessages((prev) => {
    const newMessages = [...prev, assistantMessage];
    messagePosition = newMessages.length - 1; // Cache the position
    return newMessages;
});
```

## Benefits
1. **Eliminates race condition**: Position doesn't change when ID updates
2. **Faster lookups**: Direct array access instead of searching by ID
3. **More reliable**: Works even if ID updates are delayed by React batching
4. **Maintains fallbacks**: Still has ID-based lookup as backup

## Testing
After deploying this fix:
1. Upload a document in Fast mode
2. Type a prompt and send
3. AI response should stream in real-time
4. No page refresh needed to see the content

## Files Changed
- `frontend/src/hooks/useChatStreaming.ts` - Updated `updateMessage` logic to use position-based tracking

## Deployment
```bash
cd frontend
git add -A
git commit -m "Fix: Use position-based message updates to avoid React state race conditions"
git push origin master
```

The fix is now live on Vercel (auto-deploys from GitHub).
