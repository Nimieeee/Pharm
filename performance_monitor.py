"""
Performance monitoring and optimization utilities
"""

import time
import logging
import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import psutil
import gc

from performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    timestamp: datetime

@dataclass
class AppMetrics:
    """Application performance metrics"""
    active_users: int
    total_requests: int
    avg_response_time_ms: float
    cache_hit_rate: float
    error_rate: float
    timestamp: datetime

class PerformanceMonitor:
    """Monitor and optimize application performance"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[AppMetrics] = []
        self.max_history = 100  # Keep last 100 measurements
        
        # Performance thresholds
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "response_time_warning": 2000.0,  # 2 seconds
            "response_time_critical": 5000.0,  # 5 seconds
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10   # 10%
        }
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                timestamp=datetime.now()
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, datetime.now())
    
    def collect_app_metrics(self) -> AppMetrics:
        """Collect application performance metrics"""
        try:
            # Get performance stats from optimizer
            perf_stats = performance_optimizer.get_performance_stats()
            
            # Count active users (simplified - based on session state)
            active_users = 1 if hasattr(st, 'session_state') else 0
            
            metrics = AppMetrics(
                active_users=active_users,
                total_requests=perf_stats.get('total_operations', 0),
                avg_response_time_ms=perf_stats.get('avg_duration_ms', 0),
                cache_hit_rate=perf_stats.get('cache_hit_rate', 0),
                error_rate=perf_stats.get('error_rate', 0),
                timestamp=datetime.now()
            )
            
            # Add to history
            self.app_metrics_history.append(metrics)
            if len(self.app_metrics_history) > self.max_history:
                self.app_metrics_history = self.app_metrics_history[-self.max_history:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting app metrics: {e}")
            return AppMetrics(0, 0, 0, 0, 0, datetime.now())
    
    def check_performance_alerts(self, system_metrics: SystemMetrics, app_metrics: AppMetrics) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        alerts = []
        
        # CPU alerts
        if system_metrics.cpu_percent > self.thresholds["cpu_critical"]:
            alerts.append({
                "type": "critical",
                "category": "cpu",
                "message": f"Critical CPU usage: {system_metrics.cpu_percent:.1f}%",
                "value": system_metrics.cpu_percent,
                "threshold": self.thresholds["cpu_critical"]
            })
        elif system_metrics.cpu_percent > self.thresholds["cpu_warning"]:
            alerts.append({
                "type": "warning",
                "category": "cpu",
                "message": f"High CPU usage: {system_metrics.cpu_percent:.1f}%",
                "value": system_metrics.cpu_percent,
                "threshold": self.thresholds["cpu_warning"]
            })
        
        # Memory alerts
        if system_metrics.memory_percent > self.thresholds["memory_critical"]:
            alerts.append({
                "type": "critical",
                "category": "memory",
                "message": f"Critical memory usage: {system_metrics.memory_percent:.1f}%",
                "value": system_metrics.memory_percent,
                "threshold": self.thresholds["memory_critical"]
            })
        elif system_metrics.memory_percent > self.thresholds["memory_warning"]:
            alerts.append({
                "type": "warning",
                "category": "memory",
                "message": f"High memory usage: {system_metrics.memory_percent:.1f}%",
                "value": system_metrics.memory_percent,
                "threshold": self.thresholds["memory_warning"]
            })
        
        # Response time alerts
        if app_metrics.avg_response_time_ms > self.thresholds["response_time_critical"]:
            alerts.append({
                "type": "critical",
                "category": "response_time",
                "message": f"Critical response time: {app_metrics.avg_response_time_ms:.0f}ms",
                "value": app_metrics.avg_response_time_ms,
                "threshold": self.thresholds["response_time_critical"]
            })
        elif app_metrics.avg_response_time_ms > self.thresholds["response_time_warning"]:
            alerts.append({
                "type": "warning",
                "category": "response_time",
                "message": f"Slow response time: {app_metrics.avg_response_time_ms:.0f}ms",
                "value": app_metrics.avg_response_time_ms,
                "threshold": self.thresholds["response_time_warning"]
            })
        
        # Error rate alerts
        if app_metrics.error_rate > self.thresholds["error_rate_critical"]:
            alerts.append({
                "type": "critical",
                "category": "error_rate",
                "message": f"Critical error rate: {app_metrics.error_rate:.1%}",
                "value": app_metrics.error_rate,
                "threshold": self.thresholds["error_rate_critical"]
            })
        elif app_metrics.error_rate > self.thresholds["error_rate_warning"]:
            alerts.append({
                "type": "warning",
                "category": "error_rate",
                "message": f"High error rate: {app_metrics.error_rate:.1%}",
                "value": app_metrics.error_rate,
                "threshold": self.thresholds["error_rate_warning"]
            })
        
        return alerts
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Perform automatic performance optimizations"""
        optimizations = []
        
        try:
            # Force garbage collection
            collected = gc.collect()
            if collected > 0:
                optimizations.append(f"Garbage collected {collected} objects")
            
            # Clear old cache entries
            cache_stats_before = performance_optimizer.cache.get_stats()
            
            # Clear expired entries (this is automatic, but we can force it)
            expired_keys = []
            for key, entry in performance_optimizer.cache.cache.items():
                if datetime.now() > entry.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                performance_optimizer.cache.delete(key)
            
            if expired_keys:
                optimizations.append(f"Cleared {len(expired_keys)} expired cache entries")
            
            # Optimize memory usage if high
            system_metrics = self.collect_system_metrics()
            if system_metrics.memory_percent > 85:
                # More aggressive cleanup
                performance_optimizer.cache.clear()
                gc.collect()
                optimizations.append("Performed aggressive memory cleanup")
            
            return {
                "success": True,
                "optimizations": optimizations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during performance optimization: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def render_performance_dashboard(self) -> None:
        """Render comprehensive performance dashboard"""
        st.markdown("### 🔍 System Performance Monitor")
        
        # Collect current metrics
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_app_metrics()
        
        # Check for alerts
        alerts = self.check_performance_alerts(system_metrics, app_metrics)
        
        # Display alerts if any
        if alerts:
            st.markdown("#### ⚠️ Performance Alerts")
            for alert in alerts:
                if alert["type"] == "critical":
                    st.error(f"🚨 {alert['message']}")
                else:
                    st.warning(f"⚠️ {alert['message']}")
        
        # System metrics
        st.markdown("#### 💻 System Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_color = "red" if system_metrics.cpu_percent > 80 else "orange" if system_metrics.cpu_percent > 60 else "green"
            st.metric(
                "CPU Usage", 
                f"{system_metrics.cpu_percent:.1f}%",
                delta=None,
                help=f"Current CPU utilization"
            )
        
        with col2:
            memory_color = "red" if system_metrics.memory_percent > 80 else "orange" if system_metrics.memory_percent > 60 else "green"
            st.metric(
                "Memory Usage", 
                f"{system_metrics.memory_percent:.1f}%",
                delta=f"{system_metrics.memory_used_mb:.0f}MB used"
            )
        
        with col3:
            st.metric(
                "Available Memory", 
                f"{system_metrics.memory_available_mb:.0f}MB"
            )
        
        with col4:
            st.metric(
                "Last Updated", 
                system_metrics.timestamp.strftime("%H:%M:%S")
            )
        
        # Application metrics
        st.markdown("#### 📊 Application Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Avg Response Time", 
                f"{app_metrics.avg_response_time_ms:.0f}ms"
            )
        
        with col2:
            st.metric(
                "Cache Hit Rate", 
                f"{app_metrics.cache_hit_rate:.1%}"
            )
        
        with col3:
            st.metric(
                "Error Rate", 
                f"{app_metrics.error_rate:.1%}"
            )
        
        with col4:
            st.metric(
                "Total Requests", 
                app_metrics.total_requests
            )
        
        # Performance controls
        st.markdown("#### 🛠️ Performance Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Metrics", key="refresh_metrics"):
                st.rerun()
        
        with col2:
            if st.button("🧹 Optimize Performance", key="optimize_performance"):
                with st.spinner("Optimizing performance..."):
                    result = self.optimize_performance()
                    if result["success"]:
                        st.success("✅ Performance optimized!")
                        for opt in result["optimizations"]:
                            st.info(f"• {opt}")
                    else:
                        st.error(f"❌ Optimization failed: {result['error']}")
        
        with col3:
            if st.button("🗑️ Clear All Cache", key="clear_all_cache"):
                performance_optimizer.cache.clear()
                st.success("🗑️ Cache cleared!")
                st.rerun()
        
        # Historical data (if available)
        if len(self.metrics_history) > 1:
            st.markdown("#### 📈 Performance Trends")
            
            # Create simple trend indicators
            recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
            
            if len(recent_metrics) >= 2:
                cpu_trend = recent_metrics[-1].cpu_percent - recent_metrics[0].cpu_percent
                memory_trend = recent_metrics[-1].memory_percent - recent_metrics[0].memory_percent
                
                col1, col2 = st.columns(2)
                
                with col1:
                    trend_icon = "📈" if cpu_trend > 5 else "📉" if cpu_trend < -5 else "➡️"
                    st.write(f"{trend_icon} CPU Trend: {cpu_trend:+.1f}%")
                
                with col2:
                    trend_icon = "📈" if memory_trend > 5 else "📉" if memory_trend < -5 else "➡️"
                    st.write(f"{trend_icon} Memory Trend: {memory_trend:+.1f}%")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()