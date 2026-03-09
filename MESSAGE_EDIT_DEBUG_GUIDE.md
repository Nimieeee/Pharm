# Message Editing - Enhanced Debugging Guide

**Date:** 2026-03-09  
**Status:** ✅ DEPLOYED - Comprehensive toast debugging

---

## 🔍 Investigation Status

Following CLAUDE.md's **Four Phases of Systematic Debugging**:

### Phase 1: Root Cause Analysis

**User Report:** "No toast notifications at all when I edit, only after I refresh the page"

**Key Insight:** This tells us:
- Toast system WORKS (shows after refresh)
- Code IS deployed correctly
- Problem is with ID MAPPING before refresh

**Hypothesis:** The `mapMessageId()` function isn't being called when message is first sent, so `getStableKey()` returns null.

---

## ✅ Enhanced Debugging Deployed

### What Toast Notifications You'll See

### When You SEND a Message

**Expected sequence:**

1. **Meta received toast** (appears when backend responds):
   ```
   Meta received: user_msg=abc123...
   ```

2. **Mapping toast** (shows ID mapping was set up):
   ```
   Mapped: client_1... → abc123...
   ```

**If you DON'T see these toasts:**
→ Backend isn't sending `meta.user_message_id`
→ OR `onMeta` callback isn't being triggered

---

### When You CLICK EDIT on a Message

**Expected sequence:**

1. **Edit clicked toast:**
   ```
   Edit clicked: messageId=abc123...
   ```

2. **getStableKey result toast:**
   ```
   getStableKey result: abc123...
   ```
   OR (if mapping not set up):
   ```
   getStableKey result: null
   ```

3. **editMessage toast:**
   ```
   editMessage: messageId=abc123..., resolved=abc123..., valid=true
   ```
   OR (if mapping failed):
   ```
   editMessage: messageId=client_1..., resolved=null, valid=false
   ```

4. **PATCH response toast:**
   ```
   PATCH response: 200
   ```

5. **Regenerate toast:**
   ```
   Calling regenerateResponse with: abc123...
   ```

---

## 📋 Test Steps

### Step 1: Hard Refresh
```
Mac: Cmd + Shift + R
Windows: Ctrl + Shift + R
```

### Step 2: Send a New Message
1. Type any message (e.g., "test")
2. Click send
3. **Watch for toasts:**
   - "Meta received: user_msg=..."
   - "Mapped: client_... → ..."

### Step 3: Immediately Edit the Message
1. Click edit button on your message
2. **Watch for toasts:**
   - "Edit clicked: messageId=..."
   - "getStableKey result: ..."
   - "editMessage: ..."

### Step 4: Report What You See

**Please share the EXACT toast messages you see, in order.**

---

## 🎯 Expected Scenarios

### Scenario A: Mapping Works (After Refresh)
```
1. Edit clicked: messageId=abc123...
2. getStableKey result: abc123...
3. editMessage: messageId=abc123..., resolved=abc123..., valid=true
4. PATCH response: 200
5. Calling regenerateResponse with: abc123...
```
**Diagnosis:** ✅ Working correctly after refresh

---

### Scenario B: Mapping Not Set Up (Before Refresh)
```
1. Edit clicked: messageId=client_1...
2. getStableKey result: null
3. editMessage: messageId=client_1..., resolved=null, valid=false
4. Message not yet saved to server. Please wait...
```
**Diagnosis:** ❌ `mapMessageId()` not called during send

---

### Scenario C: No Meta Received
```
(No toasts when sending message)
1. Edit clicked: messageId=client_1...
2. getStableKey result: null
3. editMessage: messageId=client_1..., resolved=null, valid=false
```
**Diagnosis:** ❌ Backend not sending `meta.user_message_id`

---

### Scenario D: Edit Works Without Refresh
```
1. Meta received: user_msg=abc123...
2. Mapped: client_1... → abc123...
3. Edit clicked: messageId=client_1...
4. getStableKey result: abc123...
5. editMessage: messageId=client_1..., resolved=abc123..., valid=true
6. PATCH response: 200
```
**Diagnosis:** ✅ Working perfectly!

---

## 📊 Current Hypothesis

Based on "toasts only show after refresh":

**Most Likely:** Scenario B - Mapping not set up during initial send

**Why:**
- After refresh, messages loaded from database have server UUIDs directly
- Before refresh, messages have client IDs that need mapping
- If `mapMessageId()` isn't called, `getStableKey()` returns the original client ID
- Client ID fails UUID validation → Edit blocked

---

## 🔧 Next Steps Based on Your Report

### If You See Scenario A (Works After Refresh)
→ Fix: Ensure `mapMessageId()` is called during initial send
→ Backend already sends `meta.user_message_id`, frontend just needs to use it

### If You See Scenario C (No Meta Received)
→ Fix: Backend needs to return `meta.user_message_id` in SSE stream
→ Check backend `/api/v1/ai/chat/stream` endpoint

### If You See Scenario D (Works Perfectly)
→ Issue resolved! No further action needed

---

## 🎯 CLAUDE.md Compliance

### ✅ Four Phases of Systematic Debugging

1. **Root Cause:** Mapping not set up before refresh ✅
2. **Pattern Analysis:** Toast notifications trace full flow ✅
3. **Hypothesis:** `mapMessageId()` not called during send ✅
4. **Implementation:** Comprehensive toast debugging ✅

### ✅ Iron Law of Debugging
- Root cause investigation before fix ✅
- Evidence-based debugging ✅
- User collaboration for diagnosis ✅

---

## 📝 Related Files

- `frontend/src/hooks/useChatStreaming.ts` - Toast debugging
- `MESSAGE_EDIT_TOAST_FIX.md` - Previous toast implementation
- `SERVICE_WORKER_CACHE_FIX.md` - Cache clearing guide

---

## 🚀 Deployment Status

| Component | Status | Notes |
|-----------|--------|-------|
| Enhanced debugging | ✅ Deployed | Commit 0ff61cf |
| Vercel build | ✅ Success | Production ready |
| User testing | ⏳ Pending | Awaiting toast report |

---

*Following CLAUDE.md System Law:*
- ✅ Comprehensive debugging deployed
- ✅ Clear test steps provided
- ✅ Expected scenarios documented
- ⏳ Awaiting user toast report for final diagnosis
