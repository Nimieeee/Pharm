# Document Upload Fixes

## Issues Fixed

### 1. Logging Conflict Error
**Problem**: `KeyError: "Attempt to overwrite 'filename' in LogRecord"`
- Python's logging module reserves 'filename' as a built-in field
- Using it in logging extra parameters caused crashes

**Solution**: 
- Renamed all `'filename'` to `'document_name'` in logging extra parameters
- Fixed in both `document_loaders.py` and `enhanced_rag.py`

### 2. Embedding Dimensions Mismatch
**Problem**: Code was hardcoded to use `MISTRAL_EMBED_DIMENSIONS` (1024) even when using other providers
- Sentence Transformers use 384 dimensions
- Cohere uses 1024 dimensions
- This caused validation failures

**Solution**:
- Changed to use `EMBEDDING_DIMENSIONS` which adapts based on provider
- Updated metadata to use `EMBEDDING_PROVIDER` instead of hardcoded "mistral-embed"

### 3. Single File Upload Only
**Problem**: Users could only upload one document at a time

**Solution**:
- Added new endpoint `/documents/upload-multiple` for batch uploads
- Supports uploading multiple files simultaneously
- Returns individual results for each file
- Provides summary with success/failure counts

## New Features

### Multiple File Upload Endpoint

**Endpoint**: `POST /api/v1/ai/documents/upload-multiple`

**Request**:
```
conversation_id: UUID (form data)
files: List[UploadFile] (multiple files)
```

**Response**:
```json
{
  "success": true,
  "message": "Processed 3 files: 2 successful, 1 failed",
  "total_files": 3,
  "successful_count": 2,
  "failed_count": 1,
  "total_chunks": 45,
  "results": [
    {
      "filename": "document1.pdf",
      "success": true,
      "message": "Successfully processed 20 chunks",
      "chunk_count": 20,
      "processing_time": 2.5,
      "file_info": {...}
    },
    {
      "filename": "document2.docx",
      "success": true,
      "message": "Successfully processed 25 chunks",
      "chunk_count": 25,
      "processing_time": 1.8
    },
    {
      "filename": "invalid.xyz",
      "success": false,
      "message": "Unsupported file format '.xyz'",
      "chunk_count": 0
    }
  ]
}
```

## Environment Variable Changes Needed

To switch from Cohere to HuggingFace embeddings (free, no rate limits):

### On Render Dashboard:
1. Go to your backend service
2. Environment Variables section
3. Change or add:
   - `EMBEDDING_PROVIDER=sentence-transformers` (or delete to use default)
   - `EMBEDDING_DIMENSIONS=384` (or delete to use default)
4. Optional: Remove `COHERE_API_KEY` if not needed
5. Save and redeploy

### Benefits of Sentence Transformers:
- ✅ Free (no API costs)
- ✅ No rate limits
- ✅ Runs locally on your server
- ✅ Fast and efficient
- ✅ Uses `all-MiniLM-L6-v2` model (384 dimensions)

## Testing

### Single File Upload:
```bash
curl -X POST "https://your-api.com/api/v1/ai/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "conversation_id=YOUR_CONVERSATION_ID" \
  -F "file=@document.pdf"
```

### Multiple File Upload:
```bash
curl -X POST "https://your-api.com/api/v1/ai/documents/upload-multiple" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "conversation_id=YOUR_CONVERSATION_ID" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx" \
  -F "files=@document3.txt"
```

## Supported File Formats

- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`, `.md`)
- PowerPoint (`.pptx`)
- Excel (`.xlsx`)
- CSV (`.csv`)
- Chemical Structure Files (`.sdf`, `.mol`)
- Images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.webp`)

## Error Handling

All errors now provide:
- Clear error messages
- Error categories (user_error vs system_error)
- Supported formats list
- Specific failure reasons
- File-by-file results for batch uploads

## Next Steps

1. **Update Environment Variables** on Render to use Sentence Transformers
2. **Wait for Deployment** (2-5 minutes)
3. **Test Document Upload** with the fixed endpoints
4. **Try Multiple File Upload** for batch processing

The document upload system is now robust, supports multiple files, and provides clear error messages!
