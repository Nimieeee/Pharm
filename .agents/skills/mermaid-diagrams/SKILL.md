---
name: mermaid-diagrams
description: Use when creating, fixing, or validating Mermaid diagram syntax. Provides syntax rules, common error patterns, and auto-correction techniques for flowcharts, sequence diagrams, class diagrams, and other Mermaid diagram types.
---

# Mermaid Diagrams

## Overview

Mermaid.js v11 is a JavaScript-based diagramming and charting tool that renders Markdown-inspired text definitions to create and modify diagrams dynamically.

**Core Principle:** Mermaid syntax is **strict** about spacing, node IDs, and arrow formats. AI models commonly generate invalid syntax that requires correction.

## When to Use

- Creating flowcharts, sequence diagrams, class diagrams, ER diagrams, state diagrams
- Fixing "Failed to render diagram" errors
- Validating Mermaid syntax before rendering
- Auto-correcting common AI-generated Mermaid errors

## Common AI-Generated Errors & Fixes

### Error 1: Spaces in Node IDs

**❌ Invalid:**
```mermaid
F --> F 1["Label"]
```

**✅ Fixed:**
```mermaid
F --> F1["Label"]
```

**Fix Pattern:** `\b([A-Za-z]+)\s+(\d+)\s*(\[)` → `$1$2$3`

### Error 2: Spaces Before Brackets

**❌ Invalid:**
```mermaid
AC ["Label"]
V ("Label")
```

**✅ Fixed:**
```mermaid
AC["Label"]
V("Label")
```

**Fix Pattern:** `([A-Za-z0-9_]+)\s+(\[")` → `$1$2`

### Error 3: Hallucinated Arrow Heads

**❌ Invalid:**
```mermaid
A -->|Label|> B["Node"]
```

**✅ Fixed:**
```mermaid
A -->|Label| B["Node"]
```

**Fix Pattern:** `\|>` → `|`

### Error 4: Spaces in Style Definitions

**❌ Invalid:**
```mermaid
style  B fill:# f88, stroke:#333
```

**✅ Fixed:**
```mermaid
style B fill:#f88,stroke:#333
```

**Fix Patterns:**
- `^(\s*style)\s{2,}([A-Za-z0-9_-]+)` → `$1 $2`
- `(fill|stroke|color):#\s+([a-fA-F0-9])` → `$1:#$2`
- `(fill|stroke|color):#[a-fA-F0-9]+,\s+(fill|stroke|color)` → remove space after comma

### Error 5: Invalid Node ID Characters

**❌ Invalid:**
```mermaid
Node-1["Label"]  %% Hyphen in ID
```

**✅ Fixed:**
```mermaid
Node1["Label"]
```

**Rule:** Node IDs must be alphanumeric (no hyphens, dots, or special chars)

## Arrow Syntax Reference

| Arrow Type | Syntax | Example |
|------------|--------|---------|
| One-way | `-->` | `A --> B` |
| Two-way | `<-->` | `A <--> B` |
| Dotted | `-.->` | `A -.-> B` |
| Solid | `--` | `A -- B` |
| With label | `-->|label|` | `A -->|yes| B` |

## Node Definition Patterns

```mermaid
%% Basic node
A["Label Text"]

%% Node with ID
id1["Label Text"]

%% Rounded rectangle
B("Label Text")

%% Circle
C(("Label"))

%% Stadium shape
D([("Label")])

%% Subroutine
E[["Label"]]

%% Cylindrical
F[("Label")]

%% Rhombus (decision)
G{"Label"}
```

## Validation Checklist

Before claiming a Mermaid diagram is valid:

- [ ] No spaces in node IDs
- [ ] No spaces between ID and bracket
- [ ] No `|>` (hallucinated arrow heads)
- [ ] Style lines have no double spaces
- [ ] Hex colors have no spaces (`#f88` not `# f88`)
- [ ] Commas in style defs have no trailing spaces
- [ ] All node IDs are alphanumeric only
- [ ] Arrow syntax uses valid patterns (`-->`, `<-->`, `-.->`)

## Auto-Correction Function

```python
def clean_mermaid_syntax(raw: str) -> str:
    """Auto-correct common AI-generated Mermaid errors"""
    lines = raw.split('\n')
    cleaned = []
    for line in lines:
        # Skip lines inside quoted labels
        # Fix 1: Spaces inside node IDs
        line = re.sub(r'\b([A-Za-z]+)\s+(\d+)\s*(\[|\(|\{)', r'\1\2\3', line)
        # Fix 2: Spaces before brackets
        line = re.sub(r'([A-Za-z0-9_]+)\s+(\[")', r'\1\2', line)
        # Fix 3: Hallucinated arrow heads
        line = re.sub(r'\|>', '|', line)
        # Fix 4: Style line fixes
        line = re.sub(r'^(\s*style)\s{2,}([A-Za-z0-9_-]+)', r'\1 \2', line)
        line = re.sub(r'(fill|stroke|color):#\s+([a-fA-F0-9])', r'\1:#\2', line)
        cleaned.append(line)
    return '\n'.join(cleaned).strip()
```

## Testing Mermaid Syntax

**Test Command:**
```bash
# Using mermaid-cli
mmdc -i diagram.mmd -o output.svg
```

**Online Validator:**
- https://mermaid.live/

## Related Skills

- **skill-creator**: For creating new skills about diagram types
- **verification-before-completion**: Always validate Mermaid syntax before claiming diagram works
