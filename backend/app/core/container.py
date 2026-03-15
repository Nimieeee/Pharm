"""
Service Container - Centralized Dependency Injection

Single source of truth for all service instances.
Prevents circular dependencies and duplicate instantiations.

Usage:
    from app.core.container import container
    
    # Initialize once at application startup
    container.initialize(db)
    
    # Get services anywhere in the codebase
    rag_service = container.get('rag_service')
    chat_service = container.get('chat_service')
"""

from typing import Optional, Dict, Any
from supabase import Client

import logging
logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Centralized service registry - Singleton pattern

    Usage:
        container = ServiceContainer()
        container.initialize(db)
        rag_service = container.get('rag_service')
    """

    _instance: Optional['ServiceContainer'] = None
    _initialized: bool = False

    def __new__(cls) -> 'ServiceContainer':
        """Singleton pattern - ensure only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize container - services loaded on initialize()"""
        if not hasattr(self, '_services'):
            self._services: Dict[str, Any] = {}
        if not hasattr(self, '_db'):
            self._db: Optional[Client] = None

    def initialize(self, db: Client) -> 'ServiceContainer':
        """
        Initialize all services with database connection.
        Call once at application startup.
        """
        if self._initialized:
            logger.info("ServiceContainer already initialized, skipping")
            return self

        logger.info("📦 Initializing ServiceContainer with ALL services...")
        self._db = db

        try:
            # Import all services here to avoid circular imports
            from app.services.chat import ChatService
            from app.services.enhanced_rag import EnhancedRAGService
            from app.services.ai import AIService
            from app.services.postprocessing.mermaid_processor import MermaidProcessor
            from app.security.security_guard import LLMSecurityGuard
            from app.services.multi_provider import MultiProviderService
            from app.services.tools import BiomedicalTools
            from app.services.plotting import PlottingService
            from app.services.image_gen import ImageGenerationService
            from app.services.vision_service import VisionService
            from app.services.auth import AuthService
            from app.services.admin import AdminService
            from app.services.support import SupportService
            from app.services.deep_research import DeepResearchService
            from app.services.research_tasks import BackgroundResearchService
            from app.services.lab_report import LabReportService
            from app.services.migration import EmbeddingMigrationService
            from app.services.scheduler import SchedulerService
            from app.services.translation_service import TranslationService
            from app.services.transcription import TranscriptionService
            from app.services.pdf_fulltext import PDFFullTextService
            from app.services.pmc_fulltext import PMCFullTextService
            from app.services.serper import SerperService
            from app.services.email import EmailService
            from app.services.postprocessing.export_processor import ExportProcessor, export_processor
            from app.services.postprocessing.admet_processor import ADMETProcessor
            from app.services.admet_service import ADMETService
            from app.services.postprocessing.prompt_processor import PromptProcessor, prompt_processor
            from app.services.router_service import RouterService, router_service
            from app.services.local_queue import LocalInferenceQueue, local_queue
            from app.services.ddi_service import DDIService

            # Core services (no inter-dependencies) - initialized first
            self._services['chat_service'] = ChatService(db)
            logger.info("✅ Registered: chat_service")

            self._services['rag_service'] = EnhancedRAGService(db)
            logger.info("✅ Registered: rag_service")

            self._services['mermaid_processor'] = MermaidProcessor()
            logger.info("✅ Registered: mermaid_processor")

            self._services['safety_guard'] = LLMSecurityGuard()
            logger.info("✅ Registered: safety_guard")

            self._services['biomedical_tools'] = BiomedicalTools()
            logger.info("✅ Registered: biomedical_tools")

            self._services['plotting_service'] = PlottingService()
            logger.info("✅ Registered: plotting_service")

            self._services['image_gen_service'] = ImageGenerationService()
            logger.info("✅ Registered: image_gen_service")

            self._services['vision_service'] = VisionService()
            logger.info("✅ Registered: vision_service")

            # AIService - depends on core services above
            self._services['ai_service'] = AIService(db)
            logger.info("✅ Registered: ai_service")

            # Auth & User services
            self._services['auth_service'] = AuthService(db)
            logger.info("✅ Registered: auth_service")

            self._services['admin_service'] = AdminService(db)
            logger.info("✅ Registered: admin_service")

            self._services['support_service'] = SupportService(db)
            logger.info("✅ Registered: support_service")

            # Research services
            self._services['deep_research_service'] = DeepResearchService(db)
            logger.info("✅ Registered: deep_research_service")

            self._services['background_research'] = BackgroundResearchService(db)
            logger.info("✅ Registered: background_research")

            self._services['lab_report_service'] = LabReportService()
            logger.info("✅ Registered: lab_report_service")

            # Infrastructure services
            self._services['migration_service'] = EmbeddingMigrationService(db)
            logger.info("✅ Registered: migration_service")

            self._services['scheduler_service'] = SchedulerService()
            logger.info("✅ Registered: scheduler_service")

            self._services['translation_service'] = TranslationService(db)
            logger.info("✅ Registered: translation_service")

            self._services['transcription_service'] = TranscriptionService()
            logger.info("✅ Registered: transcription_service")

            # External API services
            self._services['pdf_service'] = PDFFullTextService()
            logger.info("✅ Registered: pdf_service")

            # PMC service needs API key
            try:
                from app.core.config import settings
                self._services['pmc_service'] = PMCFullTextService(api_key=settings.PUBMED_API_KEY)
                logger.info("✅ Registered: pmc_service")
            except Exception as e:
                logger.warning(f"⚠️  PMC service not available: {e}")
                self._services['pmc_service'] = None

            self._services['serper_service'] = SerperService()
            logger.info("✅ Registered: serper_service")

            self._services['email_service'] = EmailService()
            logger.info("✅ Registered: email_service")

            # ADMET services (postprocessing singleton + service)
            self._services['admet_processor'] = ADMETProcessor()
            logger.info("✅ Registered: admet_processor")

            self._services['admet_service'] = ADMETService(db)
            logger.info("✅ Registered: admet_service")

            # Prompt processing and routing (postprocessing singleton + services)
            self._services['prompt_processor'] = prompt_processor
            logger.info("✅ Registered: prompt_processor")

            self._services['router_service'] = RouterService()
            logger.info("✅ Registered: router_service")

            self._services['export_processor'] = export_processor
            logger.info("✅ Registered: export_processor")

            self._services['local_queue'] = local_queue
            logger.info("✅ Registered: local_queue")

            self._services['ddi_service'] = DDIService()
            logger.info("✅ Registered: ddi_service")

            # Multi-provider LLM (depends on settings, not other services)
            try:
                self._services['llm_provider'] = MultiProviderService()
                logger.info("✅ Registered: llm_provider")
            except ValueError as e:
                logger.warning(f"⚠️  LLM provider not available: {e}")
                self._services['llm_provider'] = None

            self._initialized = True
            logger.info(f"✅ ServiceContainer initialized with {len(self._services)} services")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ServiceContainer: {e}")
            raise

        return self

    def get(self, service_name: str) -> Any:
        """
        Get service instance by name.

        Args:
            service_name: Name of service (e.g., 'rag_service')

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
            RuntimeError: If container not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "ServiceContainer not initialized! Call initialize(db) first."
            )

        if service_name not in self._services:
            raise KeyError(
                f"Service '{service_name}' not registered. "
                f"Available: {list(self._services.keys())}"
            )

        service = self._services[service_name]
        if service is None:
            raise RuntimeError(f"Service '{service_name}' is not available")

        return service

    def has(self, service_name: str) -> bool:
        """Check if service is registered and available"""
        return (
            self._initialized and
            service_name in self._services and
            self._services[service_name] is not None
        )

    def get_db(self) -> Client:
        """Get database connection"""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        return self._db

    def list_services(self) -> list:
        """List all registered services"""
        return list(self._services.keys())

    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized


# Global singleton instance
container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get global container instance"""
    return container


def get_service(service_name: str) -> Any:
    """Convenience function to get service from global container"""
    return container.get(service_name)
