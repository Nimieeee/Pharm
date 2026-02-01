from docx import Document
import io

def process_text_document(content: bytes, ext: str, user_prompt: str):
    text = ""
    try:
        if ext == 'docx':
            doc = Document(io.BytesIO(content))
            # Extract text + tables
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            tables_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    # Simple markdown table representation
                    tables_text.append(" | ".join(row_data))
            
            text_content = "\n\n".join(paragraphs)
            if tables_text:
                text_content += "\n\n--- Tables ---\n" + "\n".join(tables_text)
            text = text_content
        else:
            # MD, TXT
            text = content.decode('utf-8', errors='ignore')
            
        # Note: We append the user prompt to the TOP so the RAG system knows context
        return f"User Context: {user_prompt}\n\nDocument Content:\n{text}"
    except Exception as e:
        return f"Error processing text document: {str(e)}"
