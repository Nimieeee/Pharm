# Spreadsheet and Presentation Support

## Overview
The application now supports processing of Excel spreadsheets (XLSX), CSV files, and PowerPoint presentations (PPTX) in addition to the existing document formats.

## Supported File Types

### Spreadsheets
- **XLSX** (Excel): Multi-sheet support with column headers and data extraction
- **CSV**: Comma-separated values with automatic encoding detection

### Presentations
- **PPTX** (PowerPoint): Slide content extraction including text and notes

### Existing Formats
- PDF, TXT, MD, DOCX
- Images: PNG, JPG, JPEG, GIF, BMP, WEBP

## How It Works

### XLSX Processing
- Reads all sheets from the Excel file
- Extracts column headers and data rows
- Creates separate documents for each sheet
- Preserves metadata (sheet name, row count, column count)
- Converts data to searchable text format

### CSV Processing
- Automatic encoding detection (UTF-8, Latin-1, CP1252, ISO-8859-1)
- Extracts column headers and data rows
- Converts to searchable text format
- Preserves metadata (row count, column count)

### PPTX Processing
- Extracts text content from all slides
- Includes slide notes and text boxes
- Preserves presentation structure
- Converts to searchable text format

## API Usage

Upload any supported file type to a conversation:

```bash
POST /api/v1/chat/conversations/{conversation_id}/documents
Content-Type: multipart/form-data

file: <your-file.xlsx|csv|pptx>
```

Or use the AI endpoint:

```bash
POST /api/v1/ai/documents/upload
Content-Type: multipart/form-data

conversation_id: <uuid>
file: <your-file.xlsx|csv|pptx>
```

## Dependencies Added

- `openpyxl==3.1.2` - Excel file reading
- `pandas==2.0.3` - Data processing for spreadsheets
- `unstructured==0.10.30` - PowerPoint and document processing

## Text Extraction Examples

### XLSX Example
```
Sheet: Sales Data

Columns: Date, Product, Quantity, Revenue

Date: 2024-01-01 | Product: Widget A | Quantity: 100 | Revenue: 1000
Date: 2024-01-02 | Product: Widget B | Quantity: 150 | Revenue: 1500
```

### CSV Example
```
Columns: Name, Email, Status

Name: John Doe | Email: john@example.com | Status: Active
Name: Jane Smith | Email: jane@example.com | Status: Active
```

### PPTX Example
```
[Extracted text from all slides, including titles, content, and notes]
```

## Error Handling

The system handles:
- Corrupted or invalid files
- Encoding issues (automatic detection)
- Empty files or sheets
- Large files (10MB limit)
- Unsupported formats

## RAG Integration

All extracted content is:
1. Processed and cleaned
2. Split into chunks for embedding
3. Stored in the vector database
4. Available for semantic search and chat context

## Installation

To use these features, install the updated dependencies:

```bash
cd backend
pip install -r requirements.txt
```

## Notes

- Multi-sheet Excel files create separate documents for each sheet
- CSV files are processed as single documents
- PowerPoint presentations extract all text content
- All formats support the same RAG and search capabilities as other document types
