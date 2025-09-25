# ingestion.py
import io, uuid, re
from typing import List, Dict, Optional
import requests
from sentence_transformers import SentenceTransformer  # not used here directly

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import docx
except Exception:
    docx = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

def _read_bytes(f):
    if hasattr(f, "getvalue"):
        return f.getvalue()
    f.seek(0)
    return f.read()

def extract_text_from_pdf_bytes(raw: bytes) -> str:
    if PdfReader:
        try:
            reader = PdfReader(io.BytesIO(raw))
            pages = []
            for p in reader.pages:
                pages.append(p.extract_text() or "")
            text = "\n".join(pages)
            if text.strip():
                return text
        except Exception:
            pass
    if pdfplumber:
        try:
            import pdfplumber, io
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
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
            return "\n".join([p.text for p in document.paragraphs])
        except Exception:
            pass
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def extract_text_from_html_bytes(raw: bytes) -> str:
    try:
        s = raw.decode("utf-8", errors="ignore")
    except Exception:
        s = str(raw)
    if BeautifulSoup:
        soup = BeautifulSoup(s, "html.parser")
        for x in soup(["script", "style", "img"]):
            x.decompose()
        return soup.get_text(separator="\n", strip=True)
    return re.sub(r"<[^>]+>", "", s)

def extract_text_from_file(uploaded_file) -> str:
    raw = _read_bytes(uploaded_file)
    name = getattr(uploaded_file, "name", "").lower()
    if name.endswith(".pdf") or raw[:4] == b"%PDF":
        return extract_text_from_pdf_bytes(raw)
    if name.endswith(".docx"):
        return extract_text_from_docx_bytes(raw)
    if name.endswith((".html", ".htm")):
        return extract_text_from_html_bytes(raw)
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def chunk_texts(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    if not text:
        return []
    start = 0
    n = len(text)
    chunks = []
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks

def create_document_chunks(source_name: str, text: str, id_prefix: Optional[str] = None, chunk_size=1000, chunk_overlap=200):
    chunks = chunk_texts(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    out = []
    for i, c in enumerate(chunks):
        out.append({"id": f"{id_prefix or source_name}-{i}-{uuid.uuid4().hex[:8]}", "source": source_name, "content": c, "metadata": {"chunk_index": i, "source": source_name}})
    return out

def create_documents_from_uploads(uploads: List, id_prefix_base: Optional[str] = None, chunk_size=1000, chunk_overlap=200):
    all_docs = []
    for up in uploads:
        name = getattr(up, "name", "uploaded")
        raw_text = extract_text_from_file(up)
        prefix = f"{id_prefix_base or name}-{uuid.uuid4().hex[:6]}"
        docs = create_document_chunks(name, raw_text, id_prefix=prefix, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        all_docs.extend(docs)
    return all_docs

def extract_text_from_url(url: str):
    r = requests.get(url, timeout=15, headers={"User-Agent": "PharmGPT/1.0"})
    r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(r.content)
    if "html" in content_type or url.lower().endswith((".html", ".htm")):
        return extract_text_from_html_bytes(r.content)
    return r.text
