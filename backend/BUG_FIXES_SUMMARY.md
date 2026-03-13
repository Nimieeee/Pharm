# Bug Fixes Summary - Document Upload Issues

## Overview
Fixed three critical bugs preventing proper document upload and analysis functionality.

## Bug #1: Supabase RPC Parameter Name Mismatch (CRITICAL) ✅

### Problem
The code in `enhanced_rag.py` was calling the Supabase function `match_documents_with_user_isolation` with incorrect parameter names:
- Used: `conversation_uuid` and `user_session_uuid`
- Expected: `query_conversation_id` and `query_user_id`

This caused ALL semantic similarity searches to fail with 404 errors.

### Impact
- Semantic search completely broken
- System fell back to recency-based retrieval (degraded mode)
- Even when chunks existed (PPTX case), they weren't retrieved by similarity

### Fix
**File**: `backend/app/services/enhanced_rag.py` (lines ~567-577)

Changed:
```python
result = self.db.rpc(
    'match_documents_with_user_isolation',
    {
        'query_embedding': query_embedding,
        'conversation_uuid': str(conversation_id),      # ❌ WRONG
        'user_session_uuid': str(user_id),              # ❌ WRONG
        'match_threshold': similarity_threshold,
        'match_count': max_results
    }
).execute()
```

To:
```python
result = self.db.rpc(
    'match_documents_with_user_isolation',
    {
        'query_embedding': query_embedding,
        'query_conversation_id': str(conversation_id),  # ✅ CORRECT
        'query_user_id': str(user_id),                  # ✅ CORRECT
        'match_threshold': similarity_threshold,
        'match_count': max_results
    }
).execute()
```

---

## Bug #2: PDF Extraction Returns 0 Chunks (CRITICAL) ✅

### Problem
The `process_pdf_hybrid()` function in `vision_service.py` was silently returning empty strings when:
- PDF had no extractable text (scanned/image-based)
- VLM (Vision Language Model) failed to analyze images
- All pages were filtered out as templates

**ADDITIONAL BUG FOUND**: IndexError when filtering template images because full-page scans had 3-element tuples `(page_idx, img_bytes, label)` while embedded images had 4-element tuples `(page_idx, img_bytes, label, xref)`. The filtering code assumed all tuples had 4 elements.

This resulted in 0 chunks being stored, making the document invisible to the AI.

### Impact
- Image-based PDFs uploaded "successfully" (200 OK) but produced 0 chunks
- PDF processing crashed with `IndexError: tuple index out of range`
- No error message shown to user
- AI had no context to work with

### Fix
**File**: `backend/app/services/vision_service.py`

**Fix 1**: Added comprehensive error handling (lines ~145-165):
```python
# Log warning if no content extracted
if not full_text.strip():
    logger.error(f"❌ [Hybrid PDF] {filename}: No content extracted! "
                f"Text pages: {len(pages_content)}, Images analyzed: {len(images_to_analyze)}, "
                f"Image descriptions: {len(image_descriptions)}")
    # Return a placeholder to avoid 0 chunks
    return f"[PDF Processing Error: Could not extract content from {filename}. " \
           f"This may be a scanned/image-based PDF that requires OCR. " \
           f"Pages: {total_pages}, Text pages: {len(pages_content)}, Images: {len(images_to_analyze)}]"
```

**Fix 2**: Fixed IndexError by ensuring all tuples have 4 elements (line ~122):
```python
# Use None for xref since this is a full-page render, not an embedded image
images_to_analyze.append((page_idx, img_bytes, f"Page {page_idx+1} (full page scan)", None))
```

**Fix 3**: Updated filtering logic to handle None xref (line ~134):
```python
images_to_analyze = [
    img for img in images_to_analyze
    # Keep if: no xref (full page scan) OR xref appears on <50% of pages
    if img[3] is None or xref_page_count.get(img[3], 1) < total_pages * 0.5
]
```

