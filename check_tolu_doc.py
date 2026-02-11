#!/usr/bin/env python3
"""Check tolu-result.docx chunks"""
import os
import sys

# Read Supabase credentials from .env
supabase_url = None
supabase_key = None

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_URL='):
            supabase_url = line.split('=', 1)[1].strip()
        elif line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            supabase_key = line.split('=', 1)[1].strip()

if not supabase_url or not supabase_key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

from supabase import create_client

db = create_client(supabase_url, supabase_key)

# Search for tolu-result.docx chunks
print("=== SEARCHING FOR tolu-result.docx CHUNKS ===\n")

# Use filter on metadata
result = db.table('document_chunks').select('id, conversation_id, content, embedding, metadata, created_at').execute()

tolu_chunks = []
for chunk in result.data:
    metadata = chunk.get('metadata', {})
    if 'tolu' in metadata.get('filename', '').lower():
        tolu_chunks.append(chunk)

if not tolu_chunks:
    print("❌ NO CHUNKS FOUND FOR tolu-result.docx")
    print("\nSearching for any recent .docx files...")
    
    docx_chunks = []
    for chunk in result.data:
        metadata = chunk.get('metadata', {})
        filename = metadata.get('filename', '')
        if filename.endswith('.docx'):
            docx_chunks.append(chunk)
    
    if docx_chunks:
        print(f"\n✅ Found {len(docx_chunks)} .docx chunks:")
        for chunk in docx_chunks[:5]:
            print(f"  - {chunk.get('metadata', {}).get('filename', 'N/A')} (Conv: {chunk['conversation_id'][:8]}...)")
    else:
        print("❌ No .docx files found at all")
    
    sys.exit(1)

print(f"✅ Found {len(tolu_chunks)} chunks for tolu-result.docx\n")

for i, chunk in enumerate(tolu_chunks[:10], 1):
    print(f"--- CHUNK {i} ---")
    print(f"ID: {chunk['id']}")
    print(f"Conversation: {chunk['conversation_id']}")
    print(f"Content length: {len(chunk['content']) if chunk['content'] else 0} chars")
    print(f"Content preview: {chunk['content'][:150] if chunk['content'] else 'EMPTY'}...")
    
    has_embedding = chunk.get('embedding') is not None
    print(f"Embedding: {'✅ YES' if has_embedding else '❌ NULL'}")
    
    if has_embedding:
        emb_len = len(chunk['embedding']) if isinstance(chunk['embedding'], list) else 0
        print(f"Embedding dimensions: {emb_len}")
    
    metadata = chunk.get('metadata', {})
    print(f"Filename: {metadata.get('filename', 'N/A')}")
    print(f"User ID: {metadata.get('user_id', 'N/A')}")
    print(f"Created: {chunk['created_at']}")
    print()
