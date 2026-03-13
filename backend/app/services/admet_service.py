"""
ADMET Service

Drug discovery ADMET prediction service with ToxMCP robustness patterns.
Integrates with ADMETlab 3.0 API for 119 ADMET endpoints.

API Reference: https://admetlab3.scbdd.com
"""

import asyncio
import httpx
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
    ADMET prediction service with ToxMCP robustness patterns.
    
    Features:
    - Molecule washing (SMILES standardization)
    - Structure SVG generation
    - 119 ADMET endpoint predictions
    - PAINS/structural alerts
    - CSV export
    - Clinical report generation
    """
    
    API_BASE = "https://admetlab3.scbdd.com/api"
    
    def __init__(self, db: Client = None):
        """
        Initialize ADMETService.
        
        Args:
            db: Database client (for future caching)
        """
        self._db = db
        self._processor = None
        self._rate_limiter = RateLimiter(rps=5)
    
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/washmol",
                    params={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    data = response.json()
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/molsvg",
                    params={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    return response.text
                    
        except Exception as e:
            print(f"❌ ADMET SVG generation failed: {e}")
        
        return None
    
    async def predict_admet(self, smiles: str) -> Dict[str, Any]:
        """
        Get 119 ADMET endpoints via /api/admet.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with ADMET predictions
        """
        try:
            await self._rate_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/admet",
                    params={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except httpx.TimeoutException:
            print("⚠️ ADMET prediction timeout - trying single endpoint fallback")
            # Fallback to single endpoint prediction
            return await self._predict_single(smiles)
            
        except Exception as e:
            print(f"❌ ADMET prediction failed: {e}")
        
        return {}
    
    async def _predict_single(self, smiles: str) -> Dict[str, Any]:
        """Fallback to single endpoint prediction"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/single/admet",
                    params={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    return response.json()
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_BASE}/filters",
                    params={"smiles": smiles}
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            print(f"❌ Filter calculation failed: {e}")
        
        return {}
    
    async def generate_report(self, smiles: str) -> str:
        """
        Generate consolidated ADMET markdown report.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Markdown report string
        """
        # Standardize SMILES
        washed_smiles = await self.wash_molecule(smiles)
        
        # Get structure SVG
        svg = await self.get_svg(washed_smiles)
        
        # Get ADMET predictions
        admet_data = await self.predict_admet(washed_smiles)
        
        # Get filter results
        filters = await self.calculate_filters(washed_smiles)
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

    async def extract_smiles_from_sdf(self, content: bytes) -> list:
        """
        Extract SMILES from SDF file content.

        Args:
            content: Raw SDF file bytes

        Returns:
            List of SMILES strings
        """
        try:
            # Try to use RDKit if available
            try:
                from rdkit import Chem
                from rdkit.Chem import rdMolDescriptors

                # Decode content
                content_str = content.decode('utf-8', errors='ignore')

                # Parse SDF
                supplier = Chem.SDMolSupplier()
                supplier.SetData(content_str)

                smiles_list = []
                for mol in supplier:
                    if mol is not None:
                        smi = Chem.MolToSmiles(mol)
                        if smi:
                            smiles_list.append(smi)

                if smiles_list:
                    return smiles_list

            except ImportError:
                # RDKit not available, fall back to simple parsing
                print("⚠️ RDKit not available, using simple SDF parsing")

            # Simple SDF parsing fallback
            content_str = content.decode('utf-8', errors='ignore')
            molecules = content_str.split('$$$$')

            smiles_list = []
            for mol_block in molecules:
                mol_block = mol_block.strip()
                if not mol_block:
                    continue

                # Look for SMILES in properties (common tags: <SMILES>, <d_smiles>, <canonical_smiles>)
                lines = mol_block.split('\n')
                smiles = None

                for i, line in enumerate(lines):
                    if '<SMILES>' in line or '<d_smiles>' in line or '<canonical_smiles>' in line:
                        if i + 1 < len(lines):
                            smiles = lines[i + 1].strip()
                            break

                # If no SMILES tag found, try to extract from first line
                if not smiles and lines:
                    first_line = lines[0].strip()
                    # Basic SMILES validation (contains C, N, O, etc. and parentheses/brackets)
                    if any(c in first_line for c in ['C', 'N', 'O', 'S']) and ('(' in first_line or ')' in first_line or 'c' in first_line):
                        smiles = first_line

                if smiles:
                    smiles_list.append(smiles)

            return smiles_list

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
