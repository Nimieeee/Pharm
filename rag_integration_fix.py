#!/usr/bin/env python3
"""
RAG Integration Fix for Streamlit App
Integrates the fixed RAG pipeline into the main application
"""

import sys
import streamlit as st
from typing import List, Dict, Any, Optional
from rag_pipeline_integration import get_rag_pipeline

def initialize_rag_in_app():
    """Initialize RAG pipeline in Streamlit app context"""
    if 'rag_pipeline' not in st.session_state:
        st.session_state.rag_pipeline = get_rag_pipeline()
    
    return st.session_state.rag_pipeline

def handle_document_upload(uploaded_files: List, user_id: str) -> Dict[str, Any]:
    """
    Handle document upload with proper error handling
    
    Args:
        uploaded_files: List of uploaded files from Streamlit
        user_id: Current user ID
        
    Returns:
        Result dictionary with success status and details
    """
    if not uploaded_files:
        return {
            'success': False,
            'message': 'No files uploaded',
            'documents_processed': 0
        }
    
    pipeline = initialize_rag_in_app()
    
    # Show progress
    with st.spinner(f'Processing {len(uploaded_files)} file(s)...'):
        result = pipeline.process_documents(uploaded_files, user_id)
    
    if result['success']:
        return {
            'success': True,
            'message': f"Successfully processed {result['documents_processed']} document chunks",
            'documents_processed': result['documents_processed']
        }
    else:
        return {
            'success': False,
            'message': f"Document processing failed: {result.get('error', 'Unknown error')}",
            'documents_processed': 0
        }

def handle_rag_query(query: str, user_id: str, model_type: str = "fast") -> Dict[str, Any]:
    """
    Handle RAG query with proper error handling
    
    Args:
        query: User query
        user_id: Current user ID
        model_type: Model type to use
        
    Returns:
        Query result dictionary
    """
    pipeline = initialize_rag_in_app()
    
    # Check if documents are available
    stats = pipeline.get_user_document_stats(user_id)
    doc_count = stats.get('document_count', 0)
    
    if doc_count == 0:
        return {
            'success': True,
            'response': "I don't have any uploaded documents to search through. You can upload documents using the sidebar, or I can answer general pharmacology questions using my built-in knowledge.",
            'context_used': '',
            'documents_retrieved': 0,
            'using_rag': False
        }
    
    # Process query
    result = pipeline.query_documents(query, user_id, model_type)
    
    if result['success']:
        return {
            'success': True,
            'response': result['response'],
            'context_used': result.get('context_used', ''),
            'documents_retrieved': result.get('documents_retrieved', 0),
            'using_rag': True
        }
    else:
        # Fallback to non-RAG response
        return {
            'success': True,
            'response': f"I encountered an issue searching your documents ({result.get('error', 'unknown error')}), but I can still help with general pharmacology questions using my built-in knowledge.",
            'context_used': '',
            'documents_retrieved': 0,
            'using_rag': False
        }

def handle_rag_stream(query: str, user_id: str, model_type: str = "fast"):
    """
    Handle streaming RAG query
    
    Args:
        query: User query
        user_id: Current user ID
        model_type: Model type to use
        
    Yields:
        Response chunks
    """
    pipeline = initialize_rag_in_app()
    
    # Check if documents are available
    stats = pipeline.get_user_document_stats(user_id)
    doc_count = stats.get('document_count', 0)
    
    if doc_count == 0:
        yield "I don't have any uploaded documents to search through. You can upload documents using the sidebar, or I can answer general pharmacology questions using my built-in knowledge."
        return
    
    # Process streaming query
    result = pipeline.query_documents(query, user_id, model_type, stream=True)
    
    if result['success'] and 'stream' in result:
        try:
            for chunk in result['stream']:
                yield chunk
        except Exception as e:
            yield f"I encountered an issue while streaming the response: {str(e)}"
    else:
        yield f"I encountered an issue searching your documents, but I can still help with general pharmacology questions."

def show_document_stats(user_id: str):
    """Show document statistics in sidebar"""
    pipeline = initialize_rag_in_app()
    stats = pipeline.get_user_document_stats(user_id)
    
    if stats.get('error'):
        st.sidebar.warning(f"Document stats unavailable: {stats['error']}")
    else:
        doc_count = stats.get('document_count', 0)
        if doc_count > 0:
            st.sidebar.success(f"📚 {doc_count} document chunks available")
        else:
            st.sidebar.info("📚 No documents uploaded yet")

def show_rag_health():
    """Show RAG pipeline health status"""
    pipeline = initialize_rag_in_app()
    health = pipeline.health_check()
    
    if health['overall'] == 'healthy':
        st.sidebar.success("🟢 RAG Pipeline: Healthy")
    elif health['overall'] == 'degraded':
        st.sidebar.warning("🟡 RAG Pipeline: Degraded (some features unavailable)")
    else:
        st.sidebar.error("🔴 RAG Pipeline: Error")
    
    # Show details in expander
    with st.sidebar.expander("RAG System Details"):
        for component, status in health['components'].items():
            if status == 'ok':
                st.write(f"✅ {component}")
            elif status == 'unavailable':
                st.write(f"⚠️ {component} (unavailable)")
            else:
                st.write(f"❌ {component}")
        
        if health['errors']:
            st.write("**Issues:**")
            for error in health['errors']:
                st.write(f"- {error}")

def clear_user_documents(user_id: str) -> bool:
    """Clear all documents for a user"""
    pipeline = initialize_rag_in_app()
    return pipeline.delete_user_documents(user_id)

# Integration functions for existing app
def integrate_rag_with_chat_interface():
    """
    Integration helper for chat interface
    Returns functions that can be used in the main chat app
    """
    return {
        'handle_document_upload': handle_document_upload,
        'handle_rag_query': handle_rag_query,
        'handle_rag_stream': handle_rag_stream,
        'show_document_stats': show_document_stats,
        'show_rag_health': show_rag_health,
        'clear_user_documents': clear_user_documents
    }

def test_streamlit_integration():
    """Test RAG integration in Streamlit context"""
    print("🔧 Testing Streamlit RAG Integration")
    print("=" * 40)
    
    # Mock Streamlit session state
    class MockSessionState:
        def __init__(self):
            self._state = {}
        
        def __contains__(self, key):
            return key in self._state
        
        def __getitem__(self, key):
            return self._state[key]
        
        def __setitem__(self, key, value):
            self._state[key] = value
    
    # Mock st.session_state
    import sys
    if 'streamlit' not in sys.modules:
        class MockStreamlit:
            session_state = MockSessionState()
        
        sys.modules['streamlit'] = MockStreamlit()
        import streamlit as st
    
    # Test initialization
    pipeline = initialize_rag_in_app()
    health = pipeline.health_check()
    
    print(f"Integration Status: {health['overall']}")
    
    # Test integration functions
    integration_funcs = integrate_rag_with_chat_interface()
    print(f"Integration functions available: {len(integration_funcs)}")
    
    for func_name in integration_funcs:
        print(f"  ✅ {func_name}")
    
    return True

if __name__ == "__main__":
    success = test_streamlit_integration()
    print("\n🎉 RAG Integration ready for Streamlit app!")
    sys.exit(0 if success else 1)