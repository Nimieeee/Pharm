"""
Chat API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.chat import ChatService
from app.services.enhanced_rag import EnhancedRAGService
from app.models.user import User
from app.models.conversation import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationWithMessages,
    Message, MessageCreate
)
from app.models.document import DocumentUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request/Response Models ---

class MermaidRepairRequest(BaseModel):
    """Request model for Mermaid AI repair endpoint"""
    code: str
    error: str


class PubMedSearchRequest(BaseModel):
    """Request model for PubMed search"""
    query: str
    max_results: int = 20


class PubMedSearchResponse(BaseModel):
    """Response model for PubMed search"""
    query: str
    count: int
    results: List[Dict[str, Any]]


class DDIRequest(BaseModel):
    """Request model for drug-drug interaction check"""
    drug_a: str
    drug_b: str


class PolypharmacyRequest(BaseModel):
    """Request model for multi-drug interaction check"""
    drugs: List[str]


def get_chat_service(db: Client = Depends(get_db)) -> ChatService:
    """Get chat service"""
    return ChatService(db)


def get_rag_service(db: Client = Depends(get_db)) -> EnhancedRAGService:
    """Get Enhanced RAG service with LangChain"""
    return EnhancedRAGService(db)


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get all conversations for the current user
    
    Returns list of conversations ordered by last activity
    """
    import time
    start = time.time()
    try:
        print(f"📋 GET /conversations - user={current_user.id}")
        conversations = await chat_service.get_user_conversations(current_user)
        elapsed = (time.time() - start) * 1000
        print(f"✅ GET /conversations: {elapsed:.0f}ms, count={len(conversations)}")
        return conversations
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"❌ GET /conversations failed after {elapsed:.0f}ms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )



@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Create a new conversation
    
    - **title**: Conversation title
    """
    try:
        conversation = await chat_service.create_conversation(conversation_data, current_user)
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a specific conversation with all messages
    
    Returns conversation details and message history
    """
    try:
        conversation = await chat_service.get_conversation_with_messages(
            conversation_id, current_user
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.patch("/conversations/{conversation_id}", response_model=Conversation)
async def patch_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Partially update a conversation (title, pin, archive)
    """
    try:
        conversation = await chat_service.update_conversation(
            conversation_id, conversation_data, current_user
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update a conversation
    """
    return await patch_conversation(conversation_id, conversation_data, current_user, chat_service)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation and all its data
    
    This will permanently delete the conversation, all messages, and uploaded documents
    """
    try:
        success = await chat_service.delete_conversation(conversation_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/clone", response_model=Conversation)
async def clone_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Clone a conversation
    """
    try:
        conversation = await chat_service.clone_conversation(conversation_id, current_user)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone conversation: {str(e)}"
        )


