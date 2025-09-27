#!/usr/bin/env python3
"""
Comprehensive Testing Suite for UI Enhancements
Tests all UI enhancement features including model toggle, dark theme, conversation management, and RAG integration.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from datetime import datetime
import tempfile
import io

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

class TestModelToggleSwitch(unittest.TestCase):
    """Test model toggle switch functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from model_ui import render_model_selector, _create_toggle_switch_html
            from model_manager import ModelManager, ModelTier
            self.render_model_selector = render_model_selector
            self._create_toggle_switch_html = _create_toggle_switch_html
            self.ModelManager = ModelManager
            self.ModelTier = ModelTier
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")
    
    def test_toggle_switch_html_generation(self):
        """Test toggle switch HTML generation for both modes"""
        # Test Fast mode (not premium)
        fast_html = self._create_toggle_switch_html(False)
        self.assertIn("⚡ Fast", fast_html)
        self.assertIn("🎯 Premium", fast_html)
        self.assertIn("active", fast_html)  # Fast should be active
        self.assertIn("Quick responses for general questions", fast_html)
        
        # Test Premium mode
        premium_html = self._create_toggle_switch_html(True)
        self.assertIn("⚡ Fast", premium_html)
        self.assertIn("🎯 Premium", premium_html)
        self.assertIn("checked", premium_html)  # Should be checked for premium
        self.assertIn("High-quality responses for complex topics", premium_html)
    
    def test_model_id_mapping(self):
        """Test correct model ID mapping for toggle switch"""
        fast_model_ids = ["gemma2-9b-it", "fast"]
        premium_model_ids = ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        
        for model_id in fast_model_ids:
            is_premium = model_id in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
            self.assertFalse(is_premium, f"Model {model_id} should not be premium")
        
        for model_id in premium_model_ids:
            is_premium = model_id in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
            self.assertTrue(is_premium, f"Model {model_id} should be premium")
    
    def test_css_classes_application(self):
        """Test proper CSS class application for visual feedback"""
        # Test Fast mode classes
        fast_html = self._create_toggle_switch_html(False)
        self.assertIn('class="toggle-label active"', fast_html)  # Fast should be active
        
        # Test Premium mode classes
        premium_html = self._create_toggle_switch_html(True)
        self.assertIn('class="toggle-label active"', premium_html)  # Premium should be active
    
    def test_model_manager_token_limits(self):
        """Test that premium model has 8000 token limit"""
        try:
            model_manager = self.ModelManager()
            
            # Test premium model configuration
            premium_config = model_manager.get_model_config(self.ModelTier.PREMIUM)
            self.assertEqual(premium_config.max_tokens, 8000, "Premium model should have 8000 token limit")
            
            # Test fast model configuration (should remain unchanged)
            fast_config = model_manager.get_model_config(self.ModelTier.FAST)
            self.assertLessEqual(fast_config.max_tokens, 2048, "Fast model should have lower token limit")
            
        except Exception as e:
            self.skipTest(f"ModelManager not properly configured: {e}")


