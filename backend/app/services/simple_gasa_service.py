"""
Simple GASA-like Predictor (No DGL dependency)

Uses molecular descriptors to predict synthetic accessibility.
Based on GASA methodology but implemented with RDKit only.
"""

from typing import Dict, Any, Optional


class SimpleGASAPredictor:
    """
    Simplified GASA predictor using RDKit descriptors.
    
    Predicts Easy (0) vs Hard (1) to synthesize based on:
    - Molecular complexity
    - Ring count
    - Aromaticity
    - Functional group count
    """
    
    def __init__(self):
        self._initialized = False
        self._init_error = None
    
    def predict_single(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        Predict synthetic accessibility for a molecule.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with prediction or None if failed
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors, Lipinski, Descriptors
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                return None
            
            # Calculate molecular descriptors
            mw = Descriptors.MolWt(mol)
            num_rings = rdMolDescriptors.CalcNumRings(mol)
            num_aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
            num_rotatable_bonds = Lipinski.NumRotatableBonds(mol)
            num_h_donors = Lipinski.NumHDonors(mol)
            num_h_acceptors = Lipinski.NumHAcceptors(mol)
            tpsa = Descriptors.TPSA(mol)
            
            # GASA-like scoring (0 = easy, 1 = hard)
            # Based on molecular complexity
            complexity_score = (
                (num_rings * 0.15) +
                (num_aromatic_rings * 0.20) +
                (mw / 500.0) * 0.25 +
                (num_rotatable_bonds / 10.0) * 0.20 +
                (tpsa / 150.0) * 0.20
            )
            
            # Convert to probability (sigmoid-like)
            easy_prob = 1.0 / (1.0 + complexity_score)
            hard_prob = 1.0 - easy_prob
            
            # Prediction (threshold at 0.5)
            prediction = 0 if easy_prob > 0.5 else 1
            
            return {
                "prediction": prediction,
                "easy_probability": round(easy_prob, 4),
                "hard_probability": round(hard_prob, 4),
                "interpretation": "Easy to synthesize" if prediction == 0 else "Hard to synthesize"
            }
            
        except Exception as e:
            print(f"❌ Simple GASA prediction failed: {e}")
            return None


# Singleton instance
simple_gasa_predictor = SimpleGASAPredictor()
