# Fix Plan: Message Editing & Document Loader Issues

Following CLAUDE.md systematic debugging principles

---

## Issue 1: Message Editing Not Registering

### Root Cause (Following Iron Law of Debugging)

**Symptom**: Edit doesn't register immediately; AI responds to original query after refresh

**Root Cause Found**: Race condition in `useChatStreaming.ts`:

1. `editMessage()` updates local state with new content
2. `editMessage()` calls `regenerateResponse(messageId)` 
3. `regenerateResponse()` finds `userMessage` from `messages` array **BEFORE** edit is applied
4. Stream request sends `userMessage.content` (OLD content) to backend
5. Backend generates response based on old content

**Data Flow**:
```
User clicks Edit → editMessage() → PATCH /messages/{id} (backend updated)
                              ↓
                    setMessages() (local state updated)
                              ↓
                    regenerateResponse(messageId)
                              ↓
                    messages.find(m => m.id === messageId)  ← OLD messages array!
                              ↓
                    POST /chat/stream with userMessage.content  ← OLD content!
```

### Fix Strategy (Following Anti-Regression Guide)

**PATTERN: Pass edited content explicitly to regenerateResponse**

```typescript
// BEFORE (WRONG):
const regenerateResponse = useCallback(async (userMessageId: string) => {
    const userMessage = messages.find((m: Message) => m.id === userMessageId);
    // ... uses userMessage.content (may be stale)
}, [conversationId, messages, ...]);

const editMessage = useCallback(async (messageId: string, newContent: string) => {
    // ... update backend ...
    setMessages(...)  // Local state update
    await regenerateResponse(messageId);  // ← Race condition!
}, [regenerateResponse]);

// AFTER (CORRECT):
const regenerateResponse = useCallback(async (userMessageId: string, overrideContent?: string) => {
    const userMessage = messages.find((m: Message) => m.id === userMessageId);
    const contentToSend = overrideContent || userMessage?.content;  // Use override if provided
    // ... use contentToSend instead
}, [conversationId, messages, ...]);

const editMessage = useCallback(async (messageId: string, newContent: string) => {
    // ... update backend ...
    setMessages(...)
    await regenerateResponse(messageId, newContent);  // ← Pass edited content explicitly!
}, [regenerateResponse]);
```

### Implementation Steps

1. **Modify `regenerateResponse` signature** to accept optional `overrideContent` parameter
2. **Use `overrideContent` in stream request** instead of `userMessage.content`
3. **Update `editMessage` call** to pass `newContent` as second argument
4. **Add regression test** for message editing flow

### Regression Test Plan

```typescript
// frontend/src/hooks/__tests__/useChatStreaming.test.ts
describe('editMessage', () => {
  it('sends edited content to regenerateResponse', async () => {
    // Setup
    const originalMessage = { id: 'msg-1', content: 'Original question' };
    const editedContent = 'Edited question';
    
    // Act
    await editMessage('msg-1', editedContent);
    
    // Assert
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/stream'),
      expect.objectContaining({
        body: expect.stringContaining(editedContent)  // Verify edited content sent
      })
    );
  });
});
```

---

## Issue 2: Document Loader Testing

### Root Cause Found

**PyMuPDF missing from VPS** - PDF text extraction was failing silently because `fitz` module wasn't installed.

**Status**: ✅ Fixed - PyMuPDF installed and added to requirements.txt

### Remaining Work: Test All Document Types

Following CLAUDE.md TDD principle: **Write tests FIRST**

**Test File**: `backend/tests/regression/test_document_loaders.py`

```python
def test_pdf_loader():
    """Test PDF document loading"""
    with open('tests/fixtures/CNS_STIMULANTS.pdf', 'rb') as f:
        content = f.read()
    
    documents = await loader.load_document(content, 'test.pdf')
    
    assert len(documents) > 0
    assert len(documents[0].page_content) > 100  # Minimum content threshold

def test_docx_loader():
    """Test DOCX document loading"""
    # Similar pattern

def test_pptx_loader():
    """Test PPTX document loading"""
    # Similar pattern

def test_csv_loader():
    """Test CSV document loading"""
    # Similar pattern

def test_image_loader():
    """Test image document loading (requires VLM)"""
    # Similar pattern
```

### Test Execution

```bash
cd backend
pytest tests/regression/test_document_loaders.py -v
# Expected: All tests pass in <10s
```

---

## Implementation Checklist (Following CLAUDE.md)

### Before Coding:
- [x] Root cause identified for message editing issue
- [x] Root cause identified for PDF loading issue
- [ ] Regression tests written FIRST
- [ ] `./run_regression.sh` baseline established

### Implementation:
- [ ] Fix `regenerateResponse` to accept `overrideContent`
- [ ] Update `editMessage` to pass `newContent` explicitly
- [ ] Add regression test for message editing
- [ ] Add regression tests for all document loaders
- [ ] Run `./run_regression.sh` - must pass in <10s

### Pre-Commit:
- [ ] All regression tests pass
- [ ] No circular imports introduced
- [ ] Frontend builds successfully
- [ ] Git diff reviewed for debug code

### Pre-Deployment:
- [ ] Test on production-like data
- [ ] Deploy to VPS
- [ ] Run regression tests on VPS
- [ ] Smoke test: Edit message, verify AI responds to edited content

---

## Files to Modify

1. **`frontend/src/hooks/useChatStreaming.ts`**
   - `regenerateResponse()` - Add `overrideContent` parameter
   - `editMessage()` - Pass `newContent` to `regenerateResponse()`

2. **`frontend/src/hooks/__tests__/useChatStreaming.test.ts`** (NEW)
   - Add message editing regression test

3. **`backend/tests/regression/test_document_loaders.py`** (NEW)
   - Add document loader regression tests

4. **`backend/requirements.txt`**
   - ✅ Already added `pymupdf>=1.23.0`

---

*Generated following CLAUDE.md systematic debugging principles*
*Date: 2026-03-06*
