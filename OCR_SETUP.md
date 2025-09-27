# OCR Setup Guide

## Image Text Extraction with Tesseract OCR

To enable text extraction from images (JPG, PNG, etc.), you need to install Tesseract OCR on your system.

### Installation Instructions

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### macOS (with Homebrew)
```bash
brew install tesseract
```

#### Windows
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your system PATH

#### Python Packages (Already Included)
The following Python packages are already in requirements.txt:
- `pytesseract>=0.3.10`
- `Pillow>=10.0.0`
- `opencv-python-headless>=4.8.0`

### Verification

To verify Tesseract is installed correctly:
```bash
tesseract --version
```

### What Happens Without OCR

If Tesseract is not available:
- Images can still be uploaded
- A placeholder document is created with file information
- No text extraction occurs
- The system continues to work with other document types

### Supported Image Formats

With OCR enabled:
- JPG/JPEG
- PNG
- BMP
- TIFF
- GIF

### OCR Features

- Automatic text extraction from images
- Image preprocessing for better accuracy
- Support for multiple languages (default: English)
- Error handling for unreadable images