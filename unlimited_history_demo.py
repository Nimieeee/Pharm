"""
Demonstration of unlimited history performance optimizations.
Shows how to integrate the optimizations into the chat interface.
"""

import streamlit as st
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import optimization modules
from unlimited_history_optimizer import (
    UnlimitedHistoryOptimizer, 
    inject_unlimited_history_css,
    VirtualScrollConfig
)
from chat_interface_optimized import OptimizedChatInterface
from message_store_optimized import OptimizedMessageStore
from performance_optimizer import performance_optimizer, LoadingStateManager
from theme_manager import ThemeManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_messages(count: int = 100) -> List[Dict[str, Any]]:
    """Create demo messages for testing"""
    messages = []
    base_time = datetime.now() - timedelta(hours=count)
    
    for i in range(count):
        message = {
            'id': f'demo-msg-{i:04d}',
            'user_id': 'demo-user',
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': f"Demo message #{i+1}. " + 
                      ("This is a user question about pharmacology. " if i % 2 == 0 else 
                       "This is an AI response with detailed pharmacological information. ") +
                      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * (2 if i % 3 == 0 else 1),
            'model_used': 'gemma2-9b-it' if i % 2 == 1 else None,
            'created_at': base_time + timedelta(minutes=i * 5),
            'metadata': {'demo': True, 'index': i}
        }
        messages.append(message)
    
    return messages

def demo_unlimited_loading():
    """Demonstrate unlimited message loading"""
    st.header("📜 Unlimited History Loading Demo")
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        message_count = st.selectbox(
            "Number of demo messages",
            options=[50, 100, 500, 1000, 2000],
            index=1
        )
    
    with col2:
        loading_strategy = st.selectbox(
            "Loading Strategy",
            options=["Standard", "Chunked", "Virtual Scrolling", "Lazy Loading"],
            index=1
        )
    
    if st.button("🚀 Load Messages", key="load_unlimited"):
        # Create demo messages
        demo_messages = create_demo_messages(message_count)
        
        # Simulate loading with different strategies
        if loading_strategy == "Standard":
            with st.spinner("Loading all messages at once..."):
                time.sleep(0.1)  # Simulate load time
                st.success(f"✅ Loaded {len(demo_messages)} messages")
                
                # Display messages in container
                with st.container():
                    st.markdown('<div class="unlimited-history-container">', unsafe_allow_html=True)
                    for msg in demo_messages[-20:]:  # Show last 20 for demo
                        role_icon = "👤" if msg['role'] == 'user' else "🤖"
                        st.markdown(f"**{role_icon} {msg['role'].title()}:** {msg['content'][:100]}...")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        elif loading_strategy == "Chunked":
            chunk_size = 50
            total_chunks = (len(demo_messages) + chunk_size - 1) // chunk_size
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            loaded_messages = []
            
            for chunk_idx in range(total_chunks):
                start_idx = chunk_idx * chunk_size
                end_idx = min(start_idx + chunk_size, len(demo_messages))
                chunk = demo_messages[start_idx:end_idx]
                
                status_text.text(f"Loading chunk {chunk_idx + 1}/{total_chunks} ({len(chunk)} messages)...")
                progress_bar.progress((chunk_idx + 1) / total_chunks)
                
                loaded_messages.extend(chunk)
                time.sleep(0.05)  # Simulate chunk load time
            
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Loaded {len(loaded_messages)} messages in {total_chunks} chunks")
            
            # Show chunk statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Messages", len(loaded_messages))
            with col2:
                st.metric("Chunks Loaded", total_chunks)
            with col3:
                st.metric("Avg Chunk Size", f"{len(loaded_messages) / total_chunks:.1f}")
        
        elif loading_strategy == "Virtual Scrolling":
            config = VirtualScrollConfig()
            viewport_items = config.viewport_height // config.item_height
            
            st.info(f"Virtual scrolling: Rendering {viewport_items + config.buffer_size * 2} of {len(demo_messages)} messages")
            
            # Simulate virtual scrolling calculations
            start_time = time.time()
            visible_start = 0
            visible_end = min(viewport_items + config.buffer_size * 2, len(demo_messages))
            visible_messages = demo_messages[visible_start:visible_end]
            calc_time = time.time() - start_time
            
            st.success(f"✅ Virtual scrolling ready ({calc_time*1000:.2f}ms calculation time)")
            
            # Show virtual scrolling metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Messages", len(demo_messages))
            with col2:
                st.metric("Visible Messages", len(visible_messages))
            with col3:
                st.metric("Memory Efficiency", f"{len(visible_messages)/len(demo_messages):.1%}")
            with col4:
                st.metric("Calc Time", f"{calc_time*1000:.1f}ms")
            
            # Show visible messages
            st.markdown("**Visible Messages (Virtual Viewport):**")
            for msg in visible_messages[:10]:  # Show first 10 for demo
                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                st.markdown(f"**{role_icon} {msg['role'].title()}:** {msg['content'][:80]}...")
        
        elif loading_strategy == "Lazy Loading":
            initial_load = 20
            
            # Load initial messages
            loaded_messages = demo_messages[:initial_load]
            remaining_messages = demo_messages[initial_load:]
            
            st.success(f"✅ Initially loaded {len(loaded_messages)} messages")
            
            # Show loaded messages
            for msg in loaded_messages:
                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                st.markdown(f"**{role_icon} {msg['role'].title()}:** {msg['content'][:100]}...")
            
            # Load more button
            if remaining_messages:
                if st.button(f"📥 Load More ({len(remaining_messages)} remaining)", key="load_more_demo"):
                    next_batch = min(20, len(remaining_messages))
                    st.info(f"Loading {next_batch} more messages...")
                    time.sleep(0.2)  # Simulate load time
                    st.success(f"✅ Loaded {next_batch} additional messages")

