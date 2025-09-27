"""
RAG (Retrieval-Augmented Generation) System
Handles document processing and vector search using Langchain
"""

import os
from typing import List, Dict, Any, Optional
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import tempfile
import numpy as np

# Additional imports for enhanced document processing
try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    import cv2
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from langextract import LangExtract
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

from database import SimpleChatbotDB


class RAGManager:
    """Manages document processing and retrieval for RAG system"""
    
    def __init__(self):
        self.db_manager = SimpleChatbotDB()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Increased from 1000 for larger chunks
            chunk_overlap=300,  # Increased overlap for better continuity
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Better splitting on paragraphs and sentences
        )
        self.embedding_model = None
        self.lang_extract = None
        self._initialize_embeddings()
        self._initialize_langextract()
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        try:
            # Try to use OpenAI embeddings if available
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
            else:
                # Fallback to sentence transformers
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
        except Exception as e:
            st.error(f"Error initializing embeddings: {str(e)}")
            # Fallback to sentence transformers
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as fallback_e:
                st.error(f"Fallback embedding initialization failed: {str(fallback_e)}")
    
    def _initialize_langextract(self):
        """Initialize LangExtract for document intelligence"""
        try:
            if LANGEXTRACT_AVAILABLE:
                self.lang_extract = LangExtract()
                st.info("🧠 LangExtract initialized for enhanced document understanding")
            else:
                st.info("💡 LangExtract not available - install with: pip install langextract")
        except Exception as e:
            st.warning(f"LangExtract initialization failed: {str(e)}")
            self.lang_extract = None
    
    def process_uploaded_file(self, uploaded_file, conversation_id: str, progress_callback=None) -> tuple[bool, int]:
        """
        Process uploaded file and store chunks in database with enhanced feedback
        
        Args:
            uploaded_file: Streamlit uploaded file object
            conversation_id: ID of the conversation to associate chunks with
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success: bool, chunk_count: int)
        """
        try:
            if not uploaded_file:
                return False, 0
            
            if progress_callback:
                progress_callback("Saving temporary file...")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            if progress_callback:
                progress_callback("Loading document...")
            
            # Load document based on file type
            documents = self._load_document(tmp_file_path, uploaded_file.name)
            
            if not documents:
                os.unlink(tmp_file_path)
                return False, 0
            
            if progress_callback:
                progress_callback("Splitting into chunks...")
            
            # Enhanced document processing with LangExtract
            if self.lang_extract and len(documents) > 0:
                if progress_callback:
                    progress_callback("Analyzing document structure with LangExtract...")
                
                # Extract structured information
                enhanced_documents = self._enhance_documents_with_langextract(documents, uploaded_file.name)
                if enhanced_documents:
                    documents = enhanced_documents
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                st.error(f"No chunks created from '{uploaded_file.name}' - document may be empty or unreadable")
                os.unlink(tmp_file_path)
                return False, 0
            
            if progress_callback:
                progress_callback(f"Processing {len(chunks)} chunks...")
            
            # Process and store chunks with progress tracking
            success_count = 0
            for i, chunk in enumerate(chunks):
                # Check if chunk has content
                if not chunk.page_content.strip():
                    continue
                
                if self._process_and_store_chunk(chunk, uploaded_file.name, conversation_id):
                    success_count += 1
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return success_count > 0, success_count
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False, 0
    
    def _load_document(self, file_path: str, filename: str) -> List[Document]:
        """Load document based on file type with enhanced support including PowerPoint and OCR"""
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                if not documents:
                    st.warning(f"PDF '{filename}' loaded but contains no readable content")
                return documents
                
            elif file_extension in ['txt', 'md']:
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
                if not documents:
                    st.warning(f"Text file '{filename}' loaded but contains no content")
                return documents
                
            elif file_extension == 'docx':
                return self._process_docx(file_path, filename)
                
            elif file_extension == 'pptx':
                return self._process_pptx(file_path, filename)
                
            elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']:
                return self._process_image_ocr(file_path, filename)
                    
            else:
                st.error(f"Unsupported file type: {file_extension}. Supported types: PDF, TXT, MD, DOCX, PPTX, Images (JPG, PNG, etc.)")
                return []
                
        except Exception as e:
            st.error(f"Error loading document '{filename}': {str(e)}")
            return []
    
    def _process_docx(self, file_path: str, filename: str) -> List[Document]:
        """Process DOCX files"""
        try:
            import docx
        except ImportError:
            st.error("python-docx package not found. Please install it with: pip install python-docx")
            return []
        
        try:
            doc = docx.Document(file_path)
            
            # Extract text from all paragraphs
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text.strip())
            
            if not text_content:
                st.warning(f"DOCX '{filename}' contains no readable text")
                return []
            
            # Create a Document object
            full_text = '\n\n'.join(text_content)
            document = Document(
                page_content=full_text,
                metadata={"source": filename, "file_type": "docx"}
            )
            
            return [document]
            
        except Exception as docx_error:
            st.error(f"❌ Error processing DOCX '{filename}': {str(docx_error)}")
            return []
    
    def _process_pptx(self, file_path: str, filename: str) -> List[Document]:
        """Process PowerPoint files"""
        if not PPTX_AVAILABLE:
            st.error("python-pptx package not found. Please install it with: pip install python-pptx")
            return []
        
        try:
            prs = Presentation(file_path)
            
            text_content = []
            slide_number = 0
            
            for slide in prs.slides:
                slide_number += 1
                slide_text = []
                
                # Extract text from all shapes in the slide
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                
                if slide_text:
                    slide_content = f"Slide {slide_number}:\n" + '\n'.join(slide_text)
                    text_content.append(slide_content)
            
            if not text_content:
                st.warning(f"PowerPoint '{filename}' contains no readable text")
                return []
            
            # Create a Document object
            full_text = '\n\n'.join(text_content)
            document = Document(
                page_content=full_text,
                metadata={"source": filename, "file_type": "pptx", "slides": slide_number}
            )
            
            return [document]
            
        except Exception as pptx_error:
            st.error(f"❌ Error processing PowerPoint '{filename}': {str(pptx_error)}")
            return []
    
    def _process_image_ocr(self, file_path: str, filename: str) -> List[Document]:
        """Process images using OCR"""
        if not OCR_AVAILABLE:
            st.error("OCR packages not found. Please install: pip install pytesseract pillow opencv-python-headless")
            st.info("Note: You may also need to install Tesseract OCR on your system")
            return []
        
        try:
            # Load and preprocess image
            image = cv2.imread(file_path)
            if image is None:
                st.error(f"Could not load image '{filename}'")
                return []
            
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply some preprocessing to improve OCR accuracy
            # Denoise
            denoised = cv2.medianBlur(gray, 3)
            
            # Convert to PIL Image for pytesseract
            pil_image = Image.fromarray(denoised)
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(pil_image, lang='eng')
            
            if not extracted_text.strip():
                st.warning(f"No text found in image '{filename}' using OCR")
                return []
            
            # Clean up the extracted text
            cleaned_text = '\n'.join([line.strip() for line in extracted_text.split('\n') if line.strip()])
            
            if not cleaned_text:
                st.warning(f"No readable text extracted from image '{filename}'")
                return []
            
            # Create a Document object
            document = Document(
                page_content=cleaned_text,
                metadata={"source": filename, "file_type": "image_ocr", "original_format": filename.split('.')[-1]}
            )
            
            return [document]
            
        except Exception as ocr_error:
            st.error(f"❌ Error processing image '{filename}' with OCR: {str(ocr_error)}")
            if "tesseract" in str(ocr_error).lower():
                st.info("💡 Make sure Tesseract OCR is installed on your system")
            return []
    
    def _enhance_documents_with_langextract(self, documents: List[Document], filename: str) -> List[Document]:
        """Enhance documents using LangExtract for better structure and information extraction"""
        try:
            if not self.lang_extract or not documents:
                return documents
            
            enhanced_docs = []
            
            for doc in documents:
                # Extract structured information using LangExtract
                extracted_info = self._extract_document_intelligence(doc.page_content, filename)
                
                if extracted_info:
                    # Create enhanced document with structured metadata
                    enhanced_content = self._format_enhanced_content(doc.page_content, extracted_info)
                    
                    enhanced_metadata = doc.metadata.copy()
                    enhanced_metadata.update({
                        "extracted_entities": extracted_info.get("entities", []),
                        "key_topics": extracted_info.get("topics", []),
                        "document_type": extracted_info.get("document_type", "unknown"),
                        "structure_info": extracted_info.get("structure", {}),
                        "enhanced_with_langextract": True
                    })
                    
                    enhanced_doc = Document(
                        page_content=enhanced_content,
                        metadata=enhanced_metadata
                    )
                    enhanced_docs.append(enhanced_doc)
                else:
                    enhanced_docs.append(doc)
            
            return enhanced_docs if enhanced_docs else documents
            
        except Exception as e:
            st.warning(f"LangExtract enhancement failed: {str(e)}")
            return documents
    
    def _extract_document_intelligence(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract structured information from document content using LangExtract"""
        try:
            if not self.lang_extract:
                return {}
            
            # Define extraction schema based on document type
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf' or 'pharmacology' in filename.lower() or 'drug' in filename.lower():
                # Pharmacology-specific extraction
                schema = {
                    "drug_names": "List of drug names mentioned",
                    "mechanisms": "Mechanisms of action described",
                    "side_effects": "Side effects or adverse reactions",
                    "dosages": "Dosage information",
                    "interactions": "Drug interactions mentioned",
                    "therapeutic_uses": "Therapeutic uses or indications",
                    "key_concepts": "Important pharmacological concepts"
                }
            else:
                # General document extraction
                schema = {
                    "key_topics": "Main topics or subjects discussed",
                    "important_facts": "Key facts or findings",
                    "entities": "Important entities (people, places, organizations)",
                    "concepts": "Main concepts or ideas",
                    "document_type": "Type of document (research paper, manual, etc.)"
                }
            
            # Extract information using LangExtract
            extracted = self.lang_extract.extract(content, schema)
            
            return {
                "entities": extracted.get("entities", []) or extracted.get("drug_names", []),
                "topics": extracted.get("key_topics", []) or extracted.get("key_concepts", []),
                "document_type": extracted.get("document_type", "document"),
                "structure": {
                    "mechanisms": extracted.get("mechanisms", []),
                    "side_effects": extracted.get("side_effects", []),
                    "dosages": extracted.get("dosages", []),
                    "interactions": extracted.get("interactions", []),
                    "therapeutic_uses": extracted.get("therapeutic_uses", []),
                    "important_facts": extracted.get("important_facts", [])
                }
            }
            
        except Exception as e:
            st.warning(f"Document intelligence extraction failed: {str(e)}")
            return {}
    
    def _format_enhanced_content(self, original_content: str, extracted_info: Dict[str, Any]) -> str:
        """Format content with extracted intelligence for better RAG retrieval"""
        try:
            enhanced_parts = []
            
            # Add structured metadata at the beginning
            if extracted_info.get("entities"):
                enhanced_parts.append(f"KEY ENTITIES: {', '.join(extracted_info['entities'][:5])}")
            
            if extracted_info.get("topics"):
                enhanced_parts.append(f"MAIN TOPICS: {', '.join(extracted_info['topics'][:5])}")
            
            # Add pharmacology-specific information if available
            structure = extracted_info.get("structure", {})
            if structure.get("mechanisms"):
                enhanced_parts.append(f"MECHANISMS: {', '.join(structure['mechanisms'][:3])}")
            
            if structure.get("therapeutic_uses"):
                enhanced_parts.append(f"THERAPEUTIC USES: {', '.join(structure['therapeutic_uses'][:3])}")
            
            # Combine enhanced metadata with original content
            if enhanced_parts:
                enhanced_content = "\n".join(enhanced_parts) + "\n\n" + original_content
            else:
                enhanced_content = original_content
            
            return enhanced_content
            
        except Exception as e:
            return original_content
    
    def _add_intelligent_context_summary(self, chunks: List[Dict[str, Any]], query: str) -> str:
        """Add intelligent context summary based on extracted metadata"""
        try:
            # Collect all extracted metadata
            all_entities = set()
            all_topics = set()
            mechanisms = set()
            therapeutic_uses = set()
            
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                if metadata.get("enhanced_with_langextract"):
                    all_entities.update(metadata.get("extracted_entities", []))
                    all_topics.update(metadata.get("key_topics", []))
                    
                    structure = metadata.get("structure_info", {})
                    mechanisms.update(structure.get("mechanisms", []))
                    therapeutic_uses.update(structure.get("therapeutic_uses", []))
            
            # Create intelligent summary
            summary_parts = []
            
            if all_entities:
                summary_parts.append(f"RELEVANT ENTITIES: {', '.join(list(all_entities)[:5])}")
            
            if all_topics:
                summary_parts.append(f"RELATED TOPICS: {', '.join(list(all_topics)[:5])}")
            
            # Add pharmacology-specific summaries
            if mechanisms and any(word in query.lower() for word in ['mechanism', 'action', 'how', 'works']):
                summary_parts.append(f"MECHANISMS OF ACTION: {', '.join(list(mechanisms)[:3])}")
            
            if therapeutic_uses and any(word in query.lower() for word in ['use', 'treatment', 'therapy', 'indication']):
                summary_parts.append(f"THERAPEUTIC USES: {', '.join(list(therapeutic_uses)[:3])}")
            
            if summary_parts:
                return "=== INTELLIGENT DOCUMENT ANALYSIS ===\n" + "\n".join(summary_parts) + "\n=== DETAILED CONTENT ==="
            
            return ""
            
        except Exception as e:
            return ""
    
    def _process_and_store_chunk(self, chunk: Document, filename: str, conversation_id: str) -> bool:
        """Process chunk and store in database"""
        try:
            # Generate embedding
            embedding = self._generate_embedding(chunk.page_content)
            if not embedding:
                return False
            
            # Prepare metadata
            metadata = {
                "filename": filename,
                "page": chunk.metadata.get("page", 0),
                "source": chunk.metadata.get("source", filename)
            }
            
            # Store in database
            return self.db_manager.store_document_chunk(
                content=chunk.page_content,
                embedding=embedding,
                metadata=metadata,
                conversation_id=conversation_id
            )
            
        except Exception as e:
            st.error(f"Error processing chunk: {str(e)}")
            return False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text with detailed error handling"""
        try:
            if not self.embedding_model:
                st.error("Embedding model not initialized. Check your configuration.")
                return None
            
            if not text or not text.strip():
                st.warning("Cannot generate embedding for empty text")
                return None
            
            if hasattr(self.embedding_model, 'embed_query'):
                # OpenAI embeddings
                embedding = self.embedding_model.embed_query(text)
            else:
                # Sentence transformers
                embedding = self.embedding_model.encode(text).tolist()
            
            if not embedding or len(embedding) == 0:
                st.error("Generated embedding is empty")
                return None
            
            return embedding
            
        except Exception as e:
            st.error(f"Error generating embedding: {str(e)}")
            if "api" in str(e).lower():
                st.info("💡 Check your OpenAI API key or try using sentence-transformers")
            return None
    
    def search_relevant_context(self, query: str, conversation_id: str, max_chunks: int = 3, include_document_overview: bool = False) -> str:
        """
        Search for relevant context based on query within a conversation
        
        Args:
            query: User query
            conversation_id: ID of the conversation to search within
            max_chunks: Maximum number of chunks to retrieve
            include_document_overview: Whether to include document overview/summary
            
        Returns:
            Concatenated relevant context
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                st.write("Debug - Failed to generate query embedding")
                return ""
            
            st.write(f"Debug - Query embedding generated, length: {len(query_embedding)}")
            
            # Search for similar chunks with very low threshold to test
            similar_chunks = self.db_manager.search_similar_chunks(query_embedding, conversation_id, max_chunks, threshold=0.1)
            
            st.write(f"Debug - Found {len(similar_chunks)} similar chunks")
            
            # If no similar chunks found, try getting any chunks as fallback
            if not similar_chunks:
                st.write("Debug - No similar chunks found, trying fallback query...")
                fallback_chunks = self.db_manager.get_random_chunks(conversation_id, max_chunks)
                st.write(f"Debug - Fallback found {len(fallback_chunks)} chunks")
                if fallback_chunks:
                    similar_chunks = fallback_chunks
            
            # For now, always use fallback until vector search is fixed
            if len(similar_chunks) == 0:
                st.write("Debug - Using fallback chunks for context...")
                similar_chunks = self.db_manager.get_random_chunks(conversation_id, max_chunks)
            
            if not similar_chunks:
                return ""
            
            # Check if user is asking for comprehensive document information
            comprehensive_keywords = [
                "entire document", "whole document", "complete document", "full document",
                "summarize", "summary", "overview", "explain the document", "what is this document about",
                "document content", "all information", "everything in", "comprehensive"
            ]
            
            is_comprehensive_query = any(keyword in query.lower() for keyword in comprehensive_keywords)
            
            if is_comprehensive_query or include_document_overview:
                # For comprehensive queries, get more chunks and add document metadata
                st.write("Debug - Comprehensive query detected, retrieving more context...")
                
                # Get additional chunks for comprehensive coverage
                additional_chunks = self.db_manager.get_random_chunks(conversation_id, max_chunks * 2)
                
                # Combine and deduplicate chunks
                all_chunks = similar_chunks + additional_chunks
                seen_content = set()
                unique_chunks = []
                
                for chunk in all_chunks:
                    content = chunk.get("content", "")
                    if content and content not in seen_content:
                        seen_content.add(content)
                        unique_chunks.append(chunk)
                
                similar_chunks = unique_chunks[:max_chunks * 2]  # Use more chunks for comprehensive queries
            
            # Concatenate relevant content
            context_parts = []
            document_info = {}
            
            for i, chunk in enumerate(similar_chunks):
                content = chunk.get("content", "")
                similarity = chunk.get("similarity", 0)
                metadata = chunk.get("metadata", {})
                
                st.write(f"Debug - Chunk {i+1}: similarity={similarity:.3f}, content_length={len(content)}")
                
                if content:
                    context_parts.append(content)
                    
                    # Collect document metadata
                    filename = metadata.get("filename", "Unknown")
                    if filename not in document_info:
                        document_info[filename] = {
                            "chunks": 0,
                            "file_type": metadata.get("file_type", "unknown")
                        }
                    document_info[filename]["chunks"] += 1
            
            # Add document overview if comprehensive query
            if is_comprehensive_query and document_info:
                overview_parts = ["=== DOCUMENT OVERVIEW ==="]
                for filename, info in document_info.items():
                    overview_parts.append(f"Document: {filename} ({info['file_type']}) - {info['chunks']} sections included")
                overview_parts.append("=== DOCUMENT CONTENT ===")
                context_parts = overview_parts + context_parts
            
            # Add intelligent context enhancement if LangExtract was used
            final_context = "\n\n".join(context_parts)
            
            if self.lang_extract and similar_chunks:
                enhanced_context = self._add_intelligent_context_summary(similar_chunks, query)
                if enhanced_context:
                    final_context = enhanced_context + "\n\n" + final_context
            
            return final_context
            
        except Exception as e:
            st.error(f"Error searching context: {str(e)}")
            return ""
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored documents"""
        try:
            chunk_count = self.db_manager.get_chunk_count()
            document_info = self.db_manager.get_document_info()
            
            return {
                "total_chunks": chunk_count,
                "embedding_model": type(self.embedding_model).__name__ if self.embedding_model else "None",
                "unique_documents": document_info.get("unique_documents", 0),
                "total_size_mb": document_info.get("total_size_mb", 0),
                "last_updated": document_info.get("last_updated", "Never")
            }
            
        except Exception as e:
            st.error(f"Error getting document stats: {str(e)}")
            return {
                "total_chunks": 0, 
                "embedding_model": "Error",
                "unique_documents": 0,
                "total_size_mb": 0,
                "last_updated": "Error"
            }
    
    def clear_all_documents(self) -> bool:
        """Clear all stored documents"""
        try:
            return self.db_manager.clear_all_chunks()
        except Exception as e:
            st.error(f"Error clearing documents: {str(e)}")
            return False
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return getattr(st.session_state, 'processing_status', {
            'active': False,
            'progress': 0,
            'current_file': '',
            'total_files': 0,
            'processed_files': 0
        })