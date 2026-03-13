"""
Test Suite — Drug-Drug Interaction Engine (WS6)

Tests the DDIService for drug interaction checking.

Usage:
    pytest tests/test_ddi_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDDIServiceBasic:
    """Basic DDIService tests"""

    def test_ddi_service_import(self):
        """Smoke test: DDIService imports correctly"""
        from app.services.ddi_service import DDIService
        assert DDIService is not None

    def test_ddi_service_initialization(self):
        """Test DDIService initializes correctly"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        assert service is not None
        assert hasattr(service, '_cache')
        assert hasattr(service, '_rxcui_cache')
        assert service.SEVERITY_MAP is not None

    def test_singleton_available(self):
        """Test that singleton instance is available"""
        from app.services.ddi_service import ddi_service
        assert ddi_service is not None

    def test_severity_map_complete(self):
        """Test that severity map has all required levels"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        assert "major" in service.SEVERITY_MAP
        assert "moderate" in service.SEVERITY_MAP
        assert "minor" in service.SEVERITY_MAP
        assert service.SEVERITY_MAP["major"] == "Major"


class TestDrugResolution:
    """Test drug name to RxCUI resolution"""

    @pytest.mark.asyncio
    async def test_resolve_drug_mock_success(self):
        """Test drug resolution with mocked API"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "idGroup": {
                    "rxnormId": ["12345"]
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            rxcui = await service.resolve_drug("aspirin")
            
            assert rxcui == "12345"

    @pytest.mark.asyncio
    async def test_resolve_drug_cache_hit(self):
        """Test that cached drugs are returned immediately"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        service._rxcui_cache["warfarin"] = "6750"
        
        rxcui = await service.resolve_drug("warfarin")
        
        assert rxcui == "6750"

    @pytest.mark.asyncio
    async def test_resolve_drug_not_found(self):
        """Test handling of unknown drug"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "idGroup": {}
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            rxcui = await service.resolve_drug("nonexistent_drug_xyz")
            
            assert rxcui is None


class TestInteractionChecking:
    """Test drug-drug interaction checking"""

    @pytest.mark.asyncio
    async def test_check_interaction_mock_found(self):
        """Test interaction check with mocked positive result"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        # Mock drug resolution
        with patch.object(service, 'resolve_drug') as mock_resolve:
            mock_resolve.side_effect = ["12345", "6750"]
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "interactionTypeGroup": [{
                        "interactionPair": [{
                            "severity": "major",
                            "description": "Increased risk of bleeding",
                            "mechanism": "CYP2C9 inhibition"
                        }]
                    }]
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await service.check_interaction("aspirin", "warfarin")
                
                assert result is not None
                assert result["interaction_found"] is True
                assert result["severity"] == "Major"
                assert "bleeding" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_check_interaction_mock_none(self):
        """Test interaction check with no interaction"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        with patch.object(service, 'resolve_drug') as mock_resolve:
            mock_resolve.side_effect = ["11111", "22222"]
            
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "interactionTypeGroup": []
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await service.check_interaction("drug_a", "drug_b")
                
                assert result is not None
                assert result["interaction_found"] is False
                assert result["severity"] == "None"

    @pytest.mark.asyncio
    async def test_check_interaction_cache_hit(self):
        """Test that cached interactions are returned immediately"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        cached = {
            "drug_a": "aspirin",
            "drug_b": "warfarin",
            "severity": "Major",
            "interaction_found": True
        }
        service._cache["ddi:aspirin:warfarin"] = cached
        
        result = await service.check_interaction("aspirin", "warfarin")
        
        assert result == cached
        assert result["severity"] == "Major"


class TestPolypharmacy:
    """Test multi-drug interaction checking"""

    @pytest.mark.asyncio
    async def test_check_polypharmacy_basic(self):
        """Test polypharmacy check with 3 drugs"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        # Mock check_interaction to return different results
        async def mock_check(drug_a, drug_b):
            if "warfarin" in drug_a.lower() and "aspirin" in drug_b.lower():
                return {"severity": "Major", "pair": f"{drug_a} + {drug_b}"}
            return {"severity": "None", "pair": f"{drug_a} + {drug_b}"}
        
        with patch.object(service, 'check_interaction', side_effect=mock_check):
            drugs = ["warfarin", "aspirin", "omeprazole"]
            interactions = await service.check_polypharmacy(drugs)
            
            # Should check all 3 pairs
            assert len(interactions) == 3
            # Major should be first
            assert interactions[0]["severity"] == "Major"

    @pytest.mark.asyncio
    async def test_check_polypharmacy_two_drugs(self):
        """Test polypharmacy with only 2 drugs"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        with patch.object(service, 'check_interaction') as mock_check:
            mock_check.return_value = {"severity": "Moderate"}
            
            drugs = ["drug_a", "drug_b"]
            interactions = await service.check_polypharmacy(drugs)
            
            assert len(interactions) == 1

    @pytest.mark.asyncio
    async def test_check_polypharmacy_single_drug(self):
        """Test polypharmacy with 1 drug (should return empty)"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        drugs = ["single_drug"]
        interactions = await service.check_polypharmacy(drugs)
        
        assert interactions == []


