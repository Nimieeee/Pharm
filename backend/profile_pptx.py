"""
Profile document processing step-by-step to identify bottlenecks.
Usage: /var/www/pharmgpt-backend/venv/bin/python profile_pptx.py <filepath>
"""
import asyncio, time, os, sys, io, base64, subprocess, tempfile

async def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    if not filepath or not os.path.exists(filepath):
        print(f"Usage: python profile_pptx.py <filepath>"); return

    ext = filepath.rsplit('.', 1)[-1].lower()
    print(f"=== PROFILING: {os.path.basename(filepath)} ({ext}) ===\n", flush=True)
    t_total = time.time()

    # --- STEP 1: Read file ---
    t0 = time.time()
    with open(filepath, "rb") as f:
        content = f.read()
    print(f"[1] File read: {time.time()-t0:.2f}s ({len(content)} bytes)", flush=True)

    # --- STEP 2: Convert to images ---
    from pdf2image import convert_from_bytes, convert_from_path
    from PIL import Image

    t0 = time.time()
    if ext == 'pptx':
        with tempfile.TemporaryDirectory() as td:
            inp = os.path.join(td, "temp.pptx")
            with open(inp, "wb") as f:
                f.write(content)
            t_lo = time.time()
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", inp, "--outdir", td],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120
            )
            print(f"    LibreOffice PPTX->PDF: {time.time()-t_lo:.2f}s", flush=True)
            pdf_path = os.path.join(td, "temp.pdf")
            if not os.path.exists(pdf_path):
                print("ABORT: LibreOffice conversion failed"); return
            t_img = time.time()
            images = convert_from_path(pdf_path, dpi=200, fmt="jpeg", thread_count=4)
            print(f"    pdf2image PDF->Images: {time.time()-t_img:.2f}s", flush=True)
    elif ext == 'pdf':
        images = convert_from_bytes(content, dpi=200, fmt="jpeg", thread_count=4)
    else:
        images = [Image.open(io.BytesIO(content))]

    print(f"[2] Total conversion: {time.time()-t0:.2f}s -> {len(images)} pages", flush=True)
    for i, img in enumerate(images):
        print(f"    Page {i+1}: {img.size[0]}x{img.size[1]}", flush=True)

    # --- STEP 3: Encode images ---
    t0 = time.time()
    encoded = []
    for img in images:
        ic = img.copy()
        if ic.mode != 'RGB':
            ic = ic.convert('RGB')
        max_dim = 1280
        if max(ic.size) > max_dim:
            ic.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        ic.save(buf, format="JPEG", quality=80)
        encoded.append(base64.b64encode(buf.getvalue()).decode('utf-8'))
    print(f"[3] Image encode: {time.time()-t0:.2f}s", flush=True)
    for i, e in enumerate(encoded):
        print(f"    Page {i+1}: {len(e)/1024:.0f} KB", flush=True)

    # --- STEP 4: NVIDIA Vision API (PARALLEL with error handling) ---
    import httpx
    NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_KEY = "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"
    PROMPT = "Transcribe ALL text verbatim. Convert tables to Markdown. Describe charts with data points."

    hdrs = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
    texts = []

    async def call_page(client, idx, b64):
        payload = {
            "model": "mistralai/mistral-large-3-675b-instruct-2512",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}],
            "max_tokens": 2048, "temperature": 0.15
        }
        t = time.time()
        try:
            resp = await client.post(NVIDIA_URL, headers=hdrs, json=payload, timeout=120.0)
            e = time.time() - t
            if resp.status_code == 200:
                c = resp.json()['choices'][0]['message']['content']
                return idx, e, len(c), c
            return idx, e, 0, f"ERROR {resp.status_code}: {resp.text[:100]}"
        except Exception as exc:
            e = time.time() - t
            return idx, e, 0, f"EXCEPTION: {type(exc).__name__}: {exc}"

    t0 = time.time()
    sem = asyncio.Semaphore(2)  # Match production concurrency limit
    async with httpx.AsyncClient() as client:
        async def call_page(idx, b64):
            async with sem:
                payload = {
                    "model": "mistralai/mistral-large-3-675b-instruct-2512",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}],
                    "max_tokens": 2048, "temperature": 0.15
                }
                t = time.time()
                for attempt in range(3):
                    try:
                        resp = await client.post(NVIDIA_URL, headers=hdrs, json=payload, timeout=120.0)
                        e = time.time() - t
                        if resp.status_code == 200:
                            c = resp.json()['choices'][0]['message']['content']
                            return idx, e, len(c), c
                        elif resp.status_code == 429:
                            wait = 2 ** (attempt + 1)
                            print(f"    Page {idx+1}: 429, retrying in {wait}s...", flush=True)
                            await asyncio.sleep(wait)
                            continue
                        return idx, e, 0, f"ERROR {resp.status_code}: {resp.text[:100]}"
                    except Exception as exc:
                        if attempt < 2:
                            await asyncio.sleep(2 ** (attempt + 1))
                            continue
                        e = time.time() - t
                        return idx, e, 0, f"EXCEPTION: {type(exc).__name__}: {exc}"
                return idx, time.time() - t, 0, "Max retries exceeded"

        tasks = [call_page(i, b64) for i, b64 in enumerate(encoded)]
        results = await asyncio.gather(*tasks)

    results.sort(key=lambda x: x[0])
    print(f"[4] Vision API (parallel): {time.time()-t0:.2f}s", flush=True)
    for idx, elapsed, chars, c in results:
        status = f"{chars} chars" if chars > 0 else c[:80]
        print(f"    Page {idx+1}: {elapsed:.2f}s, {status}", flush=True)
        texts.append(c if chars > 0 else "")

    # --- STEP 5: Text splitting + Embedding ---
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

    full_text = "\n\n".join(texts)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    print(f"\n[5] Text split: {len(chunks)} chunks from {len(full_text)} chars", flush=True)

    MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "")
    if not MISTRAL_KEY:
        for ep in [os.path.join(os.path.dirname(filepath), ".env"), "/var/www/pharmgpt-backend/backend/.env"]:
            if os.path.exists(ep):
                for line in open(ep):
                    if line.startswith("MISTRAL_API_KEY="):
                        MISTRAL_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if MISTRAL_KEY: break

    if MISTRAL_KEY:
        t0 = time.time()
        async with httpx.AsyncClient() as client:
            for bs in range(0, len(chunks), 16):
                batch = chunks[bs:bs+16]
                resp = await client.post(
                    "https://api.mistral.ai/v1/embeddings",
                    headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
                    json={"model": "mistral-embed", "input": batch},
                    timeout=30.0
                )
                s = "ok" if resp.status_code == 200 else f"ERR {resp.status_code}"
                print(f"    Embed batch {bs//16+1}: {s}", flush=True)
        print(f"[6] Embedding: {time.time()-t0:.2f}s", flush=True)
    else:
        print("[6] SKIPPED - No MISTRAL_API_KEY", flush=True)

    print(f"\n{'='*50}")
    print(f"TOTAL: {time.time()-t_total:.2f}s", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
