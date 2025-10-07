"""
Enhanced RAG Service using LangChain and Mistral Embeddings
Replaces the custom RAG implementation with industry-standard tools
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from supabase import Client
from langchain_core.documents import Document
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.models.document import DocumentChunk, DocumentUploadResponse
from app.services.embeddings import embeddings_service
from app.services.document_loaders import document_loader, DocumentProcessingError
from app.services.text_splitter import text_splitter

logger = logging.getLogger(__name__)


class MistralEmbeddingsWrapper(Embeddings):
    """Wrapper to make our embeddings service compatible with LangChain"""
    
    def __init__(self, embeddings_service):
        self.embeddings_service = embeddings_service
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = []
        for text in texts:
            embedding = loop.run_until_complete(self.embeddings_service.generate_embedding(text))
            if embedding:
                embeddings.append(embedding)
            else:
                # Return zero vector if embedding fails
                embeddings.append([0.0] * settings.MISTRAL_EMBED_DIMENSIONS)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query"""
        import asyncio
        loop = asyncio.get_event_loop()
        embedding = loop.run_until_complete(self.embeddings_service.generate_embedding(text))
        return embedding if embedding else [0.0] * settings.MISTRAL_EMBED_DIMENSIONS


class EnhancedRAGService:
    """Enhanced RAG service using LangChain and Mistral embeddings"""
    
    def __init__(self, db: Client):
        self.db = db
        self.embeddings_service = embeddings_service
        self.document_loader = document_loader
        self.text_splitter = text_splitter
        
        # Initialize LangChain embeddings wrapper
        self.embeddings = MistralEmbeddingsWrapper(embeddings_service)
        
        # Initialize Supabase vector store
        self.vector_store = SupabaseVectorStore(
            client=db,
            embedding=self.embeddings,
            table_name="document_chunks",
            query_name="match_documents_with_user_isolation"
        )
        
        logger.info("✅ Enhanced RAG service initialized with LangChain SupabaseVectorStore and Mistral embeddings")
    
    async def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str, 
        conversation_id: UUID, 
        user_id: UUID
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
        
        try:
            logger.info(f"Processing file: {filename} for user {user_id}")
            
            # Check if file format is supported
            if not self.document_loader.is_supported_format(filename):
                return DocumentUploadResponse(
                    success=False,
                    message=f"Unsupported file format. Supported formats: {', '.join(self.document_loader.get_supported_formats())}",
                    chunk_count=0
                )
            
            # Load document using LangChain loaders
            try:
                documents = await self.document_loader.load_document(
                    file_content=file_content,
                    filename=filename,
                    additional_metadata={
                        "user_id": str(user_id),
                        "conversation_id": str(conversation_id)
                    }
                )
            except DocumentProcessingError as e:
                return DocumentUploadResponse(
                    success=False,
                    message=str(e),
                    chunk_count=0
                )
            
            if not documents:
                return DocumentUploadResponse(
                    success=False,
                    message=f"No content could be extracted from {filename}",
                    chunk_count=0
                )
            
            # Validate document content
            validation_result = await self.document_loader.validate_document_content(documents)
            if not validation_result["valid"]:
                return DocumentUploadResponse(
                    success=False,
                    message=validation_result.get("error", "Document validation failed"),
                    chunk_count=0
                )
            
            # Log validation warnings
            for warning in validation_result.get("warnings", []):
                logger.warning(f"⚠️  Document validation warning: {warning}")
                processing_errors.append(f"Warning: {warning}")
            
            # Split documents into chunks using LangChain text splitter
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                return DocumentUploadResponse(
                    success=False,
                    message=f"No chunks could be generated from {filename}",
                    chunk_count=0
                )
            
            logger.info(f"Generated {len(chunks)} chunks from {filename}")
            
            # Add metadata to all chunks
            for chunk in chunks:
                chunk.metadata.update({
                    "filename": filename,
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "embedding_model": settings.MISTRAL_EMBED_MODEL,
                    "embedding_version": "mistral-v1"
                })
            
            # Store chunks using LangChain vector store
            try:
                logger.info(f"💾 Storing {len(chunks)} chunks using LangChain SupabaseVectorStore...")
                
                # Use LangChain's add_documents method
                ids = self.vector_store.add_documents(chunks)
                
                success_count = len(ids) if ids else 0
                failed_count = len(chunks) - success_count
                
                logger.info(f"✅ Successfully stored {success_count}/{len(chunks)} chunks via LangChain")
                
            except Exception as e:
                logger.error(f"❌ Error storing chunks via LangChain: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback to manual storage
                logger.info("⚠️  Falling back to manual chunk storage...")
                success_count = 0
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
                        logger.error(f"❌ {error_msg}")
                        processing_errors.append(error_msg)
            
            processing_time = time.time() - start_time
            
            # Prepare response
            if success_count > 0:
                message = f"Successfully processed {success_count} chunks from {filename}"
                if failed_count > 0:
                    message += f" ({failed_count} chunks failed)"
                if processing_errors:
                    message += f". Warnings: {len(processing_errors)}"
                
                logger.info(f"✅ {message} (processing time: {processing_time:.2f}s)")
                
                return DocumentUploadResponse(
                    success=True,
                    message=message,
                    chunk_count=success_count,
                    processing_time=processing_time,
                    errors=processing_errors if processing_errors else None
                )
            else:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Failed to process any chunks from {filename}",
                    chunk_count=0,
                    processing_time=processing_time,
                    errors=processing_errors
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unexpected error processing {filename}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return DocumentUploadResponse(
                success=False,
                message=error_msg,
                chunk_count=0,
                processing_time=processing_time,
                errors=[error_msg]
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
            # Generate embedding using Mistral API
            embedding = await self.embeddings_service.generate_embedding(chunk.page_content)
            
            if not embedding:
                logger.error(f"❌ Failed to generate embedding for chunk {chunk_index}")
                return False
            
            # Validate embedding dimensions
            if len(embedding) != settings.MISTRAL_EMBED_DIMENSIONS:
                logger.error(
                    f"❌ Invalid embedding dimensions: {len(embedding)} "
                    f"(expected {settings.MISTRAL_EMBED_DIMENSIONS})"
                )
                return False
            
            # Prepare enhanced metadata
            metadata = chunk.metadata.copy()
            metadata.update({
                "filename": filename,
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "embedding_model": settings.MISTRAL_EMBED_MODEL,
                "embedding_version": "mistral-v1",
                "processing_timestamp": time.time(),
                "chunk_length": len(chunk.page_content),
                "langchain_processed": True
            })
            
            # Store in database
            chunk_data = {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "content": chunk.page_content,
                "embedding": embedding,
                "metadata": metadata,
                "embedding_version": "mistral-v1"
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
        similarity_threshold: float = 0.3
    ) -> List[DocumentChunk]:
        """
        Search for similar document chunks using LangChain SupabaseVectorStore
        
        Args:
            query: Search query
            conversation_id: Conversation UUID
            user_id: User UUID
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score (0.3 default for better recall)
            
        Returns:
            List of similar document chunks
        """
        try:
            logger.info(f"🔍 Searching for similar chunks: '{query[:50]}...' (threshold: {similarity_threshold})")
            
            # Use LangChain's similarity search with metadata filtering
            filter_dict = {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id)
            }
            
            # Perform similarity search using LangChain
            docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=max_results,
                filter=filter_dict
            )
            
            # Filter by threshold and convert to DocumentChunk
            chunks = []
            for doc, score in docs_with_scores:
                # LangChain returns relevance scores (higher is better)
                # Filter by threshold
                if score >= similarity_threshold:
                    chunk = DocumentChunk(
                        id=doc.metadata.get('id', ''),
                        conversation_id=conversation_id,
                        content=doc.page_content,
                        metadata=doc.metadata,
                        similarity=score,
                        created_at=doc.metadata.get('created_at', '2024-01-01T00:00:00Z')
                    )
                    chunks.append(chunk)
            
            logger.info(f"✅ Found {len(chunks)} similar chunks using LangChain (threshold: {similarity_threshold})")
            
            # If no results, try with lower threshold
            if not chunks and similarity_threshold > 0.1:
                logger.info(f"⚠️  No results with threshold {similarity_threshold}, retrying with 0.1")
                return await self.search_similar_chunks(
                    query, conversation_id, user_id, max_results, 0.1
                )
            
            # If still no results, fallback to recent chunks
            if not chunks:
                logger.warning("⚠️  No similar chunks found, falling back to recent chunks")
                return await self._get_recent_chunks(conversation_id, user_id, max_results)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error in LangChain similarity search: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to recent chunks
            return await self._get_recent_chunks(conversation_id, user_id, max_results)
    
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
            # Search for relevant chunks with lower threshold for better recall
            chunks = await self.search_similar_chunks(
                query, conversation_id, user_id, max_chunks, 0.2
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
        """Get all chunks for a conversation with enhanced metadata"""
        try:
            result = self.db.table("document_chunks").select(
                "id, content, metadata, created_at, embedding_version"
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