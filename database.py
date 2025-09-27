"""
Simple Chatbot Database Setup
Minimal Supabase client initialization and operations for document chunks
"""

import os
from typing import Optional, List, Dict, Any
import streamlit as st
from supabase import create_client, Client


class SimpleChatbotDB:
    """Simple database manager for chatbot with document chunks"""
    
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
                st.success("✅ Connected to Supabase database")
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
                st.success("✅ Database connection test successful")
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
    
    def store_document_chunk(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        Store document chunk with embedding in database
        
        Args:
            content: Text content of the chunk
            embedding: Vector embedding of the content
            metadata: Additional metadata about the chunk
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                return False
            
            data = {
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            }
            
            result = self.client.table("document_chunks").insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            st.error(f"Error storing document chunk: {str(e)}")
            return False
    
    def search_similar_chunks(self, query_embedding: List[float], limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity
        
        Args:
            query_embedding: Vector embedding of the query (384 dimensions)
            limit: Maximum number of results to return
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar document chunks with similarity scores
        """
        try:
            if not self.client:
                st.write("Debug - No database client available")
                return []
            
            # Use the match_document_chunks function for vector similarity search
            result = self.client.rpc(
                'match_document_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            st.write(f"Debug - Vector search found: {len(result.data) if result.data else 0} chunks")
            
            return result.data if result.data else []
            
        except Exception as e:
            st.error(f"❌ Error searching document chunks: {str(e)}")
            st.write(f"Debug - Search error details: {e}")
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
            
            st.success("✅ All document chunks cleared successfully")
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
    
    def get_random_chunks(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent chunks for fallback (better than random for context)"""
        try:
            if not self.client:
                return []
            
            # Get most recent chunks (likely more relevant)
            result = self.client.table("document_chunks").select(
                "id, content, metadata"
            ).order("created_at", desc=True).limit(limit).execute()
            
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
            
            # Try to query the document_chunks table
            result = self.client.table("document_chunks").select("id").limit(1).execute()
            return True
            
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """Check if database client is initialized"""
        return self.client is not None


# Convenience function to get database instance
@st.cache_resource
def get_database():
    """Get cached database instance"""
    return SimpleChatbotDB()