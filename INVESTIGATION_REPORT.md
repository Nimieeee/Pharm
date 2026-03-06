# Multi-Issue Investigation & Fix Report

**Date:** 2026-03-06  
**Following:** CLAUDE.md Systematic Debugging Principles

---

## 🔍 Issues Reported

1. **Message Edit Not Registering Immediately**
2. **RAG Not Using Uploaded Documents**
3. **Image Not Being Analyzed**
4. **422 Error on Stream Endpoint**

---

## 🧠 Hypothesis Generation (Opus 4.6 Style Analysis)

### Issue 1: Message Edit Not Registering

**Observed Behavior:**
- Edit doesn't show immediately after AI responds
- After refresh, edit works but appears on Branch A (should create new branch)

**Hypotheses Enumerated:**

1. **State Synchronization Issue**: `setMessages()` updates local state but UI reads from `branchData`
2. **Branch Data Conflict**: When switching branches, database values override local edits
3. **Regenerate Race Condition**: `regenerateResponse()` completes before UI state updates
4. **Branch Selection Logic**: Active branch selection doesn't account for edited messages

**Most Likely:** Hypothesis 1 & 2 - The UI has two sources of truth (messages array vs branchData map) that can be out of sync.

---

### Issue 2: RAG Not Using Uploaded Documents

**Evidence from Logs:**
```
User uploads to: conversation 965cc3ad-d049-4e6a-871e-c9a3cb3093f3
User chats in:   conversation 65111dee-4c1a-4f4d-be75-16add1e3de2a
RAG reports: "No documents found for this conversation"
```

**Hypotheses Enumerated:**

1. **Wrong Conversation**: User uploaded to different conversation than chatting in ✅ **CONFIRMED**
2. **Upload Failure**: Document upload succeeds but chunk creation fails
3. **Database Isolation**: Chunks exist but filtered out by wrong `user_id`
4. **Timing Issue**: RAG query runs before chunks are committed

**Most Likely:** Hypothesis 1 - This is a **USER FLOW ISSUE**, not a bug. Documents must be uploaded to the SAME conversation.

---

### Issue 3: Image Not Being Analyzed

**Observed Behavior:**
User uploads `spina_bifida.jpeg` but AI responds "I need a specific topic"

**Hypotheses Enumerated:**

1. **Frontend Metadata**: Images sent in `metadata.attachments` but backend doesn't process this field
2. **Vision Service Not Triggered**: No code path processes `metadata.attachments` ✅ **CONFIRMED**
3. **API Key Issue**: Vision API keys not configured (already verified as configured)
4. **Response Parsing**: VLM response not included in final output

**Most Likely:** Hypothesis 1 & 2 - **BACKEND MISSING FEATURE**. The backend receives image metadata but has no code to process it.

---

### Issue 4: 422 Error on Stream Endpoint

**Error Pattern:**
```
POST /api/v1/ai/chat/stream → 422 Unprocessable Entity
```

**Hypotheses Enumerated:**

1. **Invalid UUID**: `parent_id` contains empty string or malformed UUID ✅ **CONFIRMED**
2. **Missing Required Fields**: `message` or `conversation_id` undefined
3. **Metadata Serialization**: Non-serializable objects in `metadata`
4. **Pydantic Validation**: Strict UUID validation rejects invalid formats

**Root Cause Found:**
```typescript
// BEFORE (WRONG):
parent_id: messages.length > 0 ? messages[messages.length - 1].id : undefined

// If lastMessage.id is "" or null, this sends invalid value
parent_id: ""  // ← Pydantic rejects this → 422
```

---

## ✅ Fixes Implemented

### Fix 1: 422 Error - UUID Validation

**File:** `frontend/src/hooks/useChatStreaming.ts`

**Changes:**
```typescript
// Line 292-304: Main sendMessage flow
const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
// ...
parent_id: (lastMessage && lastMessage.id && typeof lastMessage.id === 'string' && lastMessage.id.length > 0) ? lastMessage.id : undefined,

// Line 453-456: regenerateResponse flow  
parent_id: (userMessage.parentId && typeof userMessage.parentId === 'string' && userMessage.parentId.length > 0) ? userMessage.parentId : undefined,
```

**Rationale:** Only include `parent_id` if it's a valid non-empty string UUID.

---

### Fix 2: Message Edit State (Partial)

**Status:** Previous fix already applied (overrideContent parameter)

**Remaining Issue:** UI shows edited message on wrong branch after refresh.

**Root Cause:** Database stores edited message content, but branch selection logic loads it for ALL branches referencing that `user_message_id`.

**Requires:** Backend schema change to store edits as separate message versions (out of scope for this fix).

---

### Fix 3: RAG Documents (User Education)

**Status:** Not a bug - user flow issue

**Solution:** User must upload documents to the SAME conversation they're chatting in.

**Recommended UI Improvement:** Show "Upload documents to THIS conversation" button in chat interface.

---

### Fix 4: Image Processing (Backend Feature Missing)

**Status:** Requires backend implementation

**Missing Code:** Backend needs to:
1. Extract images from `request.metadata.attachments`
2. Call vision service for each image
3. Include image descriptions in RAG context

**Estimated Effort:** 2-3 hours backend development

---

## 📊 Verification Results

### 422 Error Fix
- ✅ Frontend build successful
- ✅ UUID validation added to both sendMessage and regenerateResponse
- ✅ Deployed to Vercel

### RAG Document Issue
- ✅ Confirmed: Documents uploaded to different conversation
- ✅ Not a backend bug - user flow issue

### Image Processing
- ⚠️ Backend feature missing - requires implementation
- ⚠️ Vision API keys configured and working (verified in previous tests)

### Message Editing
- ⚠️ Partial fix applied (regenerateResponse uses overrideContent)
- ⚠️ Branch selection issue remains (database schema limitation)

---

## 🎯 Recommended Next Steps

### Immediate (High Priority)
1. **Test 422 fix** - Send messages in active conversations, verify no more 422 errors
2. **User education** - Add UI hint: "Documents must be uploaded to current conversation"

### Short Term (Medium Priority)
3. **Implement image processing** in backend:
   ```python
   # In AIService.generate_streaming_response:
   if request.metadata and request.metadata.get('attachments'):
       for attachment in request.metadata['attachments']:
           if attachment['type'] == 'image':
               # Process with vision service
   ```

### Long Term (Low Priority)
4. **Message versioning schema** - Store edits as separate versions, not mutations
5. **Branch-aware UI** - Show edited messages only in their specific branches

---

## 📝 Files Modified

### Frontend
- `frontend/src/hooks/useChatStreaming.ts` - Lines 292-304, 453-456

### Backend
- No changes (issues identified as user flow or missing features)

---

*Report generated following CLAUDE.md systematic debugging principles*
*Multiple hypotheses enumerated before implementing fixes*
*Root causes identified through log analysis and code inspection*
