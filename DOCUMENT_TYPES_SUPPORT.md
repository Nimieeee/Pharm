# Document Types Support

PharmGPT supports multiple document types for RAG (Retrieval-Augmented Generation) processing.

## Supported File Types

### Text Documents
- **PDF** (`.pdf`) - Extracts text from all pages
- **Text** (`.txt`, `.md`) - Plain text and Markdown files
- **Word** (`.docx`) - Microsoft Word documents (paragraphs and tables)

### Presentations
- **PowerPoint** (`.pptx`, `.ppt`) - Extracts text from:
  - Slide content
  - Tables
  - Speaker notes
  - Each slide is processed separately for better context

### Images (with OCR)
- **PNG** (`.png`)
- **JPEG** (`.jpg`, `.jpeg`)
- **GIF** (`.gif`)
- **BMP** (`.bmp`)
- **WebP** (`.webp`)
- **TIFF** (`.tiff`)

Images are processed using OCR (Optical Character Recognition) to extract text content.

## Processing Details

### PDF Processing
- Extracts text from each page separately
- Preserves page numbers in metadata
- Handles multi-page documents efficiently

### Word Document Processing
- Extracts text from paragraphs
- Extracts text from tables
- Maintains document structure

### PowerPoint Processing
- Processes each slide individually
- Extracts text from all shapes and text boxes
- Includes table content
- Captures speaker notes
- Slide numbers preserved in metadata

### Image Processing
**With OCR (Tesseract)**:
- Extracts text from images using OCR
- Supports multiple languages
- Handles various image formats
- Includes image dimensions in metadata

**Without OCR (Fallback)**:
- Stores basic image information
- Records image dimensions and format
- Allows referencing the image in conversation

## File Size Limits

- **Maximum file size**: 10 MB per file
- **Recommended**: Keep files under 5 MB for faster processing

## Text Chunking

All documents are split into chunks for efficient processing:
- **Chunk size**: 1500 characters
- **Chunk overlap**: 300 characters
- Preserves context across chunks
- Optimized for semantic search

## Usage

### Upload a Document
1. Click the paperclip icon in the chat input
2. Select your file (PDF, DOCX, PPTX, or image)
3. Wait for processing to complete
4. Document will show as "Ready" when processed

### Ask Questions
Once uploaded, you can ask questions about the document:
- "What does this document say about X?"
- "Summarize the key points"
- "What's on slide 5?"
- "What text is in this image?"

## Technical Details

### Dependencies
- **PyPDF2**: PDF processing
- **python-docx**: Word document processing
- **python-pptx**: PowerPoint processing
- **Pillow**: Image handling
- **pytesseract**: OCR for text extraction from images

### OCR Setup (Optional)

For image OCR to work, Tesseract must be installed on the server:

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr
```

**macOS**:
```bash
brew install tesseract
```

**Windows**:
Download from: https://github.com/UB-Mannheim/tesseract/wiki

If Tesseract is not available, images will still be processed but without text extraction.

### Embedding Generation

All extracted text is converted to embeddings using:
- **Mistral Embed** (1024 dimensions)
- Semantic search for relevant context
- Stored in Supabase pgvector

## Best Practices

### For Best Results

1. **Use clear, readable documents**
   - High-quality scans for images
   - Well-formatted text documents
   - Clear slide layouts for presentations

2. **Optimize file size**
   - Compress large PDFs
   - Reduce image resolution if needed
   - Remove unnecessary pages

3. **Structure your questions**
   - Be specific about what you're looking for
   - Reference page/slide numbers if known
   - Ask follow-up questions for clarification

### Limitations

1. **Images**:
   - OCR accuracy depends on image quality
   - Handwritten text may not be recognized
   - Complex layouts may affect extraction

2. **Tables**:
   - Complex table structures may lose formatting
   - Merged cells might affect extraction

3. **Formatting**:
   - Visual formatting (bold, italic) is not preserved
   - Colors and styling are not captured
   - Charts and graphs are not processed (only text)

## Error Handling

### Common Issues

**"No content extracted from document"**:
- File may be empty
- PDF may be image-based (needs OCR)
- File may be corrupted

**"Unsupported file type"**:
- Check file extension
- Ensure file is one of the supported types
- Try converting to a supported format

**"File too large"**:
- Reduce file size
- Split into multiple smaller files
- Compress images/PDFs

## Examples

### PDF Document
```
Upload: research_paper.pdf
Ask: "What are the main findings in this research?"
```

### PowerPoint Presentation
```
Upload: product_presentation.pptx
Ask: "Summarize the features mentioned in the slides"
```

### Image with Text
```
Upload: screenshot.png
Ask: "What does this screenshot show?"
```

### Word Document
```
Upload: report.docx
Ask: "What are the recommendations in this report?"
```

## Future Enhancements

Planned features:
- Excel spreadsheet support (`.xlsx`)
- CSV file processing
- HTML document support
- Audio transcription (`.mp3`, `.wav`)
- Video transcription (`.mp4`)
- Multi-file batch upload
- Document comparison
- Citation extraction
