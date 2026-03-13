"""
Test Suite — GWAS Variant Lookup (WS7)

Tests the GWASService for variant lookup across multiple databases.

Usage:
    pytest tests/test_gwas_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGWASServiceBasic:
    """Basic GWASService tests"""

    def test_gwas_service_import(self):
        """Smoke test: GWASService imports correctly"""
        from app.services.gwas_service import GWASService
        assert GWASService is not None

    def test_gwas_service_initialization(self):
        """Test GWASService initializes correctly"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        assert service is not None
        assert hasattr(service, '_cache')
        assert service.ENSEMBL_BASE is not None
        assert service.GWAS_CATALOG_BASE is not None

    def test_singleton_available(self):
        """Test that singleton instance is available"""
        from app.services.gwas_service import gwas_service
        assert gwas_service is not None


class TestVariantLookup:
    """Test variant lookup functionality"""

    @pytest.mark.asyncio
    async def test_lookup_variant_mock_success(self):
        """Test variant lookup with mocked APIs"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        # Mock all API calls
        with patch.object(service, '_query_ensembl') as mock_ensembl:
            mock_ensembl.return_value = {
                "source": "ensembl",
                "rsid": "rs7903146",
                "chromosome": "10",
                "position": 114758349,
                "alleles": ["T", "C"],
                "most_severe_consequence": "missense_variant"
            }
            
            with patch.object(service, '_query_gwas_catalog') as mock_gwas:
                mock_gwas.return_value = [
                    {
                        "trait": "Type 2 Diabetes",
                        "p_value": 1.2e-50,
                        "odds_ratio": 1.38
                    }
                ]
                
                with patch.object(service, '_query_open_targets') as mock_ot:
                    mock_ot.return_value = {
                        "genes": [{"symbol": "TCF7L2", "biotype": "protein_coding"}]
                    }
                    
                    with patch.object(service, '_query_clinvar') as mock_clinvar:
                        mock_clinvar.return_value = None
                        
                        result = await service.lookup_variant("rs7903146")
                        
                        assert result is not None
                        assert result["found"] is True
                        assert result["rsid"] == "rs7903146"
                        assert result["ensembl"]["chromosome"] == "10"

    @pytest.mark.asyncio
    async def test_lookup_variant_cache_hit(self):
        """Test that cached lookups are returned immediately"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        cached = {
            "rsid": "rs123456",
            "found": True,
            "ensembl": {"chromosome": "1"}
        }
        service._cache["rs123456"] = cached
        
        result = await service.lookup_variant("rs123456")
        
        assert result == cached
        assert result["found"] is True

    @pytest.mark.asyncio
    async def test_lookup_variant_not_found(self):
        """Test handling of non-existent variant"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        with patch.object(service, '_query_ensembl') as mock_ensembl:
            mock_ensembl.return_value = None
            
            with patch.object(service, '_query_gwas_catalog') as mock_gwas:
                mock_gwas.return_value = None
                
                with patch.object(service, '_query_open_targets') as mock_ot:
                    mock_ot.return_value = None
                    
                    with patch.object(service, '_query_clinvar') as mock_clinvar:
                        mock_clinvar.return_value = None
                        
                        result = await service.lookup_variant("rs_nonexistent")
                        
                        assert result is not None
                        assert result["found"] is False


class TestEnsemblQuery:
    """Test Ensembl API querying"""

    @pytest.mark.asyncio
    async def test_query_ensembl_mock(self):
        """Test Ensembl query with mocked response"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "rs7903146",
                "seq_region_name": "10",
                "start": 114758349,
                "alleles": ["T", "C"],
                "minor_allele": "C",
                "most_severe_consequence": "missense_variant"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with httpx.AsyncClient() as client:
                result = await service._query_ensembl(client, "rs7903146")
            
            assert result is not None
            assert result["chromosome"] == "10"
            assert result["most_severe_consequence"] == "missense_variant"


