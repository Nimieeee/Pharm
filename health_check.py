"""
Health Check and Monitoring System for Streamlit Cloud Deployment
Provides health check endpoints and error monitoring capabilities
"""

import streamlit as st
import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from deployment_config import deployment_config

@dataclass
class HealthStatus:
    """Health check status data class"""
    service: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time: float
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
    
    def check_database_health(self) -> HealthStatus:
        """Check Supabase database connectivity and performance"""
        start_time = time.time()
        
        try:
            from supabase import create_client
            
            db_config = deployment_config.get_database_config()
            supabase = create_client(db_config["url"], db_config["anon_key"])
            
            # Simple connectivity test
            response = supabase.table("users").select("count").limit(1).execute()
            
            response_time = time.time() - start_time
            
            if response_time > 2.0:  # Slow response
                return HealthStatus(
                    service="database",
                    status="degraded",
                    response_time=response_time,
                    message=f"Database responding slowly ({response_time:.2f}s)",
                    timestamp=datetime.now(timezone.utc),
                    details={"response_time_threshold": 2.0}
                )
            
            return HealthStatus(
                service="database",
                status="healthy",
                response_time=response_time,
                message="Database connection successful",
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return HealthStatus(
                service="database",
                status="unhealthy",
                response_time=time.time() - start_time,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )
    
    def check_groq_api_health(self) -> HealthStatus:
        """Check Groq API connectivity and performance"""
        start_time = time.time()
        
        try:
            from groq import Groq
            
            model_config = deployment_config.get_model_config()
            client = Groq(api_key=model_config["groq_api_key"])
            
            # Simple API test
            models = client.models.list()
            
            response_time = time.time() - start_time
            
            if response_time > 3.0:  # Slow API response
                return HealthStatus(
                    service="groq_api",
                    status="degraded",
                    response_time=response_time,
                    message=f"Groq API responding slowly ({response_time:.2f}s)",
                    timestamp=datetime.now(timezone.utc),
                    details={"response_time_threshold": 3.0}
                )
            
            return HealthStatus(
                service="groq_api",
                status="healthy",
                response_time=response_time,
                message="Groq API connection successful",
                timestamp=datetime.now(timezone.utc),
                details={"available_models": len(models.data) if hasattr(models, 'data') else 0}
            )
            
        except Exception as e:
            return HealthStatus(
                service="groq_api",
                status="unhealthy",
                response_time=time.time() - start_time,
                message=f"Groq API connection failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )
    
    def check_system_resources(self) -> HealthStatus:
        """Check system resource usage"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage (if available)
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
            except:
                disk_percent = 0
            
            details = {
                "memory_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "disk_percent": disk_percent,
                "memory_available_gb": memory.available / (1024**3)
            }
            
            # Determine status based on resource usage
            if memory_percent > 90 or cpu_percent > 90:
                status = "unhealthy"
                message = f"High resource usage: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%"
            elif memory_percent > 75 or cpu_percent > 75:
                status = "degraded"
                message = f"Elevated resource usage: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Resource usage normal: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%"
            
            return HealthStatus(
                service="system_resources",
                status=status,
                response_time=0.0,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details=details
            )
            
        except Exception as e:
            return HealthStatus(
                service="system_resources",
                status="unhealthy",
                response_time=0.0,
                message=f"Failed to check system resources: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )
    
    def check_application_health(self) -> HealthStatus:
        """Check application-specific health metrics"""
        try:
            uptime = time.time() - self.start_time
            
            # Check if critical components can be imported
            critical_imports = [
                "auth_manager",
                "chat_manager", 
                "rag_orchestrator_optimized",
                "model_manager"
            ]
            
            import_status = {}
            for module in critical_imports:
                try:
                    __import__(module)
                    import_status[module] = True
                except ImportError as e:
                    import_status[module] = False
                    self.logger.error(f"Failed to import {module}: {e}")
            
            failed_imports = [k for k, v in import_status.items() if not v]
            
            if failed_imports:
                return HealthStatus(
                    service="application",
                    status="unhealthy",
                    response_time=0.0,
                    message=f"Critical modules failed to import: {', '.join(failed_imports)}",
                    timestamp=datetime.now(timezone.utc),
                    details={
                        "uptime_seconds": uptime,
                        "import_status": import_status
                    }
                )
            
            return HealthStatus(
                service="application",
                status="healthy",
                response_time=0.0,
                message=f"Application running normally (uptime: {uptime:.0f}s)",
                timestamp=datetime.now(timezone.utc),
                details={
                    "uptime_seconds": uptime,
                    "import_status": import_status
                }
            )
            
        except Exception as e:
            return HealthStatus(
                service="application",
                status="unhealthy",
                response_time=0.0,
                message=f"Application health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                details={"error": str(e)}
            )
    
    def run_comprehensive_health_check(self) -> Dict[str, HealthStatus]:
        """Run all health checks and return comprehensive status"""
        health_checks = {
            "database": self.check_database_health(),
            "groq_api": self.check_groq_api_health(),
            "system_resources": self.check_system_resources(),
            "application": self.check_application_health()
        }
        
        return health_checks
    
    def get_overall_status(self, health_checks: Dict[str, HealthStatus]) -> str:
        """Determine overall system status"""
        statuses = [check.status for check in health_checks.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"

class ErrorMonitor:
    """Error monitoring and reporting system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = []
        self.max_stored_errors = 100
    
    def log_error(self, error: Exception, context: str = "", user_id: str = None):
        """Log and track application errors"""
        error_type = type(error).__name__
        error_message = str(error)
        timestamp = datetime.now(timezone.utc)
        
        # Update error counts
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Store recent errors
        error_record = {
            "timestamp": timestamp,
            "error_type": error_type,
            "message": error_message,
            "context": context,
            "user_id": user_id
        }
        
        self.last_errors.append(error_record)
        
        # Keep only recent errors
        if len(self.last_errors) > self.max_stored_errors:
            self.last_errors = self.last_errors[-self.max_stored_errors:]
        
        # Log the error
        self.logger.error(
            f"Error in {context}: {error_type}: {error_message}",
            extra={"user_id": user_id} if user_id else {}
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        return {
            "error_counts": self.error_counts,
            "recent_errors": self.last_errors[-10:],  # Last 10 errors
            "total_errors": sum(self.error_counts.values()),
            "unique_error_types": len(self.error_counts)
        }

# Global instances
health_checker = HealthChecker()
error_monitor = ErrorMonitor()

def render_health_check_page():
    """Render health check page in Streamlit"""
    st.title("🏥 System Health Check")
    
    # Check if health check is enabled and authorized
    if not deployment_config.get("HEALTH_CHECK_ENABLED", "true").lower() == "true":
        st.error("Health check is disabled")
        return
    
    # Simple token-based authorization for health check
    health_token = deployment_config.get("HEALTH_CHECK_TOKEN")
    if health_token:
        provided_token = st.query_params.get("token")
        if provided_token != health_token:
            st.error("Unauthorized access to health check")
            return
    
    # Run health checks
    with st.spinner("Running health checks..."):
        health_results = health_checker.run_comprehensive_health_check()
        overall_status = health_checker.get_overall_status(health_results)
    
    # Display overall status
    status_colors = {
        "healthy": "🟢",
        "degraded": "🟡", 
        "unhealthy": "🔴"
    }
    
    st.subheader(f"{status_colors.get(overall_status, '⚪')} Overall Status: {overall_status.upper()}")
    
    # Display individual service status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Service Status")
        for service, status in health_results.items():
            st.write(f"{status_colors.get(status.status, '⚪')} **{service.replace('_', ' ').title()}**")
            st.write(f"   Status: {status.status}")
            st.write(f"   Message: {status.message}")
            if status.response_time > 0:
                st.write(f"   Response Time: {status.response_time:.3f}s")
            st.write("---")
    
    with col2:
        st.subheader("Error Summary")
        error_summary = error_monitor.get_error_summary()
        st.metric("Total Errors", error_summary["total_errors"])
        st.metric("Unique Error Types", error_summary["unique_error_types"])
        
        if error_summary["recent_errors"]:
            st.write("**Recent Errors:**")
            for error in error_summary["recent_errors"]:
                st.write(f"- {error['timestamp'].strftime('%H:%M:%S')}: {error['error_type']}")
    
    # Detailed information in expander
    with st.expander("Detailed Health Information"):
        for service, status in health_results.items():
            st.subheader(service.replace('_', ' ').title())
            st.json({
                "status": status.status,
                "message": status.message,
                "response_time": status.response_time,
                "timestamp": status.timestamp.isoformat(),
                "details": status.details
            })
    
    # Auto-refresh option
    if st.checkbox("Auto-refresh (30s)"):
        time.sleep(30)
        st.rerun()