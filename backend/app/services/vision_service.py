import base64
import io
import os
import subprocess
import tempfile
import logging
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
    "detailed": "mistral-large-latest",   # Best reasoning
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

async def process_visual_document(
    content: bytes, 
    filename: str, 
    user_prompt: str, 
    api_key: str,
    mode: str = "detailed"
):
    client = Mistral(api_key=api_key)
    
    # 1. CONVERT TO IMAGES (High DPI for small text)
    images = _convert_to_images(content, filename)
    if not images:
        return f"Error: Could not extract images from {filename}"
        
    raw_vision_data = []
    logger.info(f"👁️ [Robust Vision] Analyzing {len(images)} pages with Pixtral-Large...")

    for i, img in enumerate(images):
        await mistral_limiter.wait_for_slot()
        
        # 2. IMAGE OPTIMIZATION (Crucial for "Detailed" mode)
        # We ensure the image isn't too large for the API but big enough to read tiny text.
        base64_img = _optimize_and_encode(img)
        
        try:
            # 3. EXTRACTION STEP (Pixtral Phase)
            response = await client.chat.complete_async(
                model="pixtral-12b-2409", # Using the stable pixtral identifier
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ROBUST_SYSTEM_PROMPT},
                            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_img}"}
                        ]
                    }
                ]
            )
            extracted_content = response.choices[0].message.content
            raw_vision_data.append(f"## --- PAGE {i+1} START ---\n{extracted_content}\n## --- PAGE {i+1} END ---")
            
        except Exception as e:
            logger.error(f"⚠️ Error on page {i+1}: {e}")
            raw_vision_data.append(f"## Page {i+1} [Extraction Failed: {str(e)}]")

    # Join all pages
    full_document_context = "\n\n".join(raw_vision_data)

    # ==========================================================
    # STAGE 2: REASONING (Augmentation Phase)
    # ==========================================================
    
    target_model = MODE_MAPPING.get(mode, "mistral-large-latest")
    logger.info(f"🧠 [Reasoning] Synthesizing answer using {target_model}...")
    
    await mistral_limiter.wait_for_slot()

    try:
        final_response = await client.chat.complete_async(
            model=target_model,
            messages=[
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
            ]
        )
        return final_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Reasoning Phase Error: {e}")
        return full_document_context # Fallback to raw transcripts if reasoning fails

# --- ROBUST HELPERS ---

def _convert_to_images(content: bytes, filename: str):
    ext = filename.split('.')[-1].lower()
    
    try:
        if ext == 'pdf':
            # DPI=300 is the sweet spot for academic papers (readable text, manageable size)
            if convert_from_bytes:
                return convert_from_bytes(content, dpi=300, fmt="jpeg")
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
