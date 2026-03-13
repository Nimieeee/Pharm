"""
Mermaid Diagram Validator and Auto-Correction Service
Validates and fixes common AI-generated Mermaid syntax errors.
"""

import re
import logging
from typing import Optional, Tuple, List, Dict

logger = logging.getLogger(__name__)


class MermaidValidator:
    """
    Validates and auto-corrects Mermaid diagram syntax.
    """
    
    # Common arrow patterns
    VALID_ARROWS = [
        '<-->', '<--', '-->', '--',
        '<-.->', '<-.', '.->', '--',
        '==>', '==',
        '..>', '..',
    ]
    
    # Node ID pattern (alphanumeric only)
    NODE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_and_fix(self, mermaid_code: str) -> Tuple[str, List[str], List[str]]:
        """
        Validate and auto-correct Mermaid syntax.
        
        Args:
            mermaid_code: Raw Mermaid diagram code
            
        Returns:
            Tuple of (corrected_code, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Step 1: Auto-correct common errors
        corrected = self._auto_correct(mermaid_code)
        
        # Step 2: Validate corrected code
        is_valid, validation_errors = self._validate_syntax(corrected)
        
        if not is_valid:
            self.errors.extend(validation_errors)
        
        return corrected, self.errors, self.warnings
    
    def _auto_correct(self, raw: str) -> str:
        """
        Auto-correct common AI-generated Mermaid errors.
        """
        lines = raw.split('\n')
        corrected = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('%%'):
                corrected.append(line)
                continue

            # Skip lines inside quoted labels (don't break label text)
            # We only fix structural syntax, not content inside ["..."]

            # --- FIX 0: Unicode character normalization ---
            # Replace non-breaking hyphens, spaces with regular ASCII
            line = line.replace('\u2011', '-')  # Non-breaking hyphen
            line = line.replace('\u00a0', ' ')  # Non-breaking space
            line = line.replace('\u2013', '-')  # En dash
            line = line.replace('\u2014', '-')  # Em dash
            # Replace ≥ with >= for better compatibility (use placeholder to protect from arrow fixes)
            line = line.replace('≥', '__GREATER_EQUAL__')
            # Replace ≤ with <=
            line = line.replace('≤', '__LESS_EQUAL__')
            # Replace × with x (multiplication)
            line = line.replace('×', 'x')
            # Replace ÷ with /
            line = line.replace('÷', '/')

            # --- FIX 1: Spaces inside node IDs ---
            # e.g. "F --> F 1[" → "F --> F1["
            line = re.sub(r'\b([A-Za-z]+)\s+(\d+)\s*(\[|\(|\{)', r'\1\2\3', line)

            # --- FIX 2: Spaces between node ID and opening bracket ---
            # e.g. "AC [" → "AC[", "AF [" → "AF["
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\[")', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\[)', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\()', r'\1\2', line)
            line = re.sub(r'([A-Za-z0-9_]+)\s+(\{)', r'\1\2', line)

            # --- FIX 3: Spaces after pipe closing in edge labels ---
            # e.g. "-->|Kidney| V[" → "-->|Kidney|V["
            line = re.sub(r'\|\s+([A-Za-z0-9_]+)(\[|\(|\{)', r'|\1\2', line)

            # --- FIX 4: Hallucinated arrow heads ---
            # e.g. "-->|Label|> B[" → "-->|Label| B["
            line = re.sub(r'\|>', '|', line)
            line = re.sub(r'->>', '-->', line)

            # --- FIX 5: Invalid arrow patterns ---
            # Detect and fix malformed arrows
            line = self._fix_arrows(line)

            # --- FIX 6: Style line fixes ---
            # 6a: Extra spaces between "style" and node ID
            line = re.sub(r'^(\s*style)\s{2,}([A-Za-z0-9_-]+)', r'\1 \2', line)

            # 6b: Spaces inside hex color values
            line = re.sub(r'(fill|stroke|color):#\s+([a-fA-F0-9])', r'\1:#\2', line)
            line = re.sub(r'(fill|stroke|color):#([a-fA-F0-9]+)\s+([a-fA-F0-9]+)', r'\1:#\2\3', line)

            # 6c: Spaces around colon in style props
            line = re.sub(r'(fill|stroke|color)\s*:\s+#', r'\1:#', line)

            # 6d: Spaces around comma in style defs
            line = re.sub(r'(fill|stroke|color):#[a-fA-F0-9]+,\s+(fill|stroke|color)',
                         lambda m: m.group(0).replace(', ', ','), line)

            # --- FIX 7: Invalid node ID characters ---
            # Replace hyphens in node IDs with underscores
            line = self._fix_node_ids(line)

            # --- FIX 8: Escape special characters in node labels ---
            # Handle parentheses and quotes inside labels
            line = self._escape_label_special_chars(line)

            # --- FIX 9: Restore Unicode replacements ---
            # Convert placeholders back to actual operators
            line = line.replace('__GREATER_EQUAL__', '>=')
            line = line.replace('__LESS_EQUAL__', '<=')

            # Log if changes were made
            if line != original_line:
                self.warnings.append(f"Line {line_num}: Auto-corrected syntax")

            corrected.append(line)

        return '\n'.join(corrected).strip()
    
    def _fix_arrows(self, line: str) -> str:
        """Fix malformed arrow patterns"""
        # Replace invalid arrow patterns with valid ones
        replacements = [
            (r'-+>', '-->'),      # Multiple dashes
            (r'<-+', '<--'),      # Multiple dashes reverse
            (r'=\s*=', '=='),     # Double equals with space
            (r'\.\s*\.', '..'),   # Double dots with space
        ]
        
        for pattern, replacement in replacements:
            line = re.sub(pattern, replacement, line)
        
        return line
    
    def _fix_node_ids(self, line: str) -> str:
        """Fix invalid node ID characters"""
        # Node IDs should be alphanumeric only
        # This is tricky - we need to fix IDs without breaking labels

        # Pattern: Start of line or after arrow, capture potential ID
        # e.g. "Node-1[" → "Node1["

        def replace_hyphen_in_id(match):
            prefix = match.group(1) or ''
            node_id = match.group(2)
            bracket = match.group(3)

            # Only fix if it looks like a node ID (before bracket)
            fixed_id = node_id.replace('-', '_')
            return f"{prefix}{fixed_id}{bracket}"

        # Match: optional prefix (arrow), node ID with hyphens, opening bracket
        line = re.sub(
            r'(^|-->|--|<-->|<--|\.->|-.->)\s*([A-Za-z][A-Za-z0-9_-]*)\s*(\[|\(|\{|\))',
            replace_hyphen_in_id,
            line
        )

        return line

    def _escape_label_special_chars(self, line: str) -> str:
        """
        Escape or fix special characters inside node labels.
        Handles parentheses, quotes, and other problematic chars.
        """
        # Pattern to find node labels: ["..."] or [...]
        # We need to be careful not to break the structure
        
        def fix_label_content(match):
            """Fix content inside labels while preserving structure"""
            prefix = match.group(1)  # Everything before the label
            label_content = match.group(2)  # Content inside quotes
            suffix = match.group(3)  # Everything after the label
            
            # Fix unbalanced parentheses inside labels
            # Count open/close parens
            open_count = label_content.count('(')
            close_count = label_content.count(')')
            
            # If unbalanced, we can't easily fix - just pass through
            # The LLM should generate balanced parens
            if open_count != close_count:
                # Try to add missing close parens at the end
                label_content = label_content + ')' * (open_count - close_count)
            
            # Escape backslashes that might break escaping
            label_content = label_content.replace('\\', '\\\\')
            
            return f'{prefix}"{label_content}"{suffix}'
        
        # Match node definitions with quoted labels: ID["label text"]
        # Be greedy to capture the full label
        line = re.sub(
            r'([A-Za-z0-9_]+\s*\[)"([^"]*?)"(\])',
            fix_label_content,
            line
        )
        
        return line
    
    def _validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate Mermaid syntax and return errors.
        """
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
        
        # Check each line for common errors
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines, comments, and graph declaration
            if not stripped or stripped.startswith('%%') or stripped.startswith('graph') or stripped.startswith('flowchart'):
                continue
            
            # Check for unclosed quotes
            quote_count = stripped.count('"') - stripped.count('\\"')
            if quote_count % 2 != 0:
                errors.append(f"Line {line_num}: Unclosed quote in node label")
            
            # Check for invalid characters in node IDs (outside labels)
            # This is a simplified check
            if re.search(r'[A-Za-z0-9_]+-[A-Za-z0-9_]+\s*[\[\(\{]', stripped):
                errors.append(f"Line {line_num}: Node ID contains invalid characters (hyphens)")
            
            # Check for spaces in node definitions
            if re.search(r'[A-Za-z]+\s+\d+\s*[\[\(\{]', stripped):
                errors.append(f"Line {line_num}: Space in node ID")
        
        return len(errors) == 0, errors
    
    def extract_diagrams_from_markdown(self, markdown: str) -> List[str]:
        """
        Extract all Mermaid code blocks from markdown text.
        """
        pattern = r'```mermaid\s*\n(.*?)\n```'
        matches = re.findall(pattern, markdown, re.DOTALL)
        return matches
    
    def validate_markdown(self, markdown: str) -> Tuple[str, List[Dict]]:
        """
        Validate and fix all Mermaid diagrams in markdown text.
        
        Args:
            markdown: Markdown text containing Mermaid code blocks
            
        Returns:
            Tuple of (corrected_markdown, list of {diagram_index, errors, warnings})
        """
        diagrams = self.extract_diagrams_from_markdown(markdown)
        results = []
        corrected_markdown = markdown
        
        for idx, diagram in enumerate(diagrams):
            corrected, errors, warnings = self.validate_and_fix(diagram)
            
            if errors or warnings:
                results.append({
                    'diagram_index': idx,
                    'errors': errors,
                    'warnings': warnings,
                    'original': diagram,
                    'corrected': corrected
                })
                
                # Replace in markdown
                corrected_markdown = corrected_markdown.replace(
                    f'```mermaid\n{diagram}\n```',
                    f'```mermaid\n{corrected}\n```'
                )
        
        return corrected_markdown, results
