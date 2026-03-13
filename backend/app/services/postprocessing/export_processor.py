import re

class ExportProcessor:
    """Generic export format processing — CLAUDE.md Postprocessing Pattern."""

    def sanitize_svg(self, svg_content: str) -> str:
        """
        Remove potentially harmful SVG elements (script, onload, etc.).
        
        Args:
            svg_content: Raw SVG string
            
        Returns:
            Sanitized SVG string
        """
        if not svg_content:
            return ""
            
        # Remove script tags and their content
        sanitized = re.sub(r'<script.*?>.*?</script>', '', svg_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove event handlers (onmouseover, onload, etc.)
        sanitized = re.sub(r'\son\w+?\s*=\s*".*?"', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\son\w+?\s*=\s*'.*?'", '', sanitized, flags=re.IGNORECASE)
        
        return sanitized

    def format_csv(self, data: list, columns: list) -> str:
        """
        Format data as CSV with proper escaping.
        
        Args:
            data: List of lists or list of dicts
            columns: List of column headers
            
        Returns:
            CSV string
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow(columns)
        
        # Write rows
        for row in data:
            if isinstance(row, dict):
                writer.writerow([row.get(col, "") for col in columns])
            else:
                writer.writerow(row)
                
        return output.getvalue()

    def format_json_export(self, data: dict) -> str:
        """
        Pretty-print JSON for export.
        
        Args:
            data: Dictionary to export
            
        Returns:
            Pretty-printed JSON string
        """
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)

# Singleton instance
export_processor = ExportProcessor()
