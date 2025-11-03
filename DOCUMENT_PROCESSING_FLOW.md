# Document Processing Flow

## Overview
This diagram shows how XLSX, CSV, and PPTX files are processed through the system.

```
┌─────────────────────────────────────────────────────────────────┐
│                         File Upload                              │
│                    (XLSX, CSV, PPTX, etc.)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Endpoint Validation                       │
│  • Check file extension (xlsx, csv, pptx, pdf, docx, etc.)     │
│  • Validate file size (max 10MB)                                │
│  • Verify conversation ownership                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EnhancedDocumentLoader                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ XLSX Loader  │  │  CSV Loader  │  │ PPTX Loader  │         │
│  │              │  │              │  │              │         │
│  │ • Read all   │  │ • Detect     │  │ • Extract    │         │
│  │   sheets     │  │   encoding   │  │   slides     │         │
│  │ • Extract    │  │ • Parse      │  │ • Get text   │         │
│  │   headers    │  │   columns    │  │   content    │         │
│  │ • Parse rows │  │ • Parse rows │  │ • Include    │         │
│  │              │  │              │  │   notes      │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Text Extraction                               │
│                                                                  │
│  XLSX: "Sheet: Sales                                            │
│         Columns: Date, Product, Revenue                         │
│         Date: 2024-01 | Product: Widget | Revenue: 1000"       │
│                                                                  │
│  CSV:  "Columns: Name, Email, Status                           │
│         Name: John | Email: john@ex.com | Status: Active"      │
│                                                                  │
│  PPTX: "[Slide 1 text] [Slide 2 text] [Notes]"                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Text Cleaning                               │
│  • Remove excessive whitespace                                   │
│  • Normalize line breaks                                         │
│  • Clean special characters                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Metadata Enhancement                          │
│  • filename: "data.xlsx"                                        │
│  • file_type: "xlsx"                                            │
│  • sheet_name: "Sales" (for XLSX)                              │
│  • rows: 100                                                     │
│  • columns: 5                                                    │
│  • loader: "PandasExcelLoader"                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Text Splitting                              │
│  • Split into optimal chunks (500-1000 chars)                   │
│  • Maintain context overlap                                      │
│  • Preserve semantic boundaries                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Embedding Generation                          │
│  • Generate vector embeddings                                    │
│  • Use configured embedding model                                │
│  • Create semantic representations                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Vector Database Storage                        │
│  • Store embeddings in Supabase                                 │
│  • Link to conversation                                          │
│  • Enable semantic search                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ready for RAG                               │
│  • Document searchable                                           │
│  • Available for chat context                                    │
│  • Semantic similarity queries enabled                           │
└─────────────────────────────────────────────────────────────────┘
```

## Format-Specific Processing

### XLSX Processing Details
```
Excel File (.xlsx)
    │
    ├─► Sheet 1: "Sales"
    │   ├─► Headers: [Date, Product, Revenue]
    │   ├─► Row 1: [2024-01-01, Widget A, 1000]
    │   ├─► Row 2: [2024-01-02, Widget B, 1500]
    │   └─► Document 1 created
    │
    ├─► Sheet 2: "Inventory"
    │   ├─► Headers: [SKU, Quantity, Location]
    │   ├─► Row 1: [WA001, 100, Warehouse A]
    │   └─► Document 2 created
    │
    └─► Result: Multiple documents (one per sheet)
```

### CSV Processing Details
```
CSV File (.csv)
    │
    ├─► Encoding Detection
    │   ├─► Try UTF-8 ✓
    │   ├─► Try Latin-1
    │   └─► Try CP1252
    │
    ├─► Parse Structure
    │   ├─► Headers: [Name, Email, Status]
    │   ├─► Row 1: [John, john@ex.com, Active]
    │   └─► Row 2: [Jane, jane@ex.com, Active]
    │
    └─► Result: Single document with all rows
```

### PPTX Processing Details
```
PowerPoint File (.pptx)
    │
    ├─► Slide 1
    │   ├─► Title: "Introduction"
    │   ├─► Content: "Welcome to..."
    │   └─► Notes: "Remember to..."
    │
    ├─► Slide 2
    │   ├─► Title: "Key Points"
    │   └─► Content: "• Point 1..."
    │
    └─► Result: Single document with all slide content
```

## Error Handling Flow

```
File Upload
    │
    ├─► Valid Format? ──No──► HTTP 400: Unsupported file type
    │       │
    │      Yes
    │       │
    ├─► Valid Size? ──No──► HTTP 413: File too large
    │       │
    │      Yes
    │       │
    ├─► Not Empty? ──No──► HTTP 400: Empty file
    │       │
    │      Yes
    │       │
    ├─► Can Parse? ──No──► HTTP 500: Processing error
    │       │
    │      Yes
    │       │
    ├─► Has Content? ──No──► HTTP 400: No content extracted
    │       │
    │      Yes
    │       │
    └─► Success ──► HTTP 200: Document processed
```

## Performance Considerations

| File Type | Avg Processing Time | Memory Usage | Notes |
|-----------|-------------------|--------------|-------|
| CSV (1MB) | 1-2 seconds | Low | Fast parsing |
| XLSX (1MB) | 2-4 seconds | Medium | Multi-sheet overhead |
| PPTX (1MB) | 3-5 seconds | Medium | Text extraction |
| PDF (1MB) | 2-3 seconds | Medium | Page-by-page |

## Integration Points

1. **API Layer**: `backend/app/api/v1/endpoints/chat.py`
2. **Document Loader**: `backend/app/services/document_loaders.py`
3. **RAG Service**: `backend/app/services/enhanced_rag.py`
4. **Vector Store**: Supabase pgvector
5. **Embedding Service**: Configurable (Mistral, Cohere, etc.)
