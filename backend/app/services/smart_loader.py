import logging
from app.services.vision_service import process_visual_document
from app.services.text_service import process_text_document
from app.services.data_service import process_spreadsheet

logger = logging.getLogger(__name__)

async def process_file(
    file_content: bytes, 
    filename: str, 
    user_prompt: str, 
    api_key: str,
    mode: str = "detailed"  # <--- NEW PARAMETER
) -> str:
    """
    The Brain: Decides how to read the file based on extension.
    Returns string content extracted/analyzed from the file.
    """
    ext = filename.split('.')[-1].lower()
    
    logger.info(f"🧠 Smart Loader processing {filename} (Ext: {ext}) in mode: {mode}")

    try:
        # --- STRATEGY 1: VISUAL DOCS (PDF, PPTX, IMAGES) ---
        # We use Pixtral to "see" these files.
        if ext in ['pdf', 'pptx', 'png', 'jpg', 'jpeg', 'webp']:
            return await process_visual_document(
                file_content, filename, user_prompt, api_key, mode=mode
            )

        # --- STRATEGY 2: DATASETS (CSV, EXCEL) ---
        # We use Pandas to analyze data structures.
        elif ext in ['csv', 'xlsx', 'xls']:
            return process_spreadsheet(file_content, ext, user_prompt)

        # --- STRATEGY 3: TEXT DOCS (DOCX, MD, TXT) ---
        # We use standard extraction
        elif ext in ['docx', 'md', 'txt']:
            return process_text_document(file_content, ext, user_prompt)

        else:
            return f"❌ Unsupported file format: {ext}"
            
    except Exception as e:
        logger.error(f"Smart processing failed for {filename}: {e}")
        return f"Error processing file: {str(e)}"
