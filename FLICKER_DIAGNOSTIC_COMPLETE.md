# Chat UX & Streaming — Exhaustive Top-to-Bottom Diagnostic

## Executive Summary

After a top-to-bottom audit of the codebase, I have identified **12 distinct root causes** that interact to degrade the chat experience. These span the frontend React lifecycle, architectural bottlenecks, and backend async streaming logic.

---

## I. The Message Flicker (Problems 1-6)

### 1. Key Instability (PRIMARY CAUSE)
> `useChatStreaming.ts:96` / `page.tsx:198`
The user message is assigned a temporary `Date.now()` ID, used as the React `key`. ~140ms later, `onMeta` replaces it with a DB UUID. React treats this as a different element → **fully unmounts/remounts the message component**.

### 2. Entrance Animation Replay
> `ChatMessage.tsx:52`
Because the component remounts (Problem 1), the `motion.div` entrance animation (400ms fade-in) replays mid-stream. This creates the "flash."

### 3. AnimatePresence Conflict
> `page.tsx:196`
`AnimatePresence` tracks children by key. The key change triggers simultaneous exit/enter animations, doubling the visual noise.

### 4. Excessive State Updates
> `useChatStreaming.ts:314-338`
In the first 200ms of a send, `setMessages` fires 4+ times to update IDs and add assistant placeholders. These are not always batched by React 18 during SSE parsing.

### 5. Layout Thrashing (Scroll)
> `page.tsx:101-104`
`scrollIntoView` triggers a synchronous layout reflow on **every** token chunk. This causes micro-stuttering ("jumping").

### 6. Synchronous Cache Overhead
> `useChatState.ts:71`
The local storage cache is overwritten on every single token, adding CPU overhead in the critical render loop.

---

## II. Architectural Performance Bottlenecks (Problems 9-12)

### 9. Global Layout Re-rendering
> `chat/layout.tsx:53`
`ChatProvider` wraps the entire layout. Every streaming token re-render ripples through the entire `ChatLayoutInner`, impacting everything from the sidebar to the input field.

### 10. Un-memoized Sidebar
> `ChatSidebar.tsx` (765 lines)
This complex component re-renders completely for every token. For users with many conversations, this is a massive performance hit.

### 11. Un-memoized Input
> `ChatInput.tsx` (738 lines)
Another heavy sibling component that re-renders on every token unnecessarily.

### 12. CSS Scroll Conflict
> `globals.css:104`
`html { scroll-behavior: smooth; }` can conflict with JS-driven scrolling, causing the container to "fight" between smooth and instant updates.

---

## III. Deep Research & State Leaks (Problems 7-8)

### 7. Backend Generator Cancellation (Empty Reports)
> `backend/.../ai.py:1181`
The VPS is still running `asyncio.wait_for(...)`. When research takes >10s, it times out and **kills the generator**. The subsequent loop fails, triggering the empty report fallback.

### 8. IsLoading State Leak
> `ChatLayoutInner:20` / `useChatState.ts:77`
`clearMessages()` (called on "New Chat") resets the messages array but NEVER resets `isLoading` to false. The UI sees `isLoading=true` + `messages=0` → **renders the "Thinking..." logo in the blank new chat**.

---

## Recommendations

1.  **P0**: Solve **Key Instability**. Use a stable `key` from the start.
2.  **P0**: Deploy the **Generator Heartbeat Fix** to the VPS to restore research reports.
3.  **P1**: **Memoize** `ChatSidebar` and `ChatInput`.
4.  **P1**: **Reset `isLoading`** in `clearMessages`.
5.  **P2**: **Throttle** scrolling and cache sync.
