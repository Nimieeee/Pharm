import os
import json
import chromadb
from mistralai import Mistral
from tqdm import tqdm
from pathlib import Path
import time

# --- CONFIGURATION ---
CORPUS_PATH = "/Users/mac/Desktop/phhh/distilled_corpus_400k_with_cot-filtered.jsonl"
DB_PATH = str(Path.home() / ".agent_reasoning" / "chroma_db")
COLLECTION_NAME = "cot_reasoning_mistral_v1"
MISTRAL_API_KEY = "uBrKHYN5sBzrvdTYgel7zyNuPVbnhijv"
BATCH_SIZE = 50  # Smaller batch size for API limits

def main():
    print(f"🚀 Initializing Mistral-Powered CoT Indexer...")
    
    # 1. Setup Storage
    os.makedirs(DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 2. Setup Mistral Client
    mistral = Mistral(api_key=MISTRAL_API_KEY)
    
    # 3. Get or Create Collection
    # Note: Mistral Embeddings are 1024 dimensions
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 4. Process JSONL
    print(f"📖 Reading corpus from {CORPUS_PATH}...")
    with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"⚙️  Indexing {total} records using Mistral Embeddings...")
    
    for i in range(0, total, BATCH_SIZE):
        batch_lines = lines[i:i + BATCH_SIZE]
        ids = []
        documents = []
        metadatas = []
        
        for j, line in enumerate(batch_lines):
            try:
                data = json.loads(line)
                problem_text = data.get("problem", "")
                thinking_text = data.get("thinking", "")
                solution_text = data.get("solution", "")
                
                if not problem_text:
                    continue
                
                doc_id = f"cot_{i + j}"
                ids.append(doc_id)
                # Combine problem and thinking for a richer vector representation
                documents.append(problem_text)
                metadatas.append({
                    "thinking": thinking_text,
                    "solution": solution_text,
                    "original_id": data.get("id", doc_id),
                    "difficulty": data.get("difficulty", "unknown")
                })
            except Exception as e:
                print(f"⚠️ Error parsing line {i+j}: {e}")
        
        if documents:
            try:
                # Generate embeddings using Mistral API
                embeddings_response = mistral.embeddings.create(
                    model="mistral-embed",
                    inputs=documents
                )
                
                embeddings = [e.embedding for e in embeddings_response.data]
                
                # Upsert into Chroma
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"✅ Indexed batch {i//BATCH_SIZE + 1}/{(total//BATCH_SIZE)+1} ({i+len(documents)}/{total})")
                
                # Brief sleep to avoid aggressive rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Mistral API Error at batch {i}: {e}")
                time.sleep(2)  # Backoff on error
        
    print(f"✨ Successfully indexed {total} records into {DB_PATH}")

if __name__ == "__main__":
    main()