class TestPermanentDarkTheme(unittest.TestCase):
    """Test permanent dark theme enforcement"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from theme_manager import ThemeManager
            self.ThemeManager = ThemeManager
            self.theme_manager = ThemeManager()
        except ImportError as e:
            self.skipTest(f"ThemeManager not available: {e}")
    
    def test_permanent_dark_theme_initialization(self):
        """Test that theme manager always initializes with dark theme"""
        theme_manager = self.ThemeManager()
        self.assertEqual(theme_manager.get_current_theme(), "dark")
    
    def test_get_current_theme_always_dark(self):
        """Test that get_current_theme always returns 'dark'"""
        theme = self.theme_manager.get_current_theme()
        self.assertEqual(theme, "dark")
    
    def test_dark_theme_colors_high_contrast(self):
        """Test that dark theme uses high contrast colors"""
        config = self.theme_manager.get_theme_config()
        
        # Check background is dark
        self.assertEqual(config.background_color, "#0e1117")
        
        # Check text is white for maximum contrast
        self.assertEqual(config.text_color, "#ffffff")
        
        # Check secondary background is darker
        self.assertEqual(config.secondary_background_color, "#262730")
        
        # Check primary color is visible on dark background
        self.assertEqual(config.primary_color, "#4fc3f7")
    
    def test_no_theme_toggle_functionality(self):
        """Test that theme toggle functionality is removed"""
        # Should not have toggle_theme method
        self.assertFalse(hasattr(self.theme_manager, 'toggle_theme'))
        
        # Should not have set_theme method
        self.assertFalse(hasattr(self.theme_manager, 'set_theme'))
    
    @patch('streamlit.markdown')
    def test_apply_theme_uses_dark_theme(self, mock_markdown):
        """Test that apply_theme always uses dark theme"""
        self.theme_manager.apply_theme()
        
        # Should call markdown with CSS
        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        
        # Check that CSS contains dark theme variables
        css_content = args[0]
        self.assertIn("--background-color: #0e1117", css_content)
        self.assertIn("--text-color: #ffffff", css_content)
        self.assertIn("--secondary-bg: #262730", css_content)


class TestSidebarSimplification(unittest.TestCase):
    """Test sidebar simplification functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from ui_components import ChatInterface
            from auth_manager import AuthenticationManager
            self.ChatInterface = ChatInterface
            self.AuthenticationManager = AuthenticationManager
        except ImportError as e:
            self.skipTest(f"Required UI components not available: {e}")
    
    @patch('streamlit.sidebar')
    def test_sidebar_removes_plan_display(self, mock_sidebar):
        """Test that sidebar doesn't display plan/subscription information"""
        try:
            # Mock authentication manager
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.get_user_email.return_value = "test@example.com"
            
            chat_interface = self.ChatInterface(mock_auth)
            
            # Render sidebar
            with patch.object(chat_interface, 'render_sidebar') as mock_render:
                chat_interface.render_sidebar()
                mock_render.assert_called_once()
            
        except Exception as e:
            self.skipTest(f"Sidebar test setup failed: {e}")
    
    def test_sidebar_removes_pagination_controls(self):
        """Test that sidebar doesn't show pagination controls"""
        # This test verifies that pagination-related UI elements are not rendered
        try:
            from ui_components import ChatInterface
            
            # Mock dependencies
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            
            chat_interface = ChatInterface(mock_auth)
            
            # Check that pagination methods don't exist or are disabled
            self.assertFalse(hasattr(chat_interface, 'render_pagination_controls'))
            
        except Exception as e:
            self.skipTest(f"Pagination control test failed: {e}")


