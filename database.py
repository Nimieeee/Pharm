"""
Simple Chatbot Database Setup
Minimal Supabase client initialization and operations for document chunks
"""

import os
from typing import Optional, List, Dict, Any
import streamlit as st
from supabase import create_client, Client


class SimpleChatbotDB:
    """Simple database manager for chatbot with document chunks and conversations"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with credentials from environment or Streamlit secrets"""
        try:
            # Try environment variables first
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            # Fallback to Streamlit secrets
            if not supabase_url or not supabase_key:
                try:
                    supabase_url = st.secrets["SUPABASE_URL"]
                    supabase_key = st.secrets["SUPABASE_ANON_KEY"]
                except KeyError:
                    pass
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
            else:
                st.error("❌ Supabase credentials not found. Please check environment variables or Streamlit secrets.")
                
        except Exception as e:
            st.error(f"❌ Error connecting to Supabase: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test database connection and document_chunks table access"""
        try:
            if not self.client:
                st.error("❌ No database client available")
                return False
            
            # Test basic connection with a simple query
            result = self.client.table("document_chunks").select("id").limit(1).execute()
            
            # Check if table exists and is accessible
            if hasattr(result, 'data'):
                return True
            else:
                st.error("❌ document_chunks table not accessible")
                return False
            
        except Exception as e:
            error_msg = str(e).lower()
            if "relation" in error_msg and "does not exist" in error_msg:
                st.error("❌ document_chunks table does not exist. Please run the schema setup first.")
            else:
                st.error(f"❌ Database connection test failed: {str(e)}")
            return False
    
    def store_document_chunk(self, content: str, embedding: List[float], metadata: Dict[str, Any], conversation_id: str, user_session_id: str = "anonymous") -> bool:
        """
        Store document chunk with embedding in database
        
        Args:
            content: Text content of the chunk
            embedding: Vector embedding of the content
            metadata: Additional metadata about the chunk
            conversation_id: ID of the conversation this chunk belongs to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                return False
            
            # Check if user_session_id column exists
            schema_updated = self._check_user_session_schema()
            
            if schema_updated:
                # Use full data with user_session_id
                data = {
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata,
                    "conversation_id": conversation_id,
                    "user_session_id": user_session_id
                }
            else:
                # Use data without user_session_id for old schema
                data = {
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata,
                    "conversation_id": conversation_id
                }
            
            result = self.client.table("document_chunks").insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            st.error(f"Error storing document chunk: {str(e)}")
            return False
    
    def search_similar_chunks(self, query_embedding: List[float], conversation_id: str, user_session_id: str, limit: int = None, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity within a conversation
        
        Args:
            query_embedding: Vector embedding of the query (384 dimensions)
            conversation_id: ID of the conversation to search within
            limit: Maximum number of results to return (None for unlimited)
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar document chunks with similarity scores
        """
        try:
            if not self.client:
                return []
            
            # Check if user_session_id schema is updated
            schema_updated = self._check_user_session_schema()
            search_limit = limit if limit is not None else 1000
            
            if schema_updated:
                # Use the updated match_document_chunks function with user session isolation
                result = self.client.rpc(
                    'match_document_chunks',
                    {
                        'query_embedding': query_embedding,
                        'conversation_uuid': conversation_id,
                        'user_session_uuid': user_session_id,
                        'match_threshold': threshold,
                        'match_count': search_limit
                    }
                ).execute()
            else:
                # Fallback: use basic vector search without user session isolation
                # This will search all documents but we'll filter by conversation_id afterward
                try:
                    # Try the old function signature first
                    result = self.client.rpc(
                        'match_document_chunks',
                        {
                            'query_embedding': query_embedding,
                            'match_threshold': threshold,
                            'match_count': search_limit
                        }
                    ).execute()
                    
                    # Filter results by conversation_id manually
                    if result.data:
                        filtered_results = []
                        for chunk in result.data:
                            # Get the full chunk data to check conversation_id
                            chunk_result = self.client.table("document_chunks").select(
                                "id, content, metadata, conversation_id"
                            ).eq("id", chunk.get("id")).execute()
                            
                            if (chunk_result.data and 
                                chunk_result.data[0].get("conversation_id") == conversation_id):
                                filtered_results.append(chunk)
                        
                        return filtered_results
                    
                except Exception:
                    # If old function doesn't exist, return empty results
                    return []
            
            return result.data if result.data else []
            
        except Exception as e:
            st.error(f"❌ Error searching document chunks: {str(e)}")
            return []
    
    def get_chunk_count(self) -> int:
        """Get total number of document chunks stored"""
        try:
            if not self.client:
                return 0
            
            result = self.client.table("document_chunks").select("id", count="exact").execute()
            return result.count if result.count else 0
            
        except Exception as e:
            st.error(f"❌ Error getting chunk count: {str(e)}")
            return 0
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get detailed information about stored documents"""
        try:
            if not self.client:
                return {"unique_documents": 0, "total_size_mb": 0, "last_updated": "Never"}
            
            # Get unique document count and metadata
            result = self.client.table("document_chunks").select("metadata, created_at, content").execute()
            
            if not result.data:
                return {"unique_documents": 0, "total_size_mb": 0, "last_updated": "Never"}
            
            # Process metadata to get unique documents
            unique_files = set()
            total_content_size = 0
            latest_date = None
            
            for row in result.data:
                # Extract filename from metadata
                metadata = row.get("metadata", {})
                if isinstance(metadata, dict) and "filename" in metadata:
                    unique_files.add(metadata["filename"])
                
                # Calculate content size
                content = row.get("content", "")
                total_content_size += len(content.encode('utf-8'))
                
                # Track latest update
                created_at = row.get("created_at")
                if created_at and (not latest_date or created_at > latest_date):
                    latest_date = created_at
            
            return {
                "unique_documents": len(unique_files),
                "total_size_mb": round(total_content_size / (1024 * 1024), 2),
                "last_updated": latest_date or "Never"
            }
            
        except Exception as e:
            st.error(f"❌ Error getting document info: {str(e)}")
            return {"unique_documents": 0, "total_size_mb": 0, "last_updated": "Error"}
    
    def clear_all_chunks(self) -> bool:
        """Clear all document chunks from the database"""
        try:
            if not self.client:
                st.error("❌ No database client available")
                return False
            
            # Delete all rows from document_chunks table
            result = self.client.table("document_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error clearing document chunks: {str(e)}")
            return False
    
    def get_documents_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific filename"""
        try:
            if not self.client:
                return []
            
            result = self.client.table("document_chunks").select("*").eq("metadata->>filename", filename).execute()
            return result.data if result.data else []
            
        except Exception as e:
            st.error(f"❌ Error getting documents by filename: {str(e)}")
            return []
    
    def get_random_chunks(self, conversation_id: str, user_session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get recent chunks for fallback (better than random for context) within a conversation"""
        try:
            if not self.client:
                return []
            
            # Set a high limit if unlimited is requested
            search_limit = limit if limit is not None else 1000
            
            # Check if user_session_id column exists
            schema_updated = self._check_user_session_schema()
            
            if schema_updated:
                # Get most recent chunks for this conversation and user session
                result = self.client.table("document_chunks").select(
                    "id, content, metadata"
                ).eq("conversation_id", conversation_id).eq("user_session_id", user_session_id).order("created_at", desc=True).limit(search_limit).execute()
            else:
                # Fallback: only filter by conversation_id
                result = self.client.table("document_chunks").select(
                    "id, content, metadata"
                ).eq("conversation_id", conversation_id).order("created_at", desc=True).limit(search_limit).execute()
            
            # Format to match similarity search results
            chunks = []
            for row in result.data:
                chunks.append({
                    "id": row.get("id"),
                    "content": row.get("content"),
                    "metadata": row.get("metadata"),
                    "similarity": 0.7  # Higher dummy similarity score
                })
            
            return chunks
            
        except Exception as e:
            st.error(f"❌ Error getting recent chunks: {str(e)}")
            return []
    
    def setup_database_schema(self) -> bool:
        """
        Setup database schema by reading and executing the SQL schema file
        Note: This requires database admin privileges
        """
        try:
            if not self.client:
                st.error("❌ No database client available")
                return False
            
            # Read the schema file
            with open('simple_chatbot_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Display schema setup instructions
            st.info("📋 Database Schema Setup Required")
            st.markdown("""
            **To set up the database schema:**
            
            1. Go to your Supabase Dashboard
            2. Navigate to **SQL Editor**
            3. Create a new query and paste the SQL below
            4. Click **Run** to execute the schema
            5. Refresh this app to test the connection
            """)
            
            st.code(schema_sql, language='sql')
            
            # Add a button to test connection after setup
            if st.button("🔄 Test Connection After Setup"):
                if self.test_connection():
                    st.success("✅ Database schema setup successful!")
                    return True
                else:
                    st.error("❌ Schema setup incomplete or connection failed")
                    return False
            
            return False  # Schema not set up yet
            
        except FileNotFoundError:
            st.error("❌ simple_chatbot_schema.sql file not found")
            return False
        except Exception as e:
            st.error(f"❌ Error setting up database schema: {str(e)}")
            return False
    
    def check_schema_exists(self) -> bool:
        """Check if the required schema exists"""
        try:
            if not self.client:
                return False
            
            # Check all required tables
            tables_to_check = ["conversations", "messages", "document_chunks"]
            
            for table in tables_to_check:
                try:
                    result = self.client.table(table).select("id").limit(1).execute()
                except Exception as table_error:
                    st.error(f"❌ Table '{table}' not found: {str(table_error)}")
                    return False
            
            return True
            
        except Exception as e:
            st.error(f"❌ Schema check failed: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if database client is initialized"""
        return self.client is not None
    
    # Conversation Management Methods
    
    def create_conversation(self, title: str, user_session_id: str = "anonymous") -> Optional[str]:
        """Create a new conversation and return its ID"""
        try:
            if not self.client:
                st.error("❌ No database client available")
                return None
            
            # Test if conversations table exists
            try:
                test_result = self.client.table("conversations").select("id").limit(1).execute()
            except Exception as table_error:
                st.error(f"❌ Conversations table not found: {str(table_error)}")
                st.info("💡 Please run the database schema setup first")
                return None
            
            result = self.client.table("conversations").insert({
                "title": title,
                "user_session_id": user_session_id
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            return None
            
        except Exception as e:
            st.error(f"❌ Error creating conversation: {str(e)}")
            return None
    
    def get_conversations(self, user_session_id: str = "anonymous") -> List[Dict[str, Any]]:
        """Get all conversations ordered by last update"""
        try:
            if not self.client:
                return []
            
            result = self.client.table("conversations").select(
                "id, title, created_at, updated_at"
            ).eq("user_session_id", user_session_id).order("updated_at", desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            st.error(f"❌ Error getting conversations: {str(e)}")
            return []
    
    def update_conversation_timestamp(self, conversation_id: str) -> bool:
        """Update the conversation's updated_at timestamp"""
        try:
            if not self.client:
                return False
            
            result = self.client.table("conversations").update({
                "updated_at": "now()"
            }).eq("id", conversation_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            st.error(f"❌ Error updating conversation timestamp: {str(e)}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its associated data"""
        try:
            if not self.client:
                return False
            
            # Delete conversation (cascades to messages and document_chunks)
            result = self.client.table("conversations").delete().eq("id", conversation_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            st.error(f"❌ Error deleting conversation: {str(e)}")
            return False
    
    def get_conversation_messages(self, conversation_id: str, user_session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        try:
            if not self.client:
                return []
            
            result = self.client.table("messages").select(
                "id, role, content, metadata, created_at"
            ).eq("conversation_id", conversation_id).eq("user_session_id", user_session_id).order("created_at").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            st.error(f"❌ Error getting conversation messages: {str(e)}")
            return []
    
    def store_message(self, conversation_id: str, role: str, content: str, user_session_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Store a message in the conversation"""
        try:
            if not self.client:
                return False
            
            data = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "user_session_id": user_session_id,
                "metadata": metadata or {}
            }
            
            result = self.client.table("messages").insert(data).execute()
            
            # Update conversation timestamp
            if len(result.data) > 0:
                self.update_conversation_timestamp(conversation_id)
            
            return len(result.data) > 0
            
        except Exception as e:
            st.error(f"❌ Error storing message: {str(e)}")
            return False
    
    def get_conversation_stats(self, conversation_id: str, user_session_id: str = "anonymous") -> Dict[str, Any]:
        """Get statistics for a conversation"""
        try:
            if not self.client:
                return {"message_count": 0, "document_count": 0, "last_activity": None}
            
            result = self.client.rpc('get_conversation_stats', {
                'conversation_uuid': conversation_id,
                'user_session_uuid': user_session_id
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return {"message_count": 0, "document_count": 0, "last_activity": None}
            
        except Exception as e:
            st.error(f"❌ Error getting conversation stats: {str(e)}")
            return {"message_count": 0, "document_count": 0, "last_activity": None}
    
    def get_all_conversation_chunks(self, conversation_id: str, user_session_id: str) -> List[Dict[str, Any]]:
        """Get ALL document chunks for a conversation (unlimited)"""
        try:
            if not self.client:
                return []
            
            # Check if user_session_id column exists (schema updated)
            schema_updated = self._check_user_session_schema()
            
            if schema_updated:
                # Use full isolation with user_session_id
                result = self.client.table("document_chunks").select(
                    "id, content, metadata, created_at, conversation_id, user_session_id"
                ).eq("conversation_id", conversation_id).eq("user_session_id", user_session_id).order("created_at").execute()
            else:
                # Fallback: only filter by conversation_id (old schema)
                result = self.client.table("document_chunks").select(
                    "id, content, metadata, created_at, conversation_id"
                ).eq("conversation_id", conversation_id).order("created_at").execute()
            
            # Format to match similarity search results with conversation isolation verification
            chunks = []
            for row in result.data:
                # For updated schema, double-check both conversation_id and user_session_id
                if schema_updated:
                    if (row.get("conversation_id") == conversation_id and 
                        row.get("user_session_id") == user_session_id):
                        chunks.append({
                            "id": row.get("id"),
                            "content": row.get("content"),
                            "metadata": row.get("metadata"),
                            "similarity": 0.5,  # Neutral similarity score
                            "created_at": row.get("created_at"),
                            "conversation_id": row.get("conversation_id"),
                            "user_session_id": row.get("user_session_id")
                        })
                else:
                    # For old schema, only check conversation_id
                    if row.get("conversation_id") == conversation_id:
                        chunks.append({
                            "id": row.get("id"),
                            "content": row.get("content"),
                            "metadata": row.get("metadata"),
                            "similarity": 0.5,  # Neutral similarity score
                            "created_at": row.get("created_at"),
                            "conversation_id": row.get("conversation_id"),
                            "user_session_id": user_session_id  # Set it for consistency
                        })
            
            return chunks
            
        except Exception as e:
            st.error(f"❌ Error getting all conversation chunks: {str(e)}")
            return []
    
    def _check_user_session_schema(self) -> bool:
        """Check if user_session_id column exists in document_chunks table"""
        try:
            if not self.client:
                return False
            
            # Try to select user_session_id column
            result = self.client.table("document_chunks").select("user_session_id").limit(1).execute()
            return True  # If this works, the column exists
            
        except Exception:
            return False  # Column doesn't exist


# Convenience function to get database instance
@st.cache_resource
def get_database():
    """Get cached database instance"""
    return SimpleChatbotDB()