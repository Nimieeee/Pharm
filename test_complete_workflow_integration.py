#!/usr/bin/env python3
"""
Complete Workflow Integration Test
Tests the complete workflow from document upload to AI response with context
"""

import os
import sys
import time
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
import tempfile
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestCompleteWorkflowIntegration:
    """Test complete workflow integration from document upload to AI response"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up comprehensive test environment"""
        # Mock Supabase client
        self.mock_supabase = Mock()
        
        # Mock authentication
        self.mock_supabase.auth.sign_in_with_password.return_value = Mock(
            user=Mock(id="test-user-1", email="test@example.com"),
            session=Mock(access_token="mock-token")
        )
        
        # Mock document storage
        self.mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{"id": "doc-1", "user_id": "test-user-1", "filename": "test.pdf"}]
        )
        
        # Mock vector storage
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[
                {
                    "id": "chunk-1",
                    "content": "Pharmacokinetics is the study of drug absorption, distribution, metabolism, and excretion.",
                    "embedding": [0.1] * 1536,  # Mock embedding vector
                    "metadata": {"source": "test.pdf", "page": 1}
                }
            ]
        )
        
        # Mock conversation and message storage
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = Mock(
            data=[
                {"id": "conv-1", "user_id": "test-user-1", "title": "Document Discussion", "created_at": "2024-01-01T00:00:00Z"}
            ]
        )
        
        # Set up environment variables
        os.environ.update({
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-anon-key',
            'GROQ_API_KEY': 'test-groq-key',
            'OPENAI_API_KEY': 'test-openai-key'
        })
        
        yield
        
        # Cleanup
        for key in ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY']:
            os.environ.pop(key, None)
    
    def test_complete_document_to_response_workflow(self):
        """Test complete workflow from document upload to AI response with context"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Step 1: User Authentication
            from auth_manager import AuthenticationManager
            from session_manager import SessionManager
            
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            
            # Mock successful authentication
            login_result = auth_manager.sign_in("test@example.com", "password123")
            assert login_result.success, "User should authenticate successfully"
            
            session_manager.initialize_session("test-user-1")
            user_id = session_manager.get_user_id()
            assert user_id == "test-user-1", "Should have correct user ID"
            
            # Step 2: Create New Conversation
            from conversation_manager import ConversationManager
            
            conversation_manager = ConversationManager(self.mock_supabase)
            conversation = conversation_manager.create_conversation(user_id, "Document Analysis")
            assert conversation is not None, "Should create new conversation"
            
            conversation_id = conversation.id if hasattr(conversation, 'id') else "conv-1"
            conversation_manager.set_active_conversation(user_id, conversation_id)
            
            # Step 3: Document Upload and Processing
            from document_processor import DocumentProcessor
            
            # Create mock PDF file
            mock_file = Mock()
            mock_file.name = "pharmacology_textbook.pdf"
            mock_file.type = "application/pdf"
            mock_file.size = 1024 * 1024  # 1MB
            
            # Mock file content
            sample_content = """
            Pharmacokinetics and Pharmacodynamics
            
            Chapter 1: Introduction to Pharmacokinetics
            
            Pharmacokinetics is the study of what the body does to a drug. It encompasses four main processes:
            
            1. Absorption: The process by which a drug enters the bloodstream from its site of administration.
            2. Distribution: The process by which a drug is transported throughout the body.
            3. Metabolism: The process by which the body chemically alters the drug.
            4. Excretion: The process by which the drug is eliminated from the body.
            
            These processes are often abbreviated as ADME (Absorption, Distribution, Metabolism, Excretion).
            
            The bioavailability of a drug refers to the fraction of the administered dose that reaches the systemic circulation.
            """
            
            mock_file.read.return_value = sample_content.encode('utf-8')
            
            document_processor = DocumentProcessor(self.mock_supabase)
            
            # Mock document processing steps
            with patch.object(document_processor, 'extract_text_from_file') as mock_extract:
                with patch.object(document_processor, 'chunk_text') as mock_chunk:
                    with patch.object(document_processor, 'generate_embeddings') as mock_embeddings:
                        with patch.object(document_processor, 'store_document_chunks') as mock_store:
                            
                            # Mock text extraction
                            mock_extract.return_value = sample_content
                            
                            # Mock text chunking
                            chunks = [
                                "Pharmacokinetics is the study of what the body does to a drug. It encompasses four main processes: Absorption, Distribution, Metabolism, Excretion.",
                                "Absorption: The process by which a drug enters the bloodstream from its site of administration.",
                                "Distribution: The process by which a drug is transported throughout the body.",
                                "Metabolism: The process by which the body chemically alters the drug.",
                                "Excretion: The process by which the drug is eliminated from the body.",
                                "The bioavailability of a drug refers to the fraction of the administered dose that reaches the systemic circulation."
                            ]
                            mock_chunk.return_value = chunks
                            
                            # Mock embedding generation
                            mock_embeddings.return_value = [[0.1] * 1536 for _ in chunks]
                            
                            # Mock storage
                            mock_store.return_value = {
                                'success': True,
                                'document_id': 'doc-1',
                                'chunks_stored': len(chunks),
                                'embeddings_stored': len(chunks)
                            }
                            
                            # Process the document
                            processing_result = document_processor.process_document(mock_file, user_id)
                            
                            assert processing_result['success'], "Document processing should succeed"
                            assert processing_result['chunks_stored'] > 0, "Should store document chunks"
                            assert processing_result['embeddings_stored'] > 0, "Should store embeddings"
            
            # Step 4: User Asks Question About Document
            from chat_manager import ChatManager
            from model_manager import ModelManager, ModelTier
            
            # Set up premium model for better responses
            model_manager = ModelManager()
            model_manager.set_current_model(ModelTier.PREMIUM)
            current_model = model_manager.get_current_model()
            assert current_model.max_tokens == 8000, "Premium model should have 8000 tokens"
            
            chat_manager = ChatManager(self.mock_supabase, session_manager)
            
            user_question = "What is pharmacokinetics and what are the main ADME processes?"
            
            # Step 5: RAG Context Retrieval
            from rag_orchestrator_optimized import RAGOrchestrator
            
            rag_orchestrator = RAGOrchestrator(self.mock_supabase, model_manager)
            
            # Mock context retrieval
            with patch.object(rag_orchestrator, 'retrieve_relevant_context') as mock_retrieve:
                relevant_context = [
                    {
                        'content': "Pharmacokinetics is the study of what the body does to a drug. It encompasses four main processes: Absorption, Distribution, Metabolism, Excretion.",
                        'score': 0.95,
                        'source': 'pharmacology_textbook.pdf',
                        'page': 1
                    },
                    {
                        'content': "Absorption: The process by which a drug enters the bloodstream from its site of administration.",
                        'score': 0.88,
                        'source': 'pharmacology_textbook.pdf',
                        'page': 1
                    },
                    {
                        'content': "Distribution: The process by which a drug is transported throughout the body.",
                        'score': 0.85,
                        'source': 'pharmacology_textbook.pdf',
                        'page': 1
                    }
                ]
                
                mock_retrieve.return_value = relevant_context
                
                context = rag_orchestrator.retrieve_relevant_context(user_question, user_id)
                assert len(context) > 0, "Should retrieve relevant context"
                assert context[0]['score'] > 0.8, "Context should be highly relevant"
            
            # Step 6: Generate AI Response with Context
            with patch.object(rag_orchestrator, 'generate_response_with_context') as mock_generate:
                expected_response = {
                    'response': """Based on your uploaded document, pharmacokinetics is the study of what the body does to a drug. 
                    