class TestFormatting:
    """Test result formatting"""

    def test_format_for_display_with_interactions(self):
        """Test formatting interactions for display"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        interactions = [
            {
                "severity": "Major",
                "pair": "warfarin + aspirin",
                "description": "Increased bleeding risk",
                "clinical_significance": "Avoid combination"
            },
            {
                "severity": "Moderate",
                "pair": "omeprazole + clopidogrel",
                "description": "Reduced efficacy",
                "clinical_significance": "Monitor"
            }
        ]
        
        formatted = service.format_for_display(interactions)
        
        assert "Drug Interaction Check" in formatted
        assert "🔴" in formatted  # Major emoji
        assert "🟡" in formatted  # Moderate emoji
        assert "warfarin + aspirin" in formatted

    def test_format_for_display_no_interactions(self):
        """Test formatting with no interactions"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        formatted = service.format_for_display([])
        
        assert "No significant interactions found" in formatted

    def test_format_for_display_disclaimer(self):
        """Test that disclaimer is included"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        interactions = [{"severity": "Minor", "pair": "a + b"}]
        formatted = service.format_for_display(interactions)
        
        assert "Disclaimer" in formatted
        assert "educational purposes" in formatted


class TestClinicalSignificance:
    """Test clinical significance mapping"""

    def test_get_clinical_significance_major(self):
        """Test clinical significance for Major severity"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        significance = service._get_clinical_significance("Major")
        
        assert "Avoid" in significance or "alternative" in significance.lower()

    def test_get_clinical_significance_moderate(self):
        """Test clinical significance for Moderate severity"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        significance = service._get_clinical_significance("Moderate")
        
        assert "Monitor" in significance

    def test_get_clinical_significance_minor(self):
        """Test clinical significance for Minor severity"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        significance = service._get_clinical_significance("Minor")
        
        assert "Minimal" in significance or "Routine" in significance


class TestDDIIntegration:
    """Integration tests with real RxNav API"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_drug_resolution(self):
        """
        Test drug resolution with real RxNorm API.
        
        Run with: pytest tests/test_ddi_service.py -v -m integration
        """
        from app.services.ddi_service import ddi_service
        
        # Well-known drug
        rxcui = await ddi_service.resolve_drug("aspirin")
        
        assert rxcui is not None
        assert rxcui.isdigit()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_interaction_check(self):
        """
        Test interaction check with real RxNav API.
        """
        from app.services.ddi_service import ddi_service
        
        # Warfarin + Aspirin is a known major interaction
        result = await ddi_service.check_interaction("warfarin", "aspirin")
        
        if result:
            assert "drug_a" in result
            assert "drug_b" in result
            assert "severity" in result


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_interaction_with_special_characters(self):
        """Test drug names with special characters"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        # Should not crash with special chars
        with patch.object(service, 'resolve_drug') as mock_resolve:
            mock_resolve.return_value = None  # Simulate not found
            
            result = await service.check_interaction("drug-123", "drug_456")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_interaction_api_error(self):
        """Test handling of API errors"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        with patch.object(service, 'resolve_drug') as mock_resolve:
            mock_resolve.side_effect = Exception("API error")
            
            result = await service.check_interaction("drug_a", "drug_b")
            
            assert result is None

    def test_evidence_estimation(self):
        """Test evidence level estimation"""
        from app.services.ddi_service import DDIService
        
        service = DDIService()
        
        # High evidence keywords
        desc_high = "Well-established interaction confirmed by multiple studies"
        assert service._estimate_evidence(desc_high) == "★★★ (High)"
        
        # Moderate evidence
        desc_mod = "Likely interaction suggested by case reports"
        assert service._estimate_evidence(desc_mod) == "★★☆ (Moderate)"
        
        # Low evidence
        desc_low = "Possible interaction"
        assert service._estimate_evidence(desc_low) == "★☆☆ (Low)"
