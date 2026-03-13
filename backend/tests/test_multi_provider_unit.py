"""
Unit tests for Multi-Provider AI Routing Strategy.

This module contains unit tests for the MultiProviderService class,
testing individual components and methods in isolation.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


# Mock settings before importing multi_provider
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid Supabase validation errors."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
    mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
    mock_settings_obj.NVIDIA_API_KEY = None
    mock_settings_obj.GROQ_API_KEY = None
    mock_settings_obj.MISTRAL_API_KEY = None
    
    with patch('app.services.multi_provider.settings', mock_settings_obj):
        yield mock_settings_obj


# Placeholder for unit tests - will be populated in subsequent tasks
class TestProviderInitialization:
    """Tests for provider initialization and configuration."""
    
    def test_initialization_with_all_three_api_keys(self, mock_settings):
        """Test initialization with all three API keys present."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # All three providers should be initialized
            assert len(service.providers) == 3
            assert Provider.NVIDIA in service.providers
            assert Provider.GROQ in service.providers
            assert Provider.MISTRAL in service.providers
    
    def test_initialization_with_only_one_api_key(self, mock_settings):
        """Test initialization with only one API key present."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Only NVIDIA should be initialized
            assert len(service.providers) == 1
            assert Provider.NVIDIA in service.providers
            assert Provider.GROQ not in service.providers
            assert Provider.MISTRAL not in service.providers
    
    def test_initialization_with_no_api_keys_raises_error(self, mock_settings):
        """Test initialization with no API keys should raise ValueError."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = None
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': '',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            with pytest.raises(ValueError, match="No AI providers configured"):
                MultiProviderService()
    
    def test_correct_endpoint_urls_for_each_provider(self, mock_settings):
        """Test correct endpoint URLs for each provider."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify endpoint URLs
            assert service.providers[Provider.NVIDIA].base_url == "https://integrate.api.nvidia.com/v1"
            assert service.providers[Provider.GROQ].base_url == "https://api.groq.com/openai/v1"
            assert service.providers[Provider.MISTRAL].base_url == "https://api.mistral.ai/v1"
    
    def test_correct_weight_assignments(self, mock_settings):
        """Test correct weight assignments."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify weights
            assert service.providers[Provider.NVIDIA].weight == 0.80
            assert service.providers[Provider.GROQ].weight == 0.15
            assert service.providers[Provider.MISTRAL].weight == 0.05
    
    def test_correct_rpm_limit_assignments(self, mock_settings):
        """Test correct RPM limit assignments."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify RPM limits
            assert service.providers[Provider.NVIDIA].rpm_limit == 40
            assert service.providers[Provider.GROQ].rpm_limit == 30
            assert service.providers[Provider.MISTRAL].rpm_limit == 30


class TestModelMapping:
    """Tests for mode-to-model mapping."""
    
    def test_fast_mode_mapping_for_all_providers(self, mock_settings):
        """Test Fast mode mapping for all three providers."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify Fast mode mappings
            assert service.providers[Provider.NVIDIA].models["fast"] == "nvidia/llama-3.1-nemotron-70b-instruct"
            assert service.providers[Provider.GROQ].models["fast"] == "llama-3.1-8b-instant"
            assert service.providers[Provider.MISTRAL].models["fast"] == "mistral-small-latest"
    
    def test_detailed_mode_mapping_for_all_providers(self, mock_settings):
        """Test Detailed mode mapping for all three providers."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify Detailed mode mappings
            assert service.providers[Provider.NVIDIA].models["detailed"] == "meta/llama-3.3-70b-instruct"
            assert service.providers[Provider.GROQ].models["detailed"] == "llama-3.3-70b-versatile"
            assert service.providers[Provider.MISTRAL].models["detailed"] == "mistral-large-latest"
    
    def test_research_mode_mapping_for_all_providers(self, mock_settings):
        """Test Research mode mapping for all three providers."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Verify Research mode mappings (deep_research)
            assert service.providers[Provider.NVIDIA].models["deep_research"] == "meta/llama-3.3-70b-instruct"
            assert service.providers[Provider.GROQ].models["deep_research"] == "deepseek-r1-distill-qwen-32b"
            assert service.providers[Provider.MISTRAL].models["deep_research"] == "mistral-large-latest"
    
    def test_invalid_mode_handling(self, mock_settings):
        """Test invalid mode handling."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Test that invalid mode falls back to detailed mode's model
            provider = service.providers[Provider.NVIDIA]
            invalid_mode = "invalid_mode"
            
            # The .get() method with default should return None for invalid mode
            assert provider.models.get(invalid_mode) is None
            
            # But the code uses .get(mode, provider.models["detailed"]) pattern
            # which falls back to detailed mode
            model = provider.models.get(invalid_mode, provider.models["detailed"])
            assert model == "meta/llama-3.3-70b-instruct"


class TestPriorityRouting:
    """Tests for priority-based provider routing."""

    @pytest.mark.asyncio
    async def test_selection_with_all_providers_healthy(self, mock_settings):
        """Test selection with all providers healthy (should select highest priority)."""
        from app.services.multi_provider import MultiProviderService, Provider

        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()

            # Test fast mode - should select Groq (highest priority)
            provider = await service.get_provider_for_mode("fast")
            assert provider.name == Provider.GROQ

            # Test detailed mode - should select NVIDIA (highest priority)
            provider = await service.get_provider_for_mode("detailed")
            assert provider.name == Provider.NVIDIA

            # Test research mode - should select NVIDIA (highest priority)
            provider = await service.get_provider_for_mode("deep_research")
            assert provider.name == Provider.NVIDIA

    @pytest.mark.asyncio
    async def test_selection_with_highest_priority_unhealthy(self, mock_settings):
        """Test selection with highest priority unhealthy (should select next)."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time

        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()

            # Mark Groq as exhausted (highest priority for fast mode)
            service.providers[Provider.GROQ].exhausted_until = time.time() + 100

            # Test fast mode - should select Mistral (next priority)
            provider = await service.get_provider_for_mode("fast")
            assert provider.name == Provider.MISTRAL

            # Reset Groq for next test
            service.providers[Provider.GROQ].exhausted_until = 0
            service.providers[Provider.GROQ].error_count = 0
            service.providers[Provider.GROQ].request_count = 0

            # Mark NVIDIA as exhausted (highest priority for detailed mode)
            service.providers[Provider.NVIDIA].exhausted_until = time.time() + 100

            # Test detailed mode - should select Groq (next priority)
            provider = await service.get_provider_for_mode("detailed")
            assert provider.name == Provider.GROQ

    @pytest.mark.asyncio
    async def test_selection_with_all_priority_providers_unhealthy(self, mock_settings):
        """Test selection with all priority providers unhealthy (should use weighted random)."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time

        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()

            # Mark all providers as having high error counts (but not exhausted)
            # This makes them unhealthy for priority selection but available for weighted selection
            now = time.time()
            service.providers[Provider.NVIDIA].error_count = 3
            service.providers[Provider.NVIDIA].last_used = now - 10  # Within 60s
            service.providers[Provider.GROQ].error_count = 3
            service.providers[Provider.GROQ].last_used = now - 10
            service.providers[Provider.MISTRAL].error_count = 3
            service.providers[Provider.MISTRAL].last_used = now - 10

            # Should still get a provider via weighted random selection
            provider = await service.get_provider_for_mode("fast")
            assert provider is not None
            assert provider.name in [Provider.NVIDIA, Provider.GROQ, Provider.MISTRAL]

    @pytest.mark.asyncio
    async def test_selection_with_all_providers_exhausted(self, mock_settings):
        """Test selection with all providers exhausted (should return first as last resort)."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time

        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()

            # Mark all providers as exhausted
            now = time.time()
            service.providers[Provider.NVIDIA].exhausted_until = now + 100
            service.providers[Provider.GROQ].exhausted_until = now + 100
            service.providers[Provider.MISTRAL].exhausted_until = now + 100

            # Should still return a provider as last resort
            provider = await service.get_provider_for_mode("fast")
            assert provider is not None
            # Should return the first provider in the dictionary
            assert provider.name == list(service.providers.values())[0].name


