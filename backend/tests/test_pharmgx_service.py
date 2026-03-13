"""
Test Suite — PharmGx Reporter (WS8)

Tests the PharmGxService for pharmacogenomic report generation.

Usage:
    pytest tests/test_pharmgx_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPharmGxServiceBasic:
    """Basic PharmGxService tests"""

    def test_pharmgx_service_import(self):
        """Smoke test: PharmGxService imports correctly"""
        from app.services.pharmgx_service import PharmGxService
        assert PharmGxService is not None

    def test_pharmgx_service_initialization(self):
        """Test PharmGxService initializes correctly"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        assert service is not None
        assert hasattr(service, '_cache')
        assert len(service.PGX_GENES) == 12  # 12 genes

    def test_singleton_available(self):
        """Test that singleton instance is available"""
        from app.services.pharmgx_service import pharmgx_service
        assert pharmgx_service is not None

    def test_gene_database_complete(self):
        """Test that gene database has all required genes"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        required_genes = ["CYP2D6", "CYP2C19", "CYP2C9", "VKORC1", "SLCO1B1", "TPMT"]
        
        for gene in required_genes:
            assert gene in service.PGX_GENES

    def test_drug_database_complete(self):
        """Test that drug database has key medications"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        required_drugs = ["warfarin", "clopidogrel", "codeine", "simvastatin"]
        
        for drug in required_drugs:
            assert drug in service.DRUG_GUIDANCE


class TestFileParsing:
    """Test genetic file parsing"""

    def test_parse_23andme_format(self):
        """Test parsing 23andMe format"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        # Mock 23andMe file content
        file_text = """# 23andMe Raw Data
# rsid	chromosome	position	genotype
rs1065852	22	42522618	CC
rs4244285	10	94762534	AG
rs1799853	10	96702047	CT
"""
        
        genotypes = service._parse_genetic_file(file_text, "23andme_raw.txt")
        
        assert "rs1065852" in genotypes
        assert genotypes["rs1065852"] == "CC"

    def test_parse_ancestry_format(self):
        """Test parsing AncestryDNA format"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        # Mock AncestryDNA file content
        file_text = """AncestryDNA Raw Data
rsid,genotype
rs1065852,CC
rs4244285,AG
"""
        
        genotypes = service._parse_genetic_file(file_text, "ancestrydna_raw.txt")
        
        # Should handle both formats
        assert isinstance(genotypes, dict)

    def test_parse_filters_to_relevant_snps(self):
        """Test that only relevant SNPs are stored"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        file_text = """# Data
rs1065852	CC
rs99999999	AA
rs4244285	AG
"""
        
        genotypes = service._parse_genetic_file(file_text, "test.txt")
        
        # Only PGx SNPs should be included
        assert "rs1065852" in genotypes
        assert "rs99999999" not in genotypes  # Not in database


class TestGeneAnalysis:
    """Test gene analysis functionality"""

    def test_analyze_gene_cyp2d6(self):
        """Test CYP2D6 analysis"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        genotypes = {
            "rs1065852": "CC",  # Homozygous variant
            "rs3892097": "GG",
        }
        
        result = service._analyze_gene(
            "CYP2D6",
            service.PGX_GENES["CYP2D6"],
            genotypes
        )
        
        assert result is not None
        assert result["gene"] == "CYP2D6"
        assert "phenotype" in result

    def test_analyze_gene_no_data(self):
        """Test gene analysis with no genotype data"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        result = service._analyze_gene(
            "CYP2D6",
            service.PGX_GENES["CYP2D6"],
            {}  # No genotypes
        )
        
        assert result is None

    def test_phenotype_determination(self):
        """Test phenotype determination logic"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        # Test various allele combinations
        gene_data = service.PGX_GENES["CYP2C19"]
        phenotype_map = gene_data["phenotype_map"]
        
        # Should have phenotype mappings
        assert "no_function/no_function" in phenotype_map
        assert phenotype_map["no_function/no_function"] == "Poor Metabolizer"


