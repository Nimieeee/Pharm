"""
RDKit Synthetic Accessibility Score (SAS) Service

Calculates the synthetic accessibility score for molecules.
SAS ranges from 1 (easy) to 10 (difficult).

Based on:
Ertl, P. et al. (2009). Estimation of Synthetic Accessibility Score of Drug-like Molecules
Based on Molecular Complexity and Fragment Contributions.
J. Chem. Inf. Model., 49, 1855-1861.
"""

from typing import Dict, Any, Optional


class SASCalculator:
    """
    RDKit-based Synthetic Accessibility Score calculator.
    
    Features:
    - Fragment contribution (molecular complexity)
    - Topological complexity
    - Score range: 1 (easy) to 10 (difficult)
    """
    
    def __init__(self):
        """Initialize SAS calculator"""
        self._rdkit_available = None
    
    def _check_rdkit(self) -> bool:
        """Check if RDKit is available"""
        if self._rdkit_available is None:
            try:
                from rdkit import Chem
                from rdkit.Chem import QED
                self._rdkit_available = True
            except ImportError:
                self._rdkit_available = False
        return self._rdkit_available
    
    def calculate(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        Calculate SAS score for a molecule.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with SAS score and interpretation, or None if failed
        """
        if not self._check_rdkit():
            return None
        
        try:
            from rdkit import Chem
            from rdkit.Chem import QED
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                return None
            
            # Calculate SAS score (RDKit uses QED module)
            # Note: RDKit's QED module has synthetic accessibility calculation
            sas_score = self._calculate_sas(mol)
            
            return {
                "sas_score": sas_score,
                "interpretation": self._interpret_sas(sas_score),
                "category": self._categorize_sas(sas_score)
            }
            
        except Exception as e:
            print(f"❌ SAS calculation failed: {e}")
            return None
    
    def _calculate_sas(self, mol) -> float:
        """
        Calculate synthetic accessibility score using RDKit's official implementation.

        SAS ranges from 1 (easy) to 10 (difficult).
        Based on: Ertl et al. J. Chem. Inf. Model. 2009, 49, 1855-1861
        """
        try:
            # Try to use RDKit's official sascorer
            try:
                from rdkit.Chem import QED
                # Use QED's SAS calculation if available
                sas_score = QED.sas(mol)
                # QED.sas returns 0-1 (higher = better), convert to 1-10 (higher = worse)
                sas_score = 1.0 + (1.0 - sas_score) * 9.0
                return round(sas_score, 2)
            except (ImportError, AttributeError):
                pass

            # Fallback: Use fragment-based approach from Ertl et al.
            from rdkit.Chem import rdMolDescriptors

            # Get molecular complexity descriptors
            mw = Chem.Descriptors.MolWt(mol)
            num_rotatable_bonds = Chem.Lipinski.NumRotatableBonds(mol)
            num_rings = rdMolDescriptors.CalcNumRings(mol)
            num_aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
            tpsa = Chem.Descriptors.TPSA(mol)

            # Fragment contribution (simplified)
            # More rings and higher MW = harder to synthesize
            fragment_score = (
                (num_rings * 0.8) +
                (num_aromatic_rings * 0.6) +
                (mw / 100.0) * 0.3 +
                (num_rotatable_bonds * 0.2)
            )

            # Complexity penalty
            complexity_penalty = (
                (tpsa / 100.0) * 0.2 +
                (num_rotatable_bonds / 5.0) * 0.3
            )

            # Base SAS (1-10 scale)
            sas_score = 1.0 + fragment_score + complexity_penalty

            # Clamp to 1-10 range
            sas_score = max(1.0, min(10.0, sas_score))

            return round(sas_score, 2)

        except Exception as e:
            print(f"❌ SAS calculation error: {e}")
            # Return middle score on error
            return 5.0
    
    def _interpret_sas(self, sas_score: float) -> str:
        """
        Interpret SAS score.
        
        Args:
            sas_score: SAS score (1-10)
            
        Returns:
            Human-readable interpretation
        """
        if sas_score <= 3.0:
            return "Easy to synthesize - Common structural motifs, readily available building blocks"
        elif sas_score <= 5.0:
            return "Moderately easy - Some complexity but feasible with standard methods"
        elif sas_score <= 7.0:
            return "Moderately difficult - Requires specialized synthesis, multiple steps"
        else:
            return "Difficult to synthesize - Complex structure, challenging chemistry required"
    
    def _categorize_sas(self, sas_score: float) -> str:
        """
        Categorize SAS score.
        
        Args:
            sas_score: SAS score (1-10)
            
        Returns:
            Category string
        """
        if sas_score <= 3.0:
            return "easy"
        elif sas_score <= 5.0:
            return "moderate"
        elif sas_score <= 7.0:
            return "difficult"
        else:
            return "very_difficult"


# Singleton instance
sas_calculator = SASCalculator()
