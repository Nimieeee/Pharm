# ingestion.py
import io
import re
import uuid
from typing import List, Dict, Optional

import requests

# PDF
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# docx
try:
    import docx
except Exception:
    docx = None

# html
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

# pdfplumber fallback
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# tiktoken (optional)
try:
    import tiktoken
except Exception:
    tiktoken = None


def _read_bytes(file_like) -> bytes:
    if hasattr(file_like, "getvalue"):
        return file_like.getvalue()
    try:
        file_like.seek(0)
    except Exception:
        pass
    if hasattr(file_like, "read"):
        return file_like.read()
    if isinstance(file_like, (bytes, bytearray)):
        return bytes(file_like)
    raise ValueError("Unsupported file-like object; couldn't read bytes.")


def extract_text_from_pdf_bytes(raw: bytes) -> str:
    text_pages = []
    if PdfReader:
        try:
            reader = PdfReader(io.BytesIO(raw))
            for page in getattr(reader, "pages", []):
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""
                text_pages.append(page_text)
            text = "\n".join(text_pages)
            if (not text.strip()) and pdfplumber:
                raise RuntimeError("PyPDF2 returned empty text — try pdfplumber fallback.")
            return text
        except Exception:
            pass

    if pdfplumber:
        try:
            text_pages = []
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for p in pdf.pages:
                    text_pages.append(p.extract_text() or "")
            return "\n".join(text_pages)
        except Exception:
            pass

    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_docx_bytes(raw: bytes) -> str:
    if docx:
        try:
            bio = io.BytesIO(raw)
            document = docx.Document(bio)
            paragraphs = [p.text for p in document.paragraphs]
            return "\n".join(paragraphs)
        except Exception:
            pass
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_html_bytes(raw: bytes) -> str:
    try:
        decoded = raw.decode("utf-8", errors="ignore")
    except Exception:
        decoded = str(raw)
    if BeautifulSoup:
        soup = BeautifulSoup(decoded, "html.parser")
        for s in soup(["script", "style", "img", "input"]):
            s.decompose()
        body = soup.get_text(separator="\n", strip=True)
        return body
    return re.sub(r"<[^>]+>", "", decoded)


def extract_text_from_file(uploaded_file) -> str:
    raw = _read_bytes(uploaded_file)
    name = getattr(uploaded_file, "name", "") or ""
    lower = name.lower()

    if lower.endswith(".pdf") or b"%PDF" in raw[:1024]:
        return extract_text_from_pdf_bytes(raw)
    if lower.endswith(".docx"):
        return extract_text_from_docx_bytes(raw)
    if lower.endswith(".html") or lower.endswith(".htm"):
        return extract_text_from_html_bytes(raw)
    if lower.endswith(".txt") or lower.endswith(".md"):
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    text = extract_text_from_html_bytes(raw)
    if len(text) < 20:
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return text or ""
    return text


def extract_text_from_url(url: str, headers: Optional[dict] = None, timeout: int = 10) -> str:
    headers = headers or {"User-Agent": "Mozilla/5.0 (compatible; PharmGPT/1.0)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    raw = r.content
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(raw)
    if "html" in content_type or url.lower().endswith((".html", ".htm")):
        return extract_text_from_html_bytes(raw)
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# Token-aware chunking (tiktoken if available)
def _get_encoding_for_model(model_name: str = "all-MiniLM-L6-v2"):
    if not tiktoken:
        return None
    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


def chunk_text_by_tokens(text: str, max_tokens: int = 500, overlap_tokens: int = 50, model: str = "all-MiniLM-L6-v2"):
    if not text:
        return []
    enc = _get_encoding_for_model(model)
    if enc:
        tokens = enc.encode(text)
        chunks = []
        start = 0
        n = len(tokens)
        while start < n:
            end = min(start + max_tokens, n)
            chunk_text = enc.decode(tokens[start:end])
            chunks.append(chunk_text)
            start = end - overlap_tokens
            if start < 0:
                start = 0
        return chunks
    else:
        approx_chars_per_token = 4
        max_chars = max_tokens * approx_chars_per_token
        overlap_chars = overlap_tokens * approx_chars_per_token
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + max_chars, text_len)
            chunks.append(text[start:end])
            start = end - overlap_chars
            if start < 0:
                start = 0
        return chunks


def chunk_texts(text: str, chunk_size: int = 1000, chunk_overlap: int = 200, prefer_token_chunking: bool = True, model: str = "all-MiniLM-L6-v2"):
    if prefer_token_chunking and tiktoken:
        return chunk_text_by_tokens(text, max_tokens=chunk_size, overlap_tokens=chunk_overlap, model=model)
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks


def create_document_chunks(source_name: str, text: str, id_prefix: Optional[str] = None, chunk_size: int = 500, chunk_overlap: int = 50, prefer_token_chunking: bool = True, model_for_tokenization: str = "all-MiniLM-L6-v2") -> List[Dict]:
    chunks = chunk_texts(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap, prefer_token_chunking=prefer_token_chunking, model=model_for_tokenization)
    docs = []
    for i, chunk in enumerate(chunks):
        doc_id = f"{id_prefix}-{i}" if id_prefix else str(uuid.uuid4())
        docs.append({
            "id": doc_id,
            "source": source_name,
            "content": chunk,
            "metadata": {"chunk_index": i, "source": source_name},
        })
    return docs


def create_documents_from_uploads(uploads: List, id_prefix_base: Optional[str] = None, chunk_size: int = 500, chunk_overlap: int = 50, prefer_token_chunking: bool = True, model_for_tokenization: str = "all-MiniLM-L6-v2") -> List[Dict]:
    all_docs = []
    for up in uploads:
        raw_name = getattr(up, "name", None) or "uploaded"
        prefix = f"{id_prefix_base or raw_name}-{uuid.uuid4()}"
        text = extract_text_from_file(up)
        docs = create_document_chunks(source_name=raw_name, text=text, id_prefix=prefix, chunk_size=chunk_size, chunk_overlap=chunk_overlap, prefer_token_chunking=prefer_token_chunking, model_for_tokenization=model_for_tokenization)
        all_docs.extend(docs)
    return all_docs
