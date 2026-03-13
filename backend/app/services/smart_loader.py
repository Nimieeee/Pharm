import logging
from app.services.vision_service import process_visual_document, process_pdf_hybrid, process_pptx_hybrid
from app.services.text_service import process_text_document
from app.services.data_service import process_spreadsheet

logger = logging.getLogger(__name__)

def process_sdf_file(file_content: bytes, filename: str, user_prompt: str) -> str:
    """
    Process SDF (Structure Data File) chemical structure files.
    Extracts compound information and properties.
    """
    try:
        content = file_content.decode('utf-8', errors='ignore')

        # SDF files contain multiple compounds separated by $$$$
        compounds = content.split('$$$$')

        result = []
        for i, compound in enumerate(compounds[:10]):  # Limit to first 10 compounds
            if not compound.strip():
                continue

            # Extract compound name (usually first line)
            lines = compound.strip().split('\n')
            compound_name = lines[0].strip() if lines else f"Compound {i+1}"

            # Extract properties (lines after structure block)
            properties = []
            in_properties = False
            for line in lines[1:]:
                if line.startswith('>  <'):
                    in_properties = True
                    prop_name = line[4:-2]  # Extract property name
                    properties.append(f"{prop_name}:")
                elif in_properties and line.strip():
                    if properties:
                        properties[-1] += f" {line.strip()}"
                    else:
                        properties.append(line.strip())
                elif line == '' and in_properties:
                    in_properties = False

            result.append(f"## {compound_name}\n")
            if properties:
                result.append('\n'.join(properties))

        if result:
            return f"SDF File: {filename}\n\n" + '\n\n'.join(result)
        else:
            return process_spreadsheet(file_content, '.sdf', user_prompt)

    except Exception as e:
        logger.error(f"SDF processing error: {e}")
        return f"Error processing SDF file: {str(e)}"

async def process_file(
    file_content: bytes,
    filename: str,
    user_prompt: str,
    api_key: str,
    mode: str = "detailed",
    chunk_callback=None
) -> str:
    """
    The Brain: Decides how to read the file based on extension.
    Uses hybrid processing (text + selective VLM) for maximum speed.
    """
    ext = filename.split('.')[-1].lower()

    logger.info(f"🧠 Smart Loader processing {filename} (Ext: {ext}) in mode: {mode}")

    try:
        # --- STRATEGY 1: PDFs — Hybrid text extraction + VLM for images ---
        if ext == 'pdf':
            return await process_pdf_hybrid(
                file_content, filename, user_prompt, api_key, mode=mode, chunk_callback=chunk_callback
            )

        # --- STRATEGY 2: PPTX — Hybrid text/table extraction + VLM for images ---
        elif ext == 'pptx':
            return await process_pptx_hybrid(
                file_content, filename, user_prompt, api_key, mode=mode, chunk_callback=chunk_callback
            )

        # --- STRATEGY 3: STANDALONE IMAGES — Full VLM ---
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            return await process_visual_document(
                file_content, filename, user_prompt, api_key, mode=mode, chunk_callback=chunk_callback
            )

        # --- STRATEGY 4: DATASETS (CSV, EXCEL, SDF) ---
        elif ext in ['csv', 'xlsx', 'xls']:
            return process_spreadsheet(file_content, ext, user_prompt)

        # --- STRATEGY 5: CHEMICAL STRUCTURES (SDF) ---
        elif ext == 'sdf':
            return process_sdf_file(file_content, filename, user_prompt)

        # --- STRATEGY 6: TEXT DOCS (DOCX, MD, TXT) ---
        elif ext in ['docx', 'md', 'txt']:
            return await process_text_document(file_content, ext, user_prompt, api_key)

        else:
            return f"❌ Unsupported file format: {ext}"

    except Exception as e:
        logger.error(f"Smart processing failed for {filename}: {e}")
        return f"Error processing file: {str(e)}"
