"""
Tests for Evidence Validator Service
"""

import pytest
from app.services.evidence_validator import EvidenceValidator


class TestEvidenceValidator:
    """Test functionality of the EvidenceValidator service"""
    
    def setup_method(self):
        self.validator = EvidenceValidator()
        
    def test_evaluate_empty_text(self):
        """Test handling of empty or None text"""
        result = self.validator.evaluate_finding("")
        
        assert result["study_type"] == "Unknown"
        assert result["sample_size"] is None
        assert result["has_significance"] is False
        assert result["quality_score"] == 0
        assert result["is_high_quality"] is False
        
    def test_meta_analysis_scoring(self):
        """Test detection and scoring of Meta-Analysis"""
        text = "This systematic review and meta-analysis included 5,234 patients. We found a statistically significant reduction in mortality (p<0.01)."
        result = self.validator.evaluate_finding(text)
        
        assert result["study_type"] == "Meta-Analysis"
        assert result["sample_size"] == 5234
        assert result["has_significance"] is True
        # Type(5) + N(3) + Sig(2) = 10
        assert result["quality_score"] == 10
        assert result["is_high_quality"] is True
        
    def test_rct_scoring(self):
        """Test detection and scoring of RCT"""
        text = "In this randomized controlled trial of 150 participants, safety was assessed. No significant differences were found between groups."
        result = self.validator.evaluate_finding(text)
        
        assert result["study_type"] == "Randomized Controlled Trial"
        assert result["sample_size"] == 150
        assert result["has_significance"] is False
        # Type(4) + N(2) + Sig(0) = 6
        assert result["quality_score"] == 6
        assert result["is_high_quality"] is True
        
    def test_in_vitro_scoring(self):
        """Test detection of cellular studies"""
        text = "Cells were cultured in vitro. We assessed viability using MTT assay."
        result = self.validator.evaluate_finding(text)
        
        assert result["study_type"] == "In Vitro (Cellular)"
        assert result["sample_size"] is None
        assert result["has_significance"] is False
        # Type(1) + N(0) + Sig(0) = 1
        assert result["quality_score"] == 1
        assert result["is_high_quality"] is False
        
    def test_sample_size_extraction(self):
        """Test various formats of sample size extraction"""
        # n = format
        res1 = self.validator.evaluate_finding("The study included n=50 subjects.")
        assert res1["sample_size"] == 50
        
        res2 = self.validator.evaluate_finding("with n = 1,234 observed.")
        assert res2["sample_size"] == 1234
        
        # natural language format
        res3 = self.validator.evaluate_finding("We enrolled 75 patients in the clinic.")
        assert res3["sample_size"] == 75
        
        res4 = self.validator.evaluate_finding("A total of 1500 cases were analyzed.")
        assert res4["sample_size"] == 1500
        
    def test_p_value_detection(self):
        """Test various formats of statistical significance"""
        res1 = self.validator.evaluate_finding("Results: p<0.05")
        assert res1["has_significance"] is True
        
        res2 = self.validator.evaluate_finding("difference was P = 0.001.")
        assert res2["has_significance"] is True
        
        res3 = self.validator.evaluate_finding("showed a statistically significant improvement")
        assert res3["has_significance"] is True
        
        res4 = self.validator.evaluate_finding("The p value was not reported.")
        assert res4["has_significance"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
