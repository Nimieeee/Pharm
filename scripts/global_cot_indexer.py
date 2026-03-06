import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from pathlib import Path

# --- CONFIGURATION ---
CORPUS_PATH = "/Users/mac/Desktop/phhh/distilled_corpus_400k_with_cot-filtered.jsonl"
DB_PATH = str(Path.home() / ".agent_reasoning" / "chroma_db")
COLLECTION_NAME = "cot_reasoning_v1"
MODEL_NAME = "/Users/mac/Desktop/phhh/scripts/model_cache"  # Local model cache
BATCH_SIZE = 100

def main():
    print(f"🚀 Initializing CoT Indexer...")
    
    # 1. Setup Storage
    os.makedirs(DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 2. Load Embedding Model
    print(f"📥 Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # 3. Get or Create Collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # 4. Process JSONL
    print(f"📖 Reading corpus from {CORPUS_PATH}...")
    with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"⚙️  Indexing {total} records in batches of {BATCH_SIZE}...")
    
    for i in range(0, total, BATCH_SIZE):
        batch_lines = lines[i:i + BATCH_SIZE]
        ids = []
        documents = []
        metadatas = []
        
        for j, line in enumerate(batch_lines):
            try:
                data = json.loads(line)
                # We index the PROBLEM (what the user asks)
                # But we store the THINKING and SOLUTION in metadata
                problem_text = data.get("problem", "")
                thinking_text = data.get("thinking", "")
                solution_text = data.get("solution", "")
                
                if not problem_text:
                    continue
                
                doc_id = f"cot_{i + j}"
                ids.append(doc_id)
                documents.append(problem_text)
                metadatas.append({
                    "thinking": thinking_text,
                    "solution": solution_text,
                    "id": data.get("id", doc_id),
                    "difficulty": data.get("difficulty", "unknown")
                })
            except Exception as e:
                print(f"⚠️ Error parsing line {i+j}: {e}")
        
        if documents:
            # Generate embeddings
            embeddings = model.encode(documents).tolist()
            
            # Upsert into Chroma
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
    print(f"✨ Successfully indexed {total} records into {DB_PATH}")

if __name__ == "__main__":
    main()
