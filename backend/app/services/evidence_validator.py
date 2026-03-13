"""
Evidence Validator Service
Validates and scores the quality of research evidence.
"""

import logging
import re
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class EvidenceValidator:
    """
    Evaluates research findings for quality indicators such as Study Type,
    Sample Size, and P-Values.
    """
    
    def __init__(self):
        pass
        
    def evaluate_finding(self, text: str) -> Dict[str, Any]:
        """
        Evaluate a text block (abstract or full text) for evidence quality.
        
        Args:
            text: The text to evaluate
            
        Returns:
            Dictionary containing evaluation metrics and a quality score
        """
        if not text:
            return self._empty_evaluation()
            
        text_lower = text.lower()
        
        # 1. Determine Study Type Hierarchy (highest score first)
        study_type, type_score = self._determine_study_type(text_lower)
        
        # 2. Extract Sample Size (n)
        sample_size, n_score = self._extract_sample_size(text_lower)
        
        # 3. Detect P-Values / Statistical Significance
        has_significance, p_score = self._detect_significance(text_lower)
        
        # 4. Calculate total quality score (0-10 scale)
        # Type: up to 5 points
        # Sample size: up to 3 points
        # Significance: up to 2 points
        total_score = min(10, type_score + n_score + p_score)
        
        return {
            "study_type": study_type,
            "sample_size": sample_size,
            "has_significance": has_significance,
            "quality_score": total_score,
            "is_high_quality": total_score >= 6
        }
        
    def _empty_evaluation(self) -> Dict[str, Any]:
        """Return default evaluation for empty text"""
        return {
            "study_type": "Unknown",
            "sample_size": None,
            "has_significance": False,
            "quality_score": 0,
            "is_high_quality": False
        }
        
    def _determine_study_type(self, text: str) -> Tuple[str, int]:
        """Determine highest-level study type and return (type_name, score)"""
        # Hierarchy from highest to lowest quality
        if "meta-analysis" in text or "meta analysis" in text:
            return "Meta-Analysis", 5
        if "systematic review" in text:
            return "Systematic Review", 5
        if "randomized controlled" in text or " randomized " in text or " rct" in text or " rcts" in text:
            return "Randomized Controlled Trial", 4
        if "cohort" in text or "prospective" in text or "retrospective" in text:
            return "Observational Study", 3
        if "case-control" in text or "case control" in text:
            return "Case-Control Study", 2
        if "in vivo" in text or "animal model" in text or "mice" in text or "rats" in text:
            return "In Vivo (Animal)", 1
        if "in vitro" in text or "cell culture" in text or "cell line" in text:
            return "In Vitro (Cellular)", 1
        if "review" in text: # General review (not systematic)
            return "Literature Review", 2
            
        return "Unknown", 0
        
    def _extract_sample_size(self, text: str) -> Tuple[Optional[int], int]:
        """
        Attempt to extract sample size (n=XXX) and return (size, score).
        Score: >1000 = 3, >100 = 2, >10 = 1, else 0
        """
        # Look for patterns like n=50, n = 50, n= 50, mostly in contexts
        # Also look for e.g. "50 patients", "50 subjects", etc.
        
        # Pattern 1: n = 123
        n_match = re.search(r'\bn\s*=\s*(\d+[,.]?\d*)\b', text)
        if n_match:
            try:
                # Remove commas
                val_str = n_match.group(1).replace(',', '').replace('.', '')
                n = int(val_str)
                return n, self._score_sample_size(n)
            except ValueError:
                pass
                
        # Pattern 2: 123 patients/subjects/cases
        p_match = re.search(r'\b(\d+[,.]?\d*)\s+(patients|subjects|cases|participants|individuals)\b', text)
        if p_match:
            try:
                val_str = p_match.group(1).replace(',', '').replace('.', '')
                n = int(val_str)
                return n, self._score_sample_size(n)
            except ValueError:
                pass
                
        return None, 0
        
    def _score_sample_size(self, n: int) -> int:
        if n > 1000: return 3
        if n > 100: return 2
        if n > 10: return 1
        return 0
        
    def _detect_significance(self, text: str) -> Tuple[bool, int]:
        """Detect if statistically significant results are reported"""
        # Look for p-value formats: p<0.05, p=0.01, P < .001
        has_p_value = bool(re.search(r'\bp\s*[<=]\s*0\.\d+', text)) or bool(re.search(r'\bp\s*[<=]\s*\.\d+', text))
        
        # Look for textual indicators
        has_text_sig = "statistically significant" in text or "significant difference" in text
        
        # Check for negations
        negations = ["no significant", "not significant", "no statistically significant"]
        if any(neg in text for neg in negations):
            has_text_sig = False
            
        is_significant = has_p_value or has_text_sig
        return is_significant, 2 if is_significant else 0
