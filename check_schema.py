#!/usr/bin/env python3
"""Check database schema for embedding dimensions"""
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

# Check the embedding column type by querying a chunk
print("=== CHECKING EMBEDDING COLUMN SCHEMA ===\n")

# Try to get a chunk with embedding to see the structure
result = db.table('document_chunks').select('id, embedding').limit(1).execute()

if result.data and len(result.data) > 0:
    chunk = result.data[0]
    embedding = chunk.get('embedding')
    
    if embedding:
        print(f"✅ Found chunk with embedding")
        print(f"Embedding type: {type(embedding)}")
        print(f"Embedding dimensions: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
    else:
        print("⚠️  Chunk has NULL embedding")
else:
    print("❌ No chunks found in database")

# Check if we can query the schema via RPC
print("\n=== CHECKING DATABASE FUNCTION ===")
try:
    # Try to call the match function with a dummy embedding to see what dimension it expects
    dummy_embedding = [0.0] * 768  # Try 768 first
    result = db.rpc('match_documents_with_user_isolation', {
        'query_embedding': dummy_embedding,
        'query_user_id': '00000000-0000-0000-0000-000000000000',
        'query_conversation_id': '00000000-0000-0000-0000-000000000000',
        'match_threshold': 0.5,
        'match_count': 1
    }).execute()
    print(f"✅ Function accepts 768-dimensional embeddings")
except Exception as e:
    error_msg = str(e)
    if '1024' in error_msg:
        print(f"⚠️  Function expects 1024-dimensional embeddings")
        print(f"Error: {error_msg[:200]}")
    elif '768' in error_msg:
        print(f"✅ Function expects 768-dimensional embeddings (confirmed by error)")
        print(f"Error: {error_msg[:200]}")
    else:
        print(f"❌ Error calling function: {error_msg[:200]}")

# Try 1024
print("\nTrying 1024 dimensions...")
try:
    dummy_embedding = [0.0] * 1024
    result = db.rpc('match_documents_with_user_isolation', {
        'query_embedding': dummy_embedding,
        'query_user_id': '00000000-0000-0000-0000-000000000000',
        'query_conversation_id': '00000000-0000-0000-0000-000000000000',
        'match_threshold': 0.5,
        'match_count': 1
    }).execute()
    print(f"✅ Function accepts 1024-dimensional embeddings")
except Exception as e:
    error_msg = str(e)
    print(f"❌ Function does NOT accept 1024-dimensional embeddings")
    print(f"Error: {error_msg[:200]}")
