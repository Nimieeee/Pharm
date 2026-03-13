import asyncio
from uuid import UUID
import os

from app.core.config import settings
from supabase import create_client
from app.services.enhanced_rag import EnhancedRAGService

async def test_rag():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    db = create_client(url, key)
    
    rag = EnhancedRAGService(db)
    
    # We found these from DB
    cid = UUID('4b8ffd6d-a74a-4961-93da-ae6bd0edda92')
    uid = UUID('cf9127ef-0f3e-4082-a261-fdd82e11cedc')
    
    context = await rag.get_conversation_context("Explain the document", cid, uid)
    print("CONTEXT LENGTH:", len(context))
    print("CONTEXT:", context[:200])

if __name__ == "__main__":
    asyncio.run(test_rag())