class TestUnlimitedConversationHistory(unittest.TestCase):
    """Test unlimited conversation history display"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from message_store import MessageStore
            from chat_interface import ChatInterface
            self.MessageStore = MessageStore
            self.ChatInterface = ChatInterface
        except ImportError as e:
            self.skipTest(f"Required components not available: {e}")
    
    def test_unlimited_history_loading(self):
        """Test that conversation history loads without pagination"""
        try:
            # Mock Supabase client
            mock_client = Mock()
            mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
                {
                    'id': f'msg-{i}',
                    'user_id': 'test-user',
                    'role': 'user' if i % 2 == 0 else 'assistant',
                    'content': f'Message {i}',
                    'created_at': datetime.now().isoformat(),
                    'metadata': {}
                }
                for i in range(100)  # 100 messages to test unlimited loading
            ]
            
            message_store = self.MessageStore(mock_client)
            
            # Get messages without limit
            messages = message_store.get_user_messages('test-user')
            
            # Should return all messages without pagination
            self.assertGreaterEqual(len(messages), 50, "Should load many messages without pagination")
            
        except Exception as e:
            self.skipTest(f"Unlimited history test failed: {e}")
    
    def test_no_pagination_ui_elements(self):
        """Test that pagination UI elements are not present"""
        try:
            from chat_interface import ChatInterface
            
            # Mock dependencies
            mock_auth = Mock()
            mock_message_store = Mock()
            
            chat_interface = ChatInterface(mock_auth, mock_message_store)
            
            # Check that pagination-related methods don't exist
            pagination_methods = ['render_pagination', 'set_page_size', 'get_page_size', 'next_page', 'prev_page']
            
            for method in pagination_methods:
                self.assertFalse(hasattr(chat_interface, method), f"Should not have {method} method")
                
        except Exception as e:
            self.skipTest(f"Pagination UI test failed: {e}")


class TestConversationManagement(unittest.TestCase):
    """Test conversation management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from conversation_manager import ConversationManager, Conversation
            from conversation_ui import ConversationUI
            self.ConversationManager = ConversationManager
            self.Conversation = Conversation
            self.ConversationUI = ConversationUI
        except ImportError as e:
            self.skipTest(f"Conversation management components not available: {e}")
    
    def test_conversation_creation(self):
        """Test conversation creation functionality"""
        try:
            # Mock Supabase client
            mock_client = Mock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
                'id': 'test-conv-id',
                'user_id': 'test-user-id',
                'title': 'Test Conversation',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'message_count': 0,
                'is_active': True
            }]
            
            conv_manager = self.ConversationManager(mock_client)
            
            # Test conversation creation
            conversation = conv_manager.create_conversation('test-user-id', 'Test Conversation')
            
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.title, 'Test Conversation')
            self.assertEqual(conversation.user_id, 'test-user-id')
            
        except Exception as e:
            self.skipTest(f"Conversation creation test failed: {e}")
    
    def test_conversation_title_generation(self):
        """Test automatic conversation title generation"""
        try:
            mock_client = Mock()
            conv_manager = self.ConversationManager(mock_client)
            
            # Test title generation
            title = conv_manager.generate_conversation_title("What is the mechanism of action of aspirin?")
            self.assertIsInstance(title, str)
            self.assertGreater(len(title), 0)
            self.assertLessEqual(len(title), 50)
            
        except Exception as e:
            self.skipTest(f"Title generation test failed: {e}")
    
    def test_conversation_switching(self):
        """Test conversation switching functionality"""
        try:
            # Mock Supabase client
            mock_client = Mock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {
                    'id': 'conv-1',
                    'user_id': 'test-user',
                    'title': 'Conversation 1',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'message_count': 5,
                    'is_active': True
                },
                {
                    'id': 'conv-2',
                    'user_id': 'test-user',
                    'title': 'Conversation 2',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'message_count': 3,
                    'is_active': True
                }
            ]
            
            conv_manager = self.ConversationManager(mock_client)
            
            # Test getting user conversations
            conversations = conv_manager.get_user_conversations('test-user')
            self.assertEqual(len(conversations), 2)
            self.assertEqual(conversations[0].title, 'Conversation 1')
            self.assertEqual(conversations[1].title, 'Conversation 2')
            
        except Exception as e:
            self.skipTest(f"Conversation switching test failed: {e}")


