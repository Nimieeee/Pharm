"""
Mermaid Diagram Processor

Centralized Mermaid validation and auto-correction.
ALL Mermaid logic lives here - tested once, used everywhere.

This module handles:
- Unicode character normalization
- Arrow pattern fixes
- Node ID validation
- Label escaping
- Parentheses balancing
"""

import re
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


class MermaidProcessor:
    """
    Production Mermaid processor with comprehensive fixes.
    
    Usage:
        processor = MermaidProcessor()
        corrected, errors, warnings = processor.validate_and_fix(mermaid_code)
    """
    
    # =====================================================================
    # CONFIGURATION - Centralized, tested, easy to modify
    # =====================================================================
    
    # Unicode normalization map (tested comprehensively)
    UNICODE_FIXES = {
        '\u2011': '-',  # Non-breaking hyphen
        '\u00a0': ' ',  # Non-breaking space
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '≥': '__GE__',  # Greater-equal (protected placeholder)
        '≤': '__LE__',  # Less-equal (protected placeholder)
        '×': 'x',       # Multiplication
        '÷': '/',       # Division
        '⁰': '0',       # Superscript zero
        '¹': '1',       # Superscript one
        '²': '2',       # Superscript two
        '³': '3',       # Superscript three
    }
    
    # Valid arrow patterns (order matters - longer patterns first)
    VALID_ARROWS = [
        '<-->', '<--', '-->', '--',
        '<-.->', '<-.', '.->',
        '==>', '==',
        '..>', '..',
    ]
    
    # Arrow regex patterns for fixing
    ARROW_FIXES = [
        (r'-+>', '-->'),      # Multiple dashes → standard arrow
        (r'<-+', '<--'),      # Multiple dashes reverse
        (r'=\s*=', '=='),     # Double equals with space
        (r'\.\s*\.', '..'),   # Double dots with space
        (r'->>', '-->'),      # Double arrow head
        (r'<<-', '<--'),      # Double arrow tail
    ]
    
    # Placeholder protection pattern
    PROTECTED_PLACEHOLDERS = {
        '__GE__': '>=',
        '__LE__': '<=',
    }
    
    # =====================================================================
    # PUBLIC API
    # =====================================================================
    
    def validate_and_fix(self, mermaid_code: str) -> Tuple[str, List[str], List[str]]:
        """
        Validate and auto-correct Mermaid syntax.
        
        Args:
            mermaid_code: Raw Mermaid diagram code
        
        Returns:
            Tuple of (corrected_code, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if not mermaid_code or not mermaid_code.strip():
            errors.append("Empty Mermaid code")
            return "", errors, warnings
        
        # Step 1: Unicode normalization (with protection)
        corrected = self._normalize_unicode(mermaid_code)
        
        # Step 2: Structural fixes
        corrected = self._fix_structure(corrected, warnings)
        
        # Step 3: Restore protected sequences
        corrected = self._restore_protected(corrected)
        
        # Step 4: Validation
        is_valid, validation_errors = self._validate(corrected)
        errors.extend(validation_errors)
        
        return corrected, errors, warnings
    
    def extract_mermaid_blocks(self, markdown: str) -> List[Dict[str, any]]:
        """
        Extract all Mermaid code blocks from markdown.
        
        Args:
            markdown: Markdown text containing Mermaid blocks
        
        Returns:
            List of {start, end, content, corrected} dicts
        """
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = list(re.finditer(pattern, markdown, re.DOTALL))
        
        blocks = []
        for match in matches:
            content = match.group(1)
            corrected, errors, warnings = self.validate_and_fix(content)
            
            blocks.append({
                'start': match.start(),
                'end': match.end(),
                'original': content,
                'corrected': corrected,
                'errors': errors,
                'warnings': warnings,
                'needs_fix': len(errors) > 0 or len(warnings) > 0
            })
        
        return blocks
    
    def fix_markdown_mermaid(self, markdown: str) -> Tuple[str, int]:
        """
        Fix all Mermaid blocks in markdown text.
        
        Args:
            markdown: Markdown text with Mermaid blocks
        
        Returns:
            Tuple of (corrected_markdown, fix_count)
        """
        blocks = self.extract_mermaid_blocks(markdown)
        
        if not blocks:
            return markdown, 0
        
        # Replace blocks from end to start to preserve positions
        corrected_markdown = markdown
        fix_count = 0
        
        for block in reversed(blocks):
            if block['needs_fix']:
                old_block = f"```mermaid\n{block['original']}\n```"
                new_block = f"```mermaid\n{block['corrected']}\n```"
                corrected_markdown = corrected_markdown[:block['start']] + new_block + corrected_markdown[block['end']:]
                fix_count += 1
        
        return corrected_markdown, fix_count
    
    # =====================================================================
    # INTERNAL METHODS - Implementation details
    # =====================================================================
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters to ASCII equivalents"""
        for unicode_char, replacement in self.UNICODE_FIXES.items():
            text = text.replace(unicode_char, replacement)
        return text
    
    def _restore_protected(self, text: str) -> str:
        """Restore protected placeholder sequences"""
        for placeholder, original in self.PROTECTED_PLACEHOLDERS.items():
            text = text.replace(placeholder, original)
        return text
    
    def _fix_structure(self, text: str, warnings: List[str]) -> str:
        """Apply structural fixes to Mermaid code"""
        # Normalize line endings
        text = text.replace('\r\n', '\n')

        # Split by concatenated lines before processing
        # Example: ]B --> or )B --> or }B -->
        text = re.sub(r'([\]\)\}])\s*([A-Za-z0-9_-]+)\s*(-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)', r'\1\n\2 \3', text)

        lines = text.split('\n')
        corrected = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('%%'):
                corrected.append(line)
                continue

            # Fix 0a: Missing arrow before edge label with pipe (CRITICAL)
            # Pattern: ]"|text"| or )"|text"| or }"|text"|  (missing arrow before "|")
            # Example: A["label"]"|text"|B["label"] → A["label"] -->|"text"|B["label"]
            # Handle multiple closing brackets: ))"|  ]] "|  }}"|
            line = re.sub(r'([\]\)\}]+)\s*"([^"]*)"\s*\|([A-Za-z0-9_-])', r'\1 -->|"\2"|\3', line)

            # Fix 0b: Missing arrow before quoted edge label (no pipe)
            # Pattern: ]"text"  (missing arrow before quoted edge label)
            # Example: A["label"]"text" → A["label"] --> "text"
            line = re.sub(r'([\]\)\}]+)\s*"([^"]+)"\s*([A-Za-z0-9_\[\(])', r'\1 --> "\2" \3', line)

            # Fix 0c: Missing arrow before node (no quotes)
            # Pattern: ]Node[  (missing arrow before node declaration)
            # Example: A["label"]B["label"] → A["label"] --> B["label"]
            line = re.sub(r'([\]\)\}]+)\s*([A-Za-z0-9_]+)\s*(\[[\(\{])', r'\1 --> \2\3', line)

            # Fix 0d: Missing arrow with unquoted edge label
            # Pattern: ]text|  (missing arrow before unquoted edge label)
            # Example: A["label"]text|B["label"] → A["label"] --> text|B["label"]
            line = re.sub(r'([\]\)\}]+)\s*([A-Za-z][A-Za-z0-9_-]*)\s*\|([A-Za-z0-9_-])', r'\1 --> \2|\3', line)

            # Fix 1: Spaces in node IDs (only at start of line or after arrows)
            line = re.sub(r'(^|-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)\s*([A-Za-z]+)\s+(\d+)\s*(\[|\(|\{)', r'\1\2\3\4', line)

            # Fix 1A: Node IDs with spaces before label (only at start of line or after arrows)
            line = re.sub(r'(^|-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)\s*([A-Za-z][A-Za-z0-9_-]*)\s+([A-Za-z][A-Za-z0-9_-]*)\s*(\[[^\]]*\]|\([^\)]*\))', r'\1\2\3\4', line)

            # Fix 2: Spaces before brackets
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\[")', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\[)', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\()', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\{)', r'\1\2', line)

            # Fix 2b: Malformed closing quotes/brackets
            # Pe")"] -->  -> Pe"] -->
            line = re.sub(r'"\s*[\]\)\}]+\s*([\]\)\}]?)\s*(-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)', r'"] \2', line)

            # Fix 3: Arrow pattern fixes
            for pattern, replacement in self.ARROW_FIXES:
                line = re.sub(pattern, replacement, line)

            # Fix 4: Node ID hyphens → underscores
            line = self._fix_node_ids(line)

            # Fix 5: Quote unquoted labels (MUST run before _escape_labels)
            line = self._quote_unquoted_labels(line)

            # Fix 6: Label special character escaping
            line = self._escape_labels(line)

            # Fix 7: Remove trailing garbage after relation
            line = re.sub(r'(-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)\s*([A-Za-z0-9_-]+)\s*[.,;:]\s*$', r'\1 \2', line)

            # Fix 8: Style syntax errors (spaces in style definitions)
            # Pattern: style A fill : #fff  →  style A fill:#fff
            line = re.sub(r'\b(style\s+[A-Za-z0-9_]+)\s+(fill|stroke|color)\s*:', r'\1 \2:', line)

            # Fix 9: Unclosed subgraph detection (add end if missing)
            # This is handled at the end after all lines are processed

            # Track warnings
            if line != original_line:
                warnings.append(f"Line {line_num}: Auto-corrected")

            corrected.append(line)

        # Post-processing: Balance subgraphs
        subgraph_count = sum(1 for line in corrected if line.strip().startswith('subgraph'))
        end_count = sum(1 for line in corrected if line.strip() == 'end')

        # Add missing 'end' statements
        for _ in range(subgraph_count - end_count):
            corrected.append('end')

        return '\n'.join(corrected)
    
    def _fix_node_ids(self, line: str) -> str:
        """Fix invalid node ID characters (hyphens → underscores)"""
        def replace_hyphen(match):
            prefix = match.group(1) or ''
            node_id = match.group(2)
            bracket = match.group(3)
            fixed_id = node_id.replace('-', '_')
            return f"{prefix}{fixed_id}{bracket}"

        return re.sub(
            r'(^|-->|--|<-->|<--|\.->|-.->)\s*([A-Za-z][A-Za-z0-9_-]*)\s*(\[|\(|\{|\))',
            replace_hyphen,
            line
        )

    def _process_labels(self, line: str, callback: callable) -> str:
        """Helper to identify and process Mermaid node labels accurately"""
        # Split by arrows to avoid matching across multiple nodes
        parts = re.split(r'(-->|--|<-->|<--|\.->|-.->|==>|==|\.\.>|\.\.)', line)
        fixed_parts = []

        for part in parts:
            if part in ['-->', '--', '<-->', '<--', '.->', '-.->', '==>', '==', '..>', '..']:
                fixed_parts.append(part)
                continue
            
            # Find start of label: NodeID [ ( or {
            match = re.search(r'([A-Za-z0-9_-]+)\s*([\[\(\{]+)', part)
            if match:
                prefix = part[:match.start(1)]
                node_id = match.group(1)
                bracket_open = match.group(2)
                
                # Find the matching closing bracket(s)
                # We look for the last occurrence of the closure set in this part
                closure_map = {'[': ']', '(': ')', '{': '}'}
                target_close = ''.join([closure_map[c] for c in reversed(bracket_open)])
                
                start_content = match.end(2)
                last_close_idx = part.rfind(target_close)
                
                if last_close_idx > start_content:
                    content = part[start_content:last_close_idx]
                    suffix = part[last_close_idx + len(target_close):]
                    
                    new_content = callback(node_id, bracket_open, content, target_close)
                    fixed_parts.append(f"{prefix}{new_content}{suffix}")
                else:
                    # Fallback to regex if manual find fails
                    fixed_parts.append(part)
            else:
                fixed_parts.append(part)

        return ''.join(fixed_parts)

    def _quote_unquoted_labels(self, line: str) -> str:
        """Quote unquoted labels"""
        def quote_callback(node_id, bracket_open, content, bracket_close):
            # Already quoted - leave as is
            if (content.startswith('"') and content.endswith('"')) or \
               (content.startswith("'") and content.endswith("'")):
                return f"{node_id}{bracket_open}{content}{bracket_close}"
            
            # Remove single quotes if present
            if content.startswith("'") and content.endswith("'"):
                content = content[1:-1]
                
            return f'{node_id}{bracket_open}"{content}"{bracket_close}'

        return self._process_labels(line, quote_callback)
    
    def _escape_labels(self, line: str) -> str:
        """Escape labels and balance parentheses"""
        def escape_callback(node_id, bracket_open, content, bracket_close):
            # Strip outer quotes if present
            is_quoted = False
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
                is_quoted = True
            
            # Balance parentheses
            open_count = content.count('(')
            close_count = content.count(')')
            if open_count != close_count:
                content = content + ')' * (open_count - close_count)
            
            # Escape backslashes
            content = content.replace('\\', '\\\\')
            
            return f'{node_id}{bracket_open}"{content}"{bracket_close}'

        return self._process_labels(line, escape_callback)
    
    def _validate(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Mermaid syntax"""
        errors = []
        lines = code.split('\n')

        # Check for graph declaration
        has_graph_decl = any(
            line.strip().startswith(('graph ', 'flowchart ', 'sequenceDiagram',
                                     'classDiagram', 'erDiagram', 'stateDiagram'))
            for line in lines
        )

        if not has_graph_decl:
            errors.append("Missing graph/flowchart declaration")

        # Check each line
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty, comments, declarations
            if not stripped or stripped.startswith('%%') or stripped.startswith(('graph', 'flowchart')):
                continue

            # Check unclosed quotes
            quote_count = stripped.count('"') - stripped.count('\\"')
            if quote_count % 2 != 0:
                errors.append(f"Line {line_num}: Unclosed quote")

            # Check for unbalanced brackets in node declarations
            bracket_count = stripped.count('[') - stripped.count(']')
            paren_count = stripped.count('(') - stripped.count(')')
            brace_count = stripped.count('{') - stripped.count('}')

            # Allow for double brackets like [[ ]] but flag obvious mismatches
            if abs(bracket_count) > 2 or abs(paren_count) > 2 or abs(brace_count) > 2:
                errors.append(f"Line {line_num}: Possibly unbalanced brackets/parentheses/braces")

        # Check subgraph balance
        subgraph_count = sum(1 for line in lines if line.strip().startswith('subgraph'))
        end_count = sum(1 for line in lines if line.strip() == 'end')

        if subgraph_count != end_count:
            errors.append(f"Unbalanced subgraphs: {subgraph_count} subgraph(s) but {end_count} end(s)")

        return len(errors) == 0, errors


# Singleton instance for global use
mermaid_processor = MermaidProcessor()
