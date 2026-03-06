#!/usr/bin/env python3
"""
Test PDF processing directly on VPS
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/var/www/benchside-backend/backend')

async def test_pdf():
    """Test PDF processing"""
    print("=" * 60)
    print("Testing PDF Processing")
    print("=" * 60)
    
    # Read PDF file
    pdf_path = '/var/www/benchside-backend/backend/CNS STIMULANTS_PHA 425.pdf'
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print(f"✅ PDF loaded: {len(pdf_content)} bytes")
    
    # Test PyMuPDF directly
    print("\n1. Testing PyMuPDF text extraction...")
    try:
        import fitz
        doc = fitz.open(pdf_path)
        print(f"   PDF has {len(doc)} pages")
        
        total_text = ""
        for page_idx in range(min(3, len(doc))):  # Test first 3 pages
            page = doc[page_idx]
            text = page.get_text("text").strip()
            total_text += text
            print(f"   Page {page_idx+1}: {len(text)} chars")
            if text:
                print(f"      Preview: {text[:100]}...")
        
        doc.close()
        
        if total_text.strip():
            print(f"   ✅ PyMuPDF extracted {len(total_text)} chars total")
        else:
            print(f"   ❌ PyMuPDF extracted 0 chars - PDF may be scanned/image-only")
    except Exception as e:
        print(f"   ❌ PyMuPDF error: {e}")
    
    # Test smart_loader
    print("\n2. Testing Smart Loader...")
    try:
        from app.services.smart_loader import process_file
        from app.core.config import settings
        
        result = await process_file(
            file_content=pdf_content,
            filename="CNS STIMULANTS_PHA 425.pdf",
            user_prompt="Extract all text from this pharmaceutical document",
            api_key=settings.MISTRAL_API_KEY,
            mode="detailed"
        )
        
        print(f"   Smart Loader returned: {len(result)} chars")
        if result:
            print(f"   Preview: {result[:200]}...")
        
        if result.startswith("Error") or result.startswith("❌") or "[PDF" in result:
            print(f"   ❌ Smart Loader returned error message")
        elif len(result.strip()) < 100:
            print(f"   ❌ Smart Loader returned very little content")
        else:
            print(f"   ✅ Smart Loader successfully extracted content")
    except Exception as e:
        print(f"   ❌ Smart Loader error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test document_loader
    print("\n3. Testing Document Loader...")
    try:
        from app.services.document_loaders import DocumentLoader
        
        loader = DocumentLoader()
        documents = await loader.load_document(
            file_content=pdf_content,
            filename="CNS STIMULANTS_PHA 425.pdf",
            additional_metadata={"test": "true"},
            mode="detailed"
        )
        
        print(f"   Document Loader returned {len(documents)} documents")
        for i, doc in enumerate(documents[:3]):
            print(f"   Doc {i}: {len(doc.page_content)} chars")
            if doc.page_content:
                print(f"      Preview: {doc.page_content[:100]}...")
    except Exception as e:
        print(f"   ❌ Document Loader error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_pdf())
