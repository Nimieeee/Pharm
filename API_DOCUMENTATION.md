# PharmGPT API Documentation - Enhanced RAG System

This document covers the enhanced API endpoints for the LangChain + Mistral embeddings integration.

## Base URL

- **Production**: `https://pharmgpt-backend.onrender.com`
- **Development**: `http://localhost:8000`

## Authentication

All endpoints require JWT authentication unless specified otherwise.

```bash
# Include in headers
Authorization: Bearer YOUR_JWT_TOKEN
```

## Enhanced AI Endpoints

### Chat with RAG

Enhanced chat endpoint with improved document context.

**POST** `/api/v1/ai/chat`

```json
{
  "message": "What are the side effects of aspirin?",
  "conversation_id": "uuid",
  "mode": "detailed",
  "use_rag": true
}
```

**Response:**
```json
{
  "response": "Based on the uploaded documents, aspirin side effects include...",
  "conversation_id": "uuid",
  "mode": "detailed",
  "context_used": true
}
```

### Document Upload

Upload documents for RAG processing with enhanced LangChain loaders.

**POST** `/api/v1/ai/documents/upload`

**Parameters:**
- `conversation_id` (query): UUID of conversation
- `file` (form-data): Document file (PDF, DOCX, TXT)

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed 5 chunks from document.pdf",
  "chunk_count": 5,
  "processing_time": 2.34,
  "errors": []
}
```

**Supported Formats:**
- PDF (via PyPDFLoader)
- DOCX (via Docx2txtLoader) 
- TXT/MD (via TextLoader with encoding detection)

**Limits:**
- Maximum file size: 10MB
- Maximum chunks per document: 1000

### Document Search

Search documents using Mistral embeddings for semantic similarity.

**POST** `/api/v1/ai/documents/search`

```json
{
  "query": "drug interactions with NSAIDs",
  "conversation_id": "uuid",
  "max_results": 10,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "chunks": [
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "content": "NSAIDs can interact with anticoagulants...",
      "similarity": 0.87,
      "metadata": {
        "filename": "drug_interactions.pdf",
        "embedding_version": "mistral-v1",
        "page": 1,
        "chunk_index": 0
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_results": 1,
  "query": "drug interactions with NSAIDs"
}
```

### Get Conversation Documents

List all documents uploaded to a conversation.

**GET** `/api/v1/ai/documents/{conversation_id}`

**Response:**
```json
[
  {
    "filename": "drug_interactions.pdf",
    "chunk_count": 15,
    "total_characters": 12450,
    "created_at": "2024-01-01T00:00:00Z",
    "embedding_version": "mistral-v1"
  }
]
```

### Delete Conversation Documents

Remove all documents from a conversation.

**DELETE** `/api/v1/ai/documents/{conversation_id}`

**Response:**
```json
{
  "message": "Documents deleted successfully"
}
```

## Health Monitoring Endpoints

### System Health

Comprehensive system health check.

**GET** `/api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "components": {
    "embeddings": {
      "status": "healthy",
      "client_available": true,
      "model": "mistral-embed",
      "dimensions": 1024
    },
    "document_loader": {
      "status": "healthy",
      "supported_formats": [".pdf", ".docx", ".txt"]
    },
    "database": {
      "status": "healthy",
      "connection": "active"
    }
  },
  "performance": {
    "document_processing": {
      "count": 150,
      "avg_duration": 2.3,
      "success_rate": 0.98
    }
  }
}
```

### Embeddings Health

Detailed embeddings service status.

**GET** `/api/v1/health/embeddings`

**Response:**
```json
{
  "health": {
    "status": "healthy",
    "embedding_test": "passed",
    "client_available": true,
    "model": "mistral-embed",
    "dimensions": 1024
  },
  "cache_statistics": {
    "hits": 1250,
    "misses": 180,
    "cache_hit_rate": 0.87,
    "cache_size": 450,
    "api_calls": 180
  }
}
```

### Migration Status

Check embedding migration progress.

**GET** `/api/v1/health/migration`

**Response:**
```json
{
  "migration_status": {
    "migration_enabled": true,
    "total_chunks": 1000,
    "old_embeddings": 50,
    "new_embeddings": 950,
    "pending_migration": 0,
    "migration_percentage": 95.0
  },
  "validation": {
    "valid": true,
    "issues": []
  }
}
```

### Performance Metrics

System performance statistics.

**GET** `/api/v1/health/performance`

**Response:**
```json
{
  "performance_statistics": {
    "document_processing": {
      "count": 150,
      "avg_duration": 2.3,
      "success_rate": 0.98
    },
    "embedding_generation": {
      "count": 500,
      "avg_duration": 0.8,
      "success_rate": 0.99
    },
    "similarity_search": {
      "count": 1200,
      "avg_duration": 0.15,
      "success_rate": 1.0
    }
  },
  "cache_statistics": {
    "cache_hit_rate": 0.87,
    "cache_size": 450
  }
}
```

### Test Embedding Generation

Test embeddings service functionality.

**POST** `/api/v1/health/test-embedding`

**Response:**
```json
{
  "success": true,
  "message": "Embedding generation test passed",
  "test_details": {
    "text_length": 50,
    "embedding_dimensions": 1024,
    "generation_time": 0.234,
    "model": "mistral-embed"
  }
}
```

## Admin Migration Endpoints

### Migration Status (Admin)

**GET** `/api/v1/admin/migration/status`

Requires admin authentication.

**Response:**
```json
{
  "migration_enabled": true,
  "total_chunks": 1000,
  "migration_percentage": 95.0,
  "configuration": {
    "batch_size": 100,
    "parallel_workers": 2,
    "use_mistral_embeddings": true
  }
}
```

### Run Migration (Admin)

**POST** `/api/v1/admin/migration/run?max_chunks=1000&batch_size=100`

Requires admin authentication.

**Response:**
```json
{
  "success": true,
  "message": "Migration completed in 45.67 seconds",
  "stats": {
    "total_processed": 1000,
    "successful_migrations": 995,
    "failed_migrations": 5
  },
  "final_status": {
    "migration_percentage": 99.5
  }
}
```

### Validate Migration (Admin)

**POST** `/api/v1/admin/migration/validate`

Requires admin authentication.

**Response:**
```json
{
  "valid": true,
  "issues": [],
  "statistics": {
    "total_chunks": 1000,
    "new_embeddings": 995,
    "migration_percentage": 99.5
  }
}
```

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `413` - Payload Too Large (file too big)
- `422` - Validation Error (invalid data format)
- `429` - Rate Limited (too many requests)
- `500` - Internal Server Error

### Enhanced Error Details

Document processing errors include specific details:

```json
{
  "success": false,
  "message": "Unsupported file format: .xyz. Supported formats: .pdf, .docx, .txt",
  "chunk_count": 0,
  "errors": [
    "File format validation failed",
    "No content could be extracted"
  ]
}
```

## Rate Limits

- **Document Upload**: 10 files per minute per user
- **Search Requests**: 100 requests per minute per user
- **Embedding Generation**: Limited by Mistral API quotas
- **Health Checks**: No limits

## Best Practices

### Document Upload

1. **File Size**: Keep files under 5MB for optimal processing
2. **Format**: Use PDF or DOCX for best text extraction
3. **Content**: Ensure documents contain readable text
4. **Naming**: Use descriptive filenames

### Search Queries

1. **Query Length**: 10-100 characters work best
2. **Specificity**: Use specific pharmaceutical terms
3. **Threshold**: Start with 0.7, adjust based on results
4. **Results**: Request 5-20 results for optimal performance

### Error Handling

1. **Retry Logic**: Implement exponential backoff for 429/500 errors
2. **Validation**: Check file format before upload
3. **Monitoring**: Use health endpoints to monitor system status
4. **Fallback**: Handle cases where RAG context isn't available

### Performance Optimization

1. **Caching**: Embeddings are cached automatically
2. **Batch Operations**: Upload multiple documents in sequence
3. **Concurrent Requests**: Limit to 5 concurrent requests per user
4. **Monitoring**: Use performance endpoints to track metrics

## SDK Examples

### Python

```python
import requests
import json

class PharmGPTClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def upload_document(self, conversation_id, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {'conversation_id': conversation_id}
            response = requests.post(
                f"{self.base_url}/api/v1/ai/documents/upload",
                headers=self.headers,
                files=files,
                params=params
            )
        return response.json()
    
    def search_documents(self, query, conversation_id, max_results=10):
        data = {
            "query": query,
            "conversation_id": conversation_id,
            "max_results": max_results,
            "similarity_threshold": 0.7
        }
        response = requests.post(
            f"{self.base_url}/api/v1/ai/documents/search",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def chat_with_rag(self, message, conversation_id):
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "mode": "detailed",
            "use_rag": True
        }
        response = requests.post(
            f"{self.base_url}/api/v1/ai/chat",
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
client = PharmGPTClient("https://pharmgpt-backend.onrender.com", "your_token")

# Upload document
result = client.upload_document("conversation_uuid", "drug_guide.pdf")
print(f"Uploaded: {result['chunk_count']} chunks")

# Search documents
results = client.search_documents("aspirin side effects", "conversation_uuid")
print(f"Found: {len(results['chunks'])} relevant chunks")

# Chat with RAG
response = client.chat_with_rag("What are aspirin's side effects?", "conversation_uuid")
print(f"AI Response: {response['response']}")
```

### JavaScript

```javascript
class PharmGPTClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async uploadDocument(conversationId, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/ai/documents/upload?conversation_id=${conversationId}`,
      {
        method: 'POST',
        headers: { 'Authorization': this.headers.Authorization },
        body: formData
      }
    );
    
    return response.json();
  }

  async searchDocuments(query, conversationId, maxResults = 10) {
    const response = await fetch(`${this.baseUrl}/api/v1/ai/documents/search`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
        max_results: maxResults,
        similarity_threshold: 0.7
      })
    });
    
    return response.json();
  }

  async chatWithRAG(message, conversationId) {
    const response = await fetch(`${this.baseUrl}/api/v1/ai/chat`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        mode: 'detailed',
        use_rag: true
      })
    });
    
    return response.json();
  }
}

// Usage
const client = new PharmGPTClient('https://pharmgpt-backend.onrender.com', 'your_token');

// Upload document
const fileInput = document.getElementById('file-input');
const result = await client.uploadDocument('conversation_uuid', fileInput.files[0]);
console.log(`Uploaded: ${result.chunk_count} chunks`);

// Search and chat
const searchResults = await client.searchDocuments('aspirin side effects', 'conversation_uuid');
const chatResponse = await client.chatWithRAG('What are aspirin side effects?', 'conversation_uuid');
```

## Changelog

### v2.1.0 - Enhanced RAG System

**Added:**
- LangChain document loaders (PDF, DOCX, TXT)
- Mistral embeddings (1024 dimensions)
- Enhanced document upload endpoint
- Document search endpoint
- Comprehensive health monitoring
- Migration management endpoints
- Performance metrics tracking
- Embedding caching system

**Improved:**
- Search accuracy with Mistral embeddings
- Error handling and recovery
- Document processing reliability
- API response times
- System monitoring capabilities

**Changed:**
- Embedding dimensions: 384 → 1024
- Document processing: Custom → LangChain
- Embeddings: Hash-based → Mistral API
- Text splitting: Custom → RecursiveCharacterTextSplitter

---

For more information, see the [Migration Guide](MIGRATION_GUIDE.md) and [Environment Variables Documentation](backend/ENVIRONMENT_VARIABLES.md).