def demo_performance_comparison():
    """Demonstrate performance comparison between strategies"""
    st.header("⚡ Performance Comparison Demo")
    
    message_counts = [100, 500, 1000, 2000]
    strategies = ["Standard", "Chunked", "Virtual Scrolling"]
    
    if st.button("🏃 Run Performance Comparison", key="perf_comparison"):
        results = []
        
        for count in message_counts:
            demo_messages = create_demo_messages(count)
            
            for strategy in strategies:
                start_time = time.time()
                
                if strategy == "Standard":
                    # Simulate loading all messages
                    _ = demo_messages
                    time.sleep(0.001 * count)  # Simulate proportional load time
                
                elif strategy == "Chunked":
                    # Simulate chunked loading
                    chunk_size = 50
                    chunks = [demo_messages[i:i+chunk_size] for i in range(0, len(demo_messages), chunk_size)]
                    time.sleep(0.001 * len(chunks))  # Simulate chunk overhead
                
                elif strategy == "Virtual Scrolling":
                    # Simulate virtual scrolling (constant time)
                    config = VirtualScrollConfig()
                    viewport_items = config.viewport_height // config.item_height
                    _ = demo_messages[:viewport_items + config.buffer_size * 2]
                    time.sleep(0.001)  # Constant time regardless of total messages
                
                load_time = time.time() - start_time
                
                results.append({
                    'Message Count': count,
                    'Strategy': strategy,
                    'Load Time (ms)': load_time * 1000,
                    'Messages/sec': count / load_time if load_time > 0 else 0
                })
        
        # Display results
        import pandas as pd
        df = pd.DataFrame(results)
        
        # Pivot table for better display
        pivot_time = df.pivot(index='Message Count', columns='Strategy', values='Load Time (ms)')
        pivot_throughput = df.pivot(index='Message Count', columns='Strategy', values='Messages/sec')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Load Time (ms)")
            st.dataframe(pivot_time, use_container_width=True)
        
        with col2:
            st.subheader("Throughput (Messages/sec)")
            st.dataframe(pivot_throughput, use_container_width=True)
        
        # Performance insights
        st.subheader("📊 Performance Insights")
        
        # Find best strategy for each message count
        for count in message_counts:
            count_data = df[df['Message Count'] == count]
            best_strategy = count_data.loc[count_data['Load Time (ms)'].idxmin(), 'Strategy']
            best_time = count_data['Load Time (ms)'].min()
            
            st.write(f"**{count} messages:** {best_strategy} is fastest ({best_time:.1f}ms)")

def demo_cache_performance():
    """Demonstrate cache performance"""
    st.header("🗄️ Cache Performance Demo")
    
    # Cache configuration
    col1, col2 = st.columns(2)
    
    with col1:
        cache_size = st.selectbox("Cache Size", options=[100, 500, 1000], index=1)
        ttl = st.selectbox("Cache TTL (seconds)", options=[30, 60, 300], index=1)
    
    with col2:
        test_operations = st.selectbox("Test Operations", options=[10, 50, 100], index=1)
    
    if st.button("🧪 Test Cache Performance", key="cache_perf"):
        # Simulate cache operations
        cache_hits = 0
        cache_misses = 0
        
        # Simulate cache warming
        with st.spinner("Warming cache..."):
            time.sleep(0.1)
        
        # Simulate operations
        progress_bar = st.progress(0)
        
        for i in range(test_operations):
            # Simulate cache lookup
            if i < cache_size * 0.7:  # 70% hit rate simulation
                cache_hits += 1
                time.sleep(0.001)  # Fast cache hit
            else:
                cache_misses += 1
                time.sleep(0.01)   # Slower cache miss
            
            progress_bar.progress((i + 1) / test_operations)
        
        progress_bar.empty()
        
        # Display results
        hit_rate = cache_hits / test_operations
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cache Hits", cache_hits)
        
        with col2:
            st.metric("Cache Misses", cache_misses)
        
        with col3:
            st.metric("Hit Rate", f"{hit_rate:.1%}")
        
        # Performance analysis
        if hit_rate > 0.8:
            st.success(f"✅ Excellent cache performance ({hit_rate:.1%} hit rate)")
        elif hit_rate > 0.6:
            st.info(f"ℹ️ Good cache performance ({hit_rate:.1%} hit rate)")
        else:
            st.warning(f"⚠️ Cache performance could be improved ({hit_rate:.1%} hit rate)")