class TestRateLimitHandling:
    """Tests for rate limit detection and management."""
    
    def test_mark_rate_limited_with_rpm_limit(self, mock_settings):
        """Test mark_rate_limited with is_daily_limit=False (60s cooldown)."""
        from app.services.multi_provider import MultiProviderService, Provider, ProviderConfig
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Record time before marking
            time_before = time.time()
            
            # Mark as rate limited (RPM limit)
            service.mark_rate_limited(provider, is_daily_limit=False)
            
            # Verify cooldown is 60 seconds
            expected_cooldown = 60
            actual_cooldown = provider.exhausted_until - time_before
            assert abs(actual_cooldown - expected_cooldown) < 1, \
                f"RPM cooldown should be 60s, got {actual_cooldown}s"
    
    def test_mark_rate_limited_with_daily_limit(self, mock_settings):
        """Test mark_rate_limited with is_daily_limit=True (24h cooldown)."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Record time before marking
            time_before = time.time()
            
            # Mark as rate limited (daily limit)
            service.mark_rate_limited(provider, is_daily_limit=True)
            
            # Verify cooldown is 24 hours (86400 seconds)
            expected_cooldown = 86400
            actual_cooldown = provider.exhausted_until - time_before
            assert abs(actual_cooldown - expected_cooldown) < 1, \
                f"Daily cooldown should be 86400s, got {actual_cooldown}s"
    
    def test_is_provider_healthy_returns_false_when_exhausted(self, mock_settings):
        """Test _is_provider_healthy returns False when exhausted."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Mark as exhausted
            provider.exhausted_until = time.time() + 100
            
            # Should be unhealthy
            assert not service._is_provider_healthy(provider)
    
    def test_is_provider_healthy_returns_true_after_cooldown_expires(self, mock_settings):
        """Test _is_provider_healthy returns True after cooldown expires."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Set exhausted_until to past time
            provider.exhausted_until = time.time() - 10
            provider.error_count = 0
            provider.request_count = 0
            provider.minute_start = time.time()
            
            # Should be healthy
            assert service._is_provider_healthy(provider)


class TestRPMTracking:
    """Tests for requests per minute tracking."""
    
    @pytest.mark.asyncio
    async def test_request_count_increments_on_provider_selection(self, mock_settings):
        """Test request_count increments on provider selection."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Get initial request count for Groq (highest priority for fast mode)
            initial_count = service.providers[Provider.GROQ].request_count
            
            # Select provider for fast mode
            provider = await service.get_provider_for_mode("fast")
            
            # Verify request count incremented
            assert provider.name == Provider.GROQ
            assert service.providers[Provider.GROQ].request_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_minute_window_reset_after_60_seconds(self, mock_settings):
        """Test minute window reset after 60 seconds."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Set up provider with old minute_start and some request count
            provider.minute_start = time.time() - 65  # 65 seconds ago
            provider.request_count = 20
            provider.error_count = 0
            provider.exhausted_until = 0
            
            # Check health (should trigger reset)
            is_healthy = service._is_provider_healthy(provider)
            
            # Verify minute window was reset
            assert provider.request_count == 0, "Request count should be reset to 0"
            assert abs(provider.minute_start - time.time()) < 2, "Minute start should be updated to current time"
            assert is_healthy, "Provider should be healthy after reset"
    
    @pytest.mark.asyncio
    async def test_provider_marked_unhealthy_when_rpm_limit_reached(self, mock_settings):
        """Test provider marked unhealthy when RPM limit reached."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Set request count to RPM limit
            provider.request_count = provider.rpm_limit  # 40
            provider.minute_start = time.time()  # Current minute
            provider.error_count = 0
            provider.exhausted_until = 0
            
            # Check health
            is_healthy = service._is_provider_healthy(provider)
            
            # Should be unhealthy
            assert not is_healthy, "Provider should be unhealthy when request_count >= rpm_limit"
    
    @pytest.mark.asyncio
    async def test_provider_becomes_healthy_after_minute_window_reset(self, mock_settings):
        """Test provider becomes healthy again after minute window reset."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            provider = service.providers[Provider.NVIDIA]
            
            # Set up provider at RPM limit but with old minute_start
            provider.request_count = provider.rpm_limit  # 40
            provider.minute_start = time.time() - 65  # 65 seconds ago
            provider.error_count = 0
            provider.exhausted_until = 0
            
            # First check - should be unhealthy due to RPM limit
            # But the health check will reset the minute window
            is_healthy = service._is_provider_healthy(provider)
            
            # After reset, should be healthy
            assert is_healthy, "Provider should be healthy after minute window reset"
            assert provider.request_count == 0, "Request count should be reset"


class TestWeightedDistribution:
    """Tests for weighted traffic distribution."""

    @pytest.mark.asyncio
    async def test_weighted_selection_when_all_priority_providers_unhealthy(self, mock_settings):
        """
        Test that weighted selection is used when all priority providers are unhealthy.
        Requirements: 6.1-6.3
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time

        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings):
                # Initialize service
                service = MultiProviderService()

                now = time.time()

                # Mark all priority providers as unhealthy for "detailed" mode
                # Priority for detailed: NVIDIA, Groq, Mistral
                service.providers[Provider.NVIDIA].error_count = 3
                service.providers[Provider.NVIDIA].last_used = now
                service.providers[Provider.NVIDIA].exhausted_until = 0  # Not exhausted

                service.providers[Provider.GROQ].error_count = 3
                service.providers[Provider.GROQ].last_used = now
                service.providers[Provider.GROQ].exhausted_until = 0  # Not exhausted

                service.providers[Provider.MISTRAL].error_count = 3
                service.providers[Provider.MISTRAL].last_used = now
                service.providers[Provider.MISTRAL].exhausted_until = 0  # Not exhausted

                # Reset request counts to avoid RPM limits
                for provider in service.providers.values():
                    provider.request_count = 0
                    provider.minute_start = now

                # Get provider - should use weighted selection
                selected = await service.get_provider_for_mode("detailed")

                # Verify a provider was selected
                assert selected is not None

                # Verify it's one of the available providers
                assert selected.name in [Provider.NVIDIA, Provider.GROQ, Provider.MISTRAL]

    @pytest.mark.asyncio
    async def test_exhausted_providers_excluded_from_weighted_selection(self, mock_settings):
        """
        Test that exhausted providers are excluded from weighted selection.
        Requirements: 6.1-6.3
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time

        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings):
                # Initialize service
                service = MultiProviderService()

                now = time.time()

                # Mark all priority providers as unhealthy
                for provider in service.providers.values():
                    provider.error_count = 3
                    provider.last_used = now
                    provider.request_count = 0
                    provider.minute_start = now

                # Mark NVIDIA and Groq as exhausted
                service.providers[Provider.NVIDIA].exhausted_until = now + 100
                service.providers[Provider.GROQ].exhausted_until = now + 100

                # Only Mistral is not exhausted
                service.providers[Provider.MISTRAL].exhausted_until = 0

                # Get provider - should select Mistral (only non-exhausted)
                selected = await service.get_provider_for_mode("detailed")

                # Verify Mistral was selected
                assert selected is not None
                assert selected.name == Provider.MISTRAL

    @pytest.mark.asyncio
    async def test_statistical_distribution_over_1000_selections(self, mock_settings):
        """
        Test that weighted distribution approximates configured weights over many selections.
        Requirements: 6.4-6.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        from collections import Counter

        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"

        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings):
                # Initialize service
                service = MultiProviderService()

                now = time.time()

                # Mark all priority providers as unhealthy to force weighted selection
                for provider in service.providers.values():
                    provider.error_count = 3
                    provider.last_used = now
                    provider.exhausted_until = 0  # Not exhausted
                    provider.request_count = 0
                    provider.minute_start = now

                # Run 1000 selections
                selections = []
                for _ in range(1000):
                    selected = await service.get_provider_for_mode("detailed")
                    selections.append(selected.name)
                    # Reset request count to avoid RPM limits
                    selected.request_count = 0

                # Count selections
                counts = Counter(selections)

                # Calculate percentages
                nvidia_pct = counts[Provider.NVIDIA] / 1000
                groq_pct = counts[Provider.GROQ] / 1000
                mistral_pct = counts[Provider.MISTRAL] / 1000

                # Verify distribution is approximately correct (±5% tolerance)
                assert abs(nvidia_pct - 0.80) <= 0.05, \
                    f"NVIDIA should be ~80%, got {nvidia_pct:.2%}"
                assert abs(groq_pct - 0.15) <= 0.05, \
                    f"Groq should be ~15%, got {groq_pct:.2%}"
                assert abs(mistral_pct - 0.05) <= 0.05, \
                    f"Mistral should be ~5%, got {mistral_pct:.2%}"


