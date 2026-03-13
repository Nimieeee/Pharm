"""
Tests for Mermaid Diagram Validator Service
"""

import pytest
from app.services.mermaid_validator import MermaidValidator


class TestMermaidValidator:
    """Test Mermaid validation and auto-correction functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = MermaidValidator()
    
    def test_fix_spaces_in_node_ids(self):
        """Test auto-correction of spaces in node IDs"""
        mermaid_code = '''
flowchart TD
    F --> F 1["Step 1"]
    F1 --> F 2["Step 2"]
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert 'F 1[' not in corrected, "Space in node ID should be fixed"
        assert 'F1[' in corrected, "Node ID should be corrected"
        assert len(warnings) > 0, "Should have warnings about auto-corrections"
    
    def test_fix_spaces_before_brackets(self):
        """Test auto-correction of spaces before brackets"""
        mermaid_code = '''
flowchart TD
    AC ["Action"]
    V ("Decision")
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert 'AC [' not in corrected, "Space before bracket should be fixed"
        assert 'AC[' in corrected or 'AC("Decision")' in corrected, "Node should be corrected"
    
    def test_fix_hallucinated_arrow_heads(self):
        """Test auto-correction of hallucinated arrow heads"""
        mermaid_code = '''
flowchart TD
    A -->|Label|> B["Node"]
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert '|>' not in corrected, "Hallucinated arrow head should be fixed"
        assert '| B[' in corrected, "Arrow should be corrected"
    
    def test_fix_style_spaces(self):
        """Test auto-correction of style line spaces"""
        mermaid_code = '''
flowchart TD
    B["Node"]
    style  B fill:# f88, stroke:#333
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert 'style  B' not in corrected, "Double space after style should be fixed"
        assert '# f88' not in corrected, "Space in hex color should be fixed"
    
    def test_fix_node_id_hyphens(self):
        """Test auto-correction of hyphens in node IDs"""
        mermaid_code = '''
flowchart TD
    Node-1["Label 1"]
    Node-2["Label 2"]
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert 'Node-1[' not in corrected, "Hyphen in node ID should be fixed"
        assert 'Node_1[' in corrected, "Node ID should use underscore"
    
    def test_validate_missing_graph_decl(self):
        """Test validation catches missing graph declaration"""
        mermaid_code = '''
A["Node"] --> B["Node"]
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert len(errors) > 0, "Should detect missing graph declaration"
        assert "Missing graph/flowchart declaration" in errors
    
    def test_validate_unclosed_quotes(self):
        """Test validation catches unclosed quotes"""
        mermaid_code = '''
flowchart TD
    A["Unclosed quote
    B["Closed quote"]
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert len(errors) > 0, "Should detect unclosed quote"
        assert "Unclosed quote" in errors[0]
    
    def test_extract_diagrams_from_markdown(self):
        """Test extraction of Mermaid diagrams from markdown"""
        markdown = '''
# Report

Some text here.

```mermaid
flowchart TD
    A --> B
```

More text.

```mermaid
graph LR
    C --> D
```
'''
        diagrams = self.validator.extract_diagrams_from_markdown(markdown)
        
        assert len(diagrams) == 2, "Should extract 2 diagrams"
        assert 'flowchart TD' in diagrams[0]
        assert 'graph LR' in diagrams[1]
    
    def test_validate_markdown_with_diagrams(self):
        """Test validation and correction of diagrams in markdown"""
        markdown = '''
# Report

```mermaid
flowchart TD
    F --> F 1["Step"]
```
'''
        corrected, results = self.validator.validate_markdown(markdown)
        
        assert len(results) == 1, "Should have 1 diagram result"
        assert 'F 1[' not in corrected, "Diagram should be corrected in markdown"
    
    def test_valid_mermaid_passes(self):
        """Test that valid Mermaid code passes validation"""
        mermaid_code = '''
flowchart TD
    A["Start"] --> B["End"]
    style A fill:#f88,stroke:#333
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        assert len(errors) == 0, f"Valid code should have no errors, got: {errors}"
    
    def test_complex_flowchart(self):
        """Test correction of complex flowchart with multiple errors"""
        mermaid_code = '''
flowchart TD
    Start --> Step 1["First Step"]
    Step 1 -->|Yes|> Decision{"Check?"}
    Decision -->|No|> End["Finish"]
    style  Step 1 fill:# f88, stroke:# 333
'''
        corrected, errors, warnings = self.validator.validate_and_fix(mermaid_code)
        
        # Should fix multiple issues
        assert 'Step 1[' not in corrected, "Space in node ID should be fixed"
        assert '|>' not in corrected, "Hallucinated arrow should be fixed"
        assert 'style  Step' not in corrected, "Double space in style should be fixed"
        assert '# f88' not in corrected, "Space in hex color should be fixed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