class TestDrugRecommendations:
    """Test drug recommendation generation"""

    def test_generate_recommendations_basic(self):
        """Test basic drug recommendation generation"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        gene_results = [
            {
                "gene": "CYP2C19",
                "phenotype": "Poor Metabolizer",
                "drug_impact": ["clopidogrel", "omeprazole"]
            }
        ]
        
        recommendations = service._generate_drug_recommendations(gene_results)
        
        assert len(recommendations) > 0
        assert any(r["drug"] == "clopidogrel" for r in recommendations)

    def test_get_drug_guidance_warfarin(self):
        """Test warfarin guidance retrieval"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        phenotype_by_gene = {
            "CYP2C9": "Poor Metabolizer",
            "VKORC1": "Low dose required"
        }
        
        guidance = service._get_drug_guidance(
            "warfarin",
            phenotype_by_gene,
            ["CYP2C9", "VKORC1"]
        )
        
        assert "Reduce" in guidance or "dose" in guidance.lower()

    def test_get_drug_guidance_codeine_ultra_rapid(self):
        """Test codeine guidance for ultra-rapid metabolizers"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        phenotype_by_gene = {
            "CYP2D6": "Ultra-rapid Metabolizer"
        }
        
        guidance = service._get_drug_guidance(
            "codeine",
            phenotype_by_gene,
            ["CYP2D6"]
        )
        
        assert "CONTRAINDICATED" in guidance or "Avoid" in guidance


class TestReportGeneration:
    """Test full report generation"""

    @pytest.mark.asyncio
    async def test_generate_report_mock_file(self):
        """Test report generation with mock file"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        # Mock file content with known genotypes
        file_content = b"""# 23andMe Raw Data
# rsid	chromosome	position	genotype
rs1065852	22	42522618	CC
rs4244285	10	94762534	AG
rs1799853	10	96702047	CT
rs9923231	16	31104684	AG
"""
        
        report = await service.generate_report(file_content, "test_23andme.txt")
        
        assert report["success"] is True
        assert "patient_id" in report
        assert "gene_results" in report
        assert "drug_recommendations" in report

    @pytest.mark.asyncio
    async def test_generate_report_invalid_file(self):
        """Test report generation with invalid file"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        # Empty/invalid file
        file_content = b"This is not genetic data"
        
        report = await service.generate_report(file_content, "invalid.txt")
        
        assert report["success"] is False
        assert "error" in report

    @pytest.mark.asyncio
    async def test_single_drug_lookup(self):
        """Test single drug lookup"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        file_content = b"""# 23andMe Raw Data
rs1065852	CC
rs4244285	AG
"""
        
        result = await service.single_drug_lookup(
            file_content=file_content,
            filename="test.txt",
            drug_name="codeine"
        )
        
        assert result["success"] is True
        assert "drug" in result or "message" in result


class TestFormatting:
    """Test report formatting"""

    def test_format_for_display_success(self):
        """Test formatting successful report"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        report = {
            "success": True,
            "patient_id": "PGx-123456",
            "genes_analyzed": 4,
            "gene_results": [
                {"gene": "CYP2D6", "phenotype": "Poor Metabolizer"}
            ],
            "drug_recommendations": [
                {"drug": "codeine", "guidance": "CONTRAINDICATED"}
            ],
            "summary": {
                "high_risk_drugs": 1,
                "poor_metabolizer_count": 1
            }
        }
        
        formatted = service.format_for_display(report)
        
        assert "Pharmacogenomic Report" in formatted
        assert "CYP2D6" in formatted
        assert "CONTRAINDICATED" in formatted
        assert "Disclaimer" in formatted

    def test_format_for_display_failure(self):
        """Test formatting failed report"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        report = {
            "success": False,
            "error": "Invalid file format"
        }
        
        formatted = service.format_for_display(report)
        
        assert "Could not analyze" in formatted


class TestPharmGxIntegration:
    """Integration tests with real data patterns"""

    @pytest.mark.asyncio
    async def test_real_23andme_pattern(self):
        """Test with realistic 23andMe data pattern"""
        from app.services.pharmgx_service import pharmgx_service
        
        # Realistic 23andMe file pattern
        file_content = b"""# 23andMe Raw Data
# Generated on 2024-01-15
# rsid	chromosome	position	genotype
rs1065852	22	42522618	CC
rs3892097	22	42524382	GA
rs1135840	22	42526618	GC
rs4244285	10	94762534	AG
rs4986893	10	94770653	GG
rs12248560	10	94781859	CC
rs1799853	10	96702047	CT
rs1057910	10	96741053	AA
rs9923231	16	31104684	AG
rs4149056	12	21178793	TC
"""
        
        report = await pharmgx_service.generate_report(
            file_content, 
            "realistic_23andme.txt"
        )
        
        assert report["success"] is True
        assert report["genes_analyzed"] > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_heterozygous_genotype_handling(self):
        """Test handling of heterozygous genotypes"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        genotypes = {
            "rs1065852": "CT",  # Heterozygous
        }
        
        result = service._analyze_gene(
            "CYP2D6",
            service.PGX_GENES["CYP2D6"],
            genotypes
        )
        
        # Should handle heterozygous without crashing
        assert result is None or "phenotype" in result

    def test_unknown_snp_handling(self):
        """Test handling of SNPs not in database"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        genotypes = {
            "rs99999999": "AA",  # Not in database
        }
        
        result = service._analyze_gene(
            "CYP2D6",
            service.PGX_GENES["CYP2D6"],
            genotypes
        )
        
        # Should return None (no data for this gene)
        assert result is None

    def test_empty_drug_recommendations(self):
        """Test empty drug recommendations"""
        from app.services.pharmgx_service import PharmGxService
        
        service = PharmGxService()
        
        recommendations = service._generate_drug_recommendations([])
        
        assert recommendations == []
