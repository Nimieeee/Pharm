import base64
import io
import os
import subprocess
import tempfile
import logging
import asyncio
from typing import List, Any
try:
    from PIL import Image
    from pdf2image import convert_from_bytes, convert_from_path
except ImportError:
    Image = None
    convert_from_bytes = None
    convert_from_path = None

from mistralai import Mistral
from app.utils.rate_limiter import mistral_limiter

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
MODE_MAPPING = {
    "fast": "mistral-small-latest",       # Fast, good for summaries
    "detailed": "mistral-medium-latest",  # Best reasoning
    "research": "mistral-large-latest"    # Research requires top-tier logic
}

# The "Audit" Prompt: Forces detailed extraction
ROBUST_SYSTEM_PROMPT = """
You are a high-precision Optical Character Recognition (OCR) and Document Analysis engine.
Your goal is to create a pixel-perfect Markdown representation of this document page.

RULES FOR EXTRACTION:
1. **Text:** Transcribe ALL text verbatim. Do not correct grammar. Do not summarize. Include headers, footers, and side-notes.
2. **Tables:** Convert every table into a Markdown table. PRESERVE every row and column. Do not skip "empty" cells if they exist in the original.
3. **Charts & Graphs:**
   - Describe the X-axis and Y-axis labels and units exactly.
   - Extract specific data points (e.g., "At 2 hours, concentration was 5.4 mg/L").
   - Describe the trend (e.g., "exponential decay").
   - If there is a legend, list all categories.
4. **Chemical Structures/Diagrams:** Describe the visual structure (e.g., "Benzene ring attached to...").
5. **Layout:** Use Markdown headers (#, ##, ###) to match the document's font hierarchy.

WARNING: Do not output "Summary of page" or "The page contains...". Just output the content itself.
"""

import httpx

# ... (Imports remain the same, ensure httpx is imported if not already)

# Constants for NVIDIA API
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_KEY = "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" 

