"""
Enhanced RAG Service using LangChain and Mistral Embeddings
Replaces the custom RAG implementation with industry-standard tools
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
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
        mode: str = "detailed"
    ) -> DocumentUploadResponse:
        """
        Process uploaded file using LangChain loaders and Mistral embeddings
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            conversation_id: Conversation UUID
            user_id: User UUID
            
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
                # Initialize AI Service for multimodal analysis (lazy import to avoid circular dependency)
                from app.services.ai import AIService
                import base64
                
                ai_service = AIService(self.db)
                
                async def image_analyzer_wrapper(image_bytes: bytes) -> str:
                    """Wrapper to convert bytes to base64 and call AI service"""
                    try:
                        b64_str = base64.b64encode(image_bytes).decode('utf-8')
                        # Assume JPEG for simplicity, or detect mime type if possible
                        data_url = f"data:image/jpeg;base64,{b64_str}"
                        return await ai_service.analyze_image(data_url)
                    except Exception as e:
                        logger.error(f"Image analysis wrapper failed: {e}")
                        return ""

                # Streaming Ingestion Support
                streamed_chunks_count = 0
                ingestion_semaphore = asyncio.Semaphore(3) # Limit concurrent embedding requests
                
                async def streaming_ingest_callback(content_chunk: str, page_idx: int):
                    async with ingestion_semaphore:
                        nonlocal streamed_chunks_count
                        try:
                            temp_doc = Document(
                                page_content=content_chunk,
                                metadata={
                                    "source": filename,
                                    "page": page_idx + 1,
                                    "user_id": str(user_id),
                                    "conversation_id": str(conversation_id),
                                    "filename": filename
                                }
                            )
                            sub_chunks = self.text_splitter.split_documents([temp_doc])
                            for i, chunk in enumerate(sub_chunks):
                                success = await self._process_and_store_chunk(
                                    chunk, filename, conversation_id, user_id, 
                                    chunk_index=streamed_chunks_count + i
                                )
                                if success:
                                    streamed_chunks_count += 1
                            logger.info(f"⚡ Streamed ingestion: Processed page {page_idx+1}")
                        except Exception as e:
                            logger.error(f"Streaming ingestion failed: {e}")

                documents = await self.document_loader.load_document(
                    file_content=file_content,
                    filename=filename,
                    additional_metadata={
                        "user_id": str(user_id),
                        "conversation_id": str(conversation_id)
                    },
                    image_analyzer=image_analyzer_wrapper,
                    user_prompt=user_prompt,
                    mode=mode,
                    chunk_callback=streaming_ingest_callback
                )
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
            
            # Validate document content with enhanced error messages
            validation_result = await self.document_loader.validate_document_content(
                documents=documents,
                filename=filename,
                file_type=file_extension
            )
            if not validation_result["valid"]:
                return DocumentUploadResponse(
                    success=False,
                    message=validation_result.get("error", "Document validation failed"),
                    chunk_count=0,
                    file_info=file_info
                )
            
            # Collect validation warnings
            for warning in validation_result.get("warnings", []):
                logger.warning(f"⚠️  Document validation warning: {warning}")
                processing_warnings.append(warning)
            
            # Split documents into chunks using LangChain text splitter
            chunk_start_time = time.time()
            
            if streamed_chunks_count > 0:
                 chunks = []
            else:
                 chunks = self.text_splitter.split_documents(documents)
            
            chunk_duration = time.time() - chunk_start_time
            
            if not chunks and streamed_chunks_count == 0:
                logger.error(
                    f"❌ No chunks generated from {filename}",
                    extra={
                        'operation': 'chunk_generation',
                        'document_name': filename,
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'document_count': len(documents),
                        'chunk_count': 0,
                        'duration': chunk_duration * 1000
                    }
                )
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
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'document_count': len(documents),
                    'chunk_count': len(chunks),
                    'duration': chunk_duration * 1000
                }
            )
            
            # Add metadata to all chunks
            for chunk in chunks:
                chunk.metadata.update({
                    "filename": filename,
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "embedding_model": settings.EMBEDDING_PROVIDER,
                    "embedding_dimensions": settings.EMBEDDING_DIMENSIONS
                })
            
            # Store chunks directly using database
            storage_start_time = time.time()
            if streamed_chunks_count > 0:
                 logger.info(f"💾 Streaming complete. {streamed_chunks_count} chunks already stored.")
            else:
                 logger.info(
                    f"💾 Storing {len(chunks)} chunks in database...",
                    extra={
                        'operation': 'chunk_storage',
                        'document_name': filename,
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'chunk_count': len(chunks)
                    }
                 )
            
            success_count = streamed_chunks_count
            failed_count = 0
            
            for chunk_index, chunk in enumerate(chunks):
                try:
                    success = await self._process_and_store_chunk(
                        chunk=chunk,
                        filename=filename,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        chunk_index=chunk_index
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        processing_errors.append(f"Failed to store chunk {chunk_index}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Error processing chunk {chunk_index}: {str(e)}"
                    logger.error(
                        f"❌ {error_msg}",
                        extra={
                            'operation': 'chunk_storage',
                            'document_name': filename,
                            'user_id': str(user_id),
                            'conversation_id': str(conversation_id),
                            'chunk_index': chunk_index,
                            'error_type': 'chunk_storage_error'
                        }
                    )
                    processing_errors.append(error_msg)
            
            storage_duration = time.time() - storage_start_time
            processing_time = time.time() - start_time
            
            # Log storage statistics
            logger.info(
                f"💾 Chunk storage completed: {success_count}/{len(chunks)} successful "
                f"({storage_duration:.2f}s)",
                extra={
                    'operation': 'chunk_storage',
                    'document_name': filename,
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'total_chunks': len(chunks),
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'duration': storage_duration * 1000
                }
            )
            
            # Prepare response
            if success_count > 0:
                message = f"Successfully processed {success_count} chunks from {filename}"
                if failed_count > 0:
                    message += f" ({failed_count} chunks failed)"
                if processing_warnings:
                    message += f". {len(processing_warnings)} warning(s)"
                
                logger.info(
                    f"✅ {message} (processing time: {processing_time:.2f}s)",
                    extra={
                        'operation': 'file_upload',
                        'document_name': filename,
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'file_size': file_size,
                        'chunk_count': success_count,
                        'failed_count': failed_count,
                        'warning_count': len(processing_warnings),
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
                    success=True
                )
                
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
                logger.error(
                    f"❌ Failed to process any chunks from {filename}",
                    extra={
                        'operation': 'file_upload',
                        'document_name': filename,
                        'user_id': str(user_id),
                        'conversation_id': str(conversation_id),
                        'file_size': file_size,
                        'error_count': len(processing_errors),
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
                    chunk_count=0,
                    file_size=file_size,
                    success=False,
                    error=f"Failed to process any chunks ({len(processing_errors)} errors)"
                )
                
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
            logger.error(
                f"❌ {error_msg}",
                extra={
                    'operation': 'file_upload',
                    'document_name': filename,
                    'user_id': str(user_id),
                    'conversation_id': str(conversation_id),
                    'file_size': file_size,
                    'error_type': 'unexpected_error',
                    'duration': processing_time * 1000
                },
                exc_info=True
            )
            
            # Use RAGLogger for comprehensive statistics
            rag_logger.log_document_processing(
                operation='file_upload',
                filename=filename,
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                duration=processing_time,
                chunk_count=0,
                file_size=file_size,
                success=False,
                error=error_msg
            )
            
            return DocumentUploadResponse(
                success=False,
                message=error_msg,
                chunk_count=0,
                processing_time=processing_time,
                errors=[error_msg],
                file_info=file_info
            )
    
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
            
            # Generate embedding based on content type
            if is_image and image_path:
                # Use Cohere's image embedding for images
                logger.debug(f"🖼️  Generating image embedding for {filename}")
                if hasattr(self.embeddings_service, 'embed_image'):
                    embedding = await self.embeddings_service.embed_image(
                        image_path=image_path,
                        image_description=chunk.page_content  # Use placeholder text as description
                    )
                else:
                    # Fallback to text embedding if image embedding not supported
                    logger.warning(f"⚠️  Image embedding not supported, using text embedding for {filename}")
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
            
            result = self.db.table("document_chunks").insert(chunk_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.debug(f"✅ Stored chunk {chunk_index} for {filename}")
                return True
            else:
                logger.error(f"❌ Database insert failed for chunk {chunk_index}")
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
                        'conversation_uuid': str(conversation_id),
                        'user_session_uuid': str(user_id),
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
            # Search for relevant chunks with very low threshold for maximum recall
            chunks = await self.search_similar_chunks(
                query, conversation_id, user_id, max_chunks, 0.05
            )
            
            if not chunks:
                logger.info("No relevant context found for query")
                return ""
            
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