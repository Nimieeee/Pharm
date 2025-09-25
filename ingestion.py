# ingestion.py
import io
import os
import re
import uuid
from typing import List, Dict, Optional, Tuple

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

# Optional high-quality pdf extraction
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# tiktoken (optional) for accurate token counts
try:
    import tiktoken
except Exception:
    tiktoken = None


def _read_bytes(file_like) -> bytes:
    """
    Return raw bytes from a Streamlit uploaded file or file-like object.
    """
    # Streamlit's UploadedFile has .getvalue() and .read() depending on object state
    if hasattr(file_like, "getvalue"):
        return file_like.getvalue()
    try:
        file_like.seek(0)
    except Exception:
        pass
    if hasattr(file_like, "read"):
        return file_like.read()
    # if it's already bytes
    if isinstance(file_like, (bytes, bytearray)):
        return bytes(file_like)
    raise ValueError("Unsupported file-like object; couldn't read bytes.")


def extract_text_from_pdf_bytes(raw: bytes) -> str:
    """Extract text from PDF bytes. Tries PyPDF2 first, then pdfplumber as fallback."""
    text_pages = []
    if PdfReader:
        try:
            reader = PdfReader(io.BytesIO(raw))
            # some PyPDF2 versions use .pages
            for page in getattr(reader, "pages", []):
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""
                text_pages.append(page_text)
            text = "\n".join(text_pages)
            # If result is very short and pdfplumber exists, try it
            if (not text.strip()) and pdfplumber:
                raise RuntimeError("PyPDF2 returned empty text — try pdfplumber fallback.")
            return text
        except Exception:
            # fall through to pdfplumber if available
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

    # Last resort: try to decode bytes as text (sometimes PDFs contain extractable text)
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_docx_bytes(raw: bytes) -> str:
    """Extract text from docx bytes using python-docx (if available)."""
    if docx:
        try:
            bio = io.BytesIO(raw)
            document = docx.Document(bio)
            paragraphs = [p.text for p in document.paragraphs]
            return "\n".join(paragraphs)
        except Exception:
            pass
    # fallback: attempt to decode as text
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_html_bytes(raw: bytes) -> str:
    """Extract text from HTML bytes using BeautifulSoup if available."""
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
    # fallback
    # strip tags with regex (crude):
    return re.sub(r"<[^>]+>", "", decoded)


def extract_text_from_file(uploaded_file) -> str:
    """
    Main extraction function for a Streamlit UploadedFile or file-like object.
    Supports: .pdf, .docx, .txt, .md, .html/.htm, other bytes.
    For unknown types, tries to decode bytes as utf-8.
    """
    raw = _read_bytes(uploaded_file)
    name = getattr(uploaded_file, "name", "") or ""
    lower = name.lower()

    # PDF
    if lower.endswith(".pdf") or b"%PDF" in raw[:1024]:
        return extract_text_from_pdf_bytes(raw)

    # DOCX
    if lower.endswith(".docx"):
        return extract_text_from_docx_bytes(raw)

    # HTML
    if lower.endswith(".html") or lower.endswith(".htm"):
        return extract_text_from_html_bytes(raw)

    # Plain text / markdown
    if lower.endswith(".txt") or lower.endswith(".md"):
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    # Fallback: try HTML detection then decode
    text = extract_text_from_html_bytes(raw)
    # if html parsing returned something short, try decode raw bytes
    if len(text) < 20:
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return text or ""

    return text


