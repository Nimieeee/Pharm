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
        # Header label mapping (ADMETlab abbreviations)
        self.header_labels = {
            # Physicochemical
            "molecular_weight": "Molecular Weight",
            "logP": "LogP",
            "hydrogen_bond_donors": "Hydrogen Bond Donors",
            "hydrogen_bond_acceptors": "Hydrogen Bond Acceptors",
            "tpsa": "Topological Polar Surface Area",
            "num_rotatable_bonds": "Rotatable Bonds",
            "num_rings": "Ring Count",
            "num_heavy_atoms": "Heavy Atoms",
            "stereo_centers": "Stereo Centers",
            
            # Drug Likeness
            "Lipinski": "Lipinski Rule of 5",
            "QED": "Quantitative Estimate of Druglikeness",
            "PAINS_alert": "PAINS Alerts",
            "BRENK_alert": "BRENK Alerts",
            "NIH_alert": "NIH Alerts",
            
            # Absorption
            "HIA_Hou": "Human Intestinal Absorption",
            "Caco2_Wang": "Cell Effective Permeability",
            "PAMPA_NCATS": "PAMPA Permeability",
            "Pgp_Broccatelli": "P-glycoprotein Inhibition",
            "Solubility_AqSolDB": "Aqueous Solubility",
            "Lipophilicity_AstraZeneca": "Lipophilicity",
            "HydrationFreeEnergy_FreeSolv": "Hydration Free Energy",
            "Bioavailability_Ma": "Oral Bioavailability",
            
            # Distribution
            "BBB_Martins": "Blood-Brain Barrier Penetration",
            "PPBR_AZ": "Plasma Protein Binding Rate",
            "VDss_Lombardo": "Volume of Distribution",
            
            # Metabolism
            "CYP1A2_Veith": "CYP1A2 Inhibition",
            "CYP2C9_Veith": "CYP2C9 Inhibition",
            "CYP2C19_Veith": "CYP2C19 Inhibition",
            "CYP2D6_Veith": "CYP2D6 Inhibition",
            "CYP3A4_Veith": "CYP3A4 Inhibition",
            "CYP2C9_Substrate_CarbonMangels": "CYP2C9 Substrate",
            "CYP2D6_Substrate_CarbonMangels": "CYP2D6 Substrate",
            "CYP3A4_Substrate_CarbonMangels": "CYP3A4 Substrate",
            
            # Excretion
            "Clearance_Hepatocyte_AZ": "Drug Clearance (Hepatocyte)",
            "Clearance_Microsome_AZ": "Drug Clearance (Microsome)",
            "Half_Life_Obach": "Half Life",
            
            # Toxicity
            "hERG": "hERG Blocking",
            "AMES": "Mutagenicity",
            "DILI": "Drug Induced Liver Injury",
            "ClinTox": "Clinical Toxicity",
            "Carcinogens_Lagunin": "Carcinogenicity",
            "LD50_Zhu": "Acute Toxicity LD50",
            "Skin_Reaction": "Skin Reaction",
            
            # Tox21
            "NR-AR": "Androgen Receptor (Full Length)",
            "NR-AR-LBD": "Androgen Receptor (LBD)",
            "NR-AhR": "Aryl Hydrocarbon Receptor",
            "NR-Aromatase": "Aromatase",
            "NR-ER": "Estrogen Receptor (Full Length)",
            "NR-ER-LBD": "Estrogen Receptor (LBD)",
            "NR-PPAR-gamma": "PPAR-γ",
            "SR-ARE": "Antioxidant Response Element",
            "SR-ATAD5": "ATAD5",
            "SR-HSE": "Heat Shock Factor Response",
            "SR-MMP": "Mitochondrial Membrane Potential",
            "SR-p53": "Tumor Protein p53",
        }

        # Organized by property groups
        self.property_groups = {
            "Physicochemical": ["molecular_weight", "logP", "hydrogen_bond_donors", 
                               "hydrogen_bond_acceptors", "tpsa", "num_rotatable_bonds", 
                               "num_rings", "num_heavy_atoms", "stereo_centers"],
            "Drug Likeness": ["Lipinski", "QED", "PAINS_alert", "BRENK_alert", "NIH_alert"],
            "Absorption": ["HIA_Hou", "Caco2_Wang", "PAMPA_NCATS", "Pgp_Broccatelli",
                           "Solubility_AqSolDB", "HydrationFreeEnergy_FreeSolv", 
                           "Lipophilicity_AstraZeneca", "Bioavailability_Ma"],
            "Distribution": ["BBB_Martins", "PPBR_AZ", "VDss_Lombardo"],
            "Metabolism": ["CYP1A2_Veith", "CYP2C9_Veith", "CYP2C19_Veith", "CYP2D6_Veith", 
                          "CYP3A4_Veith", "CYP2C9_Substrate_CarbonMangels", 
                          "CYP2D6_Substrate_CarbonMangels", "CYP3A4_Substrate_CarbonMangels"],
            "Excretion": ["Clearance_Hepatocyte_AZ", "Clearance_Microsome_AZ", 
                         "Half_Life_Obach"],
            "Toxicity": ["AMES", "Carcinogens_Lagunin", "ClinTox", "DILI", "hERG",
                        "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", 
                        "NR-ER-LBD", "NR-PPAR-gamma", "Skin_Reaction",
                        "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"],
        }
    
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
    
    def format_csv_export(self, results: Dict[str, Any], legacy: bool = False) -> str:
        """
        Convert ADMET results to CSV string.
        
        Uses vertical format: Property,Value,Percentile
        
        Args:
            results: ADMET prediction results dict
            legacy: Whether to use legacy format (ignored)
            
        Returns:
            CSV-formatted string
        """
        lines = ["Property,Value,Percentile"]
        exclude_keys = {"_engine", "_source", "error", "svg_raw"}
        
        for key, value in results.items():
            if key in exclude_keys or value is None:
                continue
            if "_percentile" in key:
                continue
                
            percentile_key = f"{key}_drugbank_approved_percentile"
            percentile = results.get(percentile_key, "")
            
            if isinstance(value, float):
                val_str = f"{value:.4f}"
            else:
                val_str = str(value).replace(',', ';')
            
            lines.append(f"{key},{val_str},{percentile}")
        
        return '\n'.join(lines)
    
    def summarize_findings(self, admet_data: Dict[str, Any]) -> str:
        """
        Generate clinical summary of ADMET results.
        
        Supports both:
        - Nested format (ADMETlab API): {"absorption": {"caco2": {...}}}
        - Flat format (ADMET-AI local): {"molecular_weight": 46.07, "PAINS_alert": 0}
        
        Args:
            admet_data: Full ADMET prediction results
            
        Returns:
            Markdown summary string
        """
        summary_parts = []
        
        # Get engine info
        engine = admet_data.get("_engine", "Unknown")
        source = admet_data.get("_source", "unknown")
        
        # Engine badge
        summary_parts.append(f"**Engine**: {engine}\n")
        
        # Check for errors
        if admet_data.get("error"):
            summary_parts.append(f"\n### ⚠️ Service Notice\n")
            summary_parts.append(f"- {admet_data['error']}")
            summary_parts.append("")
        
        # Check if flat format (ADMET-AI local engine)
        is_flat_format = "molecular_weight" in admet_data or "logP" in admet_data
        
        # Check for red flags
        red_flags = []
        
        if is_flat_format:
            # Flat format - ADMET-AI local engine
            # Lipinski violations
            if 'Lipinski' in admet_data:
                lipinski = admet_data['Lipinski']
                violations = 4 - lipinski if isinstance(lipinski, (int, float)) else 0
                if violations > 0:
                    red_flags.append(f"Lipinski violations: {int(violations)}")
            
            # PAINS alerts
            if 'PAINS_alert' in admet_data:
                pains = admet_data['PAINS_alert']
                if isinstance(pains, (int, float)) and pains > 0:
                    red_flags.append(f"⚠️ PAINS alert detected ({int(pains)} substructures)")
            
            # BRENK alerts
            if 'BRENK_alert' in admet_data:
                brenk = admet_data['BRENK_alert']
                if isinstance(brenk, (int, float)) and brenk > 0:
                    red_flags.append(f"⚠️ BRENK alert detected ({int(brenk)} substructures)")
            
            # Toxicity predictions ( Ames test)
            if 'AMES' in admet_data:
                ames = admet_data['AMES']
                if isinstance(ames, (int, float)) and ames > 0.5:
                    red_flags.append("⚠️ AMES mutagenicity positive")
            
            # hERG cardiotoxicity
            if 'hERG' in admet_data:
                herg = admet_data['hERG']
                if isinstance(herg, (int, float)) and herg > 0.5:
                    red_flags.append("⚠️ hERG liability (potential cardiotoxicity)")
            
            # DILI (Drug-Induced Liver Injury)
            if 'DILI' in admet_data:
                dili = admet_data['DILI']
                if isinstance(dili, (int, float)) and dili > 0.5:
                    red_flags.append("⚠️ Potential DILI concern")
            
            # Bioavailability
            if 'Bioavailability_Ma' in admet_data:
                bioav = admet_data['Bioavailability_Ma']
                if isinstance(bioav, (int, float)) and bioav < 0.3:
                    red_flags.append("⚠️ Low oral bioavailability predicted")
        
        else:
            # Nested format - ADMETlab API
            # Lipinski Rule of 5
            if 'lipinski' in admet_data:
                lipinski = admet_data['lipinski']
                violations = lipinski.get('violations', 0)
                if violations > 0:
                    red_flags.append(f"Lipinski violations: {violations}")
            
            # PAINS
            if 'pains' in admet_data:
                pains = admet_data['pains']
                if pains.get('has_pains', False):
                    red_flags.append("Contains PAINS substructure")
            
            # Toxicity
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
            summary_parts.append("\n### ⚠️ Red Flags\n")
            for flag in red_flags:
                summary_parts.append(f"- {flag}")
            summary_parts.append("")
        
        # Drug-likeness score (QED)
        if is_flat_format:
            if 'QED' in admet_data:
                qed = admet_data['QED']
                if isinstance(qed, (int, float)):
                    qed_label = "Good" if qed > 0.6 else "Moderate" if qed > 0.3 else "Poor"
                    summary_parts.append(f"**Drug-likeness (QED)**: {qed:.3f} ({qed_label})\n")
        else:
            if 'drug_likeness' in admet_data:
                score = admet_data['drug_likeness'].get('score', 'N/A')
                summary_parts.append(f"**Drug-likeness Score**: {score}\n")
        
        # Key Properties section
        summary_parts.append("### Key Properties\n")
        
        if is_flat_format:
            # Flat format - show key properties
            key_props = [
                ("Molecular Weight", "molecular_weight", "Da"),
                ("LogP", "logP", ""),
                ("TPSA", "tpsa", "Å²"),
                ("H-Bond Donors", "hydrogen_bond_donors", ""),
                ("H-Bond Acceptors", "hydrogen_bond_acceptors", ""),
                ("Caco-2 Permeability", "Caco2_Wang", "log cm/s"),
                ("HIA (Absorption)", "HIA_Hou", ""),
                ("BBB Penetration", "BBB_Martins", ""),
                ("Clearance (Hepatic)", "Clearance_Hepatocyte_AZ", "L/h/kg"),
            ]
            
            for label, key, unit in key_props:
                if key in admet_data:
                    val = admet_data[key]
                    if val is not None:
                        if isinstance(val, float):
                            summary_parts.append(f"- **{label}**: {val:.3f} {unit}")
                        else:
                            summary_parts.append(f"- **{label}**: {val} {unit}")
        else:
            # Nested format
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
    
    def format_report(self, admet_data: Dict[str, Any], svg: str = None, ai_interpretation: str = None) -> str:
        """
        Generate complete markdown report.
        
        Supports both:
        - Nested format (ADMETlab API): {"absorption": {"caco2": {...}}}
        - Flat format (ADMET-AI local): {"molecular_weight": 46.07, "logP": -0.001}
        
        Args:
            admet_data: Full ADMET prediction results
            svg: Optional molecule structure SVG
            ai_interpretation: Optional AI-generated interpretation
            
        Returns:
            Complete markdown report
        """
        parts = []
        
        # Title
        parts.append("## ADMET Analysis Report\n")
        
        # Key Insights section - includes AI interpretation prominently
        if ai_interpretation:
            # Clean up the AI interpretation: remove excessive asterisks and normalized spacing
            cleaned_ai = ai_interpretation.replace('**', '')
            cleaned_ai = re.sub(r'\n{3,}', '\n\n', cleaned_ai).strip()
            
            parts.append("## Medicinal Chemistry Insights\n")
            parts.append(f"{cleaned_ai}\n")
        
        # Clinical summary (red flags, QED, etc.)
        summary = self.summarize_findings(admet_data)
        parts.append(summary)
        
        # Detailed results
        parts.append("\n## Detailed Results\n")
        
        # Metadata keys to exclude
        exclude_keys = {"_engine", "_source", "error", "ai_interpretation", "molecule_name"}
        
        # Check if flat format (ADMET-AI local engine)
        is_flat_format = "molecular_weight" in admet_data
        
        if is_flat_format:
            # Flat format - organize by property groups
            for group_name, keys in self.property_groups.items():
                group_data = {}
                for key in keys:
                    if key in admet_data:
                        val = admet_data[key]
                        if val is not None:
                            group_data[key] = val
                
                if group_data:
                    parts.append(f"\n### {group_name}\n")
                    for endpoint, value in group_data.items():
                        label = self.header_labels.get(endpoint, endpoint.replace('_', ' ').title())
                        interp = self.get_interpretation(endpoint, value)
                        if isinstance(value, float):
                            line = f"- **{label}**: {value:.4f}"
                        else:
                            line = f"- **{label}**: {value}"
                        if interp:
                            line += f" {interp}"
                        parts.append(line)
        else:
            # Nested format - ADMETlab API
            for category, data in admet_data.items():
                if category in exclude_keys:
                    continue
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

    def get_interpretation(self, endpoint: str, value: Any) -> str:
        """
        Map endpoint value to clinical interpretation with status symbol.
        
        Uses DIRECTIONAL scoring:
        - RISK_ENDPOINTS: Lower values = green (good), Higher = red (bad)
        - BENEFIT_ENDPOINTS: Higher values = green (good), Lower = red (bad)
        - PHYSICOCHEMICAL: Neutral - return empty string
        
        Args:
            endpoint: The ADMET endpoint name
            value: The predicted value
            
        Returns:
            Interpretation string with emoji symbol (✅, ⚠️, ❌)
        """
        if value is None:
            return ""
        
        # Convert to float for comparison
        try:
            val = float(value)
        except (TypeError, ValueError):
            return ""
        
        # === DIRECTIONAL CLASSIFICATION ===
        
        # RISK endpoints: Lower is better (low risk = green)
        RISK_ENDPOINTS = {
            "hERG", "AMES", "DILI", "ClinTox", "Carcinogens_Lagunin", "Skin_Reaction",
            "CYP1A2_Veith", "CYP2C9_Veith", "CYP2C19_Veith", "CYP2D6_Veith", "CYP3A4_Veith",
            "CYP2C9_Substrate_CarbonMangels", "CYP2D6_Substrate_CarbonMangels",
            "CYP3A4_Substrate_CarbonMangels", "Pgp_Broccatelli",
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
            "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53",
        }
        
        # BENEFIT endpoints: Higher is better
        BENEFIT_ENDPOINTS = {
            "HIA_Hou", "Bioavailability_Ma", "BBB_Martins", "PAMPA_NCATS",
            "Lipinski", "QED"
        }
        
        # PHYSICOCHEMICAL endpoints: Neutral - return empty
        NEUTRAL_ENDPOINTS = {
            "molecular_weight", "logP", "hydrogen_bond_acceptors", "hydrogen_bond_donors",
            "tpsa", "stereo_centers", "num_rotatable_bonds", "num_rings", "num_heavy_atoms",
            "PPBR_AZ", "VDss_Lombardo", "Half_Life_Obach", "Clearance_Hepatocyte_AZ",
            "Clearance_Microsome_AZ", "LD50_Zhu", "Solubility_AqSolDB", "Lipophilicity_AstraZeneca",
            "HydrationFreeEnergy_FreeSolv"
        }
        
        # Structural alerts - special handling
        ALERT_ENDPOINTS = {"PAINS_alert", "BRENK_alert", "NIH_alert"}
        
        # === APPLY DIRECTIONAL LOGIC ===
        
        # Neutral physicochemical properties
        if endpoint in NEUTRAL_ENDPOINTS:
            return ""
        
        # RISK endpoints: <0.3 = green, 0.3-0.7 = yellow, >=0.7 = red
        if endpoint in RISK_ENDPOINTS:
            if val < 0.3:
                return f"✅ {self._get_risk_message(endpoint, val)}"
            elif val < 0.7:
                return f"⚠️ {self._get_risk_message(endpoint, val)}"
            else:
                return f"❌ {self._get_risk_message(endpoint, val)}"
        
        # BENEFIT endpoints: >=0.7 = green, 0.3-0.7 = yellow, <0.3 = red
        if endpoint in BENEFIT_ENDPOINTS:
            if val >= 0.7:
                return f"✅ {self._get_benefit_message(endpoint, val)}"
            elif val >= 0.3:
                return f"⚠️ {self._get_benefit_message(endpoint, val)}"
            else:
                return f"❌ {self._get_benefit_message(endpoint, val)}"
        
        # Structural alerts
        if endpoint in ALERT_ENDPOINTS:
            if val == 0:
                return f"✅ No {endpoint.replace('_alert', '')} alerts"
            elif val == 1:
                return f"⚠️ 1 {endpoint.replace('_alert', '')} alert"
            else:
                return f"❌ {int(val)} {endpoint.replace('_alert', '')} alerts"
        
        # Special thresholds for specific endpoints
        if endpoint == "Caco2_Wang":
            # Caco-2: Higher (less negative) = better permeability
            if val >= -4:
                return "✅ High permeability"
            elif val >= -6:
                return "⚠️ Moderate permeability"
            else:
                return "❌ Poor permeability"
        
        if endpoint == "Solubility_AqSolDB":
            # Solubility: Higher (less negative) = better
            if val >= -2:
                return "✅ Good aqueous solubility"
            elif val >= -4:
                return "⚠️ Moderate solubility"
            else:
                return "❌ Poor solubility"
        
        if endpoint == "Lipinski":
            # Lipinski: Higher = more violations (worse), but we store pass count
            if val >= 3:
                return "✅ Passes Lipinski rule"
            elif val >= 2:
                return "⚠️ 1 Lipinski violation"
            else:
                return "❌ Multiple Lipinski violations"
        
        return ""
    
    def _get_risk_message(self, endpoint: str, val: float) -> str:
        """Get risk message for endpoint"""
        messages = {
            "hERG": "Low hERG liability" if val < 0.3 else ("Moderate hERG concern" if val < 0.7 else "High hERG liability - cardiac risk"),
            "AMES": "Non-mutagenic" if val < 0.3 else ("Ambiguous" if val < 0.7 else "Mutagenic"),
            "DILI": "Low DILI concern" if val < 0.3 else ("Moderate DILI concern" if val < 0.7 else "High DILI concern"),
            "ClinTox": "Clinically non-toxic" if val < 0.3 else ("Moderate clinical toxicity" if val < 0.7 else "Clinically toxic"),
            "Skin_Reaction": "Low skin sensitization" if val < 0.3 else ("Moderate skin sensitization" if val < 0.7 else "High skin sensitization"),
            "Pgp_Broccatelli": "Not P-gp inhibitor" if val < 0.3 else ("Moderate P-gp inhibition" if val < 0.7 else "Strong P-gp inhibitor"),
        }
        # Generic message for other endpoints
        if endpoint in messages:
            return messages[endpoint]
        return f"{endpoint.replace('_', ' ').title()} risk: {val:.2f}"
    
    def _get_benefit_message(self, endpoint: str, val: float) -> str:
        """Get benefit message for endpoint"""
        messages = {
            "HIA_Hou": "High intestinal absorption",
            "Bioavailability_Ma": "Good oral bioavailability",
            "BBB_Martins": "Crosses BBB",
            "PAMPA_NCATS": "High PAMPA permeability",
            "QED": "Good drug-likeness" if val >= 0.7 else "Moderate drug-likeness",
        }
        if endpoint in messages:
            return messages[endpoint]
        return f"{endpoint.replace('_', ' ').title()}: {val:.2f}"

    def build_structured_categories(self, admet_data: Dict[str, Any]) -> list:
        """
        Build structured JSON categories from raw ADMET prediction dict.
        Returns list of {name, properties: [{name, key, value, unit, percentile, status, interpretation}]}
        """
        categories = []
        for group_name, keys in self.property_groups.items():
            props = []
            for key in keys:
                if key in admet_data and admet_data[key] is not None:
                    val = admet_data[key]
                    label = self.header_labels.get(key, key.replace('_', ' ').title())
                    interp = self.get_interpretation(key, val)
                    
                    # Determine status from interpretation emoji
                    status = "neutral"
                    if "✅" in interp: status = "success"
                    elif "⚠️" in interp: status = "warning"
                    elif "❌" in interp: status = "danger"
                    
                    # Get percentile if available
                    percentile_key = f"{key}_drugbank_approved_percentile"
                    percentile = admet_data.get(percentile_key)
                    
                    props.append({
                        "name": label,
                        "key": key,
                        "value": round(val, 4) if isinstance(val, float) else val,
                        "percentile": round(percentile, 2) if percentile else None,
                        "status": status,
                        "interpretation": interp.replace("✅ ", "").replace("⚠️ ", "").replace("❌ ", ""),
                    })
            
            if props:
                categories.append({"name": group_name, "properties": props})
        
        return categories

    def format_batch_csv(self, results: list) -> str:
        """
        Format batch results as CSV.
        One row per molecule, columns = all unique property keys.
        """
        if not results:
            return "No results"
        
        # Collect all unique property keys across all molecules
        all_keys = []
        for r in results:
            if r.get("success") and r.get("categories"):
                for cat in r["categories"]:
                    for prop in cat["properties"]:
                        if prop["key"] not in all_keys:
                            all_keys.append(prop["key"])
        
        # Header
        headers = ["#", "SMILES", "Name", "Engine"] + [
            self.header_labels.get(k, k) for k in all_keys
        ]
        lines = [",".join(headers)]
        
        # Rows
        for r in results:
            if not r.get("success"):
                row = [str(r["index"]), r["smiles"], r.get("molecule_name", ""), "FAILED"]
                row += [""] * len(all_keys)
                lines.append(",".join(row))
                continue
            
            # Build lookup from categories
            prop_lookup = {}
            for cat in r.get("categories", []):
                for prop in cat["properties"]:
                    prop_lookup[prop["key"]] = prop["value"]
            
            row = [str(r["index"]), r["smiles"], r.get("molecule_name", ""), r.get("engine", "")]
            for key in all_keys:
                val = prop_lookup.get(key, "")
                row.append(str(val) if val != "" else "")
            
            lines.append(",".join(row))
        
        return "\n".join(lines)


# Singleton instance
admet_processor = ADMETProcessor()