async def process_visual_document(
    content: bytes, 
    filename: str, 
    user_prompt: str, 
    api_key: str,
    mode: str = "detailed",
    chunk_callback: Any = None
):
    # client = Mistral(api_key=api_key) # No longer needed for Vision
    
    # 1. CONVERT TO IMAGES (High DPI for small text)
    logger.info(f"📄 [Vision] Converting {filename} to images...")
    images = _convert_to_images(content, filename)
    if not images:
        return f"Error: Could not extract images from {filename}"
        
    raw_vision_data = []
    logger.info(f"👁️ [Robust Vision] Analyzing {len(images)} pages in parallel with NVIDIA Mistral Large 3...")

    # Semaphores to control concurrency (prevent hitting rate limits too hard)
    # NVIDIA API can handle more concurrency, increasing to 25
    semaphore = asyncio.Semaphore(25)
    
    # Track background tasks to cancel them if needed
    ingestion_tasks = set()

    async def process_single_page(idx, img):
        async with semaphore:
            await mistral_limiter.wait_for_slot()
            
            # Optimization
            base64_img = _optimize_and_encode(img)
            
            try:
                headers = {
                    "Authorization": f"Bearer {NVIDIA_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                payload = {
                    "model": "mistralai/mistral-large-3-675b-instruct-2512",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ROBUST_SYSTEM_PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }],
                    "max_tokens": 2048, # increased for full page OCR
                    "temperature": 0.15
                }
                
                async with httpx.AsyncClient() as http_client:
                    resp = await http_client.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=90.0)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Streaming Ingestion: Fire and forget but track
                        if chunk_callback:
                            try:
                                t = asyncio.create_task(chunk_callback(content, idx))
                                ingestion_tasks.add(t)
                                t.add_done_callback(ingestion_tasks.discard)
                            except Exception as cb_e:
                                logger.error(f"Callback error: {cb_e}")
                                
                        return idx, f"## --- PAGE {idx+1} START ---\n{content}\n## --- PAGE {idx+1} END ---"
                    else:
                        logger.error(f"NVIDIA API Error on page {idx+1}: {resp.status_code} - {resp.text}")
                        return idx, f"## Page {idx+1} [Extraction Failed: API Error {resp.status_code}]"

            except Exception as e:
                logger.error(f"⚠️ Error on page {idx+1}: {e}")
                return idx, f"## Page {idx+1} [Extraction Failed: {str(e)}]"

    # Launch parallel tasks
    tasks = [process_single_page(i, img) for i, img in enumerate(images)]
    
    try:
        results = await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.warning(f"⚠️ Processing cancelled for {filename}. Terminating {len(ingestion_tasks)} background ingestion tasks...")
        for t in ingestion_tasks:
            t.cancel()
        raise
    
    # Sort results to ensure page order is preserved
    results.sort(key=lambda x: x[0])
    raw_vision_data = [r[1] for r in results]

    # Join all pages
    full_document_context = "\n\n".join(raw_vision_data)

    # ==========================================================
    # STAGE 2: REASONING (Augmentation Phase)
    # ==========================================================
    
    # We also use NVIDIA for the reasoning phase for consistency and speed
    logger.info(f"🧠 [Reasoning] Synthesizing answer using NVIDIA Mistral Large 3...")
    
    await mistral_limiter.wait_for_slot()

    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": "mistralai/mistral-large-3-675b-instruct-2512",
            "messages": [
                {
                    "role": "system", 
                    "content": (
                        "You are PharmGPT. You are analyzing a document that has been transcribed by a Vision AI. "
                        "The transcription is verbatim and detailed.\n"
                        "Your task is to answer the user's question using ONLY the provided context.\n"
                        "If the answer requires citing data from a table or chart in the context, do so explicitly."
                    )
                },
                {
                    "role": "user", 
                    "content": (
                        f"Document Context:\n{full_document_context}\n\n"
                        f"User Question: {user_prompt}"
                    )
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.15
        }
        
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content']
            else:
                 logger.error(f"Reasoning Phase NVIDIA Error: {resp.status_code}")
                 return full_document_context # Fallback
                 
    except Exception as e:
        logger.error(f"Reasoning Phase Error: {e}")
        return full_document_context # Fallback to raw transcripts if reasoning fails

# --- ROBUST HELPERS ---

def _convert_to_images(content: bytes, filename: str):
    ext = filename.split('.')[-1].lower()
    
    try:
        if ext == 'pdf':
            # DPI=200 is sufficient for OCR (Pixtral doesn't need 300) and faster
            if convert_from_bytes:
                return convert_from_bytes(content, dpi=200, fmt="jpeg", thread_count=4)
            else:
                raise ImportError("pdf2image missing")
            
        elif ext == 'pptx':
            return _convert_pptx_robust(content)
            
        else: # Images
            if Image:
                return [Image.open(io.BytesIO(content))]
            else:
                raise ImportError("Pillow missing")
    except Exception as e:
        logger.error(f"Image conversion failed: {e}")
        return []

def _optimize_and_encode(image):
    """
    Smart resizing: Keeps detail high but fits within API token limits.
    """
    if not Image: return ""
    
    # Max dimension for Pixtral is often safe around 2048 or 4096, 
    # but for "Detail", we want to avoid downscaling if possible.
    max_dim = 2560 
    
    # Make copy to avoid mutating original
    img_copy = image.copy()
    
    # Convert RGBA to RGB (JPEG doesn't support transparency)
    if img_copy.mode == 'RGBA':
        # Create white background and composite
        background = Image.new('RGB', img_copy.size, (255, 255, 255))
        background.paste(img_copy, mask=img_copy.split()[3])  # Use alpha channel as mask
        img_copy = background
    elif img_copy.mode != 'RGB':
        img_copy = img_copy.convert('RGB')
    
    if max(img_copy.size) > max_dim:
        img_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS) # LANCZOS is best for text sharpness
        
    buffered = io.BytesIO()
    # JPEG Quality 92 prevents artifacts around text
    img_copy.save(buffered, format="JPEG", quality=92) 
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def _convert_pptx_robust(content: bytes):
    """
    Robust PPTX converter that handles errors gracefully.
    """
    if not convert_from_path:
        raise ImportError("pdf2image required for pptx")

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "temp.pptx")
        with open(input_path, "wb") as f:
            f.write(content)
            
        # Call LibreOffice
        try:
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", temp_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception:
            # Fallback or Log
            logger.error("LibreOffice conversion failed")
            return []
        
        pdf_path = os.path.join(temp_dir, "temp.pdf")
        if not os.path.exists(pdf_path):
            return []
            
        return convert_from_path(pdf_path, dpi=300)
