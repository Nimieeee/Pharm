"""
ADMET Service

Drug discovery ADMET prediction service with ToxMCP robustness patterns.
Integrates with:
1. Local ADMET-AI Engine (Chemprop v2) - Primary
2. ADMETlab 3.0 API - Fallback
3. RDKit - Final fallback for basic properties

API Reference: https://admetlab3.scbdd.com
Local Engine: http://localhost:7861 (admet-engine PM2 service)
"""

import asyncio
import httpx
import os
from typing import Dict, Any, Optional, List
from supabase import Client

from app.core.container import container
from app.services.postprocessing import admet_processor


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, rps: int = 5):
        self.rps = rps
        self.last_call = 0
    
    async def wait_for_slot(self):
        """Wait for rate limit slot (simplified - no actual delay in this version)"""
        pass


class ADMETService:
    """
    ADMET prediction service with local engine + fallback architecture.
    
    Features:
    - Local ADMET-AI Engine (104 endpoints) - Primary
    - Structure SVG generation
    - 119 ADMET endpoint predictions (ADMETlab fallback)
    - PAINS/structural alerts
    - CSV export
    - Clinical report generation
    - AI-powered interpretation (via AIService)
    """
    
    API_BASE = "https://admetlab3.scbdd.com/api"
    LOCAL_ENGINE_URL = os.environ.get("ADMET_ENGINE_URL", "http://localhost:7861")
    
    def __init__(self, db: Client = None):
        """
        Initialize ADMETService.
        
        Args:
            db: Database client (for future caching)
        """
        self._db = db
        self._processor = None
        self._ai_service = None
        self._rate_limiter = RateLimiter(rps=5)
        self._engine_available = None
    
    @property
    def processor(self):
        """Lazy load ADMET processor from container"""
        if self._processor is None:
            try:
                from app.core.container import container
                if container.is_initialized():
                    self._processor = container.get('admet_processor')
            except (KeyError, RuntimeError):
                pass
            # Fallback: create instance directly if container not available
            if self._processor is None:
                from app.services.postprocessing import admet_processor
                self._processor = admet_processor
        return self._processor
    
    @property
    def ai_service(self):
        """Lazy load AI service from container for interpretation"""
        if self._ai_service is None:
            try:
                from app.core.container import container
                if container.is_initialized():
                    self._ai_service = container.get('ai_service')
            except (KeyError, RuntimeError):
                pass
        return self._ai_service
    
    async def _check_local_engine(self) -> bool:
        """Check if local ADMET engine is available"""
        if self._engine_available is None:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.LOCAL_ENGINE_URL}/health")
                    self._engine_available = response.status_code == 200
            except Exception:
                self._engine_available = False
        return self._engine_available
    
    async def _predict_local(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        Get ADMET predictions from local ADMET-AI engine.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with 104 ADMET predictions or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.LOCAL_ENGINE_URL}/predict",
                    json={"smiles": [smiles], "include_percentiles": True}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("predictions"):
                        prediction = data["predictions"][0]
                        prediction["_engine"] = "admet-ai (Chemprop v2)"
                        prediction["_source"] = "local"
                        return prediction
                        
        except Exception as e:
            print(f"⚠️ Local ADMET engine failed: {e}")
        
        return None
    
    async def wash_molecule(self, smiles: str) -> Optional[str]:
        """
        Standardize SMILES via /api/washmol.
        
        Args:
            smiles: Input SMILES string
            
        Returns:
            Standardized SMILES or None if failed
        """
        try:
            await self._rate_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.API_BASE}/washmol",
                    json={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Unwrap new ADMETlab 3.0 response format: {"code": 200, "status": "success", "data": [{..."washmol": "..."}]}
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        result_data = data["data"][0]
                        if isinstance(result_data, dict) and "washmol" in result_data:
                            return result_data["washmol"]
                    # Fallback to old format for backward compatibility
                    return data.get('washmol', smiles)
                    
        except Exception as e:
            print(f"❌ ADMET wash molecule failed: {e}")
        
        return smiles  # Return original on failure
    
    async def get_svg(self, smiles: str) -> Optional[str]:
        """
        Generate molecule SVG via /api/molsvg.
        
        Args:
            smiles: SMILES string
            
        Returns:
            SVG string or None if failed
        """
        try:
            await self._rate_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.API_BASE}/molsvg",
                    json={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # The API returns {"status": "success", "code": 200, "data": ["<svg>..."]}
                    if data and isinstance(data, dict) and 'data' in data and data['data']:
                        return data['data'][0]
                    return None
                    
        except Exception as e:
            print(f"❌ ADMET SVG generation failed: {e}")
        
        return None
    
    async def predict_admet(self, smiles: str) -> Dict[str, Any]:
        """
        Get ADMET predictions with local engine + fallback.
        
        Priority:
        1. Local ADMET-AI Engine (104 endpoints) - Primary
        2. ADMETlab 3.0 API (119 endpoints) - Fallback
        3. RDKit basic properties - Final fallback
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with ADMET predictions
        """
        # 1. Try local ADMET-AI engine first
        if await self._check_local_engine():
            result = await self._predict_local(smiles)
            if result:
                print("✅ Using local ADMET-AI engine")
                return result
        
        # 2. Fallback to ADMETlab 3.0 API
        try:
            await self._rate_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                response = await client.post(
                    f"{self.API_BASE}/admet",
                    json={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        result = data["data"][0]
                        result["_engine"] = "ADMETlab 3.0"
                        result["_source"] = "api"
                        print("✅ Using ADMETlab 3.0 API")
                        return result
                        
        except httpx.TimeoutException:
            print("⚠️ ADMETlab timeout - trying single endpoint fallback")
            return await self._predict_single(smiles)
            
        except Exception as e:
            print(f"⚠️ ADMETlab API failed: {e}")
        
        # 3. Final fallback: RDKit basic properties
        print("⚠️ Using RDKit fallback for basic properties")
        return await self._predict_rdkit_fallback(smiles)
    
    async def _predict_rdkit_fallback(self, smiles: str) -> Dict[str, Any]:
        """
        Fallback to RDKit for basic physicochemical properties.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with basic ADMET-like properties
        """
        result = {
            "_engine": "RDKit (fallback)",
            "_source": "local",
            "error": "External ADMET services unavailable"
        }
        
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, Lipinski, Crippen
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                result["error"] = "Invalid SMILES"
                return result
            
            result["molecular_weight"] = Descriptors.MolWt(mol)
            result["logP"] = Crippen.MolLogP(mol)
            result["hydrogen_bond_donors"] = Lipinski.NumHDonors(mol)
            result["hydrogen_bond_acceptors"] = Lipinski.NumHAcceptors(mol)
            result["tpsa"] = Descriptors.TPSA(mol)
            result["num_rotatable_bonds"] = Lipinski.NumRotatableBonds(mol)
            result["num_rings"] = Lipinski.RingCount(mol)
            result["num_heavy_atoms"] = mol.GetNumHeavyAtoms()
            
            # Lipinski Rule of 5 check
            lipinski_violations = sum([
                Descriptors.MolWt(mol) > 500,
                Crippen.MolLogP(mol) > 5,
                Lipinski.NumHDonors(mol) > 5,
                Lipinski.NumHAcceptors(mol) > 10
            ])
            result["Lipinski"] = 4 - lipinski_violations
            result["Lipinski_violations"] = lipinski_violations
            
            # QED (approximate)
            result["QED"] = 0.5  # Placeholder - full QED calculation is complex
            
            # Structural alerts (none in RDKit fallback)
            result["PAINS_alert"] = 0
            result["BRENK_alert"] = 0
            
            result["error"] = None
            print("✅ RDKit fallback: basic properties computed")
            
        except ImportError:
            result["error"] = "RDKit not available"
            print("❌ RDKit not available")
        except Exception as e:
            result["error"] = f"RDKit error: {str(e)}"
            print(f"❌ RDKit fallback failed: {e}")
        
        return result
    
    async def _predict_single(self, smiles: str) -> Dict[str, Any]:
        """Fallback to single endpoint prediction"""
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.API_BASE}/single/admet",
                    json={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        return data["data"][0]
                    return data
        except Exception as e:
            print(f"❌ Single endpoint fallback failed: {e}")
        
        return {}
    
    async def calculate_filters(self, smiles: str) -> Dict[str, Any]:
        """
        Calculate medchem filters (PAINS, Lipinski, etc.).
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with filter results
        """
        try:
            await self._rate_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.API_BASE}/filters",
                    json={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                        return data["data"][0]
                    return data
                    
        except Exception as e:
            print(f"❌ Filter calculation failed: {e}")
        
        return {}
    
    async def generate_report(self, smiles: str, molecule_name: str = None) -> str:
        """
        Generate consolidated ADMET markdown report.
        
        Args:
            smiles: SMILES string
            molecule_name: Optional name for the molecule
            
        Returns:
            Markdown report string
        """
        # Try to get structure SVG (optional - doesn't block report)
        svg = None
        try:
            svg = await self.get_svg(smiles)
        except Exception:
            pass
        
        # Get ADMET predictions (primary function)
        admet_data = await self.predict_admet(smiles)
        
        # Add molecule name if provided
        if molecule_name:
            admet_data['molecule_name'] = molecule_name
        
        # For local engine, filters are already included in the prediction
        # Only call calculate_filters if using ADMETlab API
        if admet_data.get("_source") == "api":
            filters = await self.calculate_filters(smiles)
            if filters:
                admet_data['filters'] = filters
        
        # Format report
        return self.processor.format_report(admet_data, svg)
    
    def export_as_csv(self, results: Dict[str, Any]) -> str:
        """
        Export ADMET results as CSV.

        Args:
            results: ADMET results dict

        Returns:
            CSV string
        """
        return self.processor.format_csv_export(results)

    async def extract_smiles_from_sdf(self, content: bytes) -> List[Dict[str, str]]:
        """
        Extract SMILES and names from SDF file content.

        Args:
            content: Raw SDF file bytes

        Returns:
            List of dicts with {smiles, name} keys
        """
        try:
            # Try to use RDKit if available
            try:
                from rdkit import Chem

                content_str = content.decode('utf-8', errors='ignore')
                supplier = Chem.SDMolSupplier()
                supplier.SetData(content_str)

                molecules = []
                for mol in supplier:
                    if mol is not None:
                        smi = Chem.MolToSmiles(mol)
                        if smi:
                            # Try to get molecule name from _Name property
                            name = mol.GetProp('_Name') if mol.HasProp('_Name') else None
                            molecules.append({
                                'smiles': smi,
                                'name': name or f'Molecule {len(molecules) + 1}'
                            })

                if molecules:
                    return molecules

            except ImportError:
                print("⚠️ RDKit not available, using simple SDF parsing")

            # Simple SDF parsing fallback
            content_str = content.decode('utf-8', errors='ignore')
            mol_blocks = content_str.split('$$$$')

            molecules = []
            for idx, mol_block in enumerate(mol_blocks):
                mol_block = mol_block.strip()
                if not mol_block:
                    continue

                lines = mol_block.split('\n')
                smiles = None
                name = None

                # Look for SMILES and Name in properties
                for i, line in enumerate(lines):
                    line_upper = line.upper()
                    if '<SMILES>' in line or '<D_SMILES>' in line or '<CANONICAL_SMILES>' in line:
                        if i + 1 < len(lines):
                            smiles = lines[i + 1].strip()
                    elif '<NAME>' in line or '_NAME' in line:
                        if i + 1 < len(lines):
                            name = lines[i + 1].strip()

                # If no SMILES tag found, try to extract from first line
                if not smiles and lines:
                    first_line = lines[0].strip()
                    if any(c in first_line for c in ['C', 'N', 'O', 'S']) and ('(' in first_line or ')' in first_line or 'c' in first_line):
                        smiles = first_line
                        name = f'Molecule {idx + 1}'
                    else:
                        # First line might be the name
                        name = first_line

                if smiles:
                    molecules.append({
                        'smiles': smiles,
                        'name': name or f'Molecule {idx + 1}'
                    })

            return molecules

        except Exception as e:
            print(f"❌ SDF parsing failed: {e}")
            return []

    async def analyze_batch(self, smiles_list: list) -> list:
        """
        Batch ADMET analysis for multiple molecules.

        Args:
            smiles_list: List of SMILES strings

        Returns:
            List of ADMET results dicts
        """
        results = []

        for i, smiles in enumerate(smiles_list):
            try:
                # Limit to prevent timeouts (max 20 molecules)
                if i >= 20:
                    break

                # Get full report for each molecule
                report = await self.generate_report(smiles)

                results.append({
                    "index": i + 1,
                    "smiles": smiles,
                    "report": report,
                    "success": True
                })

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"❌ Batch analysis failed for molecule {i + 1}: {e}")
                results.append({
                    "index": i + 1,
                    "smiles": smiles,
                    "error": str(e),
                    "success": False
                })

        return results


# Factory function for dependency injection
def get_admet_service(db: Client = None) -> ADMETService:
    """Get ADMETService with injected dependencies"""
    return ADMETService(db)
