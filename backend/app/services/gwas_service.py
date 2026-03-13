"""
GWAS Variant Lookup Service

Queries multiple genetic databases for variant-trait associations.
All APIs are free and require no API key.

APIs Used:
- Ensembl REST API: https://rest.ensembl.org/
- GWAS Catalog: https://www.ebi.ac.uk/gwas/rest/api
- Open Targets: https://api.platform.opentargets.org/
- ClinVar: https://www.ncbi.nlm.nih.gov/clinvar/

"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class GWASService:
    """
    GWAS variant lookup service.
    
    Features:
    - Multi-database querying (Ensembl, GWAS Catalog, Open Targets)
    - Variant annotation (consequence, frequency, clinical significance)
    - Trait/disease associations
    - eQTL data from GTEx
    - Free APIs - no key required
    """
    
    ENSEMBL_BASE = "https://rest.ensembl.org"
    GWAS_CATALOG_BASE = "https://www.ebi.ac.uk/gwas/rest/api"
    OPEN_TARGETS_BASE = "https://api.platform.opentargets.org/api/v0.4/graphql"
    
    def __init__(self):
        """Initialize GWASService"""
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def lookup_variant(self, rsid: str) -> Optional[Dict[str, Any]]:
        """
        Lookup variant information across multiple databases.
        
        Args:
            rsid: dbSNP reference SNP ID (e.g., "rs7903146")
            
        Returns:
            Dict with combined variant information from all sources
        """
        # Check cache first
        if rsid.lower() in self._cache:
            return self._cache[rsid.lower()]
        
        # Query all databases in parallel
        async with httpx.AsyncClient(timeout=15.0) as client:
            tasks = [
                self._query_ensembl(client, rsid),
                self._query_gwas_catalog(client, rsid),
                self._query_open_targets(client, rsid),
                self._query_clinvar(client, rsid)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        ensembl_data = results[0] if not isinstance(results[0], Exception) else None
        gwas_data = results[1] if not isinstance(results[1], Exception) else None
        open_targets_data = results[2] if not isinstance(results[2], Exception) else None
        clinvar_data = results[3] if not isinstance(results[3], Exception) else None
        
        # Build combined result
        combined = self._combine_results(
            rsid, 
            ensembl_data, 
            gwas_data, 
            open_targets_data, 
            clinvar_data
        )
        
        # Cache result
        self._cache[rsid.lower()] = combined
        
        return combined
    
    async def _query_ensembl(
        self, 
        client: httpx.AsyncClient, 
        rsid: str
    ) -> Optional[Dict[str, Any]]:
        """Query Ensembl for variant annotation"""
        try:
            # Get variant annotation
            response = await client.get(
                f"{self.ENSEMBL_BASE}/variation/human/{rsid}",
                params={"content-type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "ensembl",
                    "rsid": data.get("name", rsid),
                    "chromosome": data.get("seq_region_name"),
                    "position": data.get("start"),
                    "alleles": data.get("alleles", []),
                    "minor_allele": data.get("minor_allele"),
                    "minor_allele_freq": data.get("minor_allele_freq"),
                    "synonyms": data.get("synonyms", []),
                    "most_severe_consequence": data.get("most_severe_consequence")
                }
        except Exception as e:
            print(f"❌ Ensembl query failed for {rsid}: {e}")
        return None
    
    async def _query_gwas_catalog(
        self, 
        client: httpx.AsyncClient, 
        rsid: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Query GWAS Catalog for trait associations"""
        try:
            # Search for variant associations
            response = await client.get(
                f"{self.GWAS_CATALOG_BASE}/associations",
                params={
                    "rsId": rsid,
                    "size": 20
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                associations = []
                
                for item in data.get("_embedded", {}).get("associations", []):
                    associations.append({
                        "source": "gwas_catalog",
                        "trait": item.get("reportedTrait", ""),
                        "p_value": item.get("pValue"),
                        "p_value_formatted": self._format_p_value(item.get("pValue")),
                        "odds_ratio": item.get("orValue"),
                        "beta": item.get("betaValue"),
                        "risk_allele": item.get("riskAlleles"),
                        "sample_size": item.get("initialSampleSize"),
                        "study": item.get("_links", {}).get("study", {}).get("href"),
                        "pubmed_id": item.get("_links", {}).get("publication", {}).get("href", "").split("/")[-1]
                    })
                
                return associations
        except Exception as e:
            print(f"❌ GWAS Catalog query failed for {rsid}: {e}")
        return None
    
    async def _query_open_targets(
        self, 
        client: httpx.AsyncClient, 
        rsid: str
    ) -> Optional[Dict[str, Any]]:
        """Query Open Targets for variant-to-gene mapping"""
        try:
            # GraphQL query for variant
            query = """
            query VariantQuery($rsid: String!) {
                variant(id: $rsid) {
                    id
                    mostSevereConsequence
                    caddPhredScore
                    genes {
                        id
                        symbol
                        biotype
                    }
                }
            }
            """
            
            response = await client.post(
                self.OPEN_TARGETS_BASE,
                json={
                    "query": query,
                    "variables": {"rsid": rsid}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                variant = data.get("data", {}).get("variant")
                
                if variant:
                    return {
                        "source": "open_targets",
                        "rsid": variant.get("id"),
                        "consequence": variant.get("mostSevereConsequence"),
                        "cadd_score": variant.get("caddPhredScore"),
                        "genes": [
                            {
                                "symbol": g.get("symbol"),
                                "biotype": g.get("biotype")
                            }
                            for g in variant.get("genes", [])
                        ]
                    }
        except Exception as e:
            print(f"❌ Open Targets query failed for {rsid}: {e}")
        return None
    
    async def _query_clinvar(
        self, 
        client: httpx.AsyncClient, 
        rsid: str
    ) -> Optional[Dict[str, Any]]:
        """Query ClinVar for clinical significance"""
        try:
            # Search ClinVar via NCBI E-utilities
            response = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "clinvar",
                    "term": rsid,
                    "retmode": "json",
                    "retmax": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ids = data.get("esearchresult", {}).get("idlist", [])
                
                if ids:
                    # Fetch summary for first result
                    summary_response = await client.get(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                        params={
                            "db": "clinvar",
                            "id": ",".join(ids[:3]),
                            "retmode": "json"
                        }
                    )
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        clinvar_info = []
                        
                        for uid, item in summary_data.get("result", {}).items():
                            if uid == "uids":
                                continue
                            clinvar_info.append({
                                "clinvar_id": item.get("uid"),
                                "condition": item.get("condition", {}).get("name"),
                                "clinical_significance": item.get("clinical_significance"),
                                "review_status": item.get("review_status"),
                                "url": f"https://www.ncbi.nlm.nih.gov/clinvar/{item.get('uid')}"
                            })
                        
                        return {
                            "source": "clinvar",
                            "records": clinvar_info
                        }
        except Exception as e:
            print(f"❌ ClinVar query failed for {rsid}: {e}")
        return None
    
    def _combine_results(
        self,
        rsid: str,
        ensembl: Optional[Dict],
        gwas: Optional[List[Dict]],
        open_targets: Optional[Dict],
        clinvar: Optional[Dict]
    ) -> Dict[str, Any]:
        """Combine results from all sources"""
        result = {
            "rsid": rsid,
            "found": False,
            "ensembl": ensembl,
            "gwas_associations": gwas or [],
            "open_targets": open_targets,
            "clinvar": clinvar,
            "summary": {
                "chromosome": ensembl.get("chromosome") if ensembl else None,
                "position": ensembl.get("position") if ensembl else None,
                "alleles": ensembl.get("alleles") if ensembl else [],
                "genes": open_targets.get("genes") if open_targets else [],
                "trait_count": len(gwas) if gwas else 0,
                "clinvar_records": len(clinvar.get("records", [])) if clinvar else 0,
                "most_severe_consequence": ensembl.get("most_severe_consequence") if ensembl else None,
                "cadd_score": open_targets.get("cadd_score") if open_targets else None
            }
        }
        
        # Mark as found if any source returned data
        if ensembl or gwas or open_targets or clinvar:
            result["found"] = True
        
        return result
    
    def _format_p_value(self, p_value: Optional[float]) -> str:
        """Format p-value for display"""
        if p_value is None:
            return "N/A"
        if p_value < 0.0001:
            return f"{p_value:.2e}"
        return f"{p_value:.4f}"
    
    def format_for_display(self, result: Dict[str, Any]) -> str:
        """Format variant lookup results for display in chat"""
        if not result.get("found"):
            return f"No data found for variant **{result.get('rsid', 'unknown')}**."
        
        lines = [f"## GWAS Variant Lookup: {result['rsid']}\n"]
        
        # Basic info
        summary = result.get("summary", {})
        if summary.get("chromosome"):
            lines.append(f"**Location**: Chr{summary['chromosome']}:{summary.get('position', 'N/A')}")
        if summary.get("alleles"):
            lines.append(f"**Alleles**: {' / '.join(summary['alleles'])}")
        if summary.get("most_severe_consequence"):
            lines.append(f"**Consequence**: {summary['most_severe_consequence']}")
        if summary.get("cadd_score"):
            lines.append(f"**CADD Score**: {summary['cadd_score']} (higher = more deleterious)")
        
        lines.append("")
        
        # GWAS associations
        gwas = result.get("gwas_associations", [])
        if gwas:
            lines.append(f"### Trait Associations ({len(gwas)} found)\n")
            for assoc in gwas[:5]:  # Top 5
                lines.append(f"- **{assoc.get('trait', 'Unknown trait')}**")
                lines.append(f"  - P-value: {assoc.get('p_value_formatted')}")
                if assoc.get('odds_ratio'):
                    lines.append(f"  - OR: {assoc['odds_ratio']}")
                if assoc.get('beta'):
                    lines.append(f"  - Beta: {assoc['beta']}")
            if len(gwas) > 5:
                lines.append(f"\n*...and {len(gwas) - 5} more associations*")
        else:
            lines.append("### No GWAS associations found\n")
        
        # ClinVar
        clinvar = result.get("clinvar")
        if clinvar and clinvar.get("records"):
            lines.append("\n### Clinical Significance (ClinVar)\n")
            for record in clinvar["records"][:3]:
                lines.append(f"- **{record.get('condition', 'Unknown condition')}**")
                lines.append(f"  - Significance: {record.get('clinical_significance', 'Unknown')}")
                lines.append(f"  - Review: {record.get('review_status', 'N/A')}")
        
        lines.append("\n---")
        lines.append("*Data sources: Ensembl, GWAS Catalog, Open Targets, ClinVar*")
        
        return "\n".join(lines)


# Need to import asyncio at module level
import asyncio

# Singleton instance
gwas_service = GWASService()
