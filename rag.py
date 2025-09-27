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
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

from database import SimpleChatbotDB


class RAGManager:
    """Manages document processing and retrieval for RAG system"""
    
    VERSION = "2.0.0"  # Version to force cache refresh
    
    def __init__(self):
        self.db_manager = SimpleChatbotDB()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Increased from 1000 for larger chunks
            chunk_overlap=300,  # Increased overlap for better continuity
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Better splitting on paragraphs and sentences
        )
        self.embedding_model = None
        self.langextract_available = LANGEXTRACT_AVAILABLE
        self._initialize_embeddings()
        

    
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
        
        # Check LangExtract availability and show setup info
        if LANGEXTRACT_AVAILABLE:
            st.info("🧠 LangExtract available for enhanced document intelligence")
            # Check if API key is available
            if not os.getenv("LANGEXTRACT_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
                st.warning("💡 For LangExtract features, set LANGEXTRACT_API_KEY or GOOGLE_API_KEY environment variable")
        else:
            st.info("💡 Install LangExtract for enhanced document understanding: pip install langextract")
    
    def _initialize_document_intelligence(self):
        """Compatibility method for cached sessions - no longer needed"""
        pass
    
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
            if self.langextract_available and len(documents) > 0:
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
            if not LANGEXTRACT_AVAILABLE or not documents:
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
            if not LANGEXTRACT_AVAILABLE:
                return {}
            
            # Define extraction task based on document type
            file_extension = filename.lower().split('.')[-1]
            
            if 'pharmacology' in filename.lower() or 'drug' in filename.lower() or 'pharm' in filename.lower():
                # Pharmacology-specific extraction
                prompt = """Extract pharmacological information including drug names, mechanisms of action, 
                side effects, dosages, interactions, and therapeutic uses. Use exact text from the document."""
                
                examples = [
                    lx.data.ExampleData(
                        text="Tamoxifen is a selective estrogen receptor modulator (SERM) used in breast cancer treatment. Common side effects include hot flashes and nausea. The typical dose is 20mg daily.",
                        extractions=[
                            lx.data.Extraction(
                                extraction_class="drug_name",
                                extraction_text="Tamoxifen",
                                attributes={"type": "medication"}
                            ),
                            lx.data.Extraction(
                                extraction_class="mechanism",
                                extraction_text="selective estrogen receptor modulator (SERM)",
                                attributes={"category": "mechanism_of_action"}
                            ),
                            lx.data.Extraction(
                                extraction_class="therapeutic_use",
                                extraction_text="breast cancer treatment",
                                attributes={"indication": "oncology"}
                            ),
                            lx.data.Extraction(
                                extraction_class="side_effect",
                                extraction_text="hot flashes and nausea",
                                attributes={"severity": "common"}
                            ),
                            lx.data.Extraction(
                                extraction_class="dosage",
                                extraction_text="20mg daily",
                                attributes={"frequency": "daily"}
                            )
                        ]
                    )
                ]
            else:
                # General document extraction
                prompt = """Extract key topics, important facts, and main concepts from the document. 
                Focus on the most important information and use exact text."""
                
                examples = [
                    lx.data.ExampleData(
                        text="This research paper discusses the cardiovascular effects of exercise. Regular physical activity reduces blood pressure and improves heart function.",
                        extractions=[
                            lx.data.Extraction(
                                extraction_class="key_topic",
                                extraction_text="cardiovascular effects of exercise",
                                attributes={"category": "main_topic"}
                            ),
                            lx.data.Extraction(
                                extraction_class="important_fact",
                                extraction_text="Regular physical activity reduces blood pressure",
                                attributes={"type": "finding"}
                            ),
                            lx.data.Extraction(
                                extraction_class="important_fact",
                                extraction_text="improves heart function",
                                attributes={"type": "benefit"}
                            )
                        ]
                    )
                ]
            
            # Use Gemini model for extraction (you may need to set up API key)
            try:
                result = lx.extract(
                    text_or_documents=content[:5000],  # Limit content size for API efficiency
                    prompt_description=prompt,
                    examples=examples,
                    model_id="gemini-2.5-flash",  # Using recommended model
                    max_workers=1,  # Single worker for small content
                    fence_output=False
                )
                
                # Process the extraction results
                extracted_data = self._process_langextract_results(result)
                return extracted_data
                
            except Exception as api_error:
                st.warning(f"LangExtract API error: {str(api_error)}")
                st.info("💡 Make sure you have set up your Google AI API key for LangExtract")
                return {}
            
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
    
    def _process_langextract_results(self, result) -> Dict[str, Any]:
        """Process LangExtract results into structured format"""
        try:
            entities = []
            topics = []
            mechanisms = []
            side_effects = []
            dosages = []
            therapeutic_uses = []
            important_facts = []
            
            # Extract information from LangExtract result
            if hasattr(result, 'extractions') and result.extractions:
                for extraction in result.extractions:
                    extraction_class = extraction.extraction_class.lower()
                    text = extraction.extraction_text
                    
                    if extraction_class == "drug_name":
                        entities.append(text)
                    elif extraction_class == "mechanism":
                        mechanisms.append(text)
                    elif extraction_class == "side_effect":
                        side_effects.append(text)
                    elif extraction_class == "dosage":
                        dosages.append(text)
                    elif extraction_class == "therapeutic_use":
                        therapeutic_uses.append(text)
                    elif extraction_class == "key_topic":
                        topics.append(text)
                    elif extraction_class == "important_fact":
                        important_facts.append(text)
            
            return {
                "entities": entities,
                "topics": topics,
                "document_type": "processed_document",
                "structure": {
                    "mechanisms": mechanisms,
                    "side_effects": side_effects,
                    "dosages": dosages,
                    "interactions": [],  # Could be extracted separately
                    "therapeutic_uses": therapeutic_uses,
                    "important_facts": important_facts
                }
            }
            
        except Exception as e:
            st.warning(f"Error processing LangExtract results: {str(e)}")
            return {}
    
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
    
    def search_relevant_context(self, query: str, conversation_id: str, max_chunks: int = None, include_document_overview: bool = False, unlimited_context: bool = False) -> str:
        """
        Search for relevant context based on query within a conversation
        
        Args:
            query: User query
            conversation_id: ID of the conversation to search within
            max_chunks: Maximum number of chunks to retrieve (None for unlimited)
            include_document_overview: Whether to include document overview/summary
            unlimited_context: Whether to retrieve all available chunks
            
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
            
            # Search for similar chunks - use unlimited if requested
            search_limit = 1000 if unlimited_context or max_chunks is None else (max_chunks or 10)
            similar_chunks = self.db_manager.search_similar_chunks(query_embedding, conversation_id, search_limit, threshold=0.1)
            
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
                if unlimited_context:
                    st.write("Debug - Getting ALL chunks for unlimited context...")
                    similar_chunks = self.db_manager.get_all_conversation_chunks(conversation_id)
                else:
                    fallback_limit = max_chunks or 10
                    similar_chunks = self.db_manager.get_random_chunks(conversation_id, fallback_limit)
            
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
                additional_limit = 1000 if unlimited_context else (max_chunks * 3 if max_chunks else 50)
                additional_chunks = self.db_manager.get_random_chunks(conversation_id, additional_limit)
                
                # Combine and deduplicate chunks
                all_chunks = similar_chunks + additional_chunks
                seen_content = set()
                unique_chunks = []
                
                for chunk in all_chunks:
                    content = chunk.get("content", "")
                    if content and content not in seen_content:
                        seen_content.add(content)
                        unique_chunks.append(chunk)
                
                # Use all unique chunks if unlimited, otherwise limit
                if unlimited_context or max_chunks is None:
                    similar_chunks = unique_chunks  # No limit
                else:
                    similar_chunks = unique_chunks[:max_chunks * 2]
            
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
            
            # Smart context management - check total length and truncate if needed
            full_context = "\n\n".join(context_parts)
            
            # Mistral models can handle up to ~32k tokens, but let's be conservative
            max_context_chars = 100000  # ~25k tokens approximately
            
            if len(full_context) > max_context_chars:
                st.write(f"Debug - Context too large ({len(full_context)} chars), truncating to {max_context_chars} chars")
                
                # Prioritize chunks by similarity score
                sorted_chunks = sorted(similar_chunks, key=lambda x: x.get("similarity", 0), reverse=True)
                
                truncated_parts = []
                current_length = 0
                
                # Add overview first if it exists
                if is_comprehensive_query and document_info:
                    for part in overview_parts:
                        if current_length + len(part) < max_context_chars:
                            truncated_parts.append(part)
                            current_length += len(part) + 2  # +2 for \n\n
                
                # Add chunks in order of similarity
                for chunk in sorted_chunks:
                    content = chunk.get("content", "")
                    if content and current_length + len(content) < max_context_chars:
                        truncated_parts.append(content)
                        current_length += len(content) + 2
                    else:
                        break
                
                full_context = "\n\n".join(truncated_parts)
                st.write(f"Debug - Final context length: {len(full_context)} chars with {len(truncated_parts)} parts")
            
            # Add intelligent context enhancement if LangExtract was used
            if self.langextract_available and similar_chunks:
                enhanced_context = self._add_intelligent_context_summary(similar_chunks, query)
                if enhanced_context:
                    full_context = enhanced_context + "\n\n" + full_context
            
            return full_context
            
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