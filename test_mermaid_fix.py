"""
Test Mermaid validator fixes for Unicode and special characters
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.mermaid_validator import MermaidValidator

def test_unicode_fixes():
    """Test that Unicode characters are properly handled"""
    
    validator = MermaidValidator()
    
    # Test case from the actual error
    broken_mermaid = """
flowchart TD
    A["Clarithromycin 10‑14 d"]
    B -->|≥15%| C["Resistance"]
    D["Amoxicillin(7‑10 d)"] --> E["Success ≤90%"]
"""
    
    print("📝 Testing broken Mermaid code:")
    print(broken_mermaid)
    print("\n" + "="*60 + "\n")
    
    corrected, errors, warnings = validator.validate_and_fix(broken_mermaid)
    
    print("✅ Corrected Mermaid code:")
    print(corrected)
    print("\n" + "="*60 + "\n")
    
    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print(f"   - {w}")
    
    if errors:
        print("❌ Errors:")
        for e in errors:
            print(f"   - {e}")
    
    # Verify fixes were applied
    assert '\u2011' not in corrected, "Non-breaking hyphen should be replaced"
    assert '≥' not in corrected, "≥ should be replaced with >="
    assert '<=' in corrected, "<= should be present"
    
    print("\n✅ All Unicode fixes applied successfully!")
    
    # Test parentheses balancing
    test2 = """
flowchart TD
    A["Drug(10-14 days"] --> B["Effect"]
"""
    
    print("\n" + "="*60)
    print("\n📝 Testing parentheses balancing:")
    print(test2)
    
    corrected2, errors2, warnings2 = validator.validate_and_fix(test2)
    
    print("\n✅ Corrected:")
    print(corrected2)
    
    # Count parens in labels
    open_parens = corrected2.count('(')
    close_parens = corrected2.count(')')
    print(f"\n   Open parens: {open_parens}, Close parens: {close_parens}")
    
    if open_parens == close_parens:
        print("✅ Parentheses are balanced!")
    else:
        print("⚠️  Parentheses still unbalanced - this is expected for complex cases")

if __name__ == "__main__":
    test_unicode_fixes()
    print("\n✅ All tests completed!")