@router.patch("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: UUID,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update the content of an existing message
    """
    try:
        # Update the message content
        updated = await chat_service.update_message_content(message_id, content, current_user)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or update failed"
            )
        
        # Fetch and return the updated message
        updated_message = await chat_service.get_message_by_id(message_id, current_user)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found after update"
            )
        
        return updated_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_message endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update message: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=Message)
async def add_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Add a message to a conversation
    
    - **role**: Message role ('user' or 'assistant')
    - **content**: Message content
    - **metadata**: Optional metadata
    """
    try:
        # Ensure conversation_id matches
        message_data.conversation_id = conversation_id
        
        message = await chat_service.add_message(message_data, current_user)
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(
    conversation_id: UUID,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get messages for a conversation
    
    - **limit**: Optional limit on number of messages to return
    """
    import time
    start = time.time()
    try:
        print(f"📋 GET /messages - conv={conversation_id}, user={current_user.id}")
        messages = await chat_service.get_conversation_messages(
            conversation_id, current_user, limit
        )
        elapsed = (time.time() - start) * 1000
        print(f"✅ GET /messages: {elapsed:.0f}ms, count={len(messages)}")
        return messages
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"❌ GET /messages failed after {elapsed:.0f}ms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    conversation_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    mode: str = Form("detailed"),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Upload a document to a conversation

    Supported file types: PDF, TXT, MD, DOCX, PPTX, XLSX, CSV, SDF, MOL, PNG, JPG, JPEG, GIF, BMP, WEBP
    """
    import logging
    import sys
    import base64
    logger = logging.getLogger(__name__)

    print(f"DEBUG: MARKER - ENTERING UPLOAD_DOCUMENT", flush=True)
    sys.stdout.flush()
    try:
        print(f"📤 Document upload started: {file.filename}", flush=True)
    except Exception as e:
        print(f"ERROR PRINTING FILENAME: {e}", flush=True)

    try:
        # Check if conversation exists and belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Validate file type - use RAG service's supported formats
        supported_formats = rag_service.document_loader.get_supported_formats()
        allowed_extensions = {fmt.lstrip('.') for fmt in supported_formats}
        file_extension = file.filename.lower().split('.')[-1] if file.filename else ''

        print(f"📄 File type: {file_extension}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")

        if file_extension not in allowed_extensions:
            print(f"❌ Unsupported file type: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Read file content
        print(f"📖 Reading file content...")
        file_content = await file.read()
        print(f"✅ File read: {len(file_content)} bytes")

        if len(file_content) == 0:
            print(f"❌ Empty file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )

        # Create image analyzer function (injected to avoid circular dependency)
        async def image_analyzer(image_bytes: bytes) -> str:
            """Local image analyzer to avoid circular import with AIService"""
            try:
                from app.services.ai import AIService
                ai_service_temp = AIService(chat_service.db)
                b64_str = base64.b64encode(image_bytes).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{b64_str}"
                return await ai_service_temp.analyze_image(data_url)
            except Exception as e:
                logger.error(f"Image analysis failed: {e}")
                return ""

        # Define cancellation check
        async def check_cancellation() -> bool:
            return await request.is_disconnected()

        # Process file WITH image analyzer injected
        print(f"⚙️  Processing file with RAG service...")
        result = await rag_service.process_uploaded_file(
            file_content,
            file.filename,
            conversation_id,
            current_user.id,
            user_prompt=prompt,
            mode=mode,
            cancellation_check=check_cancellation,
            image_analyzer=image_analyzer  # Injected dependency
        )
        
        print(f"✅ Upload complete: {result.chunk_count} chunks processed")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}/documents")
async def delete_conversation_documents(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Delete all documents from a conversation
    """
    try:
        # Check if conversation exists and belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete documents
        success = await rag_service.delete_conversation_documents(
            conversation_id, current_user.id
        )
        
        if success:
            return {"message": "Documents deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete documents"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/branched-messages")
async def get_branched_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get all messages, responses (branches), and active selections for a conversation.
    """
    try:
        # Check if conversation exists
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        return await chat_service.get_branched_messages(conversation_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branched messages: {str(e)}"
        )


@router.post("/messages/{message_id}/responses")
async def create_response_branch(
    message_id: UUID,
    content: str = Form(...),
    model_used: Optional[str] = Form(None),
    token_count: Optional[int] = Form(None),
    metadata: Optional[str] = Form("{}"),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Create a new assistant response branch for a user message
    """
    try:
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        response = await chat_service.create_response_branch(
            user_message_id=message_id,
            content=content,
            model_used=model_used,
            token_count=token_count,
            metadata=metadata_dict
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or creation failed"
            )
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create response branch: {str(e)}"
        )


@router.patch("/messages/{message_id}/branch")
async def set_active_branch(
    message_id: UUID,
    response_id: str = Form(...),
    conversation_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Set the active branch for a user message
    """
    try:
        success = await chat_service.set_active_branch(
            conversation_id=conversation_id,
            user_message_id=str(message_id),
            response_id=response_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to set active branch"
            )
            
        return {"success": True, "message_id": str(message_id), "active_response_id": response_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set active branch: {str(e)}"
        )


@router.delete("/responses/{response_id}")
async def delete_response_branch(
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete an assistant response branch
    """
    try:
        success = await chat_service.delete_response_branch(response_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response branch not found or could not be deleted"
            )

        return {"success": True, "message": "Response branch deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete response branch: {str(e)}"
        )


@router.post("/mermaid/repair")
async def repair_mermaid(
    request: MermaidRepairRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI-powered Mermaid syntax repair.

    When regex-based auto-correction fails, this endpoint uses AI to intelligently
    fix complex Mermaid syntax errors.

    - **code**: Broken Mermaid code
    - **error**: Error message from Mermaid renderer
    - Returns: Repaired Mermaid code
    """
    try:
        from app.services.ai import AIService
        from app.core.database import get_db

        db = get_db()
        ai_service = AIService(db)

        repaired_code = await ai_service.repair_mermaid_syntax(
            code=request.code,
            error=request.error
        )

        return {"repaired_code": repaired_code}

    except Exception as e:
        logger.error(f"❌ Mermaid repair failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to repair Mermaid diagram: {str(e)}"
        )


@router.get("/pubmed/search")
async def search_pubmed(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum results"),
    current_user: User = Depends(get_current_user)
):
    """
    Search PubMed for biomedical articles.

    - **query**: Search term (supports MeSH, Boolean operators)
    - **max_results**: Number of results (1-50, default: 20)
    - Returns: List of article metadata with titles, authors, journal, year, DOI
    """
    try:
        from app.services.pubmed_service import pubmed_service

        results = await pubmed_service.search(query, max_results)

        return {
            "query": query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ PubMed search failed for '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PubMed search failed: {str(e)}"
        )


@router.get("/pubmed/article/{pmid}")
async def get_pubmed_article(
    pmid: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get full PubMed article details including abstract.

    - **pmid**: PubMed ID
    - Returns: Full article metadata with abstract
    """
    try:
        from app.services.pubmed_service import pubmed_service

        article = await pubmed_service.get_article(pmid)

        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article {pmid} not found"
            )

        return article

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PubMed article fetch failed for {pmid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch article: {str(e)}"
        )


@router.post("/ddi/check")
async def check_ddi(
    request: DDIRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check for drug-drug interaction between two drugs.

    - **drug_a**: First drug name
    - **drug_b**: Second drug name
    - Returns: Interaction details with severity, mechanism, clinical significance
    """
    try:
        from app.services.ddi_service import ddi_service

        interaction = await ddi_service.check_interaction(
            drug_a=request.drug_a,
            drug_b=request.drug_b
        )

        if not interaction:
            return {
                "drug_a": request.drug_a,
                "drug_b": request.drug_b,
                "interaction_found": False,
                "severity": "Unknown",
                "message": "Could not resolve one or both drugs"
            }

        return interaction

    except Exception as e:
        logger.error(f"❌ DDI check failed for {request.drug_a} + {request.drug_b}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DDI check failed: {str(e)}"
        )


@router.post("/ddi/polypharmacy")
async def check_polypharmacy(
    request: PolypharmacyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check all pairwise interactions for multiple drugs.

    - **drugs**: List of drug names (minimum 2)
    - Returns: All pairwise interactions sorted by severity
    """
    try:
        from app.services.ddi_service import ddi_service

        if len(request.drugs) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 drugs required for interaction check"
            )

        interactions = await ddi_service.check_polypharmacy(request.drugs)

        return {
            "drugs": request.drugs,
            "count": len(interactions),
            "interactions": interactions,
            "summary": {
                "major": sum(1 for i in interactions if i.get("severity") == "Major"),
                "moderate": sum(1 for i in interactions if i.get("severity") == "Moderate"),
                "minor": sum(1 for i in interactions if i.get("severity") == "Minor")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Polypharmacy check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Polypharmacy check failed: {str(e)}"
        )


@router.get("/gwas/lookup/{rsid}")
async def gwas_lookup(
    rsid: str,
    current_user: User = Depends(get_current_user)
):
    """
    Lookup GWAS variant information across multiple databases.

    - **rsid**: dbSNP reference SNP ID (e.g., "rs7903146")
    - Returns: Combined variant data from Ensembl, GWAS Catalog, Open Targets, ClinVar
    """
    try:
        from app.services.gwas_service import gwas_service

        result = await gwas_service.lookup_variant(rsid)

        if not result or not result.get("found"):
            return {
                "rsid": rsid,
                "found": False,
                "message": "No data found for this variant"
            }

        return result

    except Exception as e:
        logger.error(f"❌ GWAS lookup failed for {rsid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GWAS lookup failed: {str(e)}"
        )


@router.post("/pharmgx/report")
async def generate_pharmgx_report(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """
    Generate pharmacogenomic report from genetic data file.

    Accepts 23andMe or AncestryDNA raw data files.
    Returns PGx report with gene analysis and drug recommendations.
    """
    try:
        from app.services.pharmgx_service import pharmgx_service

        # Read file content
        file_content = await file.read()

        # Generate report
        report = await pharmgx_service.generate_report(
            file_content=file_content,
            filename=file.filename or "genetic_data.txt"
        )

        return report

    except Exception as e:
        logger.error(f"❌ PharmGx report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PharmGx report failed: {str(e)}"
        )


@router.post("/pharmgx/drug-lookup")
async def pharmgx_drug_lookup(
    drug_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Quick PGx lookup for a specific drug.

    - **drug_name**: Drug to check
    - **file**: Genetic data file
    - Returns: Drug-specific guidance based on genotype
    """
    try:
        from app.services.pharmgx_service import pharmgx_service

        file_content = await file.read()

        result = await pharmgx_service.single_drug_lookup(
            file_content=file_content,
            filename=file.filename or "genetic_data.txt",
            drug_name=drug_name
        )

        return result

    except Exception as e:
        logger.error(f"❌ PharmGx drug lookup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drug lookup failed: {str(e)}"
        )