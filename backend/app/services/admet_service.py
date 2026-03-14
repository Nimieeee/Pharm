"""
ADMET Service

Drug discovery ADMET prediction service.
Integrates with:
1. Local ADMET-AI Engine (Chemprop v2) - Primary
2. RDKit - Final fallback for basic properties

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
    ADMET prediction service with local engine + RDKit fallback architecture.
    
    Features:
    - Local ADMET-AI Engine (46 endpoints) - Primary
    - Structure SVG generation via RDKit
    - CSV export
    - Clinical report generation
    - AI-powered interpretation (via AIService)
    """
    
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
            Dict with 46 ADMET predictions or None if failed
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
                        prediction["smiles"] = smiles
                        return prediction
                        
        except Exception as e:
            print(f"⚠️ Local ADMET engine failed: {e}")
        
        return None
    
    async def wash_molecule(self, smiles: str) -> Optional[str]:
        """
        Standardize SMILES using RDKit.
        
        Args:
            smiles: Input SMILES string
            
        Returns:
            Standardized SMILES or original if failed
        """
        try:
            from rdkit import Chem
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return smiles
            
            # Standardize and return canonical SMILES
            return Chem.MolToSmiles(mol, canonical=True, isomericSmiles=False)
            
        except ImportError:
            print("⚠️ RDKit not available for SMILES washing")
            return smiles
        except Exception as e:
            print(f"❌ SMILES washing failed: {e}")
            return smiles
    
    async def get_svg(self, smiles: str) -> Optional[str]:
        """
        Generate molecule SVG using RDKit.
        
        Args:
            smiles: SMILES string
            
        Returns:
            SVG string or None if failed
        """
        return await self._get_svg_rdkit(smiles)
    
    async def _get_svg_rdkit(self, smiles: str) -> Optional[str]:
        """Generate molecule SVG using local RDKit"""
        try:
            from rdkit import Chem
            from rdkit.Chem.Draw import rdMolDraw2D
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                return None
            
            drawer = rdMolDraw2D.MolDraw2DSVG(400, 300)
            drawer.DrawMolecule(mol)
            drawer.FinishDrawing()
            return drawer.GetDrawingText()
            
        except ImportError:
            return None
        except Exception as e:
            print(f"❌ RDKit SVG generation failed: {e}")
            return None
    
    async def predict_admet(self, smiles: str) -> Dict[str, Any]:
        """
        Get ADMET predictions with local engine + RDKit fallback.
        
        Priority:
        1. Local ADMET-AI Engine (46 endpoints) - Primary
        2. RDKit basic properties - Final fallback
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with ADMET predictions
        """
        raw_smiles = smiles  # Store original
        
        # 1. Try local ADMET-AI engine first
        if await self._check_local_engine():
            result = await self._predict_local(smiles)
            if result:
                result["raw_smiles"] = raw_smiles
                print("✅ Using local ADMET-AI engine")
                return result
        
        # 2. Final fallback: RDKit basic properties
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
            "smiles": smiles,
            "_engine": "RDKit (fallback)",
            "_source": "local",
            "error": "ADMET-AI engine unavailable"
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
        
        # Generate AI interpretation (if AI service available)
        ai_interpretation = None
        try:
            ai_interpretation = await self._generate_ai_interpretation(admet_data, molecule_name)
        except Exception as e:
            print(f"⚠️ AI interpretation failed: {e}")
        
        # Format report with AI interpretation
        return self.processor.format_report(admet_data, svg, ai_interpretation)
    
    async def _generate_ai_interpretation(self, admet_data: Dict[str, Any], molecule_name: str = None) -> str:
        """
        Generate AI-powered interpretation of ADMET results.
        
        Args:
            admet_data: Full ADMET prediction results
            molecule_name: Optional molecule name
            
        Returns:
            AI-generated interpretation string
        """
        ai = self.ai_service
        if not ai:
            return None
        
        # Extract key properties for the prompt
        key_props = []
        
        # Drug likeness
        if 'QED' in admet_data:
            key_props.append(f"QED: {admet_data['QED']:.3f}")
        if 'Lipinski' in admet_data:
            lip = admet_data['Lipinski']
            violations = 4 - int(lip) if isinstance(lip, (int, float)) else 0
            key_props.append(f"Lipinski violations: {violations}")
        
        # Absorption
        if 'HIA_Hou' in admet_data:
            key_props.append(f"HIA: {admet_data['HIA_Hou']:.2f}")
        if 'Caco2_Wang' in admet_data:
            key_props.append(f"Caco-2: {admet_data['Caco2_Wang']:.2f}")
        
        # Toxicity - critical endpoints
        toxicity_concerns = []
        for endpoint in ['hERG', 'AMES', 'DILI', 'ClinTox']:
            if endpoint in admet_data:
                val = admet_data[endpoint]
                if isinstance(val, (int, float)) and val > 0.5:
                    toxicity_concerns.append(f"{endpoint} ({val:.2f})")
        
        if toxicity_concerns:
            key_props.append(f"Toxicity concerns: {', '.join(toxicity_concerns)}")
        
        # Build the prompt
        name_str = f" for {molecule_name}" if molecule_name else ""
        properties_str = "\n".join(f"- {prop}" for prop in key_props) if key_props else "No properties available"
        
        prompt = f"""You are a medicinal chemistry expert. Provide a brief clinical interpretation of the following ADMET analysis for a drug candidate{name_str}.

{properties_str}

Provide a 2-3 sentence summary focusing on:
1. Drug-likeness and developability
2. Key safety concerns (if any)
3. Recommendations for progression

Keep it concise and actionable."""
        
        try:
            # Use Mistral API directly for simple text generation
            from mistralai import Mistral
            from app.core.config import settings
            
            api_key = settings.MISTRAL_API_KEY
            if not api_key:
                print("⚠️ No MISTRAL_API_KEY available")
                return None
                
            client = Mistral(api_key=api_key)
            
            chat_response = client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": "You are a medicinal chemistry expert providing brief, actionable clinical interpretations of ADMET analysis results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            if chat_response and chat_response.choices and chat_response.choices[0].message.content:
                return chat_response.choices[0].message.content.strip()
            
        except ImportError:
            print("⚠️ Mistral SDK not available for AI interpretation")
        except Exception as e:
            print(f"⚠️ AI interpretation generation failed: {e}")
        
        return None
    
    async def export_as_csv(self, results: Dict[str, Any]) -> str:
        """
        Export ADMET results as CSV.

        Args:
            results: ADMET results dict

        Returns:
            CSV string
        """
        # Ensure SVG is present for molstr column
        if "svg_raw" not in results and "smiles" in results:
            try:
                results["svg_raw"] = await self.get_svg(results["smiles"])
            except Exception:
                pass
                
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

    async def analyze_batch_structured(self, molecules: list) -> list:
        """Batch analysis returning structured JSON per molecule."""
        results = []
        
        for i, mol in enumerate(molecules):
            smiles = mol["smiles"] if isinstance(mol, dict) else mol
            name = mol.get("name") if isinstance(mol, dict) else (mol if isinstance(mol, str) else f"Molecule {i+1}")
            
            try:
                # 1. Get raw predictions (dict with 46 keys)
                admet_data = await self.predict_admet(smiles)
                
                # 2. Build structured categories from raw data
                categories = self.processor.build_structured_categories(admet_data)
                
                results.append({
                    "index": i + 1,
                    "smiles": smiles,
                    "molecule_name": name,
                    "success": True,
                    "engine": admet_data.get("_engine", "Unknown"),
                    "categories": categories,
                })
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Batch structured analysis failed for molecule {i + 1}: {e}")
                results.append({
                    "index": i + 1,
                    "smiles": smiles,
                    "molecule_name": name,
                    "success": False,
                    "error": str(e),
                })
        
        return results

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
                # Limit to prevent timeouts (increased to 100 as per plan)
                if i >= 100:
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
                await asyncio.sleep(0.1)

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
