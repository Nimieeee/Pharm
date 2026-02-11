#!/usr/bin/env python3
"""Check document chunks in database"""
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

# Check recent chunks
print("=== CHECKING RECENT DOCUMENT CHUNKS ===\n")
result = db.table('document_chunks').select('id, conversation_id, content, embedding, metadata, created_at').order('created_at', desc=True).limit(5).execute()

if not result.data:
    print("❌ NO CHUNKS FOUND IN DATABASE")
    sys.exit(1)

print(f"✅ Found {len(result.data)} recent chunks\n")

for i, chunk in enumerate(result.data, 1):
    print(f"--- CHUNK {i} ---")
    print(f"ID: {chunk['id']}")
    print(f"Conversation: {chunk['conversation_id']}")
    print(f"Content length: {len(chunk['content']) if chunk['content'] else 0} chars")
    print(f"Content preview: {chunk['content'][:100] if chunk['content'] else 'EMPTY'}...")
    
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

# Check if there are any chunks with NULL embeddings
print("\n=== CHECKING FOR NULL EMBEDDINGS ===")
null_check = db.table('document_chunks').select('id, conversation_id, metadata').is_('embedding', 'null').limit(10).execute()

if null_check.data:
    print(f"⚠️  Found {len(null_check.data)} chunks with NULL embeddings:")
    for chunk in null_check.data:
        print(f"  - ID: {chunk['id']}, Conv: {chunk['conversation_id']}, File: {chunk.get('metadata', {}).get('filename', 'N/A')}")
else:
    print("✅ All chunks have embeddings")
