# Document Persistence and Context Usage Fix

## Issues Fixed

### 1. Documents Not Staying in Chat Bubble
**Problem**: After sending a message with attached documents, the document cards would disappear when the conversation was reloaded.

**Root Cause**: The frontend was only showing documents in temporary messages, but wasn't saving the document metadata to the backend when creating the user message.

**Solution**:
- Added `addMessage` API function to save user messages with metadata
- Modified `sendMessage` to save the user message with `attachedFiles` metadata before sending to AI
- Documents are now persisted in the database and will appear in chat history after reload

### 2. Documents Not Being Used in AI Context
**Problem**: The AI wasn't properly using uploaded documents to answer questions, even though documents were uploaded successfully.

**Root Cause**: 
- No visibility into whether RAG context was being retrieved
- No indication to the user that documents were being used

**Solution**:
- Added extensive logging to track RAG context retrieval
- Added fallback to retrieve all chunks if semantic search returns nothing
- Added visual indicator "📚 *Based on uploaded documents*" when AI uses document context
- Added context preview in logs for debugging

## Changes Made

### Frontend (`frontend/src/pages/ChatPage.tsx`)
```typescript
// Save user message with document metadata before sending to AI
if (attachedFiles.length > 0) {
  await chatAPI.addMessage(conversationId, {
    role: 'user',
    content: userMessage,
    metadata: { attachedFiles }
  })
}
```

### API (`frontend/src/lib/api.ts`)
```typescript
// New function to save messages with metadata
addMessage: (conversationId: string, data: { 
  role: string; 
  content: string; 
  metadata?: Record<string, any> 
}): Promise<Message> =>
  api.post(`/chat/conversations/${conversationId}/messages`, data).then(res => res.data)
```

### Backend (`backend/app/services/ai.py`)
- Added `context_used` flag to track when documents are retrieved
- Added context preview logging for debugging
- Added visual indicator in AI response when documents are used
- Improved fallback logic to use all chunks if semantic search fails

## Testing

### Test Document Persistence
1. Upload a document to a conversation
2. Send a message
3. Reload the page
4. Verify the document card appears with the message in chat history

### Test Document Context Usage
1. Upload a document with specific information
2. Ask a question about that information
3. Verify the AI response includes "📚 *Based on uploaded documents*"
4. Check backend logs for context retrieval confirmation

## Expected Behavior

### Document Cards
- ✅ Show in input area while uploading (with progress)
- ✅ Attach to user message when sent
- ✅ Persist in chat history after reload
- ✅ Display with message in conversation view

### AI Context
- ✅ Retrieve relevant document chunks using semantic search
- ✅ Fall back to all chunks if semantic search returns nothing
- ✅ Include document context in AI prompt
- ✅ Show visual indicator when documents are used
- ✅ Log context retrieval for debugging

## Debugging

If documents still aren't being used:

1. **Check backend logs** for:
   - "📚 Getting RAG context with semantic search..."
   - "✅ RAG context retrieved: X chars"
   - "📄 Context preview: ..."

2. **Verify document upload**:
   - Check for "✅ Successfully stored X chunks"
   - Verify chunks in `document_chunks` table

3. **Check semantic search**:
   - Verify embeddings are being generated
   - Check `match_documents_with_user_isolation_v2` function
   - Verify conversation_id and user_id match

4. **Check AI prompt**:
   - Look for "**Document Context:**" in logs
   - Verify context is being included in user message
