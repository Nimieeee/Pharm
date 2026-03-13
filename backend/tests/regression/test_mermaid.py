"""
Regression Test Suite - Mermaid Processing

Fast, comprehensive tests for Mermaid diagram processing.
Run time: <100ms

Usage:
    pytest tests/regression/test_mermaid.py -v
"""

import pytest
from app.services.postprocessing.mermaid_processor import MermaidProcessor, mermaid_processor


class TestMermaidProcessor:
    """Comprehensive Mermaid processing tests"""
    
    @pytest.fixture
    def processor(self):
        """Create fresh processor instance"""
        return MermaidProcessor()
    
    # =====================================================================
    # UNICODE NORMALIZATION TESTS
    # =====================================================================
    
    def test_non_breaking_hyphen(self, processor):
        """Test non-breaking hyphen → regular hyphen"""
        broken = 'flowchart TD\n    A["Drug 10‑14 days"]'  # \u2011
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '10-14' in fixed
        assert len(errors) == 0, f"Errors: {errors}"
    
    def test_greater_equal_symbol(self, processor):
        """Test ≥ symbol → >="""
        broken = 'flowchart TD\n    A -->|≥15%| B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '>=' in fixed
        assert '≥' not in fixed
        assert len(errors) == 0, f"Errors: {errors}"
    
    def test_less_equal_symbol(self, processor):
        """Test ≤ symbol → <="""
        broken = 'A -->|≤90%| B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '<=' in fixed
        assert '≤' not in fixed
    
    def test_multiplication_symbol(self, processor):
        """Test × symbol → x"""
        broken = 'A["5× daily"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '5x' in fixed
        assert '×' not in fixed
    
    def test_en_dash(self, processor):
        """Test en dash → regular hyphen"""
        broken = 'A["10–14 days"]'  # \u2013
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '10-14' in fixed
    
    def test_em_dash(self, processor):
        """Test em dash → regular hyphen"""
        broken = 'A["Start—End"]'  # \u2014
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert 'Start-End' in fixed
    
    # =====================================================================
    # ARROW PATTERN TESTS
    # =====================================================================
    
    def test_double_arrow_head(self, processor):
        """Test ->> → -->"""
        broken = 'A ->> B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '-->' in fixed
        assert '->>' not in fixed
    
    def test_double_arrow_tail(self, processor):
        """Test <<-- → <--"""
        broken = 'A <<-- B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '<--' in fixed
    
    def test_multiple_dashes(self, processor):
        """Test ---> → -->"""
        broken = 'A ---> B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '-->' in fixed
    
    def test_equals_with_space(self, processor):
        """Test = = → =="""
        broken = 'A = = B'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert '==' in fixed
    
    # =====================================================================
    # NODE ID TESTS
    # =====================================================================
    
    def test_node_id_with_hyphen(self, processor):
        """Test node ID hyphen → underscore"""
        broken = 'Node-1["Label"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert 'Node_1[' in fixed
        assert 'Node-1[' not in fixed
    
    def test_node_id_with_space(self, processor):
        """Test node ID space removal"""
        broken = 'F 1["Label"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert 'F1[' in fixed
    
    def test_node_id_with_space_before_bracket(self, processor):
        """Test space before bracket removal"""
        broken = 'AC ["Label"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert 'AC[' in fixed
    
    # =====================================================================
    # LABEL TESTS
    # =====================================================================

    def test_unquoted_labels_with_parentheses(self, processor):
        """Test unquoted labels with parentheses are quoted: B[walKR (yycFG)] → B["walKR(yycFG)"]"""
        broken = 'flowchart TD\n    B[walKR (yycFG)]'
        fixed, errors, warnings = processor.validate_and_fix(broken)

        # Should be quoted now (spaces may be normalized)
        assert 'B["' in fixed
        assert 'walKR' in fixed
        assert 'yycFG' in fixed
        assert len(errors) == 0, f"Errors: {errors}"

    def test_unquoted_labels_multiple_nodes(self, processor):
        """Test multiple unquoted labels are all quoted"""
        broken = '''flowchart TD
    A[S. aureus genes] --> B[walKR (yycFG)]
    B --> C[Resistance mechanism]'''
        fixed, errors, warnings = processor.validate_and_fix(broken)

        # All labels should be quoted
        assert 'A["' in fixed
        assert 'B["' in fixed
        assert 'C["' in fixed
        assert 'S. aureus' in fixed
        assert 'walKR' in fixed
        assert 'yycFG' in fixed
        assert 'Resistance mechanism' in fixed
        assert len(errors) == 0, f"Errors: {errors}"

    def test_already_quoted_labels_unchanged(self, processor):
        """Test already quoted labels are not double-quoted"""
        broken = 'flowchart TD\n    A["Already quoted (test)"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)

        # Should not be double-quoted
        assert 'A[["' not in fixed
        assert 'A["' in fixed
        assert 'Already quoted' in fixed
        assert len(errors) == 0

    def test_unbalanced_parentheses(self, processor):
        """Test parentheses balancing in labels"""
        broken = 'A["Drug(10-14 days"] --> B["Effect"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)

        # Count parens in labels only
        label_start = fixed.find('["')
        label_end = fixed.find('"]')
        if label_start >= 0 and label_end > label_start:
            label = fixed[label_start:label_end+2]
            assert label.count('(') == label.count(')')

    def test_backslash_escaping(self, processor):
        """Test backslash escaping in labels"""
        broken = r'A["Path\to\file"]'
        fixed, errors, warnings = processor.validate_and_fix(broken)
        assert r'\\' in fixed or '\\\\' in fixed
    
    # =====================================================================
    # FULL DIAGRAM TESTS
    # =====================================================================
    
    def test_production_diagram_1(self, processor):
        """Test real production diagram from error log"""
        broken = '''
flowchart TD
    A["Clarithromycin 10‑14 d"]
    B -->|≥15%| C["Resistance"]
    D["Amoxicillin(7‑10 d)"] --> E["Success ≤90%"]
'''
        fixed, errors, warnings = processor.validate_and_fix(broken)
        
        # Should have no errors
        assert len(errors) == 0, f"Errors: {errors}"
        
        # Should have fixes applied
        assert '10-14' in fixed  # Non-breaking hyphen fixed
        assert '>=' in fixed     # ≥ fixed
        assert '<=' in fixed     # ≤ fixed
        assert 'flowchart TD' in fixed
    
    def test_production_diagram_2(self, processor):
        """Test complex multi-node diagram"""
        broken = '''
flowchart LR
    A["Drug A (10mg)"] -->|≥50%| B["Effect B"]
    B --> C["Outcome ≥90%"]
    C -->|≤10%| D["Side Effect"]
'''
        fixed, errors, warnings = processor.validate_and_fix(broken)
        
        assert len(errors) == 0
        assert '>=' in fixed
        assert '<=' in fixed
        assert '(10mg)' in fixed  # Balanced parens
    
    def test_empty_input(self, processor):
        """Test empty input handling"""
        fixed, errors, warnings = processor.validate_and_fix("")
        assert len(errors) > 0
        assert "Empty" in errors[0]
    
    def test_none_input(self, processor):
        """Test None input handling"""
        fixed, errors, warnings = processor.validate_and_fix(None)
        assert len(errors) > 0
    
    # =====================================================================
    # MARKDOWN INTEGRATION TESTS
    # =====================================================================
    
    def test_extract_mermaid_blocks(self, processor):
        """Test extracting Mermaid blocks from markdown"""
        markdown = '''
Here's a diagram:

```mermaid
flowchart TD
    A --> B
```

Some text.
'''
        blocks = processor.extract_mermaid_blocks(markdown)
        
        assert len(blocks) == 1
        assert 'flowchart TD' in blocks[0]['original']
        assert blocks[0]['start'] > 0
        assert blocks[0]['end'] > blocks[0]['start']
    
    def test_fix_markdown_mermaid(self, processor):
        """Test fixing Mermaid in markdown"""
        markdown = '''
Diagram:

```mermaid
A ->> B
```
'''
        fixed, count = processor.fix_markdown_mermaid(markdown)
        
        assert count == 1
        assert '-->' in fixed
        assert '->>' not in fixed
    
    def test_no_mermaid_blocks(self, processor):
        """Test markdown without Mermaid blocks"""
        markdown = "Just regular text"
        fixed, count = processor.fix_markdown_mermaid(markdown)
        
        assert fixed == markdown
        assert count == 0


class TestMermaidProcessorSingleton:
    """Test the global singleton instance"""
    
    def test_singleton_available(self):
        """Test that singleton is available"""
        from app.services.postprocessing.mermaid_processor import mermaid_processor
        
        assert mermaid_processor is not None
        assert isinstance(mermaid_processor, MermaidProcessor)
    
    def test_singleton_functionality(self):
        """Test that singleton works correctly"""
        from app.services.postprocessing.mermaid_processor import mermaid_processor
        
        broken = 'flowchart TD\n    A -->|≥50%| B'
        fixed, errors, warnings = mermaid_processor.validate_and_fix(broken)
        
        assert '>=' in fixed
        assert len(errors) == 0, f"Errors: {errors}"


# =====================================================================
# PERFORMANCE TESTS
# =====================================================================

class TestPerformance:
    """Ensure tests run fast enough for regression suite"""
    
    @pytest.fixture
    def processor(self):
        """Create fresh processor for performance tests"""
        return MermaidProcessor()
    
    def test_processing_speed(self, processor):
        """Test that processing completes in <10ms"""
        import time
        
        broken = '''
flowchart TD
    A["Clarithromycin 10‑14 d"]
    B -->|≥15%| C["Resistance"]
    D["Amoxicillin(7‑10 d)"] --> E["Success ≤90%"]
'''
        start = time.perf_counter()
        processor.validate_and_fix(broken)
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 10, f"Processing took {elapsed:.2f}ms (target: <10ms)"
    
    def test_batch_processing_speed(self, processor):
        """Test batch processing of 100 diagrams in <500ms"""
        import time
        
        diagrams = [
            'flowchart TD\n    A -->|≥50%| B'
            for _ in range(100)
        ]
        
        start = time.perf_counter()
        for diagram in diagrams:
            processor.validate_and_fix(diagram)
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 500, f"Batch took {elapsed:.2f}ms (target: <500ms)"