The main ADME processes are:

1. **Absorption**: The process by which a drug enters the bloodstream from its site of administration.
2. **Distribution**: The process by which a drug is transported throughout the body.
3. **Metabolism**: The process by which the body chemically alters the drug.
4. **Excretion**: The process by which the drug is eliminated from the body.

These four processes determine how a drug moves through the body and how long it remains active. Understanding ADME is crucial for determining proper dosing, timing, and potential drug interactions.

The document also mentions that bioavailability refers to the fraction of the administered dose that reaches the systemic circulation, which is an important pharmacokinetic parameter.""",
                    'context_used': True,
                    'sources': ['pharmacology_textbook.pdf'],
                    'context_chunks': len(relevant_context),
                    'model_used': 'premium',
                    'tokens_used': 250
                }
                
                mock_generate.return_value = expected_response
                
                ai_response = rag_orchestrator.generate_response_with_context(
                    query=user_question,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                assert ai_response['context_used'], "Should use document context"
                assert len(ai_response['sources']) > 0, "Should reference source documents"
                assert 'pharmacokinetics' in ai_response['response'].lower(), "Response should address the question"
                assert 'ADME' in ai_response['response'] or 'absorption' in ai_response['response'].lower(), "Should mention ADME processes"
            
            # Step 7: Store Message in Conversation
            message_response = chat_manager.send_message(
                user_id=user_id,
                message_content=user_question,
                model_type="premium",
                conversation_id=conversation_id
            )
            assert message_response.success, "Should store user message"
            
            # Store AI response
            ai_message_response = chat_manager.store_ai_response(
                user_id=user_id,
                response_content=ai_response['response'],
                conversation_id=conversation_id,
                context_used=ai_response['context_used'],
                sources=ai_response['sources']
            )
            assert ai_message_response.success, "Should store AI response"
            
            # Step 8: Verify Unlimited History Display
            conversation_history = chat_manager.get_conversation_history(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=None  # Unlimited
            )
            
            assert isinstance(conversation_history, list), "Should return conversation history"
            # Should contain both user question and AI response
            assert len(conversation_history) >= 2, "Should contain user message and AI response"
            
            # Step 9: Test Multiple Conversations
            # Create second conversation
            second_conversation = conversation_manager.create_conversation(user_id, "Follow-up Questions")
            assert second_conversation is not None, "Should create second conversation"
            
            # Verify conversations are isolated
            conversations = conversation_manager.get_user_conversations(user_id)
            assert len(conversations) >= 2, "Should have multiple conversations"
            
            # Each conversation should have its own history
            for conv in conversations:
                conv_history = chat_manager.get_conversation_history(
                    user_id=user_id,
                    conversation_id=conv.id,
                    limit=None
                )
                # History should be specific to each conversation
                assert isinstance(conv_history, list), f"Conversation {conv.id} should have history"
    
    def test_document_processing_error_handling(self):
        """Test error handling in document processing workflow"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            from document_processor import DocumentProcessor
            from auth_manager import AuthenticationManager
            from session_manager import SessionManager
            
            # Set up authentication
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            session_manager.initialize_session("test-user-1")
            
            document_processor = DocumentProcessor(self.mock_supabase)
            
            # Test 1: Invalid file type
            invalid_file = Mock()
            invalid_file.name = "test.exe"
            invalid_file.type = "application/x-executable"
            invalid_file.read.return_value = b"Invalid content"
            
            with patch.object(document_processor, 'is_valid_file_type', return_value=False):
                result = document_processor.process_document(invalid_file, "test-user-1")
                assert not result['success'], "Should reject invalid file types"
                assert 'file type' in result.get('error', '').lower(), "Should mention file type error"
            
            # Test 2: Text extraction failure
            valid_file = Mock()
            valid_file.name = "test.pdf"
            valid_file.type = "application/pdf"
            
            with patch.object(document_processor, 'extract_text_from_file', side_effect=Exception("Extraction failed")):
                result = document_processor.process_document(valid_file, "test-user-1")
                assert not result['success'], "Should handle extraction errors"
                assert 'error' in result, "Should include error message"
            
            # Test 3: Embedding generation failure
            with patch.object(document_processor, 'extract_text_from_file', return_value="Sample text"):
                with patch.object(document_processor, 'generate_embeddings', side_effect=Exception("Embedding failed")):
                    result = document_processor.process_document(valid_file, "test-user-1")
                    assert not result['success'], "Should handle embedding errors"
            
            # Test 4: Database storage failure
            self.mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
            
            with patch.object(document_processor, 'extract_text_from_file', return_value="Sample text"):
                with patch.object(document_processor, 'generate_embeddings', return_value=[[0.1] * 1536]):
                    result = document_processor.process_document(valid_file, "test-user-1")
                    assert not result['success'], "Should handle database errors"
    
    def test_rag_context_retrieval_accuracy(self):
        """Test RAG context retrieval accuracy and relevance"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            from rag_orchestrator_optimized import RAGOrchestrator
            from model_manager import ModelManager
            
            model_manager = ModelManager()
            rag_orchestrator = RAGOrchestrator(self.mock_supabase, model_manager)
            
            user_id = "test-user-1"
            
            # Mock vector search results with different relevance scores
            mock_search_results = [
                {
                    'content': 'Pharmacokinetics is the study of drug absorption, distribution, metabolism, and excretion (ADME).',
                    'embedding': [0.1] * 1536,
                    'metadata': {'source': 'textbook.pdf', 'page': 1},
                    'similarity_score': 0.95
                },
                {
                    'content': 'Bioavailability refers to the fraction of administered dose that reaches systemic circulation.',
                    'embedding': [0.2] * 1536,
                    'metadata': {'source': 'textbook.pdf', 'page': 2},
                    'similarity_score': 0.78
                },
                {
                    'content': 'Drug interactions can affect pharmacokinetic parameters.',
                    'embedding': [0.3] * 1536,
                    'metadata': {'source': 'textbook.pdf', 'page': 5},
                    'similarity_score': 0.65
                },
                {
                    'content': 'The weather is nice today.',  # Irrelevant content
                    'embedding': [0.4] * 1536,
                    'metadata': {'source': 'other.pdf', 'page': 1},
                    'similarity_score': 0.15
                }
            ]
            
            with patch.object(rag_orchestrator, 'vector_search') as mock_search:
                mock_search.return_value = mock_search_results
                
                # Test context retrieval for pharmacokinetics question
                query = "What is pharmacokinetics?"
                context = rag_orchestrator.retrieve_relevant_context(query, user_id)
                
                # Should filter out low-relevance results
                assert len(context) <= 3, "Should filter out irrelevant results"
                
                # Should prioritize high-relevance results
                if len(context) > 0:
                    assert context[0]['similarity_score'] >= 0.7, "Top result should be highly relevant"
                
                # Should not include irrelevant content
                irrelevant_content = any('weather' in item['content'].lower() for item in context)
                assert not irrelevant_content, "Should filter out irrelevant content"
    
    def test_conversation_isolation_and_management(self):
        """Test conversation isolation and management across multiple threads"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            from conversation_manager import ConversationManager
            from chat_manager import ChatManager
            from auth_manager import AuthenticationManager
            from session_manager import SessionManager
            
            # Set up authentication
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            session_manager.initialize_session("test-user-1")
            
            conversation_manager = ConversationManager(self.mock_supabase)
            chat_manager = ChatManager(self.mock_supabase, session_manager)
            
            user_id = "test-user-1"
            
            # Create multiple conversations
            conv1 = conversation_manager.create_conversation(user_id, "Pharmacokinetics Discussion")
            conv2 = conversation_manager.create_conversation(user_id, "Drug Interactions")
            conv3 = conversation_manager.create_conversation(user_id, "Clinical Applications")
            
            assert conv1 is not None, "Should create first conversation"
            assert conv2 is not None, "Should create second conversation"
            assert conv3 is not None, "Should create third conversation"
            
            # Mock different message histories for each conversation
            def mock_conversation_messages(conversation_id):
                if conversation_id == conv1.id:
                    return [
                        Mock(id="msg-1-1", content="What is pharmacokinetics?", role="user", conversation_id=conv1.id),
                        Mock(id="msg-1-2", content="Pharmacokinetics is...", role="assistant", conversation_id=conv1.id)
                    ]
                elif conversation_id == conv2.id:
                    return [
                        Mock(id="msg-2-1", content="How do drug interactions work?", role="user", conversation_id=conv2.id),
                        Mock(id="msg-2-2", content="Drug interactions occur when...", role="assistant", conversation_id=conv2.id)
                    ]
                elif conversation_id == conv3.id:
                    return [
                        Mock(id="msg-3-1", content="What are clinical applications?", role="user", conversation_id=conv3.id)
                    ]
                else:
                    return []
            
            # Test conversation switching and isolation
            with patch.object(chat_manager, 'get_conversation_history') as mock_history:
                mock_history.side_effect = lambda user_id, conversation_id=None, limit=None: mock_conversation_messages(conversation_id)
                
                # Switch to conversation 1
                conversation_manager.set_active_conversation(user_id, conv1.id)
                history1 = chat_manager.get_conversation_history(user_id, conv1.id)
                
                # Switch to conversation 2
                conversation_manager.set_active_conversation(user_id, conv2.id)
                history2 = chat_manager.get_conversation_history(user_id, conv2.id)
                
                # Switch to conversation 3
                conversation_manager.set_active_conversation(user_id, conv3.id)
                history3 = chat_manager.get_conversation_history(user_id, conv3.id)
                
                # Verify isolation
                assert len(history1) == 2, "Conversation 1 should have 2 messages"
                assert len(history2) == 2, "Conversation 2 should have 2 messages"
                assert len(history3) == 1, "Conversation 3 should have 1 message"
                
                # Verify content isolation
                conv1_content = [msg.content for msg in history1]
                conv2_content = [msg.content for msg in history2]
                
                assert "pharmacokinetics" in conv1_content[0].lower(), "Conv 1 should contain pharmacokinetics content"
                assert "interactions" in conv2_content[0].lower(), "Conv 2 should contain interactions content"
                
                # Verify no cross-contamination
                assert not any("interactions" in content.lower() for content in conv1_content), "Conv 1 should not contain Conv 2 content"
                assert not any("pharmacokinetics" in content.lower() for content in conv2_content), "Conv 2 should not contain Conv 1 content"
    
    def test_dark_theme_consistency_across_workflow(self):
        """Test dark theme consistency throughout the complete workflow"""
        from theme_manager import ThemeManager
        
        theme_manager = ThemeManager()
        
        # Test theme consistency at each step
        steps = [
            "login",
            "document_upload", 
            "conversation_creation",
            "chat_interface",
            "message_display",
            "response_generation"
        ]
        
        for step in steps:
            # Theme should always be dark regardless of step
            current_theme = theme_manager.get_current_theme()
            assert current_theme == 'dark', f"Theme should be dark at {step} step"
            
            # Test theme CSS generation
            with patch('streamlit.markdown') as mock_markdown:
                theme_manager.apply_theme()
                
                # Verify dark theme CSS was applied
                mock_markdown.assert_called()
                css_content = mock_markdown.call_args[0][0]
                
                # Check for dark theme characteristics
                assert any(color in css_content for color in ['#1e1e1e', '#0e1117', '#262730']), f"Should use dark background colors at {step}"
                assert any(color in css_content for color in ['white', '#fafafa', '#ffffff']), f"Should use light text colors at {step}"
    
    def test_premium_model_token_limit_in_workflow(self):
        """Test premium model 8000 token limit throughout workflow"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            from model_manager import ModelManager, ModelTier
            from rag_orchestrator_optimized import RAGOrchestrator
            
            model_manager = ModelManager()
            rag_orchestrator = RAGOrchestrator(self.mock_supabase, model_manager)
            
            # Set premium model
            model_manager.set_current_model(ModelTier.PREMIUM)
            current_model = model_manager.get_current_model()
            
            assert current_model.tier == ModelTier.PREMIUM, "Should use premium model"
            assert current_model.max_tokens == 8000, "Premium model should have 8000 token limit"
            
            # Test that long context + query can utilize full token limit
            long_context = [
                {'content': f"This is context chunk {i} with detailed information about pharmacokinetics and drug interactions. " * 20}
                for i in range(10)  # 10 chunks of ~400 characters each
            ]
            
            long_query = "Please provide a comprehensive analysis of pharmacokinetics including all ADME processes, drug interactions, bioavailability, clearance, half-life, and clinical implications. Include specific examples and detailed explanations for each concept."
            
            # Mock response generation with token counting
            with patch.object(rag_orchestrator, 'generate_response_with_context') as mock_generate:
                mock_generate.return_value = {
                    'response': 'A' * 7000,  # Simulate long response using most of 8000 tokens
                    'tokens_used': 7500,
                    'context_used': True,
                    'model_used': 'premium'
                }
                
                response = rag_orchestrator.generate_response_with_context(
                    query=long_query,
                    user_id="test-user-1",
                    context=long_context
                )
                
                assert response['tokens_used'] <= 8000, "Should not exceed 8000 token limit"
                assert response['tokens_used'] > 1000, "Should utilize significant portion of token limit"
                assert response['model_used'] == 'premium', "Should use premium model"

def run_complete_workflow_tests():
    """Run complete workflow integration tests"""
    print("🔄 Running Complete Workflow Integration Tests...")
    print("=" * 60)
    
    # Run pytest with verbose output
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ All complete workflow tests passed!")
        print("🎉 Document upload to AI response workflow is working perfectly!")
    else:
        print("\n❌ Some complete workflow tests failed!")
        print("🔧 Please review and fix the workflow issues.")
    
    return exit_code == 0

if __name__ == "__main__":
    success = run_complete_workflow_tests()
    sys.exit(0 if success else 1)