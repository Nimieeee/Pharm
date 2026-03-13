"""
Regression Test Suite - Service Integration

Tests for ServiceContainer, Mermaid processor edge cases, and performance.
Run time target: <2s
"""

import pytest
import time


class TestMermaidProcessorEdgeCases:
    """Test Mermaid processor edge cases"""
    
    @pytest.fixture
    def processor(self):
        from app.services.postprocessing.mermaid_processor import MermaidProcessor
        return MermaidProcessor()
    
    def test_empty_string(self, processor):
        """Test empty string handling"""
        fixed, errors, warnings = processor.validate_and_fix("")
        assert len(errors) > 0
        assert "Empty" in errors[0]
    
    def test_none_input(self, processor):
        """Test None input handling"""
        fixed, errors, warnings = processor.validate_and_fix(None)
        assert len(errors) > 0
    
    def test_whitespace_only(self, processor):
        """Test whitespace-only input"""
        fixed, errors, warnings = processor.validate_and_fix("   \n\n  ")
        assert len(errors) > 0
    
    def test_unicode_variations(self, processor):
        """Test various Unicode characters"""
        test_cases = [
            ('A["Test\u2011hyphen"]', '-'),  # Non-breaking hyphen
            ('A -->|\u226550%| B', '>='),  # Greater-equal
            ('A -->|\u226450%| B', '<='),  # Less-equal
            ('A["5\u00d7 daily"]', 'x'),  # Multiplication
        ]
        
        for broken, expected_contains in test_cases:
            fixed, errors, warnings = processor.validate_and_fix(f"flowchart TD\n    {broken}")
            assert expected_contains in fixed
    
    def test_nested_parentheses(self, processor):
        """Test nested parentheses in labels"""
        broken = 'A["Drug (dose (mg))"] --> B["Effect"]'
        fixed, errors, warnings = processor.validate_and_fix(f"flowchart TD\n    {broken}")
        
        # Should balance parentheses
        label_start = fixed.find('["')
        label_end = fixed.find('"]')
        if label_start >= 0 and label_end > label_start:
            label = fixed[label_start:label_end+2]
            assert label.count('(') == label.count(')')
    
    def test_special_characters_in_labels(self, processor):
        """Test special characters in labels"""
        test_cases = [
            'A["Path\\\\to\\\\file"]',  # Backslashes
            'A["Ampersand & more"]',  # Special chars
        ]
        
        for test in test_cases:
            fixed, errors, warnings = processor.validate_and_fix(f"flowchart TD\n    {test}")
            # Should not crash, may have warnings
            assert isinstance(fixed, str)


class TestServiceContainerIntegration:
    """Test ServiceContainer integration"""
    
    def test_container_has_all_services(self):
        """Test that container registers all expected services"""
        from app.core.container import container
        
        expected_services = [
            'chat_service',
            'rag_service',
            'mermaid_processor',
            'safety_guard',
            'biomedical_tools',
            'plotting_service',
            'image_gen_service',
            'vision_service',
            'ai_service',
            'auth_service',
            'admin_service',
            'support_service',
            'deep_research_service',
            'background_research',
            'lab_report_service',
            'migration_service',
            'scheduler_service',
            'translation_service',
            'transcription_service',
            'pdf_service',
            'pmc_service',
            'serper_service',
            'email_service',
            'admet_processor',
            'admet_service',
            'prompt_processor',
            'router_service',
            'export_processor',
            'local_queue',
            'llm_provider'
        ]
        
        # Container should be initialized by now
        if container.is_initialized():
            for service in expected_services:
                assert container.has(service) or service in container.list_services()
    
    def test_mermaid_processor_from_container(self):
        """Test getting Mermaid processor from container"""
        from app.core.container import container
        
        if container.is_initialized():
            processor = container.get('mermaid_processor')
            assert processor is not None
            
            # Test it works
            fixed, errors, warnings = processor.validate_and_fix("flowchart TD\n    A -->|>=50%| B")
            assert '>=' in fixed


class TestPerformanceRegression:
    """Test performance doesn't regress"""
    
    def test_mermaid_processing_under_10ms(self):
        """Test Mermaid processing stays under 10ms"""
        from app.services.postprocessing import mermaid_processor
        
        complex_diagram = '''
flowchart TD
    A["Clarithromycin 10‑14 d"] -->|≥15%| B["Resistance"]
    B --> C["Switch therapy"]
    C --> D["Amoxicillin(7‑10 d)"]
    D -->|≤90%| E["Success"]
    D -->|>10%| F["Failure"]
    style A fill:#e1f5ff
    style B fill:#ffe1e1
    style C fill:#fff4e1
    style D fill:#e1f5ff
    style E fill:#e1ffe1
    style F fill:#ffe1e1
'''
        
        start = time.perf_counter()
        for _ in range(10):
            mermaid_processor.validate_and_fix(complex_diagram)
        elapsed = (time.perf_counter() - start) * 1000 / 10
        
        assert elapsed < 10, f"Processing took {elapsed:.2f}ms (target: <10ms)"
    
    def test_container_initialization_under_100ms(self):
        """Test container initialization stays under 100ms"""
        from app.core.container import ServiceContainer
        
        # Create new container instance for testing
        start = time.perf_counter()
        test_container = ServiceContainer()
        # Don't initialize with DB, just test object creation
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 100, f"Container creation took {elapsed:.2f}ms (target: <100ms)"
    
    def test_batch_processing_under_100ms(self):
        """Test batch processing of 50 diagrams under 100ms"""
        from app.services.postprocessing import mermaid_processor
        
        diagrams = [
            f'flowchart TD\n    A -->|>= {i}%| B'
            for i in range(50)
        ]
        
        start = time.perf_counter()
        for diagram in diagrams:
            mermaid_processor.validate_and_fix(diagram)
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 100, f"Batch processing took {elapsed:.2f}ms (target: <100ms)"
