"""
ADMET Processor

Postprocessing module for ADMET report formatting and export.
Part of the centralized postprocessing architecture (CLAUDE.md compliant).
"""

import re
from typing import Dict, Any, List


class ADMETProcessor:
    """
    ADMET report formatting and export.
    
    Features:
    - SVG sanitization for markdown rendering
    - CSV export formatting
    - Clinical findings summarization
    """
    
    def __init__(self):
        """Initialize ADMETProcessor"""
        pass
    
    def format_svg_for_report(self, svg: str) -> str:
        """
        Clean and optimize SVG for markdown embedding.
        
        Args:
            svg: Raw SVG from ADMETlab API
            
        Returns:
            Cleaned SVG safe for embedding
        """
        if not svg:
            return ""
        
        # Remove XML declaration if present
        svg = re.sub(r'<\?xml.*?\?>', '', svg)
        
        # Remove potentially harmful elements
        svg = re.sub(r'<script[^>]*>.*?</script>', '', svg, flags=re.DOTALL)
        svg = re.sub(r'<foreignObject[^>]*>.*?</foreignObject>', '', svg, flags=re.DOTALL)
        
        # Optimize: remove comments
        svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)
        
        # Optimize: remove metadata
        svg = re.sub(r'<metadata[^>]*>.*?</metadata>', '', svg, flags=re.DOTALL)
        
        # Ensure proper viewBox for responsive rendering
        if 'viewBox' not in svg and 'width' in svg and 'height' in svg:
            width_match = re.search(r'width="(\d+)"', svg)
            height_match = re.search(r'height="(\d+)"', svg)
            if width_match and height_match:
                svg = svg.replace(
                    '<svg ',
                    f'<svg viewBox="0 0 {width_match.group(1)} {height_match.group(1)}" '
                )
        
        # Add responsive class
        svg = svg.replace('<svg ', '<svg class="w-full h-auto" ')
        
        return svg.strip()
    
    def format_csv_export(self, results: Dict[str, Any]) -> str:
        """
        Convert ADMET results to CSV string.
        
        Args:
            results: ADMET prediction results dict
            
        Returns:
            CSV-formatted string
        """
        lines = []
        
        # Header
        lines.append("Category,Endpoint,Value,Unit,Interpretation")
        
        # Process each category
        for category, data in results.items():
            if isinstance(data, dict):
                for endpoint, value in data.items():
                    # Handle nested values
                    if isinstance(value, dict):
                        val = value.get('value', value)
                        unit = value.get('unit', '')
                        interp = value.get('interpretation', '')
                    else:
                        val = value
                        unit = ''
                        interp = ''
                    
                    # Escape commas in values
                    val_str = str(val).replace(',', ';')
                    interp_str = str(interp).replace(',', ';')
                    
                    lines.append(f"{category},{endpoint},{val_str},{unit},{interp_str}")
        
        return '\n'.join(lines)
    
    def summarize_findings(self, admet_data: Dict[str, Any]) -> str:
        """
        Generate clinical summary of ADMET results.
        
        Args:
            admet_data: Full ADMET prediction results
            
        Returns:
            Markdown summary string
        """
        summary_parts = []
        
        # Check for red flags
        red_flags = []
        
        # Lipinski Rule of 5
        if 'lipinski' in admet_data:
            lipinski = admet_data['lipinski']
            violations = lipinski.get('violations', 0)
            if violations > 0:
                red_flags.append(f"Lipinski violations: {violations}")
        
        # PAINS (Pan-Assay Interference Compounds)
        if 'pains' in admet_data:
            pains = admet_data['pains']
            if pains.get('has_pains', False):
                red_flags.append("Contains PAINS substructure")
        
        # Toxicity alerts
        if 'toxicity' in admet_data:
            toxicity = admet_data['toxicity']
            if toxicity.get('mutagenic', False):
                red_flags.append("⚠️ Mutagenic potential")
            if toxicity.get('carcinogenic', False):
                red_flags.append("⚠️ Carcinogenic potential")
            if toxicity.get('hepatotoxic', False):
                red_flags.append("⚠️ Hepatotoxic")
        
        # Absorption
        if 'absorption' in admet_data:
            absorption = admet_data['absorption']
            caco2 = absorption.get('caco2', {})
            if isinstance(caco2, dict):
                caco2_val = caco2.get('value', 0)
            else:
                caco2_val = caco2
            
            if caco2_val < 0:
                red_flags.append("Poor intestinal absorption")
        
        # Build summary
        if red_flags:
            summary_parts.append("### ⚠️ Red Flags\n")
            for flag in red_flags:
                summary_parts.append(f"- {flag}")
            summary_parts.append("")
        
        # Drug-likeness score
        if 'drug_likeness' in admet_data:
            score = admet_data['drug_likeness'].get('score', 'N/A')
            summary_parts.append(f"**Drug-likeness Score**: {score}\n")
        
        # Key ADMET properties
        summary_parts.append("### Key Properties\n")
        
        if 'absorption' in admet_data:
            caco2 = admet_data['absorption'].get('caco2', 'N/A')
            summary_parts.append(f"- **Caco-2 Permeability**: {caco2}")
        
        if 'distribution' in admet_data:
            vd = admet_data['distribution'].get('volume_distribution', 'N/A')
            bb = admet_data['distribution'].get('bbb', 'N/A')
            summary_parts.append(f"- **Volume of Distribution**: {vd}")
            summary_parts.append(f"- **BBB Penetration**: {bb}")
        
        if 'metabolism' in admet_data:
            cyp_sub = admet_data['metabolism'].get('cyp_substrate', [])
            cyp_inh = admet_data['metabolism'].get('cyp_inhibitor', [])
            if cyp_sub:
                summary_parts.append(f"- **CYP Substrates**: {', '.join(cyp_sub)}")
            if cyp_inh:
                summary_parts.append(f"- **CYP Inhibitors**: {', '.join(cyp_inh)}")
        
        if 'excretion' in admet_data:
            cl = admet_data['excretion'].get('clearance', 'N/A')
            summary_parts.append(f"- **Clearance**: {cl}")
        
        return '\n'.join(summary_parts)
    
    def format_report(self, admet_data: Dict[str, Any], svg: str = None) -> str:
        """
        Generate complete markdown report.
        
        Args:
            admet_data: Full ADMET prediction results
            svg: Optional molecule structure SVG
            
        Returns:
            Complete markdown report
        """
        parts = []
        
        # Title
        parts.append("## ADMET Analysis Report\n")
        
        # Clinical summary
        summary = self.summarize_findings(admet_data)
        parts.append(summary)
        
        # Detailed results
        parts.append("\n## Detailed Results\n")
        
        for category, data in admet_data.items():
            if isinstance(data, dict):
                parts.append(f"\n### {category.replace('_', ' ').title()}\n")
                
                for endpoint, value in data.items():
                    if isinstance(value, dict):
                        val = value.get('value', 'N/A')
                        unit = value.get('unit', '')
                        interp = value.get('interpretation', '')
                        parts.append(f"- **{endpoint.replace('_', ' ').title()}**: {val} {unit}")
                        if interp:
                            parts.append(f"  - {interp}")
                    else:
                        parts.append(f"- **{endpoint.replace('_', ' ').title()}**: {value}")
        
        return '\n'.join(parts)


# Singleton instance
admet_processor = ADMETProcessor()