Also added:
- Logging of VLM results: `logger.info(f"📊 [Hybrid PDF] VLM returned {len(image_descriptions)} image descriptions")`
- Character count in final log: `extracted {len(full_text)} chars`

### Next Steps for Complete Fix
The placeholder prevents 0 chunks, but doesn't solve the root cause. Consider:
1. Investigate why VLM is failing silently (check API key, rate limits, error responses)
2. Add OCR fallback for scanned PDFs (e.g., Tesseract)
3. Improve image filtering logic (may be too aggressive)

---

## Bug #3: Generic Greeting Despite Document Context (MODERATE) ✅

### Problem
Even when document context was successfully retrieved (10,804 chars in PPTX case), the AI still started responses with:
> "Hello Toluwanimi! I'm Benchside, your pharmacology assistant..."

This happened because:
- System prompt's greeting pattern competed with document analysis instructions
- AI interpreted greeting as separate from "asking for clarification"
- Model followed its training habit first, then appended document analysis

### Impact
- Poor user experience (unnecessary greeting delays actual content)
- Makes AI seem unaware of uploaded documents
- Wastes tokens and response time

### Fix
**File**: `backend/app/services/ai.py` (lines ~583-606)

Added explicit GREETING PROTOCOL section to system prompt:
```python
GREETING PROTOCOL:
- When <document_context> is present, DO NOT start with a greeting. Jump directly into analyzing the document.
- Only use greetings when starting a new conversation WITHOUT document context.
- If document context exists, the user wants document analysis, not pleasantries.
```

This instructs the model to:
1. Check for `<document_context>` tags
2. Skip greeting if document context exists
3. Jump directly to document analysis

---

## Testing

Created `backend/test_bug_fixes.py` to verify all fixes:

```bash
cd backend
python3 test_bug_fixes.py
```

**Results**: ✅ All 3 tests passed

---

## Deployment Checklist

- [x] Fix #1: Update RPC parameter names in `enhanced_rag.py`
- [x] Fix #2: Add error handling in `vision_service.py`
- [x] Fix #3: Update system prompt in `ai.py`
- [x] Create verification tests
- [ ] Deploy to VPS
- [ ] Test with actual PDF upload (CNS STIMULANTS_PHA 425.pdf)
- [ ] Verify semantic search works (check logs for successful RPC calls)
- [ ] Verify AI skips greeting when document context present
- [ ] Monitor logs for "No content extracted" errors

---

## Monitoring

After deployment, watch for these log patterns:

### Success Indicators
```
✅ Generated query embedding: 1024 dimensions
✅ Found N similar chunks (threshold: 0.3, max_sim: 0.XXX, avg_sim: 0.XXX)
📊 [Hybrid PDF] VLM returned N image descriptions
⏱️ [Hybrid PDF] Total: X.Xs, extracted NNNN chars
```

### Failure Indicators
```
❌ Database search error: Could not find the function...  # Should be GONE
❌ [Hybrid PDF] filename: No content extracted!           # Indicates OCR needed
⚠️ RAG Context EMPTY                                      # Should be rare now
```

---

## Root Cause Analysis

### Why These Bugs Existed

1. **RPC Parameter Mismatch**: Database schema changed but code wasn't updated. Suggests:
   - Missing integration tests for database functions
   - No type checking for RPC parameters
   - Schema changes not communicated to backend team

2. **Silent PDF Failures**: Error handling was too permissive. Suggests:
   - Insufficient logging at critical points
   - No validation of extraction results
   - Missing alerts for 0-chunk uploads

3. **Greeting Issue**: System prompt wasn't explicit enough. Suggests:
   - Prompt engineering needs more testing with document context
   - Model behavior not validated against requirements
   - Missing A/B testing for prompt changes

### Prevention Strategies

1. Add integration tests for RAG pipeline
2. Add validation: reject uploads that produce 0 chunks
3. Add monitoring: alert when chunk count is 0
4. Add type hints for Supabase RPC calls
5. Test system prompts with real user scenarios