def demo_memory_optimization():
    """Demonstrate memory optimization techniques"""
    st.header("💾 Memory Optimization Demo")
    
    # Memory usage simulation
    message_counts = [100, 500, 1000, 5000]
    
    st.subheader("Memory Usage Comparison")
    
    memory_data = []
    
    for count in message_counts:
        # Simulate memory usage for different strategies
        standard_memory = count * 0.5  # KB per message
        chunked_memory = min(50 * 0.5, count * 0.5)  # Max 50 messages in memory
        virtual_memory = min(20 * 0.5, count * 0.5)  # Max 20 messages in viewport
        
        memory_data.append({
            'Message Count': count,
            'Standard (KB)': standard_memory,
            'Chunked (KB)': chunked_memory,
            'Virtual Scrolling (KB)': virtual_memory
        })
    
    import pandas as pd
    df = pd.DataFrame(memory_data)
    
    # Display memory usage table
    st.dataframe(df, use_container_width=True)
    
    # Memory efficiency chart
    try:
        import plotly.express as px
        
        # Melt dataframe for plotting
        df_melted = df.melt(id_vars=['Message Count'], 
                           value_vars=['Standard (KB)', 'Chunked (KB)', 'Virtual Scrolling (KB)'],
                           var_name='Strategy', value_name='Memory Usage (KB)')
        
        fig = px.line(df_melted, x='Message Count', y='Memory Usage (KB)', 
                     color='Strategy', title='Memory Usage by Strategy')
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.info("Install plotly for memory usage charts: pip install plotly")
    
    # Memory optimization tips
    st.subheader("💡 Memory Optimization Tips")
    
    st.markdown("""
    **Virtual Scrolling Benefits:**
    - Constant memory usage regardless of total messages
    - Smooth scrolling performance
    - Suitable for very large conversations
    
    **Chunked Loading Benefits:**
    - Controlled memory usage
    - Progressive loading
    - Good balance between performance and memory
    
    **Caching Benefits:**
    - Faster subsequent loads
    - Reduced database queries
    - Configurable TTL for freshness
    """)

def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Unlimited History Performance Demo",
        page_icon="⚡",
        layout="wide"
    )
    
    # Inject CSS
    inject_unlimited_history_css()
    
    st.title("⚡ Unlimited History Performance Demo")
    st.markdown("Interactive demonstration of performance optimizations for unlimited conversation history")
    
    # Navigation
    demo_tabs = st.tabs([
        "📜 Loading Strategies", 
        "⚡ Performance Comparison", 
        "🗄️ Cache Performance", 
        "💾 Memory Optimization"
    ])
    
    with demo_tabs[0]:
        demo_unlimited_loading()
    
    with demo_tabs[1]:
        demo_performance_comparison()
    
    with demo_tabs[2]:
        demo_cache_performance()
    
    with demo_tabs[3]:
        demo_memory_optimization()
    
    # Sidebar with information
    st.sidebar.header("📋 Demo Information")
    st.sidebar.markdown("""
    ### Performance Optimizations
    
    **Loading Strategies:**
    - **Standard:** Load all messages at once
    - **Chunked:** Load messages in batches
    - **Virtual Scrolling:** Render only visible messages
    - **Lazy Loading:** Load on demand
    
    **Key Benefits:**
    - Faster initial load times
    - Reduced memory usage
    - Better user experience
    - Scalable to thousands of messages
    
    **Implementation Features:**
    - Database query optimization
    - Intelligent caching
    - Progressive loading
    - Memory-efficient rendering
    """)
    
    # Performance metrics
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Current Metrics")
    
    # Get current performance metrics
    try:
        perf_stats = performance_optimizer.get_performance_stats()
        
        st.sidebar.metric("Cache Entries", perf_stats.get('total_operations', 0))
        st.sidebar.metric("Avg Response Time", f"{perf_stats.get('avg_duration_ms', 0):.1f}ms")
        st.sidebar.metric("Cache Hit Rate", f"{perf_stats.get('cache_hit_rate', 0):.1%}")
        
    except Exception as e:
        st.sidebar.info("Performance metrics not available")
    
    # Clear cache button
    if st.sidebar.button("🧹 Clear Cache"):
        performance_optimizer.cache.clear()
        st.sidebar.success("Cache cleared!")

if __name__ == "__main__":
    main()