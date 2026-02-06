"""
External Tool Integrations
Provides access to OpenFDA and PubChem APIs for real-time biomedical data.
"""

import httpx
import logging
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BiomedicalTools:
    """Service to handle external biomedical API requests"""
    
    OPENFDA_ENDPOINT = "https://api.fda.gov/drug/label.json"
    PUBCHEM_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    async def fetch_openfda_label(self, drug_name: str) -> Dict[str, Any]:
        """
        Fetch drug label information (indications, warnings, boxed warnings) from OpenFDA.
        """
        try:
            # OpenFDA search syntax: search=openfda.brand_name:"name" matches brand names
            # We use .exact matching for precision, usually formatted as 'brand_name.exact'
            # or try generic_name if brand fails.
            
            # First try brand name
            query = f'openfda.brand_name:"{drug_name}"'
            params = {
                "search": query,
                "limit": 1
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.OPENFDA_ENDPOINT, params=params)
                
                # If brand name fails, try generic name
                if response.status_code != 200:
                    query = f'openfda.generic_name:"{drug_name}"'
                    params["search"] = query
                    response = await client.get(self.OPENFDA_ENDPOINT, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if "results" in data and len(data["results"]) > 0:
                        result = data["results"][0]
                        return {
                            "found": True,
                            "drug_name": drug_name,
                            "indications": result.get("indications_and_usage", ["Not listed"])[0],
                            "warnings": result.get("warnings", ["Not listed"])[0],
                            "boxed_warnings": result.get("boxed_warning", ["No boxed warning found"])[0],
                            "contraindications": result.get("contraindications", ["Not listed"])[0]
                        }
            
            logger.warning(f"OpenFDA: No data found for {drug_name}")
            return {"found": False, "error": "Drug label not found"}

        except Exception as e:
            logger.error(f"OpenFDA API Error: {e}")
            return {"found": False, "error": str(e)}

    async def fetch_pubchem_data(self, compound_name: str) -> Dict[str, Any]:
        """
        Fetch chemical property data from PubChem.
        """
        try:
            # 1. Search for the CID (Compound ID) first
            search_url = f"{self.PUBCHEM_ENDPOINT}/compound/name/{urllib.parse.quote(compound_name)}/cids/JSON"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get CID
                cid_response = await client.get(search_url)
                if cid_response.status_code != 200:
                    return {"found": False, "error": "Compound not found"}
                
                cid_data = cid_response.json()
                if "IdentifierList" not in cid_data or "CID" not in cid_data["IdentifierList"]:
                    return {"found": False, "error": "No CID found"}
                
                cid = cid_data["IdentifierList"]["CID"][0]
                
                # 2. Get Properties (MolecularWeight, MolecularFormula, IUPACName)
                props = "MolecularWeight,MolecularFormula,IUPACName,XLogP"
                prop_url = f"{self.PUBCHEM_ENDPOINT}/compound/cid/{cid}/property/{props}/JSON"
                
                prop_response = await client.get(prop_url)
                if prop_response.status_code == 200:
                    prop_data = prop_response.json()
                    properties = prop_data["PropertyTable"]["Properties"][0]
                    
                    return {
                        "found": True,
                        "compound_name": compound_name,
                        "cid": cid,
                        "molecular_weight": properties.get("MolecularWeight"),
                        "molecular_formula": properties.get("MolecularFormula"),
                        "iupac_name": properties.get("IUPACName"),
                        "xlogp": properties.get("XLogP", "N/A")
                    }
            
            return {"found": False, "error": "Properties not found"}

        except Exception as e:
            logger.error(f"PubChem API Error: {e}")
            return {"found": False, "error": str(e)}