def extract_text_from_url(url: str, headers: Optional[dict] = None, timeout: int = 10) -> str:
    """
    Fetches a URL and extracts text. Uses requests + BeautifulSoup (if available).
    """
    headers = headers or {
        "User-Agent": "Mozilla/5.0 (compatible; PharmGPT/1.0; +https://example.com)"
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    raw = r.content
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(raw)
    if "html" in content_type or url.lower().endswith((".html", ".htm")):
        return extract_text_from_html_bytes(raw)
    # fallback to decode
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ----------------------------
# Token counting & chunking
# ----------------------------
def _get_encoding_for_model(model_name: str = "text-embedding-3-small"):
    """
    Return a tiktoken encoding object if possible.
    If not available or unknown model, return None.
    """
    if not tiktoken:
        return None
    try:
        # prefer model-specific encoding
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            # fallback to cl100k_base which is used by recent OpenAI models
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """
    Count tokens using tiktoken when available; otherwise approximate.
    Approximation: 1 token ~= 4 characters (very rough).
    """
    enc = _get_encoding_for_model(model)
    if enc:
        return len(enc.encode(text))
    # fallback
    return max(1, int(len(text) / 4))


def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
    model: str = "text-embedding-3-small",
) -> List[str]:
    """
    Token-aware sliding window chunker.
    If tiktoken not available, falls back to simple char-based chunks using rough conversion.
    Returns list of chunk strings.
    """
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
            chunk_tokens = tokens[start:end]
            chunk_text = enc.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end - overlap_tokens
            if start < 0:
                start = 0
        return chunks
    else:
        # fallback to character-based approach
        # approximate conversion: tokens -> chars
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


def chunk_texts(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    prefer_token_chunking: bool = True,
    model: str = "text-embedding-3-small",
) -> List[str]:
    """
    Backwards-compatible char-based chunker (keeps older API).
    If prefer_token_chunking and tiktoken is available, we use token-based chunking with
    chunk_size interpreted as *tokens*; otherwise chunk_size is characters.
    """
    if prefer_token_chunking and tiktoken:
        return chunk_text_by_tokens(text, max_tokens=chunk_size, overlap_tokens=chunk_overlap, model=model)
    # Character-based fallback (old behaviour)
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


# ----------------------------
# Helpers to create upsert-ready docs
# ----------------------------
def create_document_chunks(
    *,
    source_name: str,
    text: str,
    id_prefix: Optional[str] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    prefer_token_chunking: bool = True,
    model_for_tokenization: str = "text-embedding-3-small",
) -> List[Dict]:
    """
    Given a large text and a source name (filename or URL), returns a list of dicts ready for upsert:
    [
      {"id": <uuid or provided>, "source": source_name, "content": chunk_text, "metadata": {...}},
      ...
    ]
    - id_prefix: optional string prefix (useful to tie chunks to upload)
    - chunk_size & chunk_overlap: if tiktoken available and prefer_token_chunking True, treated as tokens;
      otherwise treated as characters.
    """
    chunks = chunk_texts(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        prefer_token_chunking=prefer_token_chunking,
        model=model_for_tokenization,
    )
    docs = []
    for i, chunk in enumerate(chunks):
        doc_id = f"{id_prefix}-{i}" if id_prefix else str(uuid.uuid4())
        docs.append(
            {
                "id": doc_id,
                "source": source_name,
                "content": chunk,
                "metadata": {"chunk_index": i, "source": source_name},
            }
        )
    return docs


def create_documents_from_uploads(
    uploads: List,
    *,
    id_prefix_base: Optional[str] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    prefer_token_chunking: bool = True,
    model_for_tokenization: str = "text-embedding-3-small",
) -> List[Dict]:
    """
    Helper to accept a list of uploaded files (Streamlit UploadedFile objects) and return a
    list of docs ready for upsert.
    """
    all_docs = []
    for up in uploads:
        raw_name = getattr(up, "name", None) or "uploaded"
        prefix = f"{id_prefix_base or raw_name}-{uuid.uuid4()}"
        text = extract_text_from_file(up)
        docs = create_document_chunks(
            source_name=raw_name,
            text=text,
            id_prefix=prefix,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            prefer_token_chunking=prefer_token_chunking,
            model_for_tokenization=model_for_tokenization,
        )
        all_docs.extend(docs)
    return all_docs


# ----------------------------
# Example usage (commented)
# ----------------------------
# from ingestion import create_documents_from_uploads, extract_text_from_url
# uploads = st.file_uploader(..., accept_multiple_files=True)
# docs = create_documents_from_uploads(uploads, chunk_size=500, chunk_overlap=50)
# upsert_documents(docs, supabase_client=supabase)
#
# or from URL:
# txt = extract_text_from_url("https://example.com/article")
# docs = create_document_chunks(source_name="example.com/article", text=txt)
# upsert_documents(docs, supabase_client=supabase)
