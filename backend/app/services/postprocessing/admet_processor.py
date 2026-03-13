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
    
    def format_csv_export(self, results: Dict[str, Any], legacy: bool = True) -> str:
        """
        Convert ADMET results to CSV string.
        
        Supports:
        - Legacy format (ADMETlab 3.0 horizontal): 119+ columns
        - Standard format (Vertical): Property,Value,Percentile
        
        Args:
            results: ADMET prediction results dict
            legacy: Whether to use the ADMETlab 3.0 horizontal format
            
        Returns:
            CSV-formatted string
        """
        if not legacy:
            # Vertical format implementation
            lines = ["Property,Value,Percentile"]
            exclude_keys = {"_engine", "_source", "error", "smiles"}
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

        # ADMETlab 3.0 Horizontal Format Header
        headers = [
            "raw_smiles","smiles","MW","Vol","Dense","nHA","nHD","TPSA","nRot","nRing",
            "MaxRing","nHet","fChar","nRig","Flex","nStereo","gasa","QED","Synth","Fsp3",
            "MCE-18","Natural Product-likeness","Alarm_NMR","BMS","Chelating","PAINS","Lipinski",
            "Pfizer","GSK","GoldenTriangle","logS","logD","logP","mp","bp","pka_acidic","pka_basic",
            "caco2","MDCK","PAMPA","pgp_inh","pgp_sub","hia","f20","f30","f50","OATP1B1",
            "OATP1B3","BCRP","BSEP","BBB","MRP1","PPB","logVDss","Fu","CYP1A2-inh","CYP1A2-sub",
            "CYP2C19-inh","CYP2C19-sub","CYP2C9-inh","CYP2C9-sub","CYP2D6-inh","CYP2D6-sub",
            "CYP3A4-inh","CYP3A4-sub","CYP2B6-inh","CYP2B6-sub","CYP2C8-inh","LM-human","cl-plasma",
            "t0.5","BCF","IGC50","LC50DM","LC50FM","hERG","hERG-10um","DILI","Ames","ROA","FDAMDD",
            "SkinSen","Carcinogenicity","EC","EI","Respiratory","H-HT","Neurotoxicity-DI","Ototoxicity",
            "Hematotoxicity","Nephrotoxicity-DI","Genotoxicity","RPMI-8226","A549","HEK293","NR-AhR",
            "NR-AR","NR-AR-LBD","NR-Aromatase","NR-ER","NR-ER-LBD","NR-PPAR-gamma","SR-ARE","SR-ATAD5",
            "SR-HSE","SR-MMP","SR-p53","molstr","NonBiodegradable","NonGenotoxic_Carcinogenicity",
            "SureChEMBL","LD50_oral","Skin_Sensitization","Acute_Aquatic_Toxicity","FAF-Drugs4 Rule",
            "Genotoxic_Carcinogenicity_Mutagenicity","Aggregators","Fluc","Blue_fluorescence",
            "Green_fluorescence","Reactive","Other_assay_interference","Promiscuous"
        ]

        # Key Mapping (Internal Key -> ADMETlab Header)
        mapping = {
            "molecular_weight": "MW",
            "hydrogen_bond_acceptors": "nHA",
            "hydrogen_bond_donors": "nHD",
            "tpsa": "TPSA",
            "num_rotatable_bonds": "nRot",
            "num_rings": "nRing",
            "stereo_centers": "nStereo",
            "QED": "QED",
            "PAINS_alert": "PAINS",
            "Lipinski": "Lipinski",
            "logP": "logP",
            "Caco2_Wang": "caco2",
            "PAMPA_NCATS": "PAMPA",
            "HIA_Hou": "hia",
            "BBB_Martins": "BBB",
            "PPBR_AZ": "PPB",
            "VDss_Lombardo": "logVDss",
            "CYP1A2_Veith": "CYP1A2-inh",
            "CYP2C19_Veith": "CYP2C19-inh",
            "CYP2C9_Veith": "CYP2C9-inh",
            "CYP2C9_Substrate_CarbonMangels": "CYP2C9-sub",
            "CYP2D6_Veith": "CYP2D6-inh",
            "CYP2D6_Substrate_CarbonMangels": "CYP2D6-sub",
            "CYP3A4_Veith": "CYP3A4-inh",
            "CYP3A4_Substrate_CarbonMangels": "CYP3A4-sub",
            "Clearance_Hepatocyte_AZ": "cl-plasma",
            "Half_Life_Obach": "t0.5",
            "hERG": "hERG",
            "DILI": "DILI",
            "AMES": "Ames",
            "NR-AR": "NR-AR",
            "NR-AR-LBD": "NR-AR-LBD",
            "NR-AhR": "NR-AhR",
            "NR-Aromatase": "NR-Aromatase",
            "NR-ER": "NR-ER",
            "NR-ER-LBD": "NR-ER-LBD",
            "NR-PPAR-gamma": "NR-PPAR-gamma",
            "SR-ARE": "SR-ARE",
            "SR-ATAD5": "SR-ATAD5",
            "SR-HSE": "SR-HSE",
            "SR-MMP": "SR-MMP",
            "SR-p53": "SR-p53",
            "Skin_Reaction": "SkinSen",
            "LD50_Zhu": "LD50_oral",
            "Solubility_AqSolDB": "logS"
        }

        # Value lookup table
        column_to_key = {v: k for k, v in mapping.items()}
        smiles = results.get("smiles", "")
        
        row_values = []
        for header in headers:
            if header == "raw_smiles":
                row_values.append(smiles)
            elif header == "smiles":
                row_values.append(smiles)
            elif header in column_to_key:
                val = results.get(column_to_key[header], "")
                if isinstance(val, (int, float)):
                    row_values.append(f"{val:.4f}")
                else:
                    # Clean up strings but keep precision for floats
                    row_values.append(str(val).replace(",", ";"))
            else:
                row_values.append("")
        
        return ",".join(headers) + "\n" + ",".join(row_values)
    
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
    
    def format_report(self, admet_data: Dict[str, Any], svg: str = None) -> str:
        """
        Generate complete markdown report.
        
        Supports both:
        - Nested format (ADMETlab API): {"absorption": {"caco2": {...}}}
        - Flat format (ADMET-AI local): {"molecular_weight": 46.07, "logP": -0.001}
        
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
        
        # Metadata keys to exclude
        exclude_keys = {"_engine", "_source", "error"}
        
        # Check if flat format (ADMET-AI local engine)
        is_flat_format = "molecular_weight" in admet_data
        
        if is_flat_format:
            # Flat format - organize by property groups
            property_groups = {
                "Physicochemical": ["molecular_weight", "logP", "hydrogen_bond_donors", 
                                   "hydrogen_bond_acceptors", "tpsa", "num_rotatable_bonds", 
                                   "num_rings", "num_heavy_atoms", "stereo_centers"],
                "Drug Likeness": ["Lipinski", "QED", "PAINS_alert", "BRENK_alert", "NIH_alert"],
                "Absorption": ["HIA_Hou", "Caco2_Wang", "PAMPA_NCATS", "Pgp_Broccatelli"],
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
                "Solubility": ["Solubility_AqSolDB", "HydrationFreeEnergy_FreeSolv", 
                             "Lipophilicity_AstraZeneca"]
            }
            
            for group_name, keys in property_groups.items():
                group_data = {}
                for key in keys:
                    if key in admet_data:
                        val = admet_data[key]
                        if val is not None:
                            group_data[key] = val
                
                if group_data:
                    parts.append(f"\n### {group_name}\n")
                    for endpoint, value in group_data.items():
                        if isinstance(value, float):
                            parts.append(f"- **{endpoint.replace('_', ' ').title()}**: {value:.4f}")
                        else:
                            parts.append(f"- **{endpoint.replace('_', ' ').title()}**: {value}")
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
        
        # Define thresholds for different endpoints
        thresholds = {
            # Drug Likeness (higher is better)
            "QED": [(0.6, "Good drug-likeness", "✅"), (0.3, "Moderate drug-likeness", "⚠️"), (0, "Poor drug-likeness", "❌")],
            "Lipinski": [(3, "Passes Lipinski rule", "✅"), (2, "1 Lipinski violation", "⚠️"), (0, "Multiple Lipinski violations", "❌")],
            
            # Absorption (higher is generally better for permeability)
            "HIA_Hou": [(0.9, "High intestinal absorption", "✅"), (0.5, "Moderate absorption", "⚠️"), (0, "Poor absorption", "❌")],
            "Caco2_Wang": [(-4, "High permeability", "✅"), (-6, "Moderate permeability", "⚠️"), (-8, "Poor permeability", "❌")],
            "PAMPA_NCATS": [(0.9, "High PAMPA permeability", "✅"), (0.5, "Moderate permeability", "⚠️"), (0, "Poor permeability", "❌")],
            
            # Distribution (BBB - higher is better for brain penetration)
            "BBB_Martins": [(0.7, "Crosses BBB", "✅"), (0.3, "Limited BBB penetration", "⚠️"), (0, "Does not cross BBB", "❌")],
            
            # Toxicity (lower is better)
            "hERG": [(0.3, "Low hERG liability", "✅"), (0.6, "Moderate hERG concern", "⚠️"), (1.0, "High hERG liability - cardiac risk", "❌")],
            "AMES": [(0.3, "Non-mutagenic (Ames negative)", "✅"), (0.6, "Ambiguous", "⚠️"), (1.0, "Mutagenic (Ames positive)", "❌")],
            "DILI": [(0.3, "Low DILI concern", "✅"), (0.6, "Moderate DILI concern", "⚠️"), (1.0, "High DILI concern", "❌")],
            "ClinTox": [(0.3, "Clinically non-toxic", "✅"), (0.6, "Moderate clinical toxicity", "⚠️"), (1.0, "Clinically toxic", "❌")],
            
            # Structural alerts (lower is better)
            "PAINS_alert": [(0, "No PAINS alerts", "✅"), (1, "1 PAINS alert - potential assay interference", "⚠️"), (2, "Multiple PAINS alerts", "❌")],
            "BRENK_alert": [(0, "No BRENK alerts", "✅"), (1, "1 BRENK alert", "⚠️"), (2, "Multiple BRENK alerts", "❌")],
            
            # Solubility (higher is better)
            "Solubility_AqSolDB": [(-2, "Good aqueous solubility", "✅"), (-4, "Moderate solubility", "⚠️"), (-6, "Poor solubility", "❌")],
            
            # Bioavailability
            "Bioavailability_Ma": [(0.5, "Good oral bioavailability", "✅"), (0.3, "Moderate bioavailability", "⚠️"), (0, "Low oral bioavailability", "❌")],
        }
        
        # Check if endpoint has thresholds defined
        if endpoint in thresholds:
            for threshold, message, symbol in thresholds[endpoint]:
                if val >= threshold:
                    return f"{symbol} {message}"
        
        return ""


# Singleton instance
admet_processor = ADMETProcessor()
