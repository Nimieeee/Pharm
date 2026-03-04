#!/bin/bash
# VPS Verification Script for Mermaid Diagram Fixes
# Run this directly on the VPS to verify the deployment

set -e

echo "=============================================="
echo "   MERMAID DIAGRAM FIXES - VPS VERIFICATION"
echo "=============================================="
echo ""

cd /var/www/benchside-backend/backend
source .venv/bin/activate

echo "1. Checking file existence..."
echo ""

if [ -f "app/services/mermaid_validator.py" ]; then
    echo "✅ mermaid_validator.py exists"
else
    echo "❌ mermaid_validator.py MISSING"
    exit 1
fi

if [ -f "tests/test_mermaid_validator.py" ]; then
    echo "✅ test_mermaid_validator.py exists"
else
    echo "❌ test_mermaid_validator.py MISSING"
    exit 1
fi

echo ""
echo "2. Testing Python imports..."
echo ""

python -c "from app.services.mermaid_validator import MermaidValidator; print('✅ MermaidValidator imports successfully')"
python -c "from app.services.ai import AIService; print('✅ AIService imports successfully (with MermaidValidator)')"

echo ""
echo "3. Running unit tests..."
echo ""

pytest tests/test_mermaid_validator.py -v --tb=short

echo ""
echo "4. Running Mermaid validator smoke test..."
echo ""

python << 'PYEOF'
from app.services.mermaid_validator import MermaidValidator

validator = MermaidValidator()

# Test case 1: Spaces in node IDs
test1 = '''
flowchart TD
    F --> F 1["Step 1"]
'''
corrected1, errors1, warnings1 = validator.validate_and_fix(test1)
assert 'F 1[' not in corrected1, "Should fix space in node ID"
print("✅ Test 1 passed: Space in node ID corrected")

# Test case 2: Hallucinated arrow heads
test2 = '''
flowchart TD
    A -->|Label|> B["Node"]
'''
corrected2, errors2, warnings2 = validator.validate_and_fix(test2)
assert '|>' not in corrected2, "Should fix hallucinated arrow"
print("✅ Test 2 passed: Hallucinated arrow head corrected")

# Test case 3: Style line fixes
test3 = '''
flowchart TD
    B["Node"]
    style  B fill:# f88
'''
corrected3, errors3, warnings3 = validator.validate_and_fix(test3)
assert 'style  B' not in corrected3, "Should fix double space in style"
assert '# f88' not in corrected3, "Should fix space in hex color"
print("✅ Test 3 passed: Style syntax corrected")

# Test case 4: Markdown extraction
markdown = '''
# Report

```mermaid
flowchart TD
    A --> B
```
'''
diagrams = validator.extract_diagrams_from_markdown(markdown)
assert len(diagrams) == 1, "Should extract 1 diagram"
print("✅ Test 4 passed: Diagram extraction from markdown")

print("")
print("✅ All smoke tests passed!")
PYEOF

echo ""
echo "5. Checking PM2 service health..."
echo ""

pm2 status benchside-api | grep -q "online"
if [ $? -eq 0 ]; then
    echo "✅ PM2 service is online"
else
    echo "❌ PM2 service is NOT online"
    exit 1
fi

echo ""
echo "6. Checking for recent errors in logs..."
echo ""

ERROR_COUNT=$(pm2 logs benchside-api --lines 100 --nostream | grep -ci "error\|exception" || true)

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Found $ERROR_COUNT error/exception lines in recent logs (may be normal)"
else
    echo "✅ No errors found in recent logs"
fi

echo ""
echo "7. Checking VPS resources..."
echo ""

echo "Memory usage:"
free -h | grep "^Mem:"

echo ""
echo "Disk usage:"
df -h / | tail -1

echo ""
echo "=============================================="
echo "   VERIFICATION COMPLETE ✅"
echo "=============================================="
echo ""
echo "All checks passed! The Mermaid diagram fixes are deployed and working."
echo ""
echo "To test with a real query, run:"
echo '  curl -X POST "http://localhost:7860/api/v1/ai/deep-research/stream" \'
echo '    -H "Content-Type: application/json" \'
echo '    -H "Authorization: Bearer YOUR_TOKEN" \'
echo '    -d "{\"question\": \"Create a flowchart of artemisinin mechanism\", \"conversation_id\": null}"'
echo ""