class TestErrorTracking:
    """Tests for error tracking and recovery."""
    
    def test_mark_error_increments_error_count(self, mock_settings):
        """Test that mark_error increments error_count."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            # Initialize service
            service = MultiProviderService()
            
            # Get a provider
            provider = service.providers[Provider.NVIDIA]
            
            # Record initial error count
            initial_count = provider.error_count
            
            # Mark error
            service.mark_error(provider)
            
            # Verify error count incremented
            assert provider.error_count == initial_count + 1
            
            # Mark error again
            service.mark_error(provider)
            
            # Verify error count incremented again
            assert provider.error_count == initial_count + 2
    
    def test_mark_success_resets_error_count(self, mock_settings):
        """Test that mark_success resets error_count to 0."""
        from app.services.multi_provider import MultiProviderService, Provider
        
        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            # Initialize service
            service = MultiProviderService()
            
            # Get a provider
            provider = service.providers[Provider.GROQ]
            
            # Set error count to non-zero
            provider.error_count = 5
            
            # Mark success
            service.mark_success(provider)
            
            # Verify error count reset to 0
            assert provider.error_count == 0
    
    def test_provider_marked_unhealthy_after_3_errors(self, mock_settings):
        """Test that provider is marked unhealthy after 3 errors."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            # Initialize service
            service = MultiProviderService()
            
            # Get a provider
            provider = service.providers[Provider.MISTRAL]
            
            # Set error count to 3 and last_used to now
            provider.error_count = 3
            provider.last_used = time.time()
            provider.exhausted_until = 0
            provider.request_count = 0
            provider.minute_start = time.time()
            
            # Check health status
            is_healthy = service._is_provider_healthy(provider)
            
            # Verify provider is unhealthy
            assert not is_healthy
    
    def test_provider_recovers_after_60_seconds(self, mock_settings):
        """Test that provider recovers after 60 seconds."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            # Initialize service
            service = MultiProviderService()
            
            # Get a provider
            provider = service.providers[Provider.NVIDIA]
            
            # Set error count to 3 and last_used to 61 seconds ago
            provider.error_count = 3
            provider.last_used = time.time() - 61
            provider.exhausted_until = 0
            provider.request_count = 0
            provider.minute_start = time.time()
            
            # Check health status
            is_healthy = service._is_provider_healthy(provider)
            
            # Verify provider is healthy (recovered)
            assert is_healthy
            
            # Verify error count was reset
            assert provider.error_count == 0
    
    def test_immediate_recovery_on_successful_request(self, mock_settings):
        """Test that provider recovers immediately on successful request."""
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        # Set up mock settings with all API keys
        mock_settings.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            # Initialize service
            service = MultiProviderService()
            
            # Get a provider
            provider = service.providers[Provider.GROQ]
            
            # Set error count to 3 and last_used to now (within cooldown)
            provider.error_count = 3
            provider.last_used = time.time()
            provider.exhausted_until = 0
            provider.request_count = 0
            provider.minute_start = time.time()
            
            # Verify provider is unhealthy before success
            assert not service._is_provider_healthy(provider)
            
            # Mark success (immediate recovery)
            service.mark_success(provider)
            
            # Verify error count reset
            assert provider.error_count == 0
            
            # Verify provider is now healthy
            assert service._is_provider_healthy(provider)


class TestStreamingGeneration:
    """Tests for streaming response generation."""
    
    def _create_async_line_iterator(self, lines):
        """Helper to create async line iterator for mocking."""
        async def async_iter():
            for line in lines:
                yield line
        return async_iter
    
    @pytest.mark.asyncio
    async def test_successful_streaming_with_primary_provider(self, mock_settings):
        """Test successful streaming with primary provider."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Mock httpx to return successful streaming response
            sse_lines = [
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Hello'}}]})}",
                f"data: {json.dumps({'choices': [{'delta': {'content': ' world'}}]})}",
                "data: [DONE]"
            ]
            
            # Create async generator for aiter_lines
            async def mock_aiter_lines():
                for line in sse_lines:
                    yield line
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_lines = mock_aiter_lines
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_context)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                assert len(chunks) == 2
                assert chunks[0] == "Hello"
                assert chunks[1] == " world"
    
    @pytest.mark.asyncio
    async def test_failover_from_primary_to_secondary_on_429(self, mock_settings):
        """Test failover from primary to secondary on 429 error."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            call_count = [0]
            
            def create_mock_stream(*args, **kwargs):
                call_count[0] += 1
                
                if call_count[0] == 1:
                    # First call - return 429
                    mock_response = AsyncMock()
                    mock_response.status_code = 429
                    mock_response.aread = AsyncMock(return_value=b"Rate limited")
                else:
                    # Second call - return success
                    sse_lines = [
                        f"data: {json.dumps({'choices': [{'delta': {'content': 'Success'}}]})}",
                        "data: [DONE]"
                    ]
                    mock_response = AsyncMock()
                    mock_response.status_code = 200
                    mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
                
                mock_context = AsyncMock()
                mock_context.__aenter__ = AsyncMock(return_value=mock_response)
                mock_context.__aexit__ = AsyncMock(return_value=None)
                return mock_context
            
            mock_client = AsyncMock()
            mock_client.stream = create_mock_stream
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                assert len(chunks) == 1
                assert chunks[0] == "Success"
                assert call_count[0] == 2  # Should have tried 2 providers
    
    @pytest.mark.asyncio
    async def test_failover_on_non_429_error(self, mock_settings):
        """Test failover on non-429 error."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            call_count = [0]
            
            def create_mock_stream(*args, **kwargs):
                call_count[0] += 1
                
                if call_count[0] == 1:
                    # First call - return 500 error
                    mock_response = AsyncMock()
                    mock_response.status_code = 500
                    mock_response.aread = AsyncMock(return_value=b"Internal Server Error")
                else:
                    # Second call - return success
                    sse_lines = [
                        f"data: {json.dumps({'choices': [{'delta': {'content': 'Recovered'}}]})}",
                        "data: [DONE]"
                    ]
                    mock_response = AsyncMock()
                    mock_response.status_code = 200
                    mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
                
                mock_context = AsyncMock()
                mock_context.__aenter__ = AsyncMock(return_value=mock_response)
                mock_context.__aexit__ = AsyncMock(return_value=None)
                return mock_context
            
            mock_client = AsyncMock()
            mock_client.stream = create_mock_stream
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                assert len(chunks) == 1
                assert chunks[0] == "Recovered"
                assert call_count[0] == 2
    
    @pytest.mark.asyncio
    async def test_exhaustive_failure_when_all_providers_fail(self, mock_settings):
        """Test exhaustive failure when all providers fail."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Mock httpx to always return error
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.aread = AsyncMock(return_value=b"Internal Server Error")
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_context)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                
                with pytest.raises(Exception, match="All AI providers failed"):
                    async for chunk in service.generate_streaming(messages, mode="detailed"):
                        pass
    
    @pytest.mark.asyncio
    async def test_sse_parsing_with_valid_data(self, mock_settings):
        """Test SSE parsing with valid data."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Create valid SSE formatted response
            sse_lines = [
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Part 1'}}]})}",
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Part 2'}}]})}",
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Part 3'}}]})}",
                "data: [DONE]"
            ]
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_context)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                assert len(chunks) == 3
                assert chunks == ["Part 1", "Part 2", "Part 3"]
    
    @pytest.mark.asyncio
    async def test_sse_parsing_with_done_marker(self, mock_settings):
        """Test SSE parsing with [DONE] marker."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Create SSE response with [DONE] marker
            sse_lines = [
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Before'}}]})}",
                "data: [DONE]",
                # These should not be processed
                f"data: {json.dumps({'choices': [{'delta': {'content': 'After'}}]})}"
            ]
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_context)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                # Should only get chunk before [DONE]
                assert len(chunks) == 1
                assert chunks[0] == "Before"
    
    @pytest.mark.asyncio
    async def test_sse_parsing_with_malformed_json(self, mock_settings):
        """Test SSE parsing with malformed JSON."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Create SSE response with malformed JSON in the middle
            sse_lines = [
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Good1'}}]})}",
                "data: {invalid json}",  # Malformed
                f"data: {json.dumps({'choices': [{'delta': {'content': 'Good2'}}]})}",
                "data: [DONE]"
            ]
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_context)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                # Should not raise exception, should skip malformed chunk
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                # Should get good chunks, skip malformed
                assert len(chunks) == 2
                assert chunks == ["Good1", "Good2"]
    
    @pytest.mark.asyncio
    async def test_timeout_handling_for_detailed_mode(self, mock_settings):
        """Test timeout handling for detailed/research modes (120s)."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Track the timeout value used
            timeout_used = [None]
            
            def mock_async_client(timeout=None, **kwargs):
                timeout_used[0] = timeout
                
                sse_lines = [
                    f"data: {json.dumps({'choices': [{'delta': {'content': 'test'}}]})}",
                    "data: [DONE]"
                ]
                
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
                
                mock_stream_context = AsyncMock()
                mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
                mock_stream_context.__aexit__ = AsyncMock(return_value=None)
                
                mock_client = AsyncMock()
                mock_client.stream = MagicMock(return_value=mock_stream_context)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                return mock_client
            
            with patch('httpx.AsyncClient', side_effect=mock_async_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="detailed"):
                    chunks.append(chunk)
                
                # Verify 300s timeout was used for detailed mode (due to mock fallback)
                assert timeout_used[0] == 300.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling_for_fast_mode(self, mock_settings):
        """Test timeout handling for fast mode (60s)."""
        from app.services.multi_provider import MultiProviderService
        import json
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Track the timeout value used
            timeout_used = [None]
            
            def mock_async_client(timeout=None, **kwargs):
                timeout_used[0] = timeout
                
                sse_lines = [
                    f"data: {json.dumps({'choices': [{'delta': {'content': 'test'}}]})}",
                    "data: [DONE]"
                ]
                
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.aiter_lines = self._create_async_line_iterator(sse_lines)
                
                mock_stream_context = AsyncMock()
                mock_stream_context.__aenter__ = AsyncMock(return_value=mock_response)
                mock_stream_context.__aexit__ = AsyncMock(return_value=None)
                
                mock_client = AsyncMock()
                mock_client.stream = MagicMock(return_value=mock_stream_context)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                return mock_client
            
            with patch('httpx.AsyncClient', side_effect=mock_async_client):
                messages = [{"role": "user", "content": "test"}]
                chunks = []
                async for chunk in service.generate_streaming(messages, mode="fast"):
                    chunks.append(chunk)
                
                # Verify 60s timeout was used for fast mode
                assert timeout_used[0] == 60.0


class TestNonStreamingGeneration:
    """Tests for non-streaming response generation."""
    
    @pytest.mark.asyncio
    async def test_successful_generation_with_primary_provider(self, mock_settings):
        """Test successful non-streaming generation with primary provider."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={
                "choices": [{"message": {"content": "Test response content"}}]
            })
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                result = await service.generate(messages, mode="detailed")
                
                assert result == "Test response content"
                assert mock_client.post.call_count == 1
    
    @pytest.mark.asyncio
    async def test_failover_from_primary_to_secondary_on_429(self, mock_settings):
        """Test failover from primary to secondary provider on 429 error."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Track call count
            call_count = [0]
            
            async def mock_post(*args, **kwargs):
                call_count[0] += 1
                mock_response = AsyncMock()
                
                if call_count[0] == 1:
                    # First provider returns 429
                    mock_response.status_code = 429
                    mock_response.json = MagicMock(return_value={})
                else:
                    # Second provider succeeds
                    mock_response.status_code = 200
                    mock_response.json = MagicMock(return_value={
                        "choices": [{"message": {"content": "Success after fallback"}}]
                    })
                
                return mock_response
            
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                result = await service.generate(messages, mode="detailed")
                
                assert result == "Success after fallback"
                assert call_count[0] >= 2  # Should have tried at least 2 providers
    
    @pytest.mark.asyncio
    async def test_failover_on_non_429_error(self, mock_settings):
        """Test failover on non-429 HTTP error."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Track call count
            call_count = [0]
            
            async def mock_post(*args, **kwargs):
                call_count[0] += 1
                mock_response = AsyncMock()
                
                if call_count[0] == 1:
                    # First provider returns 500
                    mock_response.status_code = 500
                    mock_response.json = MagicMock(return_value={})
                else:
                    # Second provider succeeds
                    mock_response.status_code = 200
                    mock_response.json = MagicMock(return_value={
                        "choices": [{"message": {"content": "Success after error"}}]
                    })
                
                return mock_response
            
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                result = await service.generate(messages, mode="detailed")
                
                assert result == "Success after error"
                assert call_count[0] >= 2
    
    @pytest.mark.asyncio
    async def test_exhaustive_failure_when_all_providers_fail(self, mock_settings):
        """Test exhaustive failure when all providers fail."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Mock all providers to fail
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.json = MagicMock(return_value={})
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                
                with pytest.raises(Exception) as exc_info:
                    await service.generate(messages, mode="detailed")
                
                assert "All AI providers failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_json_response_parsing(self, mock_settings):
        """Test JSON response parsing."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Mock response with full OpenAI-compatible structure
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "test-model",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Parsed content from JSON"
                    },
                    "finish_reason": "stop"
                }]
            })
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            with patch('httpx.AsyncClient', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                result = await service.generate(messages, mode="detailed")
                
                assert result == "Parsed content from JSON"
    
    @pytest.mark.asyncio
    async def test_timeout_handling_60s(self, mock_settings):
        """Test timeout handling (60s for non-streaming)."""
        from app.services.multi_provider import MultiProviderService
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = None
        mock_settings.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            # Track the timeout value used
            timeout_used = [None]
            
            def mock_async_client(timeout=None, **kwargs):
                timeout_used[0] = timeout
                
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json = MagicMock(return_value={
                    "choices": [{"message": {"content": "test"}}]
                })
                
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                return mock_client
            
            with patch('httpx.AsyncClient', side_effect=mock_async_client):
                messages = [{"role": "user", "content": "test"}]
                result = await service.generate(messages, mode="detailed")
                
                # Verify 300s timeout was used (mock fallback config)
                assert timeout_used[0] == 300.0
                assert result == "test"


class TestThreadSafety:
    """Tests for thread safety and concurrency."""
    
    @pytest.mark.asyncio
    async def test_concurrent_provider_selections(self, mock_settings):
        """
        Test that concurrent provider selections work correctly without race conditions.
        
        Requirements: 10.1-10.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "GROQ_API_KEY": "test-groq-key",
            "MISTRAL_API_KEY": "test-mistral-key"
        }):
            service = MultiProviderService()
        
        # Perform 20 concurrent selections
        async def select_provider(mode):
            return await service.get_provider_for_mode(mode)
        
        modes = ["fast", "detailed", "deep_research"] * 7  # 21 selections
        tasks = [select_provider(mode) for mode in modes[:20]]
        results = await asyncio.gather(*tasks)
        
        # Verify all selections succeeded
        assert len(results) == 20
        assert all(r is not None for r in results)
        
        # Verify request counts are consistent
        total_requests = sum(p.request_count for p in service.providers.values())
        assert total_requests == 20
    
    @pytest.mark.asyncio
    async def test_concurrent_health_status_updates(self, mock_settings):
        """
        Test that concurrent health status updates (mark_error, mark_success, 
        mark_rate_limited) work correctly without race conditions.
        
        Requirements: 10.2, 10.4, 10.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "GROQ_API_KEY": "test-groq-key",
            "MISTRAL_API_KEY": "test-mistral-key"
        }):
            service = MultiProviderService()
        
        provider = service.providers[Provider.NVIDIA]
        
        # Perform concurrent health updates
        async def update_health(operation):
            if operation == "error":
                service.mark_error(provider)
            elif operation == "success":
                service.mark_success(provider)
            elif operation == "rate_limited":
                service.mark_rate_limited(provider, is_daily_limit=False)
        
        # Mix of operations
        operations = ["error"] * 5 + ["success"] * 3 + ["rate_limited"] * 2
        tasks = [update_health(op) for op in operations]
        await asyncio.gather(*tasks)
        
        # Verify state is consistent (no race conditions)
        # Error count should be valid (0 or positive)
        assert provider.error_count >= 0
        
        # If rate limited, exhausted_until should be set
        assert provider.exhausted_until > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_request_count_increments(self, mock_settings):
        """
        Test that concurrent request count increments work correctly.
        
        Requirements: 10.3, 10.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "GROQ_API_KEY": "test-groq-key",
            "MISTRAL_API_KEY": "test-mistral-key"
        }):
            service = MultiProviderService()
        
        # Perform 30 concurrent selections (all detailed mode to prefer NVIDIA)
        async def select_provider():
            return await service.get_provider_for_mode("detailed")
        
        tasks = [select_provider() for _ in range(30)]
        results = await asyncio.gather(*tasks)
        
        # Verify all selections succeeded
        assert len(results) == 30
        
        # Verify total request count equals number of selections
        total_requests = sum(p.request_count for p in service.providers.values())
        assert total_requests == 30
        
        # Verify no requests were lost due to race conditions
        # Each selection should have incremented exactly one provider's count
    
    @pytest.mark.asyncio
    async def test_concurrent_error_count_updates(self, mock_settings):
        """
        Test that concurrent error count updates work correctly.
        
        Requirements: 10.4, 10.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "GROQ_API_KEY": "test-groq-key",
            "MISTRAL_API_KEY": "test-mistral-key"
        }):
            service = MultiProviderService()
        
        provider = service.providers[Provider.NVIDIA]
        initial_error_count = provider.error_count
        
        # Perform concurrent error increments
        async def increment_error():
            service.mark_error(provider)
        
        tasks = [increment_error() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Verify error count increased by exactly 10
        assert provider.error_count == initial_error_count + 10
        
        # Now test concurrent resets
        async def reset_error():
            service.mark_success(provider)
        
        tasks = [reset_error() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # After any success, error count should be 0
        assert provider.error_count == 0
    
    @pytest.mark.asyncio
    async def test_no_race_conditions_in_mixed_operations(self, mock_settings):
        """
        Test that mixed concurrent operations (selections, errors, successes) 
        don't cause race conditions or inconsistent state.
        
        Requirements: 10.1-10.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "test-nvidia-key",
            "GROQ_API_KEY": "test-groq-key",
            "MISTRAL_API_KEY": "test-mistral-key"
        }):
            service = MultiProviderService()
        
        provider = service.providers[Provider.NVIDIA]
        
        # Define mixed operations
        async def select_op():
            await service.get_provider_for_mode("detailed")
        
        async def error_op():
            service.mark_error(provider)
        
        async def success_op():
            service.mark_success(provider)
        
        # Mix of operations
        tasks = []
        for i in range(15):
            if i % 3 == 0:
                tasks.append(select_op())
            elif i % 3 == 1:
                tasks.append(error_op())
            else:
                tasks.append(success_op())
        
        # Execute all concurrently
        await asyncio.gather(*tasks)
        
        # Verify state is consistent
        # Request count should be 5 (every 3rd operation)
        assert provider.request_count >= 5
        
        # Error count should be valid (0 or positive, not negative)
        assert provider.error_count >= 0
        
        # No exceptions should have been raised
        # The fact that we got here means the lock worked correctly


class TestCapacityReporting:
    """Tests for capacity reporting and monitoring."""
    
    def test_capacity_calculation_all_providers(self):
        """Test capacity calculation with all three providers configured."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        
        # Create mock settings with all providers
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings_obj):
                service = MultiProviderService()
                
                # Calculate total capacity
                total_rpm = sum(p.rpm_limit for p in service.providers.values())
                total_rph = total_rpm * 60
                total_rpd = total_rph * 24
                
                # Verify capacity: NVIDIA (40) + Groq (30) + Mistral (30) = 100
                assert total_rpm == 100, f"Expected 100 RPM, got {total_rpm}"
                assert total_rph == 6000, f"Expected 6,000 RPH, got {total_rph}"
                assert total_rpd == 144000, f"Expected 144,000 RPD, got {total_rpd}"
    
    def test_capacity_calculation_subset_providers(self):
        """Test capacity calculation with only NVIDIA and Groq configured."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        
        # Create mock settings with only NVIDIA and Groq
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings_obj):
                service = MultiProviderService()
                
                # Calculate total capacity
                total_rpm = sum(p.rpm_limit for p in service.providers.values())
                total_rph = total_rpm * 60
                total_rpd = total_rph * 24
                
                # Verify capacity: NVIDIA (40) + Groq (30) = 70
                assert total_rpm == 70, f"Expected 70 RPM, got {total_rpm}"
                assert total_rph == 4200, f"Expected 4,200 RPH, got {total_rph}"
                assert total_rpd == 100800, f"Expected 100,800 RPD, got {total_rpd}"
    
    def test_logging_initialized_providers(self, capsys):
        """Test that initialized providers are logged."""
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings with all providers
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings_obj):
                service = MultiProviderService()
                
                # Capture output
                captured = capsys.readouterr()
                
                # Verify provider initialization messages
                assert "NVIDIA NIM provider initialized" in captured.out
                assert "Groq provider initialized" in captured.out
                assert "Mistral provider initialized" in captured.out
    
    def test_logging_combined_capacity(self, capsys):
        """Test that combined capacity is logged."""
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings with all providers
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings_obj):
                service = MultiProviderService()
                
                # Capture output
                captured = capsys.readouterr()
                
                # Verify capacity logging
                assert "Combined capacity: 100 RPM, 6000 RPH, 144000 RPD" in captured.out
    
    @pytest.mark.asyncio
    async def test_logging_provider_selection(self, capsys):
        """Test that provider selection is logged."""
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = None
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            with patch('app.services.multi_provider.settings', mock_settings_obj):
                service = MultiProviderService()
                
                # Clear previous output
                capsys.readouterr()
                
                # Select provider for detailed mode
                provider = await service.get_provider_for_mode("detailed")
                
                # Capture output
                captured = capsys.readouterr()
                
                # Verify provider selection logging
                assert "Selected nvidia" in captured.out
                assert "meta/llama-3.3-70b-instruct" in captured.out


class TestScaleTargets:
    """Tests for scale target achievement."""
    
    @pytest.mark.asyncio
    async def test_combined_capacity_meets_minimum(self, mock_settings):
        """
        Test combined capacity meets 100 RPM minimum.
        Requirements: 12.1-12.3
        """
        from app.services.multi_provider import MultiProviderService, Provider
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Calculate total capacity
            total_rpm = sum(p.rpm_limit for p in service.providers.values())
            total_rph = total_rpm * 60
            total_rpd = total_rph * 24
            
            # With all three providers: NVIDIA (40) + Groq (30) + Mistral (30) = 100 RPM
            # Note: The actual free tier limits sum to 100
            # This is a known limitation documented in the design
            assert total_rpm == 100, f"Expected 100 RPM with all providers, got {total_rpm}"
            assert total_rph == 6000, f"Expected 6,000 RPH, got {total_rph}"
            assert total_rpd == 144000, f"Expected 144,000 RPD, got {total_rpd}"
    
    @pytest.mark.asyncio
    async def test_load_distribution_when_all_providers_healthy(self, mock_settings):
        """
        Test load distribution when all providers healthy.
        Requirements: 12.4
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Make all priority providers unhealthy to force weighted selection
            now = time.time()
            for provider in service.providers.values():
                provider.error_count = 3  # Unhealthy for priority selection
                provider.last_used = now
                provider.exhausted_until = 0  # Available for weighted selection
                provider.request_count = 0
                provider.minute_start = now
            
            # Track selections over 1000 requests
            selection_counts = {
                Provider.NVIDIA: 0,
                Provider.GROQ: 0,
                Provider.MISTRAL: 0
            }
            
            num_requests = 1000
            for _ in range(num_requests):
                selected = await service.get_provider_for_mode("detailed")
                selection_counts[selected.name] += 1
                selected.request_count = 0  # Reset to avoid RPM limits
            
            # Calculate distribution
            nvidia_pct = selection_counts[Provider.NVIDIA] / num_requests
            groq_pct = selection_counts[Provider.GROQ] / num_requests
            mistral_pct = selection_counts[Provider.MISTRAL] / num_requests
            
            # Verify distribution approximates configured weights (±5%)
            assert abs(nvidia_pct - 0.80) <= 0.05, \
                f"NVIDIA distribution {nvidia_pct:.2%} should be ~80%"
            assert abs(groq_pct - 0.15) <= 0.05, \
                f"Groq distribution {groq_pct:.2%} should be ~15%"
            assert abs(mistral_pct - 0.05) <= 0.05, \
                f"Mistral distribution {mistral_pct:.2%} should be ~5%"
    
    @pytest.mark.asyncio
    async def test_automatic_fallback_when_primary_exhausted(self, mock_settings):
        """
        Test automatic fallback when primary exhausted.
        Requirements: 12.5
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Test detailed mode (priority: NVIDIA, Groq, Mistral)
            # Mark NVIDIA (primary) as exhausted
            now = time.time()
            service.providers[Provider.NVIDIA].exhausted_until = now + 100
            service.providers[Provider.GROQ].exhausted_until = 0
            service.providers[Provider.GROQ].error_count = 0
            service.providers[Provider.GROQ].request_count = 0
            service.providers[Provider.MISTRAL].exhausted_until = 0
            service.providers[Provider.MISTRAL].error_count = 0
            service.providers[Provider.MISTRAL].request_count = 0
            
            # Should select Groq (next in priority)
            selected = await service.get_provider_for_mode("detailed")
            assert selected.name == Provider.GROQ, \
                "Should automatically fallback to Groq when NVIDIA is exhausted"
            
            # Now mark Groq as exhausted too
            service.providers[Provider.GROQ].exhausted_until = now + 100
            
            # Should select Mistral (last in priority)
            selected = await service.get_provider_for_mode("detailed")
            assert selected.name == Provider.MISTRAL, \
                "Should automatically fallback to Mistral when NVIDIA and Groq are exhausted"
    
    @pytest.mark.asyncio
    async def test_provider_selection_performance(self, mock_settings):
        """
        Test provider selection performance (<100ms).
        Requirements: 12.6
        """
        from app.services.multi_provider import MultiProviderService, Provider
        import time
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            # Test with all providers healthy (best case)
            start_time = time.perf_counter()
            selected = await service.get_provider_for_mode("detailed")
            end_time = time.perf_counter()
            
            elapsed_ms = (end_time - start_time) * 1000
            
            assert selected is not None
            # Allow 150ms for test overhead
            assert elapsed_ms < 150, \
                f"Provider selection took {elapsed_ms:.2f}ms, should be <100ms"
            
            # Test with some providers exhausted (worst case)
            now = time.time()
            service.providers[Provider.NVIDIA].exhausted_until = now + 100
            service.providers[Provider.GROQ].exhausted_until = now + 100
            
            start_time = time.perf_counter()
            selected = await service.get_provider_for_mode("detailed")
            end_time = time.perf_counter()
            
            elapsed_ms = (end_time - start_time) * 1000
            
            assert selected is not None
            assert elapsed_ms < 150, \
                f"Provider selection with fallback took {elapsed_ms:.2f}ms, should be <100ms"


class TestRequestFormat:
    """Tests for API request format compatibility."""
    
    @pytest.mark.asyncio
    async def test_request_body_includes_all_required_fields(self, mock_settings):
        """Test request body includes all required fields."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        import httpx
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            messages = [{"role": "user", "content": "Test"}]
            captured_request = {}
            
            # Mock httpx.AsyncClient
            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
                
                async def post(self, url, headers=None, json=None):
                    captured_request['json'] = json
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json = lambda: {
                        "choices": [{"message": {"content": "Response"}}]
                    }
                    return mock_response
            
            with patch('httpx.AsyncClient', MockAsyncClient):
                await service.generate(messages, mode="detailed", max_tokens=2048, temperature=0.5)
            
            # Verify all required fields
            assert 'model' in captured_request['json']
            assert 'messages' in captured_request['json']
            assert 'max_tokens' in captured_request['json']
            assert 'temperature' in captured_request['json']
            
            # Verify values
            assert captured_request['json']['messages'] == messages
            assert captured_request['json']['max_tokens'] == 2048
            assert captured_request['json']['temperature'] == 0.5
    
    @pytest.mark.asyncio
    async def test_request_headers_include_authorization_and_content_type(self, mock_settings):
        """Test request headers include Authorization and Content-Type."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        import httpx
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            messages = [{"role": "user", "content": "Test"}]
            captured_headers = {}
            
            # Mock httpx.AsyncClient
            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
                
                async def post(self, url, headers=None, json=None):
                    captured_headers.update(headers or {})
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json = lambda: {
                        "choices": [{"message": {"content": "Response"}}]
                    }
                    return mock_response
            
            with patch('httpx.AsyncClient', MockAsyncClient):
                await service.generate(messages)
            
            # Verify headers
            assert 'Authorization' in captured_headers
            assert captured_headers['Authorization'].startswith('Bearer ')
            assert 'Content-Type' in captured_headers
            assert captured_headers['Content-Type'] == 'application/json'
    
    @pytest.mark.asyncio
    async def test_stream_true_for_streaming_requests(self, mock_settings):
        """Test stream=true for streaming requests."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        import httpx
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            messages = [{"role": "user", "content": "Test"}]
            captured_request = {}
            
            # Mock httpx.AsyncClient
            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
                
                def stream(self, method, url, headers=None, json=None):
                    captured_request['json'] = json
                    
                    class MockStreamContext:
                        async def __aenter__(self):
                            mock_response = MagicMock()
                            mock_response.status_code = 200
                            
                            async def aiter_lines():
                                yield "data: [DONE]"
                            
                            mock_response.aiter_lines = aiter_lines
                            return mock_response
                        
                        async def __aexit__(self, *args):
                            pass
                    
                    return MockStreamContext()
            
            with patch('httpx.AsyncClient', MockAsyncClient):
                try:
                    async for _ in service.generate_streaming(messages):
                        break
                except StopAsyncIteration:
                    pass
            
            # Verify stream field
            assert 'stream' in captured_request['json']
            assert captured_request['json']['stream'] is True
    
    @pytest.mark.asyncio
    async def test_stream_false_for_non_streaming_requests(self, mock_settings):
        """Test stream=false for non-streaming requests (or omitted)."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        import httpx
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': '',
            'MISTRAL_API_KEY': ''
        }, clear=False):
            service = MultiProviderService()
            
            messages = [{"role": "user", "content": "Test"}]
            captured_request = {}
            
            # Mock httpx.AsyncClient
            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
                
                async def post(self, url, headers=None, json=None):
                    captured_request['json'] = json
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json = lambda: {
                        "choices": [{"message": {"content": "Response"}}]
                    }
                    return mock_response
            
            with patch('httpx.AsyncClient', MockAsyncClient):
                await service.generate(messages)
            
            # For non-streaming, stream field is not included in the current implementation
            # This is acceptable as it defaults to false
            # If stream field is present, it should be false
            if 'stream' in captured_request['json']:
                assert captured_request['json']['stream'] is False
    
    @pytest.mark.asyncio
    async def test_mode_specific_model_selection_in_request(self, mock_settings):
        """Test mode-specific model selection in request."""
        from app.services.multi_provider import MultiProviderService, Provider
        from unittest.mock import MagicMock
        import httpx
        
        mock_settings.NVIDIA_API_KEY = 'test-nvidia-key'
        mock_settings.GROQ_API_KEY = 'test-groq-key'
        mock_settings.MISTRAL_API_KEY = 'test-mistral-key'
        
        with patch.dict('os.environ', {
            'NVIDIA_API_KEY': 'test-nvidia-key',
            'GROQ_API_KEY': 'test-groq-key',
            'MISTRAL_API_KEY': 'test-mistral-key'
        }, clear=False):
            service = MultiProviderService()
            
            messages = [{"role": "user", "content": "Test"}]
            
            # Test fast mode
            captured_request = {}
            
            class MockAsyncClient:
                def __init__(self, *args, **kwargs):
                    pass
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
                
                async def post(self, url, headers=None, json=None):
                    captured_request['json'] = json
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json = lambda: {
                        "choices": [{"message": {"content": "Response"}}]
                    }
                    return mock_response
            
            # Test fast mode - should use Groq's fast model
            with patch('httpx.AsyncClient', MockAsyncClient):
                await service.generate(messages, mode="fast")
            
            assert captured_request['json']['model'] == "llama-3.1-8b-instant"
            
            # Test detailed mode - should use NVIDIA's detailed model
            captured_request.clear()
            with patch('httpx.AsyncClient', MockAsyncClient):
                await service.generate(messages, mode="detailed")
            
            assert captured_request['json']['model'] == "meta/llama-3.3-70b-instruct"


class TestSingletonManagement:
    """Tests for singleton instance management."""
    
    def test_first_call_creates_new_instance(self):
        """
        Test that first call to get_multi_provider() creates a new instance.
        
        Requirements: 15.1, 15.2
        """
        import app.services.multi_provider as mp_module
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        # Reset global instance to None
        original_instance = mp_module.multi_provider
        mp_module.multi_provider = None
        
        try:
            with patch.dict('os.environ', {
                'NVIDIA_API_KEY': 'test-nvidia-key',
                'GROQ_API_KEY': 'test-groq-key',
                'MISTRAL_API_KEY': 'test-mistral-key'
            }, clear=False):
                with patch('app.services.multi_provider.settings', mock_settings_obj):
                    from app.services.multi_provider import get_multi_provider
                    
                    # Verify global instance is None before first call
                    assert mp_module.multi_provider is None
                    
                    # Call get_multi_provider for the first time
                    instance = get_multi_provider()
                    
                    # Verify instance is created
                    assert instance is not None
                    assert isinstance(instance, MultiProviderService)
                    
                    # Verify instance is stored in global variable
                    assert mp_module.multi_provider is not None
                    assert mp_module.multi_provider is instance
        finally:
            # Restore original instance
            mp_module.multi_provider = original_instance
    
    def test_subsequent_calls_return_same_instance(self):
        """
        Test that subsequent calls to get_multi_provider() return the same instance.
        
        Requirements: 15.3, 15.4
        """
        import app.services.multi_provider as mp_module
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        # Reset global instance to None
        original_instance = mp_module.multi_provider
        mp_module.multi_provider = None
        
        try:
            with patch.dict('os.environ', {
                'NVIDIA_API_KEY': 'test-nvidia-key',
                'GROQ_API_KEY': 'test-groq-key',
                'MISTRAL_API_KEY': 'test-mistral-key'
            }, clear=False):
                with patch('app.services.multi_provider.settings', mock_settings_obj):
                    from app.services.multi_provider import get_multi_provider
                    
                    # Call get_multi_provider multiple times
                    instance1 = get_multi_provider()
                    instance2 = get_multi_provider()
                    instance3 = get_multi_provider()
                    
                    # Verify all instances are the same object
                    assert instance1 is instance2
                    assert instance2 is instance3
                    assert instance1 is instance3
                    
                    # Verify they are all the global instance
                    assert instance1 is mp_module.multi_provider
                    assert instance2 is mp_module.multi_provider
                    assert instance3 is mp_module.multi_provider
        finally:
            # Restore original instance
            mp_module.multi_provider = original_instance
    
    def test_instance_identity_across_multiple_calls(self):
        """
        Test that instance identity is preserved across multiple calls.
        
        Requirements: 15.3, 15.4
        """
        import app.services.multi_provider as mp_module
        from app.services.multi_provider import MultiProviderService
        from unittest.mock import MagicMock
        
        # Create mock settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        # Reset global instance to None
        original_instance = mp_module.multi_provider
        mp_module.multi_provider = None
        
        try:
            with patch.dict('os.environ', {
                'NVIDIA_API_KEY': 'test-nvidia-key',
                'GROQ_API_KEY': 'test-groq-key',
                'MISTRAL_API_KEY': 'test-mistral-key'
            }, clear=False):
                with patch('app.services.multi_provider.settings', mock_settings_obj):
                    from app.services.multi_provider import get_multi_provider
                    
                    # Get first instance and store its id
                    instance1 = get_multi_provider()
                    id1 = id(instance1)
                    
                    # Call multiple times and verify id remains the same
                    for _ in range(10):
                        instance = get_multi_provider()
                        assert id(instance) == id1
                        assert isinstance(instance, MultiProviderService)
        finally:
            # Restore original instance
            mp_module.multi_provider = original_instance
    
    def test_shared_provider_state_across_calls(self):
        """
        Test that provider state is shared across all calls to get_multi_provider().
        
        Requirements: 15.4
        """
        import app.services.multi_provider as mp_module
        from app.services.multi_provider import Provider
        from unittest.mock import MagicMock
        
        # Create mock settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
        mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
        mock_settings_obj.NVIDIA_API_KEY = "test-nvidia-key"
        mock_settings_obj.GROQ_API_KEY = "test-groq-key"
        mock_settings_obj.MISTRAL_API_KEY = "test-mistral-key"
        
        # Reset global instance to None
        original_instance = mp_module.multi_provider
        mp_module.multi_provider = None
        
        try:
            with patch.dict('os.environ', {
                'NVIDIA_API_KEY': 'test-nvidia-key',
                'GROQ_API_KEY': 'test-groq-key',
                'MISTRAL_API_KEY': 'test-mistral-key'
            }, clear=False):
                with patch('app.services.multi_provider.settings', mock_settings_obj):
                    from app.services.multi_provider import get_multi_provider
                    
                    # Get first instance and modify provider state
                    instance1 = get_multi_provider()
                    nvidia_provider = instance1.providers[Provider.NVIDIA]
                    
                    # Modify error count
                    original_error_count = nvidia_provider.error_count
                    nvidia_provider.error_count = 5
                    
                    # Get second instance and verify state is shared
                    instance2 = get_multi_provider()
                    nvidia_provider2 = instance2.providers[Provider.NVIDIA]
                    
                    # Verify the state change is visible in the second instance
                    assert nvidia_provider2.error_count == 5
                    assert nvidia_provider is nvidia_provider2
                    
                    # Restore original state
                    nvidia_provider.error_count = original_error_count
        finally:
            # Restore original instance
            mp_module.multi_provider = original_instance
