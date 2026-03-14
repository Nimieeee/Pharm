"""
Drug-Drug Interaction (DDI) Engine

Checks for interactions between drugs using NLM RxNorm and RxNav APIs.
All APIs are free and require no API key.

API Documentation:
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/docs/
- RxNav: https://nmctest.nlm.nih.gov/RxNav/
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class DDIService:
    """
    Drug-Drug Interaction checking service.
    
    Features:
    - Drug name to RxCUI resolution via RxNorm
    - Interaction checking via RxNav API
    - Severity classification (Major, Moderate, Minor)
    - Polypharmacy checking (multiple drugs)
    - Free NLM APIs - no key required
    """
    
    RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"
    
    # Severity mapping from RxNorm interaction types
    SEVERITY_MAP = {
        "major": "Major",
        "moderate": "Moderate",
        "minor": "Minor",
        "unknown": "Unknown",
        "contraindicated": "Major",
        "serious": "Major",
        "significant": "Moderate",
    }
    
    def __init__(self):
        """Initialize DDIService"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._rxcui_cache: Dict[str, str] = {}
    
    async def resolve_drug(self, drug_name: str) -> Optional[str]:
        """
        Resolve drug name to RxCUI identifier.
        
        Args:
            drug_name: Drug name (brand or generic)
            
        Returns:
            RxCUI string or None if not found
        """
        # Check cache first
        name_lower = drug_name.lower().strip()
        if name_lower in self._rxcui_cache:
            return self._rxcui_cache[name_lower]
        
        # Hardcoded common mappings for broad terms
        common_mappings = {
            "calcium": "1901",
            "aspirin": "1191",
            "warfarin": "11289",
            "simvastatin": "36567",
            "ketoconazole": "6135",
            "methotrexate": "6809",
            "tetracycline": "10395",
            "ibuprofen": "5640",
            "acetaminophen": "161",
            "naproxen": "7258",
            "insulin": "5856"
        }
        
        if name_lower in common_mappings:
            rxcui = common_mappings[name_lower]
            self._rxcui_cache[name_lower] = rxcui
            return rxcui
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for drug by name
                response = await client.get(
                    f"{self.RXNAV_BASE}/rxcui.json",
                    params={
                        "name": drug_name,
                        "search": "1"  # Fuzzy search
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    id_group = data.get("idGroup", {})
                    
                    # Try rxnormId first
                    rxnorm_ids = id_group.get("rxnormId", [])
                    if rxnorm_ids:
                        rxcui = str(rxnorm_ids[0])
                        self._rxcui_cache[drug_name.lower()] = rxcui
                        return rxcui
                    
                    # Try drugbank ID as fallback
                    drugbank_ids = id_group.get("drugbankId", [])
                    if drugbank_ids:
                        # We need to convert drugbank to rxcui
                        pass
                        
                return None
                
        except Exception as e:
            print(f"❌ RxNorm drug resolution failed for '{drug_name}': {e}")
            return None
    
    async def check_interaction(
        self, 
        drug_a: str, 
        drug_b: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check for interaction between two drugs.
        
        Args:
            drug_a: First drug name
            drug_b: Second drug name
            
        Returns:
            Dict with interaction details or None if no interaction
        """
        # Check cache
        cache_key = f"ddi:{drug_a.lower()}:{drug_b.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Resolve drugs to RxCUIs
        rxcui_a = await self.resolve_drug(drug_a)
        rxcui_b = await self.resolve_drug(drug_b)
        
        if not rxcui_a or not rxcui_b:
            # Try to check with partial resolution
            if not rxcui_a:
                print(f"⚠️ Could not resolve drug: {drug_a}")
            if not rxcui_b:
                print(f"⚠️ Could not resolve drug: {drug_b}")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check for interactions
                response = await client.get(
                    f"{self.RXNAV_BASE}/interaction/list.json",
                    params={
                        "rxcuis": f"{rxcui_a}+{rxcui_b}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    interaction_group = data.get("interactionTypeGroup", [])
                    
                    if interaction_group:
                        interaction = self._parse_interaction(
                            interaction_group, 
                            drug_a, 
                            drug_b,
                            rxcui_a,
                            rxcui_b
                        )
                        self._cache[cache_key] = interaction
                        return interaction
                    else:
                        # No interaction found
                        result = {
                            "drug_a": drug_a,
                            "drug_b": drug_b,
                            "rxcui_a": rxcui_a,
                            "rxcui_b": rxcui_b,
                            "interaction_found": False,
                            "severity": "None",
                            "description": "No significant interaction found",
                            "mechanism": "",
                            "evidence_level": "N/A",
                            "alternatives": [],
                            "clinical_significance": "No known interaction"
                        }
                        self._cache[cache_key] = result
                        return result
                        
                return None
                
        except Exception as e:
            print(f"❌ DDI check failed for {drug_a} + {drug_b}: {e}")
            return None
    
    def _parse_interaction(
        self, 
        interaction_group: List[Dict], 
        drug_a: str, 
        drug_b: str,
        rxcui_a: str,
        rxcui_b: str
    ) -> Dict[str, Any]:
        """Parse RxNav interaction response"""
        # Collect all interactions
        all_interactions = []
        max_severity = "None"
        severity_order = ["None", "Minor", "Moderate", "Major", "Contraindicated"]
        
        for group in interaction_group:
            interaction_list = group.get("interactionPair", [])
            for interaction in interaction_list:
                severity = interaction.get("severity", "unknown").lower()
                description = interaction.get("description", "")
                mechanism = interaction.get("mechanism", "")
                
                all_interactions.append({
                    "severity": severity,
                    "description": description,
                    "mechanism": mechanism
                })
                
                # Track highest severity
                mapped_severity = self.SEVERITY_MAP.get(severity, "Unknown")
                if mapped_severity in severity_order:
                    if severity_order.index(mapped_severity) > severity_order.index(max_severity):
                        max_severity = mapped_severity
        
        # Combine descriptions if multiple interactions
        combined_description = " | ".join([i["description"] for i in all_interactions if i["description"]])[:500]
        combined_mechanism = " | ".join([i["mechanism"] for i in all_interactions if i["mechanism"]])[:300]
        
        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "rxcui_a": rxcui_a,
            "rxcui_b": rxcui_b,
            "interaction_found": True,
            "severity": max_severity,
            "description": combined_description or "Interaction detected",
            "mechanism": combined_mechanism,
            "evidence_level": self._estimate_evidence(combined_description),
            "alternatives": self._suggest_alternatives(drug_a, drug_b, max_severity),
            "clinical_significance": self._get_clinical_significance(max_severity),
            "interaction_count": len(all_interactions)
        }
    
    def _estimate_evidence(self, description: str) -> str:
        """Estimate evidence level from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["well-established", "confirmed", "proven"]):
            return "★★★ (High)"
        elif any(word in desc_lower for word in ["likely", "probable", "suggested"]):
            return "★★☆ (Moderate)"
        else:
            return "★☆☆ (Low)"
    
    def _get_clinical_significance(self, severity: str) -> str:
        """Get clinical significance based on severity"""
        significance_map = {
            "Major": "Avoid combination or use alternative agents. Close monitoring required.",
            "Moderate": "Monitor for adverse effects. Dose adjustments may be needed.",
            "Minor": "Minimal risk. Routine monitoring sufficient.",
            "None": "No special precautions needed.",
            "Unknown": "Insufficient data. Use clinical judgment."
        }
        return significance_map.get(severity, significance_map["Unknown"])
    
    def _suggest_alternatives(self, drug_a: str, drug_b: str, severity: str) -> List[str]:
        """Suggest alternative drugs (simplified)"""
        # This is a simplified version - in production would query drug classes
        alternatives = []
        
        if severity in ["Major", "Contraindicated"]:
            alternatives.append(f"Consider alternative to {drug_b}")
            alternatives.append("Consult pharmacist for drug class alternatives")
            alternatives.append("Review therapeutic options with similar efficacy")
        
        return alternatives
    
    async def check_polypharmacy(
        self, 
        drugs: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check all pairwise interactions for multiple drugs.
        
        Args:
            drugs: List of drug names
            
        Returns:
            List of all pairwise interactions
        """
        if len(drugs) < 2:
            return []
        
        interactions = []
        
        # Check all pairs
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                drug_a = drugs[i]
                drug_b = drugs[j]
                
                interaction = await self.check_interaction(drug_a, drug_b)
                if interaction:
                    interaction["pair"] = f"{drug_a} + {drug_b}"
                    interactions.append(interaction)
        
        # Sort by severity (most severe first)
        severity_order = {"Major": 0, "Moderate": 1, "Minor": 2, "None": 3, "Unknown": 4}
        interactions.sort(key=lambda x: severity_order.get(x.get("severity", "Unknown"), 4))
        
        return interactions
    
    def format_for_display(self, interactions: List[Dict[str, Any]]) -> str:
        """
        Format interactions for display in chat.
        
        Args:
            interactions: List of interaction dicts
            
        Returns:
            Formatted markdown string
        """
        if not interactions:
            return "No significant interactions found."
        
        # Count by severity
        major_count = sum(1 for i in interactions if i.get("severity") == "Major")
        moderate_count = sum(1 for i in interactions if i.get("severity") == "Moderate")
        minor_count = sum(1 for i in interactions if i.get("severity") == "Minor")
        
        lines = [f"## Drug Interaction Check\n"]
        
        if major_count > 0:
            lines.append(f"🔴 **{major_count} Major** interaction(s) found")
        if moderate_count > 0:
            lines.append(f"🟡 **{moderate_count} Moderate** interaction(s)")
        if minor_count > 0:
            lines.append(f"🟢 **{minor_count} Minor** interaction(s)")
        
        lines.append("")
        
        # Show most severe first
        for interaction in interactions[:5]:  # Top 5
            severity = interaction.get("severity", "Unknown")
            pair = interaction.get("pair", f"{interaction.get('drug_a')} + {interaction.get('drug_b')}")
            description = interaction.get("description", "")[:200]
            
            emoji = "🔴" if severity == "Major" else "🟡" if severity == "Moderate" else "🟢"
            
            lines.append(f"### {emoji} {pair}")
            lines.append(f"**Severity**: {severity}")
            if description:
                lines.append(f"{description}")
            lines.append(f"**Clinical Significance**: {interaction.get('clinical_significance', '')}")
            lines.append("")
        
        if len(interactions) > 5:
            lines.append(f"*...and {len(interactions) - 5} more interactions*")
        
        lines.append("\n---")
        lines.append("*Disclaimer: This information is for educational purposes only. Always consult a healthcare professional.*")
        
        return "\n".join(lines)


# Singleton instance
ddi_service = DDIService()
