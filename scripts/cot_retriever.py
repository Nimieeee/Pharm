import sys
import chromadb
from mistralai import Mistral
from pathlib import Path
import json

# --- CONFIGURATION ---
DB_PATH = str(Path.home() / ".agent_reasoning" / "chroma_db")
COLLECTION_NAME = "cot_reasoning_mistral_v1"
MISTRAL_API_KEY = "uBrKHYN5sBzrvdTYgel7zyNuPVbnhijv"

def retrieve(query, n_results=3):
    """Search for relevant CoT examples in the local ChromaDB."""
    try:
        # 1. Setup Clients
        client = chromadb.PersistentClient(path=DB_PATH)
        mistral = Mistral(api_key=MISTRAL_API_KEY)
        
        # 2. Get Collection
        collection = client.get_collection(name=COLLECTION_NAME)
        
        # 3. Generate Query Embedding
        embeddings_response = mistral.embeddings.create(
            model="mistral-embed",
            inputs=[query]
        )
        query_embedding = embeddings_response.data[0].embedding
        
        # 4. Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    except Exception as e:
        return {"error": str(e)}

def format_output(results):
    """Format the results for agent prompt consumption."""
    if "error" in results:
        return f"Error during retrieval: {results['error']}"
    
    if not results or not results["documents"]:
        return "No relevant reasoning patterns found."
    
    output = []
    output.append("### RELEVANT REASONING PATTERNS FOUND")
    
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        
        output.append(f"\n--- Example {i+1} ---")
        output.append(f"Related Problem: {doc}")
        output.append(f"\nInternal thinking (Process):\n{meta.get('thinking', 'N/A')}")
        output.append(f"\nFinal Solution Summary:\n{meta.get('solution', 'N/A')}")
    
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cot_retriever.py 'your coding problem description'")
        sys.exit(1)
    
    user_query = " ".join(sys.argv[1:])
    raw_results = retrieve(user_query)
    print(format_output(raw_results))
