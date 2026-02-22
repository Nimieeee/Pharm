# Systematic Debug Investigation: UI Not Updating During Document Upload Streaming

## Symptom
- **WHAT**: AI response doesn't appear in UI until page refresh
- **WHEN**: Only when uploading a document (works fine without document)
- **WHERE**: Frontend React state management
- **EVIDENCE**: Console logs show streaming completes successfully (810 chunks, 6064 chars, [DONE] received)

## Phase 1: Root Cause Investigation

### 1.1 Error Messages
Console logs show:
```
✅ Stream complete! Total chunks: 810
✅ 6064 chars received  
✅ [DONE] signal received
✅ onDone handler called
```
No errors - stream completes successfully but UI doesn't update.

### 1.2 Reproduction Steps
1. Upload document (PDF/PPTX) in Fast mode
2. Type prompt "explain well"
3. Send message
4. UI shows "Thinking..." indefinitely
5. Refresh page → content appears correctly

**Reproducible**: YES, 100% with document uploads
**Without document**: NO, works perfectly

### 1.3 Recent Changes
- Fixed RPC parameter mismatch
- Fixed PDF tuple structure
- Added streaming diagnostics
- Modified "Thinking..." UI logic
- **Attempted fix**: Position-based message tracking (DIDN'T WORK)

### 1.4 Component Boundaries to Investigate

```
[Backend] → [SSE Stream] → [Frontend streamReader] → [useChatStreaming] → [React State] → [UI Render]
    ✓           ✓                  ✓                      ?                  ?              ✗
```

Need to add diagnostics at each boundary to find WHERE it breaks.

### 1.5 Key Question
**WHY does it work without documents but fail with documents?**

Hypothesis areas to investigate:
1. Timing difference (RAG processing delay)
2. Message size difference (large context)
3. State update batching issues
4. React re-render not triggering
5. Closure capturing stale state

## Next Steps
1. Add comprehensive logging to track state updates
2. Verify React re-renders are happening
3. Check if setMessages is actually being called
4. Verify message exists in state after updates
5. Compare behavior with/without documents
