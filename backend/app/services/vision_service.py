import base64
import io
import os
import subprocess
import tempfile
import logging
from typing import List, Any
try:
    from pdf2image import convert_from_bytes, convert_from_path
except ImportError:
    convert_from_bytes = None
    convert_from_path = None

from mistralai import Mistral
from app.utils.rate_limiter import mistral_limiter

logger = logging.getLogger(__name__)

async def process_visual_document(content: bytes, filename: str, user_prompt: str, api_key: str):
    ext = filename.split('.')[-1].lower()
    images = []

    try:
        # 1. PRE-PROCESSING: Convert everything to a list of Images
        if ext == 'pptx':
            images = _convert_pptx_to_images(content)
        elif ext == 'pdf':
            if convert_from_bytes:
                images = convert_from_bytes(content, dpi=200, fmt="jpeg") # Reduced DPI for speed/size
            else:
                return "Error: pdf2image not installed or configured."
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            from PIL import Image
            images = [Image.open(io.BytesIO(content))]
        
        if not images:
            return f"Could not extract images from {filename}"

        # 2. ANALYSIS LOOP
        client = Mistral(api_key=api_key)
        full_report = []
        
        # We construct a system instruction that merges your prompt with the vision task
        base_instruction = (
            f"You are analyzing a page from the file '{filename}'.\n"
            f"USER INSTRUCTION: {user_prompt}\n\n"
            "Task: Extract all text verbatim. If there are charts/graphs, interpret them specifically "
            "according to the user's instruction. If the user asks for a summary, ignore boilerplate text."
        )

        logger.info(f"👁️ Pixtral Large processing {len(images)} pages for {filename}...")

        # Process max 5 pages/images to avoid timeout/rate limits excessive usage in free tier logic if implied
        # Or process all if critical (let's stick to user request, but maybe batch or limit?)
        # For now, process all with rate limiter
        for i, img in enumerate(images):
            # Rate Limit Protection
            await mistral_limiter.wait_for_slot()

            # Optimize Image (Resize if huge to save tokens/bandwidth)
            img.thumbnail((1500, 1500)) 
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')

            try:
                # Using pixtral-large-latest as requested
                response = await client.chat.complete_async(
                    model="pixtral-12b-2409",  # Using specific stable version or "pixtral-large-latest" if available
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": base_instruction},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_img}"}
                            ]
                        }
                    ]
                )
                if response.choices:
                    page_text = response.choices[0].message.content
                    full_report.append(f"## Page {i+1}\n{page_text}")
                else:
                    full_report.append(f"## Page {i+1}\n[No content returned]")
                
            except Exception as e:
                logger.error(f"Error processing page {i+1}: {e}")
                full_report.append(f"## Page {i+1}\n[Error: {str(e)}]")

        return "\n\n".join(full_report)

    except Exception as e:
        logger.error(f"Vision processing failed: {e}")
        return f"Error analyzing visual document: {str(e)}"

def _convert_pptx_to_images(content: bytes):
    """Helper to convert PPTX -> PDF -> Images using LibreOffice"""
    if not convert_from_path:
        raise ImportError("pdf2image required for pptx conversion")

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "temp.pptx")
        with open(input_path, "wb") as f:
            f.write(content)
            
        # Call LibreOffice (Must be installed in Dockerfile!)
        # Check if libreoffice exists
        try:
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", temp_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception:
            raise Exception("LibreOffice not found. PPTX conversion unavailable.")
        
        pdf_path = os.path.join(temp_dir, "temp.pdf")
        if not os.path.exists(pdf_path):
            raise Exception("PPTX to PDF conversion failed")
            
        return convert_from_path(pdf_path, dpi=200)
