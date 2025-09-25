"""
Document Management Usage Example
Demonstrates how to use the document management system in the pharmacology chat app
"""

import os
from datetime import datetime
from typing import List

# Import document management components
from document_manager import DocumentManager
from document_ui import DocumentInterface

def example_document_upload():
    """Example of uploading documents for a user"""
    print("📁 Document Upload Example")
    print("-" * 40)
    
    # Initialize document manager (requires Supabase credentials)
    try:
        doc_manager = DocumentManager()
        user_id = "example-user-123"
        
        print(f"User ID: {user_id}")
        print("Ready to upload documents...")
        
        # In a real Streamlit app, you would get uploaded_files from st.file_uploader
        # For this example, we'll show the method signature
        print("\nUpload method signature:")
        print("doc_manager.upload_documents(")
        print("    uploaded_files=uploaded_files,  # From st.file_uploader")
        print("    user_id=user_id,")
        print("    chunk_size=1000,")
        print("    chunk_overlap=200")
        print(")")
        
        return doc_manager, user_id
        
    except Exception as e:
        print(f"❌ Error initializing document manager: {e}")
        print("Make sure your Supabase credentials are configured.")
        return None, None


def example_document_retrieval(doc_manager: DocumentManager, user_id: str):
    """Example of retrieving user documents"""
    print("\n📚 Document Retrieval Example")
    print("-" * 40)
    
    try:
        # Get user documents
        documents = doc_manager.get_user_documents(user_id, limit=10)
        
        print(f"Found {len(documents)} document sources for user {user_id}")
        
        for doc in documents:
            print(f"\n📄 {doc.source}")
            print(f"   Chunks: {doc.chunk_count}")
            print(f"   Type: {doc.file_type}")
            print(f"   Uploaded: {doc.upload_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Preview: {doc.content_preview[:100]}...")
        
        return documents
        
    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")
        return []


def example_document_search(doc_manager: DocumentManager, user_id: str):
    """Example of searching through user documents"""
    print("\n🔍 Document Search Example")
    print("-" * 40)
    
    try:
        # Search for pharmacology-related content
        search_query = "drug interactions"
        results = doc_manager.search_user_documents(
            user_id=user_id,
            query=search_query,
            limit=5
        )
        
        print(f"Search query: '{search_query}'")
        print(f"Found {len(results)} matching documents")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result.source}")
            print(f"   Similarity: {result.similarity:.3f}")
            print(f"   Content: {result.content[:150]}...")
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        return []


def example_document_stats(doc_manager: DocumentManager, user_id: str):
    """Example of getting document statistics"""
    print("\n📊 Document Statistics Example")
    print("-" * 40)
    
    try:
        stats = doc_manager.get_document_stats(user_id)
        
        print(f"User: {user_id}")
        print(f"Total document sources: {stats['total_sources']}")
        print(f"Total document chunks: {stats['total_chunks']}")
        print(f"Total messages sent: {stats['message_count']}")
        
        if stats['file_types']:
            print("\nFile type breakdown:")
            for file_type, count in stats['file_types'].items():
                print(f"  {file_type.upper()}: {count} sources")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting document stats: {e}")
        return {}


def example_document_deletion(doc_manager: DocumentManager, user_id: str):
    """Example of deleting user documents"""
    print("\n🗑️ Document Deletion Example")
    print("-" * 40)
    
    try:
        # Example: Delete a specific document by source
        source_to_delete = "example_document.pdf"
        
        print(f"Deleting document: {source_to_delete}")
        print("Method signature:")
        print("success = doc_manager.delete_document_by_source(")
        print(f"    user_id='{user_id}',")
        print(f"    source='{source_to_delete}'")
        print(")")
        
        # Example: Delete all user documents
        print("\nTo delete all user documents:")
        print("success = doc_manager.delete_all_user_documents(")
        print(f"    user_id='{user_id}'")
        print(")")
        
        print("\n⚠️  Note: Deletion is permanent and cannot be undone!")
        
    except Exception as e:
        print(f"❌ Error in deletion example: {e}")


def example_streamlit_integration():
    """Example of integrating with Streamlit"""
    print("\n🎨 Streamlit Integration Example")
    print("-" * 40)
    
    print("""
# In your Streamlit app:

import streamlit as st
from document_manager import DocumentManager
from document_ui import DocumentInterface

# Initialize components
doc_manager = DocumentManager()
doc_interface = DocumentInterface(doc_manager)

# Get current user ID from session
user_id = st.session_state.get('user_id')

if user_id:
    # Render document management page
    doc_interface.render_document_page(user_id)
    
    # Or render sidebar summary
    doc_interface.render_sidebar_summary(user_id)
else:
    st.error("Please log in to access document management")
""")


def example_chat_integration():
    """Example of integrating with chat functionality"""
    print("\n💬 Chat Integration Example")
    print("-" * 40)
    
    print("""
# Document-enhanced chat workflow:

1. User uploads documents via document management interface
2. Documents are processed and stored with user ID association
3. When user asks a question in chat:
   - RAG system searches user's documents for relevant context
   - AI generates response using both general knowledge and user documents
   - Response includes citations from user's uploaded documents

# In RAG pipeline:
user_documents = doc_manager.search_user_documents(
    user_id=user_id,
    query=user_question,
    limit=5
)

# Use retrieved documents as context for AI response
context = "\\n".join([doc.content for doc in user_documents])
enhanced_prompt = f"Context: {context}\\n\\nQuestion: {user_question}"
""")


def main():
    """Main example demonstration"""
    print("🧬 Pharmacology Chat App - Document Management Examples")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("⚠️  Supabase credentials not configured.")
        print("Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        print("\nShowing example usage without actual database operations:")
        print("=" * 60)
    
    # Document upload example
    doc_manager, user_id = example_document_upload()
    
    if doc_manager and user_id:
        # Document retrieval example
        documents = example_document_retrieval(doc_manager, user_id)
        
        # Document search example
        search_results = example_document_search(doc_manager, user_id)
        
        # Document statistics example
        stats = example_document_stats(doc_manager, user_id)
        
        # Document deletion example
        example_document_deletion(doc_manager, user_id)
    
    # Integration examples
    example_streamlit_integration()
    example_chat_integration()
    
    print("\n" + "=" * 60)
    print("✅ Document Management Examples Complete!")
    print("\nKey Features Demonstrated:")
    print("• User-scoped document upload and storage")
    print("• Document retrieval and management")
    print("• Semantic search through user documents")
    print("• Document statistics and analytics")
    print("• Integration with Streamlit and chat functionality")
    print("• User data isolation and security")


if __name__ == "__main__":
    main()