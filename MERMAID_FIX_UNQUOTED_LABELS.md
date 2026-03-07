# Mermaid Parenthesis Syntax Fix

**Date:** 2026-03-07  
**Status:** ✅ FIXED - Deployed to VPS

---

## 🔍 Root Cause (Following CLAUDE.md CoT Retrieval)

**Symptom:** Mermaid diagrams fail to render with parse error:
```
Expecting 'SQE', 'TAGEND' got 'PE'
```

**Root Cause:** Unquoted node labels with parentheses break Mermaid parser

**Data Flow:**
```
1. AI generates: B[walKR (yycFG)]
2. Mermaid parser sees: ( as reserved token
3. Parser expects: quoted string or identifier
4. Parse error thrown: "Expecting 'SQE', 'TAGEND' got 'PE'"
5. Frontend can't render diagram ❌
```

**Why mermaid_processor Didn't Catch It:**
- `_escape_labels()` only matches ALREADY quoted labels
- Regex: `r'([A-Za-z0-9_]+\s*\[)"([^"]*?)"(\])'`
- Unquoted labels like `B[walKR (yycFG)]` completely ignored ❌

---

## ✅ Fix Implemented

### Added _quote_unquoted_labels() Method

**File:** `backend/app/services/postprocessing/mermaid_processor.py`

```python
def _quote_unquoted_labels(self, line: str) -> str:
    """
    Quote unquoted node labels to prevent Mermaid parse errors.
    
    Fixes: B[walKR (yycFG)] → B["walKR (yycFG)"]
    
    This MUST run before _escape_labels to ensure all labels are quoted.
    """
    def replacer(match):
        prefix = match.group(1)
        bracket_open = match.group(2)
        content = match.group(3)
        bracket_close = match.group(4)
        
        # Already quoted - leave as is
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            return match.group(0)
        
        # Remove existing single quotes but preserve content
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        
        return f'{prefix}{bracket_open}"{content}"{bracket_close}'
    
    # Split by arrows to avoid matching arrow syntax
    parts = re.split(r'(-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)', line)
    fixed_parts = []
    
    for part in parts:
        # Skip arrow tokens
        if part in ['-->', '--', '<-->', '<--', '.->', '-.->', '==>', '==', '..>', '..']:
            fixed_parts.append(part)
        # Process node declarations with brackets/parentheses/braces
        elif re.search(r'[\[\(\{].*?[\]\)\}]', part):
            # Match: NodeID[content] or NodeID(content) or NodeID{content}
            fixed_part = re.sub(
                r'([A-Za-z0-9_-]+)\s*([\[\(\{])(.*?)([\]\)\}])\s*$',
                replacer,
                part
            )
            fixed_parts.append(fixed_part)
        else:
            fixed_parts.append(part)
    
    return ''.join(fixed_parts)
```

### Integration in _fix_structure()

```python
def _fix_structure(self, text: str, warnings: List[str]) -> str:
    """Apply structural fixes to Mermaid code"""
    # ... other fixes ...
    
    # Fix 5: Quote unquoted labels (MUST run before _escape_labels)
    line = self._quote_unquoted_labels(line)
    
    # Fix 6: Label special character escaping
    line = self._escape_labels(line)
```

---

## 🧪 Test Coverage

### New Tests Added

**File:** `backend/tests/regression/test_mermaid.py`

```python
def test_unquoted_labels_with_parentheses(self, processor):
    """Test unquoted labels with parentheses are quoted"""
    broken = 'flowchart TD\n    B[walKR (yycFG)]'
    fixed, errors, warnings = processor.validate_and_fix(broken)
    
    # Should be quoted now
    assert 'B["' in fixed
    assert 'walKR' in fixed
    assert 'yycFG' in fixed
    assert len(errors) == 0

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

def test_already_quoted_labels_unchanged(self, processor):
    """Test already quoted labels are not double-quoted"""
    broken = 'flowchart TD\n    A["Already quoted (test)"]'
    fixed, errors, warnings = processor.validate_and_fix(broken)
    
    # Should not be double-quoted
    assert 'A[["' not in fixed
    assert 'A["' in fixed
```

### Test Results

```
============================== 29 passed in 0.17s ==============================
```

---

## 📊 Impact

### Before Fix
```
AI generates: B[walKR (yycFG)]
Mermaid parser: Parse Error ❌
Frontend: Diagram doesn't render ❌
User: Sees broken diagram ❌
```

### After Fix
```
AI generates: B[walKR (yycFG)]
mermaid_processor: B["walKR (yycFG)"] ✅
Mermaid parser: Valid syntax ✅
Frontend: Diagram renders correctly ✅
User: Sees proper diagram ✅
```

---

## 🚀 Deployment

**Backend:**
- ✅ Deployed to VPS (15.237.208.231)
- ✅ PM2 service restarted
- ✅ 29/29 regression tests passing

**Frontend:**
- ✅ No changes needed (backend auto-fixes)

---

## 🎯 CLAUDE.md Compliance

### ✅ CoT Retrieval Mandate
- Ran `cot_retriever.py` for "mermaid diagram render error Expecting 'SQE', 'TAGEND' got 'PE'"
- Retrieved pattern: "parentheses in labels treated as broken syntax unless quoted"
- Applied pattern to fix

### ✅ Iron Law of Debugging
- Root cause identified BEFORE fix (unquoted labels ignored by processor)
- Failure modes enumerated (double-quoting, arrow mutilation, ReDoS)
- Single targeted fix implemented

### ✅ Failure Mode Analysis
1. **Double-Quoting Corruptions** - Fixed: Check if already quoted
2. **Arrow Mutilation** - Fixed: Split by arrows, skip arrow tokens
3. **Regex Timeout (ReDoS)** - Fixed: Non-greedy, bounded patterns

### ✅ Four Phases
1. **Root Cause:** Unquoted labels ignored ✅
2. **Pattern Analysis:** CoT retrieval confirmed pattern ✅
3. **Failure Mode Analysis:** 3 failure modes identified ✅
4. **Implementation:** _quote_unquoted_labels() added ✅

---

## 📝 Related Files

- `backend/app/services/postprocessing/mermaid_processor.py` - Core fix
- `backend/tests/regression/test_mermaid.py` - Test coverage
- `backend/app/services/postprocessing/__init__.py` - Module exports

---

## 🔧 Example Transformations

| Before | After |
|--------|-------|
| `B[walKR (yycFG)]` | `B["walKR (yycFG)"]` |
| `A[S. aureus genes]` | `A["S. aureus genes"]` |
| `C[Resistance mechanism]` | `C["Resistance mechanism"]` |
| `A["Already quoted"]` | `A["Already quoted"]` (unchanged) |

---

*Following CLAUDE.md System Law:*
- ✅ CoT Retrieval mandate followed
- ✅ Root cause identified through evidence
- ✅ Failure modes enumerated before implementation
- ✅ Single targeted fix implemented
- ✅ Tests written and passing (29/29)
