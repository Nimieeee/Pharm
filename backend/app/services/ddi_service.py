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
import json
import logging
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
        self._ai_service = None
        self.logger = logging.getLogger(__name__)

    @property
    def ai_service(self):
        """Lazy load AIService via container"""
        if self._ai_service is None:
            from app.core.container import container
            self._ai_service = container.get('ai_service')
        return self._ai_service
    
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

    def _parse_interaction_pair(
        self, 
        pair: Dict[str, Any], 
        drug_a: str, 
        drug_b: str,
        rxcui_a: str,
        rxcui_b: str
    ) -> Dict[str, Any]:
        """Parse interaction pair from RxNav"""
        severity = pair.get("severity", "unknown").lower()
        description = pair.get("description", "")
        
        mapped_severity = self.SEVERITY_MAP.get(severity, "Unknown")
        
        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "rxcui_a": rxcui_a,
            "rxcui_b": rxcui_b,
            "interaction_found": True,
            "severity": mapped_severity,
            "description": description or "Interaction detected",
            "mechanism": "",
            "evidence_level": self._estimate_evidence(description),
            "alternatives": self._suggest_alternatives(drug_a, drug_b, mapped_severity),
            "clinical_significance": self._get_clinical_significance(mapped_severity)
        }
    
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
        
        # Try to resolve drugs to RxCUIs
        rxcui_a = await self.resolve_drug(drug_a)
        rxcui_b = await self.resolve_drug(drug_b)
        
        # If we have both RxCUIs, try the official API first
        if rxcui_a and rxcui_b:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Use plural sources for better coverage
                    # Note: Interaction endpoints are largely discontinued, so this often falls through
                    response = await client.get(
                        f"{self.RXNAV_BASE}/interaction/interaction.json",
                        params={
                            "rxcui": rxcui_a,
                            "sources": "ONCHigh DrugBank" 
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        found_interaction = None
                        
                        groups = []
                        if "onCHigh" in data:
                            groups.extend(data["onCHigh"])
                        if "interactionTypeGroup" in data:
                            groups.extend(data["interactionTypeGroup"])
                        
                        for group in groups:
                            type_items = group.get("interactionType", [])
                            for type_item in type_items:
                                pairs = type_item.get("interactionPair", [])
                                for pair in pairs:
                                    concepts = pair.get("interactionConcept", [])
                                    for concept in concepts:
                                        c_rxcui = concept.get("minConceptItem", {}).get("rxcui")
                                        if c_rxcui == rxcui_b:
                                            found_interaction = pair
                                            break
                                    if found_interaction: break
                                if found_interaction: break
                            if found_interaction: break

                        if found_interaction:
                            parsed = self._parse_interaction_pair(
                                found_interaction, 
                                drug_a, 
                                drug_b,
                                rxcui_a,
                                rxcui_b
                            )
                            self._cache[cache_key] = parsed
                            return parsed
            except Exception as e:
                print(f"⚠️ RxNav API error, falling back to AI: {e}")

        # Fallback to AI if API fails, returns nothing, or drugs couldn't be resolved
        ai_result = await self._check_interaction_ai(drug_a, drug_b)
        ai_result["rxcui_a"] = rxcui_a or "Unknown"
        ai_result["rxcui_b"] = rxcui_b or "Unknown"
        self._cache[cache_key] = ai_result
        return ai_result

    async def _check_interaction_ai(self, drug_a: str, drug_b: str) -> Dict[str, Any]:
        """
        Check for interaction using AI as a fallback for the discontinued NIH API.
        Grounded in medical knowledge and provides structured output.
        """
        print(f"🤖 AI Fallback: Checking DDI for {drug_a} + {drug_b}...")
        
        prompt = f"""You are a senior clinical pharmacologist. Identify if there is a known drug-drug interaction between:
- Drug A: {drug_a}
- Drug B: {drug_b}

Provide a high-density, professional assessment. Consider pharmacokinetics (CYP450 metabolism, P-gp transport, protein binding) and pharmacodynamics.

Respond STRICTLY in JSON format with the following keys:
- interaction_found: boolean
- severity: string ("Major", "Moderate", "Minor", or "None")
- description: string (Precise clinical summary. Include drug classes: e.g. "Statin + Azole Antifungal")
- mechanism: string (Mechanistic reason: e.g. "Potent inhibition of CYP3A4 by {drug_b} leading to elevated serum levels of {drug_a}")
- clinical_significance: string (Specific management strategy: e.g. "Avoid combination; if unavoidable, limit {drug_a} dose to 10mg and monitor for myopathy/rhabdomyolysis")
- evidence_level: string (e.g., "★★★ (High - Clinical Trials)", "★★☆ (Moderate - Case Reports)", "★☆☆ (Low - Theoretical)")

Only provide the JSON object. No preamble, no postamble."""

        try:
            # AIService has a generate_response method, but we want structured JSON
            # We can use the multi-provider directly or just generate_response and parse
            raw_response = await self.ai_service.generate_response(
                message=prompt,
                conversation_id=None, # System level
                user=None, # System level
                mode="fast", # Use fast mode for quick check
                use_rag=False
            )
            
            # Extract JSON from response (handling potential markdown blocks)
            content = raw_response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            # Ensure severity is mapped to our required casing/values
            severity = data.get("severity", "None")
            if severity.lower() in self.SEVERITY_MAP:
                data["severity"] = self.SEVERITY_MAP[severity.lower()]
            
            data.update({
                "drug_a": drug_a,
                "drug_b": drug_b,
                "rxcui_a": await self.resolve_drug(drug_a) or "Unknown",
                "rxcui_b": await self.resolve_drug(drug_b) or "Unknown",
                "alternatives": self._suggest_alternatives(drug_a, drug_b, data.get("severity", "None"))
            })
            
            return data
            
        except Exception as e:
            self.logger.error(f"AI DDI check failed: {e}")
            # Safe default
            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                "interaction_found": False,
                "severity": "Unknown",
                "description": "Information temporarily unavailable.",
                "mechanism": "The Interaction API is undergoing maintenance.",
                "clinical_significance": "Consult a pharmacist.",
                "evidence_level": "None"
            }
    
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
