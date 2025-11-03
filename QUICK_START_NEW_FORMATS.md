# Quick Start: Using XLSX, CSV, and PPTX Files

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Upload a File

### Using cURL

```bash
# Upload XLSX file
curl -X POST "http://localhost:8000/api/v1/chat/conversations/{conversation_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.xlsx"

# Upload CSV file
curl -X POST "http://localhost:8000/api/v1/chat/conversations/{conversation_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.csv"

# Upload PPTX file
curl -X POST "http://localhost:8000/api/v1/chat/conversations/{conversation_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@presentation.pptx"
```

### Using Python

```python
import requests

url = "http://localhost:8000/api/v1/chat/conversations/{conversation_id}/documents"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Upload XLSX
with open("data.xlsx", "rb") as f:
    files = {"file": ("data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())

# Upload CSV
with open("data.csv", "rb") as f:
    files = {"file": ("data.csv", f, "text/csv")}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())

# Upload PPTX
with open("presentation.pptx", "rb") as f:
    files = {"file": ("presentation.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Upload XLSX
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch(`/api/v1/chat/conversations/${conversationId}/documents`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Expected Response

```json
{
  "document_id": "uuid",
  "filename": "data.xlsx",
  "chunk_count": 5,
  "status": "processed",
  "message": "Document processed successfully"
}
```

## What Happens Behind the Scenes

1. **File Upload**: File is received by the API endpoint
2. **Validation**: File type and size are validated
3. **Processing**: 
   - XLSX: Each sheet is extracted with headers and data
   - CSV: Data is parsed with automatic encoding detection
   - PPTX: Text from all slides is extracted
4. **Text Extraction**: Content is converted to searchable text
5. **Chunking**: Text is split into optimal chunks
6. **Embedding**: Chunks are embedded using your configured model
7. **Storage**: Embeddings are stored in the vector database
8. **Ready**: Content is now searchable and available for RAG

## Chat with Your Documents

After uploading, simply chat normally:

```
User: "What's the total revenue in the Q4 sheet?"
AI: [Searches the uploaded XLSX and provides answer]

User: "Summarize the key points from slide 3"
AI: [Searches the uploaded PPTX and provides summary]

User: "How many customers are in the active status?"
AI: [Searches the uploaded CSV and provides count]
```

## Supported Formats Summary

| Format | Extension | Use Case |
|--------|-----------|----------|
| Excel | .xlsx | Spreadsheets with multiple sheets |
| CSV | .csv | Simple tabular data |
| PowerPoint | .pptx | Presentations and slides |
| PDF | .pdf | Documents and reports |
| Word | .docx | Text documents |
| Text | .txt, .md | Plain text files |
| Images | .png, .jpg, .jpeg, .gif, .bmp, .webp | Visual content |

## Troubleshooting

### "Unsupported file type"
- Check file extension is correct
- Ensure file is not corrupted
- Verify file size is under 10MB

### "No content extracted"
- Check if file has actual content
- For XLSX: Ensure sheets have data
- For CSV: Ensure file is not empty
- For PPTX: Ensure slides have text

### "Failed to process document"
- Check backend logs for detailed error
- Verify all dependencies are installed
- Ensure file is not password-protected

## Need Help?

Check the full documentation in `SPREADSHEET_PRESENTATION_SUPPORT.md`
