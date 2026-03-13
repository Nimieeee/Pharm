"""
Enhanced RAG Service using LangChain and Mistral Embeddings
Replaces the custom RAG implementation with industry-standard tools
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable, Awaitable
from uuid import UUID
from supabase import Client
from langchain_core.documents import Document

from app.core.config import settings
from app.models.document import DocumentChunk, DocumentUploadResponse
from app.services.embeddings import embeddings_service
from app.services.document_loaders import document_loader, DocumentProcessingError
from app.services.text_splitter import text_splitter
from app.core.logging_config import RAGLogger

logger = logging.getLogger(__name__)
rag_logger = RAGLogger(__name__)


class EnhancedRAGService:
    """Enhanced RAG service using LangChain document processing and Mistral embeddings"""
    
    def __init__(self, db: Client):
        self.db = db
        self.embeddings_service = embeddings_service
        self.document_loader = document_loader
        self.text_splitter = text_splitter
        
        logger.info("✅ Enhanced RAG service initialized with LangChain and Mistral embeddings")
    
    async def process_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        conversation_id: UUID,
        user_id: UUID,
        user_prompt: Optional[str] = None,
        mode: str = "detailed",
        cancellation_check: Optional[Callable[[], Awaitable[bool]]] = None,
        image_analyzer: Optional[Callable[[bytes], Awaitable[str]]] = None  # Injected dependency
    ) -> DocumentUploadResponse:
        """
        Process uploaded file using LangChain loaders and Mistral embeddings
        OPTIMIZED: Uses batch embedding generation and bulk database inserts

        Args:
            file_content: Raw file bytes
            filename: Original filename
            conversation_id: Conversation UUID
            user_id: User UUID
            image_analyzer: Optional callable for image analysis (injected to avoid circular dependency)

        Returns:
            DocumentUploadResponse with processing results
        """
        start_time = time.time()
        processing_errors = []
        processing_warnings = []

        # Collect file information
        from pathlib import Path
        file_extension = Path(filename).suffix.lower()
        file_size = len(file_content)
        file_info = {
            "filename": filename,
            "format": file_extension,
            "size_bytes": file_size,
            "content_length": 0,  # Will be updated after extraction
            "encoding": None  # Will be updated if applicable
        }

        try:
            logger.info(
                f"📤 Processing uploaded file: {filename} ({file_size} bytes) for user {user_id}",
                extra={
                    'operation': 'file_upload',
                    'document_name': filename,
                    'file_size': file_size,
                    'file_type': file_extension,
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id)
                }
            )

            # Check if file format is supported
            if not self.document_loader.is_supported_format(filename):
                return DocumentUploadResponse(
                    success=False,
                    message=f"Unsupported file format. Supported formats: {', '.join(self.document_loader.get_supported_formats())}",
                    chunk_count=0,
                    file_info=file_info
                )

            # Load document using LangChain loaders
            try:
                # Use injected image analyzer if provided, otherwise create a simple one
                if image_analyzer is None:
                    # No image analyzer provided - images will be skipped or handled differently
                    logger.warning(f"⚠️  No image analyzer provided for {filename}, images will not be analyzed")
                    image_analyzer_func = None
                else:
                    image_analyzer_func = image_analyzer

                # NOTE: We disabled streaming ingestion callback to support BATCH processing
                # Batch processing yields better total throughput than streaming 1-by-1
                logger.info(f"📥 Starting document load for {filename}...")
                documents = await self.document_loader.load_document(
                    file_content=file_content,
                    filename=filename,
                    additional_metadata={
                        "user_id": str(user_id),
                        "conversation_id": str(conversation_id)
                    },
                    image_analyzer=image_analyzer_func,
                    user_prompt=user_prompt,
                    mode=mode,
                    chunk_callback=None # Disable callback for batch mode
                )
                logger.info(f"📄 Document loader returned {len(documents)} documents for {filename}")

                # Debug: Log document content preview
                if documents:
                    for i, doc in enumerate(documents[:3]):  # Log first 3 docs
                        preview = doc.page_content[:200].replace('\n', ' ') if doc.page_content else "[EMPTY]"
                        logger.info(f"   Doc {i}: {len(doc.page_content)} chars - Preview: {preview}...")
            except DocumentProcessingError as e:
                # Use structured error information from DocumentProcessingError
                logger.error(
                    f"❌ Document processing error for {filename}: "
                    f"category={e.error_category}, is_user_error={e.is_user_error}, "
                    f"details={e.details}"
                )
                return DocumentUploadResponse(
                    success=False,
                    message=e.message,
                    chunk_count=0,
                    errors=[e.message],
                    processing_time=time.time() - start_time
                )
            
            if not documents:
                return DocumentUploadResponse(
                    success=False,
                    message=f"No content could be extracted from {filename}",
                    chunk_count=0,
                    file_info=file_info
                )
            
            # Update file_info with content length and encoding from documents
            total_content_length = sum(len(doc.page_content) for doc in documents)
            file_info["content_length"] = total_content_length
            
            # Extract encoding from document metadata if available
            if documents and documents[0].metadata.get("encoding"):
                file_info["encoding"] = documents[0].metadata.get("encoding")
            
            # DEBUG: Log content preview to verify extraction quality
            if documents:
                preview_len = 500
                preview_text = documents[0].page_content[:preview_len].replace('\n', ' ')
                logger.info(f"📄 Content Preview for {filename}: {preview_text}...")
            
            # Validate document content with enhanced error messages
            logger.info(f"🔍 Validating document content for {filename}...")
            validation_result = await self.document_loader.validate_document_content(
                documents=documents,
                filename=filename,
                file_type=file_extension
            )
            logger.info(f"🔍 Validation result: {validation_result}")
            if not validation_result["valid"]:
                logger.error(f"❌ Document validation failed for {filename}: {validation_result.get('error')}")
                return DocumentUploadResponse(
                    success=False,
                    message=validation_result.get("error", "Document validation failed"),
                    chunk_count=0,
                    file_info=file_info
                )
            logger.info(f"✅ Document validation passed for {filename}")
            
            # Collect validation warnings
            for warning in validation_result.get("warnings", []):
                logger.warning(f"⚠️  Document validation warning: {warning}")
                processing_warnings.append(warning)
            
            # Split documents into chunks using LangChain text splitter
            chunk_start_time = time.time()
            logger.info(f"✂️  Splitting {len(documents)} documents into chunks...")
            chunks = self.text_splitter.split_documents(documents)
            chunk_duration = time.time() - chunk_start_time

            logger.info(f"✂️  Text splitter returned {len(chunks)} chunks from {filename} ({chunk_duration:.2f}s)")

            if not chunks:
                logger.error(f"❌ No chunks generated from {filename}")
                # Debug: Log why no chunks were generated
                for i, doc in enumerate(documents):
                    logger.warning(f"   Doc {i}: {len(doc.page_content)} chars, metadata: {doc.metadata}")
                return DocumentUploadResponse(
                    success=False,
                    message=f"No chunks could be generated from {filename}",
                    chunk_count=0,
                    file_info=file_info
                )
            
            logger.info(
                f"✂️  Generated {len(chunks)} chunks from {filename} ({chunk_duration:.2f}s)",
                extra={
                    'operation': 'chunk_generation',
                    'document_name': filename,
                    'chunk_count': len(chunks),
                    'duration': chunk_duration * 1000
                }
            )
            
            # ==================================================================================
            # OPTIMIZED BATCH PROCESSING START
            # ==================================================================================
            
            # 1. Prepare texts for batch embedding
            chunk_texts = [chunk.page_content for chunk in chunks]
            
            embedding_start_time = time.time()
            logger.info(f"🧠 Generating embeddings for {len(chunks)} chunks in BATCH mode...")
            
            # Check for cancellation before expensive API call
            if cancellation_check and await cancellation_check():
                logger.warning(f"🚫 Upload cancelled by user before embedding: {filename}")
                return DocumentUploadResponse(success=False, message="Upload cancelled", chunk_count=0)
            
            # 2. Call Batch API
            # This is the key optimization: 1 API call per 16 chunks instead of 16 API calls
            logger.info(f"🧠 Starting batch embedding generation for {len(chunk_texts)} texts...")
            embeddings = await self.embeddings_service.generate_embeddings_batch(chunk_texts)
            embedding_duration = time.time() - embedding_start_time
            valid_embeddings_count = sum(1 for e in embeddings if e is not None)

            logger.info(
                f"✅ Generated {valid_embeddings_count}/{len(chunks)} embeddings in {embedding_duration:.2f}s",
                extra={'operation': 'batch_embedding', 'duration': embedding_duration*1000}
            )

            # Debug: Log embedding failures
            if valid_embeddings_count < len(chunks):
                for i, emb in enumerate(embeddings):
                    if emb is None:
                        logger.warning(f"   Embedding {i} failed - text preview: {chunk_texts[i][:100]}...")

            if valid_embeddings_count == 0:
                 logger.error(f"❌ ALL embeddings failed for {filename}")
                 return DocumentUploadResponse(
                    success=False,
                    message=f"Failed to generate embeddings for file {filename}",
                    chunk_count=0,
                    file_info=file_info
                )

            # 3. Prepare Bulk Insert Data
            bulk_data = []
            success_count = 0
            failed_count = 0
            
            expected_dims = settings.EMBEDDING_DIMENSIONS
            current_timestamp = time.time()
            
            for i, chunk in enumerate(chunks):
                embedding = embeddings[i]
                
                if not embedding:
                    processing_errors.append(f"Failed to generate embedding for chunk {i}")
                    failed_count += 1
                    continue
                
                if len(embedding) != expected_dims:
                    processing_errors.append(f"Invalid embedding dimensions for chunk {i}: {len(embedding)}")
                    failed_count += 1
                    continue

                # Prepare enhanced metadata
                metadata = chunk.metadata.copy()
                metadata.update({
                    "filename": filename,
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "embedding_model": settings.EMBEDDING_PROVIDER,
                    "embedding_dimensions": expected_dims,
                    "processing_timestamp": current_timestamp,
                    "chunk_length": len(chunk.page_content),
                    "langchain_processed": True
                })
                
                chunk_data = {
                    "conversation_id": str(conversation_id),
                    "user_id": str(user_id),
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "metadata": metadata
                }
                bulk_data.append(chunk_data)
                success_count += 1
            
            # 4. Perform Bulk Insert
            storage_start_time = time.time()
            if bulk_data:
                try:
                    # Check cancellation before insert
                    if cancellation_check and await cancellation_check():
                        logger.warning(f"🚫 Upload cancelled by user before DB insert: {filename}")
                        return DocumentUploadResponse(success=False, message="Upload cancelled", chunk_count=0)
                        
                    logger.info(f"💾 Bulk inserting {len(bulk_data)} chunks into database...")
                    
                    # Supabase/PostgREST supports list of dicts for bulk insert
                    # We might need to chunk the insert if it's too large (e.g. > 1000 items)
                    BATCH_INSERT_SIZE = 100
                    
                    for i in range(0, len(bulk_data), BATCH_INSERT_SIZE):
                        batch = bulk_data[i : i + BATCH_INSERT_SIZE]
                        result = self.db.table("document_chunks").insert(batch).execute()
                        if not result.data:
                            logger.error(f"❌ Batch insert failed for batch starting at index {i}")
                            # We count these as failed for reporting but continue trying others
                            # In reality transaction might rollback depending on RPC, but direct insert is per-request
                        
                except Exception as e:
                    logger.error(f"❌ Bulk insert failed: {e}")
                    raise e
            
            storage_duration = time.time() - storage_start_time
            processing_time = time.time() - start_time
            
            # Log final statistics
            logger.info(
                f"✅ File processing complete: {success_count}/{len(chunks)} chunks successful "
                f"({processing_time:.2f}s total)",
                extra={
                    'operation': 'file_upload',
                    'document_name': filename,
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'chunk_count': success_count,
                    'failed_count': failed_count,
                    'duration': processing_time * 1000
                }
            )
            
            # Use RAGLogger for comprehensive statistics
            rag_logger.log_document_processing(
                operation='file_upload',
                filename=filename,
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                duration=processing_time,
                chunk_count=success_count,
                file_size=file_size,
                success=(success_count > 0)
            )
            
            if success_count > 0:
                message = f"Successfully processed {success_count} chunks from {filename}"
                return DocumentUploadResponse(
                    success=True,
                    message=message,
                    chunk_count=success_count,
                    processing_time=processing_time,
                    errors=processing_errors if processing_errors else None,
                    warnings=processing_warnings if processing_warnings else None,
                    file_info=file_info
                )
            else:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Failed to process any chunks from {filename}",
                    chunk_count=0,
                    processing_time=processing_time,
                    errors=processing_errors,
                    file_info=file_info
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unexpected error processing {filename}: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            
            return DocumentUploadResponse(
                success=False,
                message=error_msg,
                chunk_count=0,
                processing_time=processing_time,
                errors=[error_msg],
                file_info=file_info
            )


    
    async def store_text_as_memory(
        self,
        text: str,
        conversation_id: UUID,
        user_id: UUID,
        source: str = "system_memory",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Store a text block (like image analysis) as a persistent memory chunk in the vector DB.
        """
        try:
            from langchain_core.documents import Document
            
            # Create a document
            doc = Document(
                page_content=text,
                metadata={
                    "source": source,
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "created_at": time.time(),
                    **(metadata or {})
                }
            )
            
            # Use internal chunk storage logic
            return await self._process_and_store_chunk(
                chunk=doc,
                filename=source,
                conversation_id=conversation_id,
                user_id=user_id,
                chunk_index=int(time.time()), # Use timestamp as unique index
            )
        except Exception as e:
            logger.error(f"❌ Failed to store text memory: {e}")
            return False

    async def _process_and_store_chunk(
        self, 
        chunk: Document, 
        filename: str, 
        conversation_id: UUID, 
        user_id: UUID,
        chunk_index: int
    ) -> bool:
        """Process a single chunk and store it in the database"""
        try:
            # Check if this is an image document
            is_image = chunk.metadata.get("file_type") == "image"
            image_path = chunk.metadata.get("image_path")
            
            # Generate embedding
            # Mistral embeddings are text-only for now
            if is_image:
                 logger.warning(f"⚠️  Image embedding not supported by Mistral, using placeholder for {filename}")
                 # For images we might want to use a vision model to describe it first (via smart loader)
                 # But at this chunk storage level, we just store text content
                 embedding = await self.embeddings_service.generate_embedding(chunk.page_content)
            else:
                # Generate text embedding
                embedding = await self.embeddings_service.generate_embedding(chunk.page_content)
            
            if not embedding:
                logger.error(f"❌ Failed to generate embedding for chunk {chunk_index}")
                return False
            
            # Validate embedding dimensions
            expected_dims = settings.EMBEDDING_DIMENSIONS
            if len(embedding) != expected_dims:
                logger.error(
                    f"❌ Invalid embedding dimensions: {len(embedding)} "
                    f"(expected {expected_dims})"
                )
                return False
            
            # Prepare enhanced metadata
            metadata = chunk.metadata.copy()
            metadata.update({
                "filename": filename,
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "embedding_model": settings.EMBEDDING_PROVIDER,
                "embedding_dimensions": expected_dims,
                "processing_timestamp": time.time(),
                "chunk_length": len(chunk.page_content),
                "langchain_processed": True
            })
            
            # Store in database (embedding_version stored in metadata)
            chunk_data = {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "content": chunk.page_content,
                "embedding": embedding,
                "metadata": metadata
            }
            
            # DEBUG: Print payload details
            print(f"DEBUG: Inserting Chunk {chunk_index}")
            print(f" - Content Len: {len(chunk.page_content)}")
            print(f" - Embedding Len: {len(embedding)}")
            print(f" - Metadata: {metadata}")
            
            result = self.db.table("document_chunks").insert(chunk_data).execute()
            
            # DEBUG: Print Result
            print(f"DEBUG: Insert Result: {result}")
            
            if result.data and len(result.data) > 0:
                logger.debug(f"✅ Stored chunk {chunk_index} for {filename}")
                return True
            else:
                logger.error(f"❌ Database insert failed for chunk {chunk_index}")
                # DEBUG print
                if hasattr(result, 'error'):
                    print(f"ERROR DETAILS: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing chunk {chunk_index}: {e}")
            return False
    
    async def search_similar_chunks(
        self, 
        query: str, 
        conversation_id: UUID, 
        user_id: UUID, 
        max_results: int = 10,
        similarity_threshold: float = 0.1
    ) -> List[DocumentChunk]:
        """
        Search for similar document chunks using Mistral embeddings and pgvector
        
        Args:
            query: Search query
            conversation_id: Conversation UUID
            user_id: User UUID
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score (0.1 default for better recall)
            
        Returns:
            List of similar document chunks
        """
        start_time = time.time()
        query_length = len(query)
        
        try:
            logger.info(
                f"🔍 Searching for similar chunks: '{query[:50]}...' (threshold: {similarity_threshold})",
                extra={
                    'operation': 'similarity_search',
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'query_length': query_length,
                    'max_results': max_results,
                    'similarity_threshold': similarity_threshold
                }
            )
            
            # OPTIMIZATION: Check if conversation has documents before paying for embedding
            # This saves ~500ms for "New Chat" or chat without docs
            try:
                # Use a simple limited select instead of count+head (which has issues)
                check = self.db.table("document_chunks").select("id")\
                    .eq("conversation_id", str(conversation_id)).limit(1).execute()
                
                if not check.data or len(check.data) == 0:
                    logger.info("⏩ Skipping RAG search: No documents found for this conversation")
                    return []
            except Exception as e:
                # If check fails, fall through to normal flow (safe)
                logger.warning(f"Optimization check failed: {e}")
            
            # Generate query embedding using Mistral
            query_embedding = await self.embeddings_service.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("⚠️  Failed to generate query embedding, falling back to recent chunks")
                return await self._get_recent_chunks(conversation_id, user_id, max_results)
            
            logger.info(f"✅ Generated query embedding: {len(query_embedding)} dimensions")
            
            # Search using database function with pgvector similarity
            try:
                result = self.db.rpc(
                    'match_documents_with_user_isolation',
                    {
                        'query_embedding': query_embedding,
                        'query_conversation_id': str(conversation_id),
                        'query_user_id': str(user_id),
                        'match_threshold': similarity_threshold,
                        'match_count': max_results
                    }
                ).execute()
                
                chunks = []
                for row in result.data or []:
                    chunk = DocumentChunk(
                        id=row['id'],
                        conversation_id=conversation_id,
                        content=row['content'],
                        metadata=row['metadata'],
                        similarity=row['similarity'],
                        created_at=row.get('created_at', '2024-01-01T00:00:00Z')
                    )
                    chunks.append(chunk)
                
                # Calculate similarity statistics
                max_similarity = max([c.similarity for c in chunks]) if chunks else 0.0
                avg_similarity = sum([c.similarity for c in chunks]) / len(chunks) if chunks else 0.0
                search_duration = time.time() - start_time
                
                logger.info(
                    f"✅ Found {len(chunks)} similar chunks (threshold: {similarity_threshold}, "
                    f"max_sim: {max_similarity:.3f}, avg_sim: {avg_similarity:.3f}, {search_duration:.3f}s)",
                    extra={
                        'operation': 'similarity_search',
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'query_length': query_length,
                        'result_count': len(chunks),
                        'max_similarity': max_similarity,
                        'avg_similarity': avg_similarity,
                        'similarity_threshold': similarity_threshold,
                        'duration': search_duration * 1000
                    }
                )
                
                # Use RAGLogger for comprehensive statistics
                rag_logger.log_similarity_search(
                    query_length=query_length,
                    user_id=str(user_id),
                    conversation_id=str(conversation_id),
                    duration=search_duration,
                    result_count=len(chunks),
                    max_similarity=max_similarity,
                    avg_similarity=avg_similarity,
                    success=True
                )
                
                # If no results and threshold is high, try with lower threshold
                if not chunks and similarity_threshold > 0.05:
                    logger.info(f"⚠️  No results with threshold {similarity_threshold}, retrying with 0.05")
                    return await self.search_similar_chunks(
                        query, conversation_id, user_id, max_results, 0.05
                    )
                
                # If still no results, fallback to all chunks
                if not chunks:
                    logger.warning("⚠️  No similar chunks found, returning all chunks")
                    return await self.get_all_conversation_chunks(conversation_id, user_id)
                
                return chunks
                
            except Exception as db_error:
                search_duration = time.time() - start_time
                logger.error(
                    f"❌ Database search error: {db_error}",
                    extra={
                        'operation': 'similarity_search',
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'query_length': query_length,
                        'error_type': 'database_error',
                        'duration': search_duration * 1000
                    },
                    exc_info=True
                )
                
                # Use RAGLogger for comprehensive statistics
                rag_logger.log_similarity_search(
                    query_length=query_length,
                    user_id=str(user_id),
                    conversation_id=str(conversation_id),
                    duration=search_duration,
                    result_count=0,
                    success=False,
                    error=str(db_error)
                )
                
                # Fallback to all chunks
                return await self.get_all_conversation_chunks(conversation_id, user_id)
            
        except Exception as e:
            search_duration = time.time() - start_time
            logger.error(
                f"❌ Error in similarity search: {e}",
                extra={
                    'operation': 'similarity_search',
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'query_length': query_length,
                    'error_type': 'unexpected_error',
                    'duration': search_duration * 1000
                },
                exc_info=True
            )
            
            # Use RAGLogger for comprehensive statistics
            rag_logger.log_similarity_search(
                query_length=query_length,
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                duration=search_duration,
                result_count=0,
                success=False,
                error=str(e)
            )
            
            # Fallback to all chunks
            return await self.get_all_conversation_chunks(conversation_id, user_id)
    
    async def _get_recent_chunks(
        self, 
        conversation_id: UUID, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[DocumentChunk]:
        """Get recent chunks as fallback when similarity search fails"""
        try:
            result = self.db.table("document_chunks").select(
                "id, content, metadata, created_at"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user_id)
            ).order("created_at", desc=True).limit(limit).execute()
            
            chunks = []
            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    conversation_id=conversation_id,
                    content=row['content'],
                    metadata=row['metadata'],
                    similarity=0.5,  # Default similarity for fallback
                    created_at=row['created_at']
                )
                chunks.append(chunk)
            
            logger.info(f"✅ Retrieved {len(chunks)} recent chunks as fallback")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error getting recent chunks: {e}")
            return []
    
    async def get_conversation_context(
        self,
        query: str,
        conversation_id: UUID,
        user_id: UUID,
        max_chunks: int = 20
    ) -> str:
        """
        Get relevant context for a query using LangChain similarity search

        Args:
            query: User query
            conversation_id: Conversation UUID
            user_id: User UUID
            max_chunks: Maximum number of chunks to include

        Returns:
            Formatted context string
        """
        try:
            # Search for relevant chunks with improved threshold for better relevance
            chunks = await self.search_similar_chunks(
                query, conversation_id, user_id, max_chunks, 0.3  # Increased from 0.05 to 0.3
            )

            if not chunks:
                # 🔍 FALLBACK: Try to get recent chunks directly if similarity search fails
                logger.warning(f"⚠️ Similarity search returned 0 chunks for conversation {conversation_id}, trying fallback...")
                chunks = await self._get_recent_chunks(conversation_id, user_id, max_chunks)

                if not chunks:
                    logger.info("📭 No document chunks found at all - conversation has no uploaded documents")
                    return ""
                else:
                    logger.info(f"✅ Fallback retrieved {len(chunks)} recent chunks")
            
            # Organize chunks by document and similarity
            documents = {}
            for chunk in chunks:
                filename = chunk.metadata.get("filename", "Unknown Document")
                if filename not in documents:
                    documents[filename] = []
                documents[filename].append({
                    "content": chunk.content,
                    "similarity": chunk.similarity,
                    "metadata": chunk.metadata
                })
            
            # Sort chunks within each document by similarity
            for filename in documents:
                documents[filename].sort(key=lambda x: x["similarity"], reverse=True)
            
            # Build enhanced context
            context_parts = []
            
            # Add document overview if multiple documents
            if len(documents) > 1:
                context_parts.append("=== DOCUMENT OVERVIEW ===")
                for filename, chunks_data in documents.items():
                    avg_similarity = sum(c["similarity"] for c in chunks_data) / len(chunks_data)
                    context_parts.append(
                        f"📄 {filename} - {len(chunks_data)} sections "
                        f"(avg similarity: {avg_similarity:.2f})"
                    )
                context_parts.append("")
            
            # Add content from each document
            for filename, chunks_data in documents.items():
                if len(documents) > 1:
                    context_parts.append(f"=== {filename} ===")
                
                for chunk_data in chunks_data:
                    content = chunk_data["content"].strip()
                    if content:
                        # Add similarity score for debugging (can be removed in production)
                        if logger.isEnabledFor(logging.DEBUG):
                            context_parts.append(f"[Similarity: {chunk_data['similarity']:.2f}]")
                        context_parts.append(content)
                
                if len(documents) > 1:
                    context_parts.append("")
            
            context = "\n\n".join(context_parts)
            
            logger.info(
                f"✅ Generated context from {len(chunks)} chunks "
                f"across {len(documents)} documents ({len(context)} chars)"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error generating context: {e}")
            return ""
    
    async def get_all_conversation_chunks(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> List[DocumentChunk]:
        """Get all chunks for a conversation"""
        try:
            result = self.db.table("document_chunks").select(
                "id, content, metadata, created_at"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user_id)
            ).order("created_at").execute()
            
            chunks = []
            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    conversation_id=conversation_id,
                    content=row['content'],
                    metadata=row['metadata'],
                    similarity=0.5,
                    created_at=row['created_at']
                )
                chunks.append(chunk)
            
            logger.info(f"✅ Retrieved {len(chunks)} chunks for conversation")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error getting conversation chunks: {e}")
            return []
    
    async def delete_conversation_documents(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete all documents for a conversation"""
        try:
            result = self.db.table("document_chunks").delete().eq(
                "conversation_id", str(conversation_id)
            ).eq("user_id", str(user_id)).execute()
            
            logger.info(f"✅ Deleted documents for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            return False
    
    async def delete_file_documents(
        self, 
        conversation_id: UUID, 
        filename: str,
        user_id: UUID = None
    ) -> bool:
        """Delete all chunks for a specific file in a conversation (cleanup/rollback)"""
        try:
            # Construct query
            query = self.db.table("document_chunks").delete().eq(
                "conversation_id", str(conversation_id)
            )
            
            if user_id:
                query = query.eq("user_id", str(user_id))
            
            # Using Supabase JSON filtering syntax: metadata->>filename = filename
            # Note: The syntax depends on the specific client version, but often custom filters are used 
            # or we assume 'metadata' column. 
            # A safer approach if filter syntax is unsure: verify 'filename' is in metadata
            result = query.filter("metadata->>filename", "eq", filename).execute()
            
            logger.info(f"✅ Deleted chunks for file {filename} in conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting document chunks for {filename}: {e}")
            return False

    async def get_recent_image_analyses(
        self,
        conversation_id: UUID,
        filenames: List[str] = None,
        limit: int = 10
    ) -> str:
        """
        Get recent image analyses stored in vector DB for a conversation.
        
        Args:
            conversation_id: Conversation UUID
            filenames: Optional list of filenames to filter by
            limit: Maximum number of analyses to return
            
        Returns:
            Formatted string containing all image analyses
        """
        try:
            # Query document_chunks for image analyses in this conversation
            query = self.db.table("document_chunks").select("content, metadata").eq(
                "conversation_id", str(conversation_id)
            ).order("created_at", desc=True).limit(limit)
            
            result = query.execute()
            
            if not result.data:
                logger.info(f"📭 No image analyses found for conversation {conversation_id}")
                return ""
            
            # Filter for image analyses and optionally by filename
            analyses = []
            for chunk in result.data:
                metadata = chunk.get("metadata", {})
                
                # Check if this is an image analysis chunk
                if metadata.get("type") == "image_analysis":
                    content = chunk.get("content", "")
                    if content:
                        analyses.append(content)
                        continue
                
                # Also check source field for image uploads
                source = metadata.get("source", "")
                if "image_upload" in source or any(source.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
                    content = chunk.get("content", "")
                    if content and ("Visual Content Analysis" in content or "image" in content.lower()[:100]):
                        analyses.append(content)
            
            if analyses:
                logger.info(f"🖼️ Found {len(analyses)} image analyses for conversation {conversation_id}")
                return "\n\n".join(analyses)
            
            logger.info(f"📭 No image analyses matched criteria for conversation {conversation_id}")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Error fetching image analyses: {e}")
            return ""

    async def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of the enhanced RAG service"""
        health = {
            "status": "healthy",
            "components": {},
            "errors": []
        }
        
        try:
            # Check embeddings service
            embeddings_health = await self.embeddings_service.health_check()
            health["components"]["embeddings"] = embeddings_health
            
            if embeddings_health["status"] != "healthy":
                health["status"] = "degraded"
                health["errors"].extend(embeddings_health.get("errors", []))
            
            # Check document loader
            loader_stats = self.document_loader.get_processing_stats()
            health["components"]["document_loader"] = {
                "status": "healthy",
                "supported_formats": loader_stats["supported_formats"],
                "loaders": loader_stats["loaders"]
            }
            
            # Check text splitter
            splitter_config = self.text_splitter.get_splitter_config()
            health["components"]["text_splitter"] = {
                "status": "healthy",
                "config": splitter_config
            }
            
            # Test database connectivity
            try:
                test_result = self.db.table("document_chunks").select("id").limit(1).execute()
                health["components"]["database"] = {
                    "status": "healthy",
                    "connection": "active"
                }
            except Exception as db_error:
                health["components"]["database"] = {
                    "status": "unhealthy",
                    "error": str(db_error)
                }
                health["status"] = "unhealthy"
                health["errors"].append(f"Database error: {str(db_error)}")
            
            # Add configuration info
            health["configuration"] = {
                "use_mistral_embeddings": settings.USE_MISTRAL_EMBEDDINGS,
                "use_langchain_loaders": settings.USE_LANGCHAIN_LOADERS,
                "embedding_cache_enabled": settings.ENABLE_EMBEDDING_CACHE,
                "chunk_size": settings.LANGCHAIN_CHUNK_SIZE,
                "chunk_overlap": settings.LANGCHAIN_CHUNK_OVERLAP
            }
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["errors"].append(f"Health check error: {str(e)}")
        
        return health
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics and capabilities"""
        return {
            "service_type": "EnhancedRAGService",
            "langchain_integration": True,
            "mistral_embeddings": settings.USE_MISTRAL_EMBEDDINGS,
            "embedding_dimensions": settings.MISTRAL_EMBED_DIMENSIONS,
            "supported_formats": self.document_loader.get_supported_formats(),
            "text_splitter_config": self.text_splitter.get_splitter_config(),
            "embeddings_stats": self.embeddings_service.get_cache_stats(),
            "features": [
                "LangChain document loaders",
                "Mistral embeddings API",
                "Recursive text splitting",
                "Embedding caching",
                "Enhanced error handling",
                "Comprehensive logging",
                "Metadata preservation",
                "Similarity search optimization"
            ]
        }