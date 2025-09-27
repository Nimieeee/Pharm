"""
Performance verification script for unlimited history optimizations.
Tests the implementation with various data sizes and measures performance metrics.
"""

import streamlit as st
import time
import logging
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import our optimization modules
from unlimited_history_optimizer import UnlimitedHistoryOptimizer, inject_unlimited_history_css
from message_store import Message, MessageStore
from performance_optimizer import performance_optimizer
from database_utils import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Test suite for unlimited history performance verification"""
    
    def __init__(self):
        """Initialize performance test suite"""
        self.supabase_client = get_supabase_client()
        self.message_store = MessageStore(self.supabase_client)
        self.optimizer = UnlimitedHistoryOptimizer(self.supabase_client, self.message_store)
        self.test_results = []
    
    def create_test_user_and_messages(self, user_id: str, message_count: int) -> bool:
        """
        Create test user and messages for performance testing
        
        Args:
            user_id: Test user ID
            message_count: Number of messages to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            st.info(f"Creating {message_count} test messages for user {user_id}...")
            
            # Create test conversation
            conversation_id = f"test-conv-{int(time.time())}"
            
            # Use database function for bulk creation if available
            try:
                result = self.supabase_client.rpc('create_test_messages', {
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'message_count': message_count
                }).execute()
                
                if result.data:
                    st.success(f"✅ Created {result.data} test messages using database function")
                    return True
                    
            except Exception as e:
                logger.warning(f"Database function failed, falling back to individual inserts: {e}")
            
            # Fallback to individual message creation
            progress_bar = st.progress(0)
            batch_size = 50
            created_count = 0
            
            for i in range(0, message_count, batch_size):
                batch_end = min(i + batch_size, message_count)
                
                for j in range(i, batch_end):
                    role = "user" if j % 2 == 0 else "assistant"
                    content = f"Performance test message #{j+1}. " + \
                             "This is a longer message to simulate real conversation content. " * 2
                    model_used = "gemma2-9b-it" if role == "assistant" else None
                    
                    message = self.message_store.save_message(
                        user_id=user_id,
                        role=role,
                        content=content,
                        model_used=model_used,
                        metadata={"test": True, "batch": i // batch_size, "index": j}
                    )
                    
                    if message:
                        created_count += 1
                
                # Update progress
                progress = batch_end / message_count
                progress_bar.progress(progress)
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.1)
            
            progress_bar.empty()
            
            if created_count == message_count:
                st.success(f"✅ Created {created_count} test messages successfully")
                return True
            else:
                st.error(f"❌ Only created {created_count} out of {message_count} messages")
                return False
                
        except Exception as e:
            st.error(f"❌ Error creating test messages: {e}")
            logger.error(f"Error creating test messages: {e}")
            return False
    
    def test_unlimited_loading_performance(self, user_id: str, test_name: str) -> Dict[str, Any]:
        """
        Test unlimited message loading performance
        
        Args:
            user_id: Test user ID
            test_name: Name of the test
            
        Returns:
            Performance test results
        """
        st.subheader(f"🔄 Testing: {test_name}")
        
        try:
            # Clear cache to ensure fresh test
            self.optimizer.clear_unlimited_history_cache(user_id)
            
            # Test 1: Cold load (no cache)
            start_time = time.time()
            messages_cold = self.optimizer.get_unlimited_messages_optimized(user_id)
            cold_load_time = time.time() - start_time
            
            # Test 2: Warm load (with cache)
            start_time = time.time()
            messages_warm = self.optimizer.get_unlimited_messages_optimized(user_id)
            warm_load_time = time.time() - start_time
            
            # Test 3: Message count optimization
            start_time = time.time()
            message_count = self.optimizer._get_message_count_optimized(user_id)
            count_time = time.time() - start_time
            
            # Test 4: Chunked loading
            chunk_times = []
            chunk_size = 50
            total_chunks = (len(messages_cold) + chunk_size - 1) // chunk_size
            
            for i in range(min(5, total_chunks)):  # Test first 5 chunks
                start_time = time.time()
                chunk = self.optimizer._load_message_chunk(user_id, None, i * chunk_size, chunk_size)
                chunk_time = time.time() - start_time
                chunk_times.append(chunk_time)
            
            avg_chunk_time = sum(chunk_times) / len(chunk_times) if chunk_times else 0
            
            # Calculate performance metrics
            results = {
                'test_name': test_name,
                'user_id': user_id,
                'message_count': len(messages_cold),
                'cold_load_time': cold_load_time,
                'warm_load_time': warm_load_time,
                'count_time': count_time,
                'avg_chunk_time': avg_chunk_time,
                'cache_speedup': cold_load_time / warm_load_time if warm_load_time > 0 else 0,
                'messages_per_second_cold': len(messages_cold) / cold_load_time if cold_load_time > 0 else 0,
                'messages_per_second_warm': len(messages_warm) / warm_load_time if warm_load_time > 0 else 0,
                'timestamp': datetime.now()
            }
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Messages Loaded", len(messages_cold))
            
            with col2:
                st.metric("Cold Load Time", f"{cold_load_time:.3f}s")
            
            with col3:
                st.metric("Warm Load Time", f"{warm_load_time:.3f}s")
            
            with col4:
                st.metric("Cache Speedup", f"{results['cache_speedup']:.1f}x")
            
            # Performance analysis
            if cold_load_time > 2.0:
                st.warning(f"⚠️ Cold load time ({cold_load_time:.2f}s) is high for {len(messages_cold)} messages")
            elif cold_load_time > 1.0:
                st.info(f"ℹ️ Cold load time ({cold_load_time:.2f}s) is acceptable for {len(messages_cold)} messages")
            else:
                st.success(f"✅ Cold load time ({cold_load_time:.2f}s) is excellent for {len(messages_cold)} messages")
            
            if results['cache_speedup'] > 5:
                st.success(f"✅ Cache provides excellent speedup ({results['cache_speedup']:.1f}x)")
            elif results['cache_speedup'] > 2:
                st.info(f"ℹ️ Cache provides good speedup ({results['cache_speedup']:.1f}x)")
            else:
                st.warning(f"⚠️ Cache speedup is low ({results['cache_speedup']:.1f}x)")
            
            self.test_results.append(results)
            return results
            
        except Exception as e:
            st.error(f"❌ Error in performance test: {e}")
            logger.error(f"Error in performance test: {e}")
            return {}
    
    def test_virtual_scrolling_performance(self, user_id: str, container_height: int = 600) -> Dict[str, Any]:
        """
        Test virtual scrolling performance
        
        Args:
            user_id: Test user ID
            container_height: Height of virtual scroll container
            
        Returns:
            Virtual scrolling performance results
        """
        st.subheader("📜 Testing Virtual Scrolling Performance")
        
        try:
            # Load messages
            messages = self.optimizer.get_unlimited_messages_optimized(user_id)
            
            if not messages:
                st.warning("No messages found for virtual scrolling test")
                return {}
            
            # Test virtual scrolling calculations
            config = self.optimizer.virtual_scroll_config
            viewport_items = container_height // config.item_height
            
            # Test different scroll positions
            scroll_positions = [0, len(messages) // 4, len(messages) // 2, len(messages) * 3 // 4]
            calculation_times = []
            
            for scroll_pos in scroll_positions:
                start_time = time.time()
                
                # Calculate visible range
                start_index = max(0, scroll_pos - config.buffer_size)
                end_index = min(len(messages), scroll_pos + viewport_items + config.buffer_size)
                visible_messages = messages[start_index:end_index]
                
                calc_time = time.time() - start_time
                calculation_times.append(calc_time)
            
            avg_calc_time = sum(calculation_times) / len(calculation_times)
            
            # Test rendering performance (simulated)
            start_time = time.time()
            # Simulate rendering first viewport
            visible_range = messages[:viewport_items + config.buffer_size]
            render_time = time.time() - start_time
            
            results = {
                'total_messages': len(messages),
                'viewport_items': viewport_items,
                'buffer_size': config.buffer_size,
                'avg_calculation_time': avg_calc_time,
                'render_time': render_time,
                'visible_messages_count': len(visible_range),
                'memory_efficiency': len(visible_range) / len(messages)
            }
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Messages", len(messages))
                st.metric("Viewport Items", viewport_items)
            
            with col2:
                st.metric("Visible Messages", len(visible_range))
                st.metric("Memory Efficiency", f"{results['memory_efficiency']:.1%}")
            
            with col3:
                st.metric("Calc Time", f"{avg_calc_time*1000:.2f}ms")
                st.metric("Render Time", f"{render_time*1000:.2f}ms")
            
            # Performance analysis
            if avg_calc_time < 0.001:
                st.success("✅ Virtual scrolling calculations are very fast")
            elif avg_calc_time < 0.01:
                st.info("ℹ️ Virtual scrolling calculations are acceptable")
            else:
                st.warning("⚠️ Virtual scrolling calculations may be slow")
            
            return results
            
        except Exception as e:
            st.error(f"❌ Error in virtual scrolling test: {e}")
            logger.error(f"Error in virtual scrolling test: {e}")
            return {}
    
    def test_database_optimizations(self, user_id: str) -> Dict[str, Any]:
        """
        Test database optimization functions
        
        Args:
            user_id: Test user ID
            
        Returns:
            Database optimization test results
        """
        st.subheader("🗄️ Testing Database Optimizations")
        
        try:
            results = {}
            
            # Test 1: Optimized message count
            start_time = time.time()
            count_optimized = self.optimizer._get_message_count_optimized(user_id)
            count_time_optimized = time.time() - start_time
            
            # Test 2: Standard message count (for comparison)
            start_time = time.time()
            count_standard = self.message_store.get_message_count(user_id)
            count_time_standard = time.time() - start_time
            
            # Test 3: RPC function performance
            rpc_times = []
            try:
                for _ in range(3):  # Test 3 times
                    start_time = time.time()
                    result = self.supabase_client.rpc('get_all_user_messages_unlimited', {
                        'user_id': user_id
                    }).execute()
                    rpc_time = time.time() - start_time
                    rpc_times.append(rpc_time)
                
                avg_rpc_time = sum(rpc_times) / len(rpc_times)
                rpc_available = True
                
            except Exception as e:
                logger.warning(f"RPC function not available: {e}")
                avg_rpc_time = 0
                rpc_available = False
            
            # Test 4: Chunked loading performance
            chunk_times = []
            chunk_size = 50
            
            for i in range(3):  # Test 3 chunks
                start_time = time.time()
                chunk = self.optimizer._load_message_chunk(user_id, None, i * chunk_size, chunk_size)
                chunk_time = time.time() - start_time
                chunk_times.append(chunk_time)
            
            avg_chunk_time = sum(chunk_times) / len(chunk_times) if chunk_times else 0
            
            results = {
                'count_optimized': count_optimized,
                'count_standard': count_standard,
                'count_time_optimized': count_time_optimized,
                'count_time_standard': count_time_standard,
                'count_speedup': count_time_standard / count_time_optimized if count_time_optimized > 0 else 0,
                'rpc_available': rpc_available,
                'avg_rpc_time': avg_rpc_time,
                'avg_chunk_time': avg_chunk_time,
                'counts_match': count_optimized == count_standard
            }
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Message Count", count_optimized)
                st.metric("Counts Match", "✅" if results['counts_match'] else "❌")
            
            with col2:
                st.metric("Optimized Count Time", f"{count_time_optimized*1000:.2f}ms")
                st.metric("Standard Count Time", f"{count_time_standard*1000:.2f}ms")
            
            with col3:
                st.metric("Count Speedup", f"{results['count_speedup']:.1f}x")
                st.metric("RPC Available", "✅" if rpc_available else "❌")
            
            # Analysis
            if results['counts_match']:
                st.success("✅ Optimized and standard counts match")
            else:
                st.error("❌ Count mismatch - check optimization implementation")
            
            if results['count_speedup'] > 1.5:
                st.success(f"✅ Count optimization provides good speedup ({results['count_speedup']:.1f}x)")
            else:
                st.info(f"ℹ️ Count optimization speedup is modest ({results['count_speedup']:.1f}x)")
            
            if rpc_available:
                st.success("✅ Database RPC functions are available")
                if avg_rpc_time < 0.5:
                    st.success(f"✅ RPC performance is excellent ({avg_rpc_time:.3f}s)")
                else:
                    st.warning(f"⚠️ RPC performance could be better ({avg_rpc_time:.3f}s)")
            else:
                st.warning("⚠️ Database RPC functions not available - using fallback methods")
            
            return results
            
        except Exception as e:
            st.error(f"❌ Error in database optimization test: {e}")
            logger.error(f"Error in database optimization test: {e}")
            return {}
    
    def generate_performance_report(self) -> None:
        """Generate comprehensive performance report"""
        if not self.test_results:
            st.warning("No test results available for report generation")
            return
        
        st.header("📊 Performance Report")
        
        # Convert results to DataFrame
        df = pd.DataFrame(self.test_results)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_cold_load = df['cold_load_time'].mean()
            st.metric("Avg Cold Load Time", f"{avg_cold_load:.3f}s")
        
        with col2:
            avg_warm_load = df['warm_load_time'].mean()
            st.metric("Avg Warm Load Time", f"{avg_warm_load:.3f}s")
        
        with col3:
            avg_speedup = df['cache_speedup'].mean()
            st.metric("Avg Cache Speedup", f"{avg_speedup:.1f}x")
        
        with col4:
            total_messages = df['message_count'].sum()
            st.metric("Total Messages Tested", total_messages)
        
        # Performance charts
        st.subheader("Performance Charts")
        
        # Load time vs message count
        fig1 = px.scatter(df, x='message_count', y='cold_load_time', 
                         title='Cold Load Time vs Message Count',
                         labels={'message_count': 'Number of Messages', 
                                'cold_load_time': 'Load Time (seconds)'})
        fig1.add_scatter(x=df['message_count'], y=df['warm_load_time'], 
                        mode='markers', name='Warm Load Time')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Cache speedup chart
        fig2 = px.bar(df, x='test_name', y='cache_speedup',
                     title='Cache Speedup by Test',
                     labels={'test_name': 'Test Name', 'cache_speedup': 'Speedup Factor'})
        st.plotly_chart(fig2, use_container_width=True)
        
        # Messages per second
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Cold Load', x=df['test_name'], y=df['messages_per_second_cold']))
        fig3.add_trace(go.Bar(name='Warm Load', x=df['test_name'], y=df['messages_per_second_warm']))
        fig3.update_layout(title='Messages Per Second by Test', 
                          xaxis_title='Test Name', 
                          yaxis_title='Messages/Second')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Detailed results table
        st.subheader("Detailed Results")
        st.dataframe(df, use_container_width=True)
        
        # Performance recommendations
        st.subheader("🎯 Performance Recommendations")
        
        max_load_time = df['cold_load_time'].max()
        min_speedup = df['cache_speedup'].min()
        
        if max_load_time > 3.0:
            st.warning(f"⚠️ Maximum load time ({max_load_time:.2f}s) is high. Consider implementing virtual scrolling for large conversations.")
        
        if min_speedup < 2.0:
            st.warning(f"⚠️ Minimum cache speedup ({min_speedup:.1f}x) is low. Check cache configuration and TTL settings.")
        
        if df['message_count'].max() > 1000:
            st.info("ℹ️ For conversations with >1000 messages, consider using chunked loading or virtual scrolling.")
        
        st.success("✅ Performance testing completed successfully!")

def main():
    """Main function for performance verification"""
    st.set_page_config(
        page_title="Unlimited History Performance Verification",
        page_icon="⚡",
        layout="wide"
    )
    
    # Inject CSS
    inject_unlimited_history_css()
    
    st.title("⚡ Unlimited History Performance Verification")
    st.markdown("Testing performance optimizations for unlimited conversation history display")
    
    # Initialize test suite
    test_suite = PerformanceTestSuite()
    
    # Sidebar controls
    st.sidebar.header("Test Configuration")
    
    test_user_id = st.sidebar.text_input("Test User ID", value="test-user-perf")
    
    # Test size options
    test_sizes = {
        "Small (100 messages)": 100,
        "Medium (500 messages)": 500,
        "Large (1000 messages)": 1000,
        "Very Large (2000 messages)": 2000,
        "Extreme (5000 messages)": 5000
    }
    
    selected_tests = st.sidebar.multiselect(
        "Select Test Sizes",
        options=list(test_sizes.keys()),
        default=["Small (100 messages)", "Medium (500 messages)"]
    )
    
    # Test controls
    if st.sidebar.button("🧪 Run Performance Tests"):
        if not selected_tests:
            st.error("Please select at least one test size")
            return
        
        st.header("🚀 Running Performance Tests")
        
        for test_name in selected_tests:
            message_count = test_sizes[test_name]
            
            with st.expander(f"Test: {test_name}", expanded=True):
                # Create test data
                if test_suite.create_test_user_and_messages(test_user_id, message_count):
                    # Run performance tests
                    test_suite.test_unlimited_loading_performance(test_user_id, test_name)
                    test_suite.test_virtual_scrolling_performance(test_user_id)
                    test_suite.test_database_optimizations(test_user_id)
                    
                    # Clean up test data
                    if st.button(f"🗑️ Clean up test data for {test_name}", key=f"cleanup_{test_name}"):
                        try:
                            test_suite.message_store.delete_user_messages(test_user_id)
                            st.success(f"✅ Cleaned up test data for {test_name}")
                        except Exception as e:
                            st.error(f"❌ Error cleaning up: {e}")
        
        # Generate report
        if test_suite.test_results:
            test_suite.generate_performance_report()
    
    # Manual test controls
    st.sidebar.markdown("---")
    st.sidebar.header("Manual Testing")
    
    if st.sidebar.button("🔍 Test Current User Messages"):
        if test_user_id:
            with st.expander("Current User Message Test", expanded=True):
                test_suite.test_unlimited_loading_performance(test_user_id, "Current User")
                test_suite.test_virtual_scrolling_performance(test_user_id)
                test_suite.test_database_optimizations(test_user_id)
    
    if st.sidebar.button("📊 Show Performance Metrics"):
        st.header("📊 Current Performance Metrics")
        metrics = test_suite.optimizer.get_performance_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cache Entries", metrics.get("cache_entries", 0))
        
        with col2:
            st.metric("Cache Hit Rate", f"{metrics.get('cache_hit_rate', 0):.1%}")
        
        with col3:
            st.metric("Memory Usage", f"{metrics.get('memory_usage_mb', 0):.1f}MB")
        
        # Virtual scroll config
        st.subheader("Virtual Scroll Configuration")
        config = metrics.get("virtual_scroll_config", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Viewport Height", f"{config.get('viewport_height', 0)}px")
        
        with col2:
            st.metric("Item Height", f"{config.get('item_height', 0)}px")
        
        with col3:
            st.metric("Buffer Size", config.get('buffer_size', 0))
        
        with col4:
            st.metric("Chunk Size", config.get('chunk_size', 0))
    
    if st.sidebar.button("🧹 Clear All Caches"):
        test_suite.optimizer.clear_unlimited_history_cache()
        performance_optimizer.cache.clear()
        st.success("✅ All caches cleared")
    
    # Information section
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📋 Test Information
    
    **Performance Tests:**
    - Unlimited message loading
    - Virtual scrolling calculations
    - Database optimizations
    - Cache performance
    
    **Metrics Measured:**
    - Load times (cold/warm)
    - Cache speedup
    - Messages per second
    - Memory efficiency
    """)

if __name__ == "__main__":
    main()