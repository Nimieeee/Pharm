"""
Prompt Processor

Prompt complexity analysis for intelligent routing.
Part of the centralized postprocessing architecture (CLAUDE.md compliant).

Signals:
- COMPLEXITY: "review", "synthesize", "comprehensive", "compare and contrast"
- PRIVACY: "patient", "genotype", "rs", "CYP", "HLA-", "allele", "my results"
"""

import re
from typing import List, Tuple


class PromptProcessor:
    """
    Prompt complexity and privacy analysis.
    
    Features:
    - Complexity scoring (0.0-1.0)
    - Privacy signal detection
    - Token count estimation
    """
    
    COMPLEXITY_SIGNALS = [
        "review", "synthesize", "comprehensive", "compare and contrast",
        "systematic", "meta-analysis", "literature", "in-depth",
        "detailed analysis", "critical evaluation", "thorough examination",
        "extensive", "exhaustive", "multifaceted", "nuanced"
    ]
    
    PRIVACY_SIGNALS = [
        "patient", "genotype", "rs", "CYP", "HLA-", "allele",
        "my results", "my data", "confidential", "HIPAA",
        "personal", "private", "medical record", "health information"
    ]
    
    def __init__(self):
        """Initialize PromptProcessor"""
        pass
    
    def score_complexity(self, prompt: str, token_count: int = None) -> float:
        """
        Score prompt complexity from 0.0 (simple) to 1.0 (complex).
        
        Args:
            prompt: User input text
            token_count: Optional pre-computed token count
            
        Returns:
            Complexity score 0.0-1.0
        """
        if not prompt:
            return 0.0
        
        prompt_lower = prompt.lower()
        score = 0.0
        
        # Signal-based scoring (0.0-0.6)
        signals_found = 0
        for signal in self.COMPLEXITY_SIGNALS:
            if signal in prompt_lower:
                signals_found += 1
                score += 0.1
        
        # Cap signal score at 0.6
        score = min(score, 0.6)
        
        # Length-based scoring (0.0-0.4)
        if token_count is None:
            token_count = len(prompt.split())  # Rough estimate
        
        if token_count > 500:
            score += 0.4
        elif token_count > 200:
            score += 0.3
        elif token_count > 100:
            score += 0.2
        elif token_count > 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def detect_privacy(self, prompt: str) -> bool:
        """
        Detect if prompt contains sensitive/privacy data.
        
        Args:
            prompt: User input text
            
        Returns:
            True if privacy signals detected
        """
        if not prompt:
            return False
        
        prompt_lower = prompt.lower()
        
        for signal in self.PRIVACY_SIGNALS:
            if signal in prompt_lower:
                return True
        
        # Also check for rsID patterns (e.g., rs7903146)
        if re.search(r'\brs\d+\b', prompt_lower):
            return True
        
        # Check for HLA alleles (e.g., HLA-B*57:01)
        if re.search(r'HLA-[A-Z0-9*:+]+', prompt, re.IGNORECASE):
            return True
            
        # Check for CYP alleles (e.g., CYP2C19*2)
        if re.search(r'CYP[0-9]+[A-Z]+[0-9]+\*[0-9]+', prompt, re.IGNORECASE):
            return True
            
        return False
    
    def estimate_tokens(self, prompt: str) -> int:
        """
        Estimate token count for prompt.
        
        Args:
            prompt: User input text
            
        Returns:
            Estimated token count
        """
        if not prompt:
            return 0
        
        # Rough estimate: 1 token ≈ 4 characters or 0.75 words
        char_tokens = len(prompt) / 4
        word_tokens = len(prompt.split()) * 0.75
        
        return int((char_tokens + word_tokens) / 2)
    
    def analyze(self, prompt: str) -> dict:
        """
        Full prompt analysis.
        
        Args:
            prompt: User input text
            
        Returns:
            Dict with complexity, privacy, and token estimates
        """
        tokens = self.estimate_tokens(prompt)
        complexity = self.score_complexity(prompt, tokens)
        is_private = self.detect_privacy(prompt)
        
        return {
            "complexity": complexity,
            "is_private": is_private,
            "token_count": tokens,
            "signals_found": sum(1 for s in self.COMPLEXITY_SIGNALS if s in prompt.lower())
        }


# Singleton instance
prompt_processor = PromptProcessor()