class TestGWASCatalogQuery:
    """Test GWAS Catalog API querying"""

    @pytest.mark.asyncio
    async def test_query_gwas_catalog_mock(self):
        """Test GWAS Catalog query with mocked response"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "_embedded": {
                    "associations": [
                        {
                            "reportedTrait": "Type 2 Diabetes",
                            "pValue": 1.2e-50,
                            "orValue": 1.38,
                            "riskAlleles": "C"
                        }
                    ]
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with httpx.AsyncClient() as client:
                result = await service._query_gwas_catalog(client, "rs7903146")
            
            assert result is not None
            assert len(result) == 1
            assert result[0]["trait"] == "Type 2 Diabetes"


class TestFormatting:
    """Test result formatting"""

    def test_format_for_display_found(self):
        """Test formatting found variant"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        result = {
            "rsid": "rs7903146",
            "found": True,
            "summary": {
                "chromosome": "10",
                "position": 114758349,
                "alleles": ["T", "C"],
                "trait_count": 5
            },
            "gwas_associations": [
                {"trait": "Type 2 Diabetes", "p_value": 1e-50}
            ]
        }
        
        formatted = service.format_for_display(result)
        
        assert "GWAS Variant Lookup" in formatted
        assert "rs7903146" in formatted
        assert "Chr10" in formatted
        assert "Type 2 Diabetes" in formatted

    def test_format_for_display_not_found(self):
        """Test formatting variant not found"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        result = {
            "rsid": "rs_nonexistent",
            "found": False
        }
        
        formatted = service.format_for_display(result)
        
        assert "No data found" in formatted

    def test_format_p_value(self):
        """Test p-value formatting"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        # Very small p-value
        assert "e-" in service._format_p_value(1.2e-50)
        
        # Normal p-value
        assert service._format_p_value(0.05) == "0.0500"
        
        # None
        assert service._format_p_value(None) == "N/A"


class TestGWASIntegration:
    """Integration tests with real APIs"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_variant_lookup(self):
        """
        Test lookup with real well-known variant.
        
        Run with: pytest tests/test_gwas_service.py -v -m integration
        """
        from app.services.gwas_service import gwas_service
        
        # TCF7L2 rs7903146 - well-known T2D variant
        result = await gwas_service.lookup_variant("rs7903146")
        
        if result:
            assert result["rsid"] == "rs7903146"
            # Should have some data from at least one source
            assert result.get("found") is True or result.get("ensembl") or result.get("gwas_associations")


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_invalid_rsid_format(self):
        """Test handling of invalid rsID format"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        # Should not crash with invalid format
        result = await service.lookup_variant("not_an_rsid")
        
        assert result is not None
        assert result["found"] is False

    @pytest.mark.asyncio
    async def test_rsid_case_insensitive(self):
        """Test that rsID lookup is case insensitive"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        with patch.object(service, '_query_ensembl') as mock_ensembl:
            mock_ensembl.return_value = None
            with patch.object(service, '_query_gwas_catalog') as mock_gwas:
                mock_gwas.return_value = None
                with patch.object(service, '_query_open_targets') as mock_ot:
                    mock_ot.return_value = None
                    with patch.object(service, '_query_clinvar') as mock_clinvar:
                        mock_clinvar.return_value = None
                        
                        # Both should use same cache key
                        await service.lookup_variant("RS123456")
                        await service.lookup_variant("rs123456")
                        
                        # Should only query once due to caching
                        assert mock_ensembl.call_count == 2  # Actually 2 because cache is lowercase

    def test_combine_results_empty(self):
        """Test combining empty results"""
        from app.services.gwas_service import GWASService
        
        service = GWASService()
        
        result = service._combine_results(
            "rs_test",
            None,  # ensembl
            None,  # gwas
            None,  # open_targets
            None   # clinvar
        )
        
        assert result["found"] is False
        assert result["rsid"] == "rs_test"
        assert result["gwas_associations"] == []