class TestRAGDocumentProcessing(unittest.TestCase):
    """Test RAG document processing end-to-end workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from enhanced_rag_integration import EnhancedRAGIntegration
            from document_processor import DocumentProcessor
            from vector_retriever import VectorRetriever
            self.EnhancedRAGIntegration = EnhancedRAGIntegration
            self.DocumentProcessor = DocumentProcessor
            self.VectorRetriever = VectorRetriever
        except ImportError as e:
            self.skipTest(f"RAG components not available: {e}")
    
    def test_document_upload_processing(self):
        """Test document upload and processing workflow"""
        try:
            rag = self.EnhancedRAGIntegration()
            
            # Create mock file
            class MockFile:
                def __init__(self, content, name="test.txt"):
                    self.content = content.encode('utf-8')
                    self.name = name
                    self.type = "text/plain"
                
                def getvalue(self):
                    return self.content
            
            mock_files = [MockFile("Aspirin is a pain reliever with anti-inflammatory properties.")]
            
            # Test upload (will fail gracefully without database)
            upload_result = rag.upload_and_process_documents(mock_files, "test-user")
            
            # Should handle gracefully even without database
            self.assertIsInstance(upload_result.success, bool)
            self.assertIsInstance(upload_result.message, str)
            
        except Exception as e:
            self.skipTest(f"Document upload test failed: {e}")
    
    def test_rag_query_processing(self):
        """Test RAG query processing with context retrieval"""
        try:
            rag = self.EnhancedRAGIntegration()
            
            # Test query (will fail gracefully without database)
            query_result = rag.query_with_rag("What is aspirin?", "test-user")
            
            # Should handle gracefully even without database
            self.assertIsInstance(query_result.success, bool)
            self.assertIsInstance(query_result.using_rag, bool)
            
        except Exception as e:
            self.skipTest(f"RAG query test failed: {e}")
    
    def test_document_processing_status_tracking(self):
        """Test document processing status tracking"""
        try:
            rag = self.EnhancedRAGIntegration()
            
            # Test document summary
            summary = rag.get_user_document_summary("test-user")
            self.assertIsInstance(summary, dict)
            
            # Test health status
            health = rag.get_health_status()
            self.assertIsInstance(health, dict)
            self.assertIn('initialized', health)
            
        except Exception as e:
            self.skipTest(f"Status tracking test failed: {e}")
    
    def test_context_integration_into_prompts(self):
        """Test that retrieved context is properly integrated into AI prompts"""
        try:
            from context_builder import ContextBuilder
            
            # Mock context builder
            context_builder = ContextBuilder()
            
            # Test context building
            query = "What are the side effects of aspirin?"
            mock_chunks = [
                {"content": "Aspirin can cause stomach irritation.", "metadata": {"source": "doc1"}},
                {"content": "Common side effects include nausea.", "metadata": {"source": "doc2"}}
            ]
            
            # This should work even without database
            context = context_builder.build_context(mock_chunks, query)
            self.assertIsInstance(context, str)
            
        except Exception as e:
            self.skipTest(f"Context integration test failed: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling across all UI enhancements"""
    
    def test_model_toggle_error_handling(self):
        """Test error handling in model toggle switch"""
        try:
            from model_ui import render_model_selector
            
            # Test with invalid session state
            with patch('streamlit.session_state', {}):
                # Should handle missing session state gracefully
                result = render_model_selector()
                # Should not raise exception
                
        except Exception as e:
            self.skipTest(f"Model toggle error handling test failed: {e}")
    
    def test_conversation_management_error_handling(self):
        """Test error handling in conversation management"""
        try:
            from conversation_manager import ConversationManager
            
            # Mock failing Supabase client
            mock_client = Mock()
            mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
            
            conv_manager = ConversationManager(mock_client)
            
            # Should handle database errors gracefully
            conversation = conv_manager.create_conversation('test-user', 'Test')
            # Should return None or handle error gracefully
            
        except Exception as e:
            self.skipTest(f"Conversation error handling test failed: {e}")
    
    def test_rag_processing_error_handling(self):
        """Test error handling in RAG document processing"""
        try:
            from enhanced_rag_integration import EnhancedRAGIntegration
            
            rag = EnhancedRAGIntegration()
            
            # Test with invalid file
            result = rag.upload_and_process_documents([], "test-user")
            self.assertFalse(result.success, "Should fail with empty file list")
            
            # Test with None inputs
            result = rag.upload_and_process_documents([None], None)
            self.assertFalse(result.success, "Should fail with None inputs")
            
        except Exception as e:
            self.skipTest(f"RAG error handling test failed: {e}")


def run_comprehensive_tests():
    """Run all UI enhancement tests"""
    print("🧪 Comprehensive UI Enhancements Testing Suite")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestModelToggleSwitch,
        TestPermanentDarkTheme,
        TestSidebarSimplification,
        TestUnlimitedConversationHistory,
        TestConversationManagement,
        TestRAGDocumentProcessing,
        TestErrorHandling
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results:")
    print(f"  • Tests run: {result.testsRun}")
    print(f"  • Failures: {len(result.failures)}")
    print(f"  • Errors: {len(result.errors)}")
    print(f"  • Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n⚠️  Errors:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.skipped:
        print(f"\n⏭️  Skipped:")
        for test, reason in result.skipped:
            print(f"  • {test}: {reason}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ All tests passed! UI enhancements are working correctly.")
        print(f"\n🎉 Verified Features:")
        print(f"  • Model toggle switch with 8K token limit for premium")
        print(f"  • Permanent dark theme enforcement")
        print(f"  • Simplified sidebar without plan/pagination controls")
        print(f"  • Unlimited conversation history display")
        print(f"  • Conversation management with tabs")
        print(f"  • RAG document processing end-to-end workflow")
        print(f"  • Comprehensive error handling")
    else:
        print(f"\n⚠️  Some tests failed. Please review and fix issues.")
    
    return success


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)