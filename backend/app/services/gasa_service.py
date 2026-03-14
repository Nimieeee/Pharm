"""
GASA Service - Graph Attention-based Synthetic Accessibility

Wrapper for GASA model integration.
Predicts synthetic accessibility (Easy/Hard) using graph neural networks.

Based on: J. Chem. Inf. Model. 2022, DOI: 10.1021/acs.jcim.2c00038
GitHub: https://github.com/cadd-synthetic/GASA
"""

import os
import sys
from typing import Dict, Any, Optional, List
import torch

# Add gasa_model to path
GASA_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'gasa_model')
if GASA_MODEL_PATH not in sys.path:
    sys.path.insert(0, GASA_MODEL_PATH)


class GASAPredictor:
    """
    GASA model predictor for synthetic accessibility.
    
    Features:
    - Graph neural network with attention mechanism
    - Binary classification: Easy (0) vs Hard (1) to synthesize
    - Trained on 800K compounds from ChEMBL, GDBChEMBL, ZINC15
    """
    
    def __init__(self):
        """Initialize GASA predictor"""
        self._model = None
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._initialized = False
        self._init_error = None
    
    def _initialize(self):
        """Lazy initialization of GASA model"""
        if self._initialized:
            return

        try:
            # Import GASA model - use absolute path
            import sys
            import os

            # Ensure gasa_model is in path
            model_dir = os.path.join(os.path.dirname(__file__), 'gasa_model')
            if model_dir not in sys.path:
                sys.path.insert(0, model_dir)

            # Now import
            from model import gasa_classifier
            from gasa_utils import generate_graph

            # Load model configuration
            model_path = os.path.join(GASA_MODEL_PATH, 'gasa.pth')
            if not os.path.exists(model_path):
                self._init_error = f"GASA model file not found: {model_path}"
                print(f"❌ {self._init_error}")
                return

            # Initialize model
            self._model = gasa_classifier(
                dropout=0.2,
                num_heads=8,
                hidden_dim1=128,
                hidden_dim2=128,
                hidden_dim3=128
            )

            # Load weights
            checkpoint = torch.load(model_path, map_location=self._device)
            self._model.load_state_dict(checkpoint['model_state_dict'])
            self._model.to(self._device)
            self._model.eval()

            self._initialized = True
            print(f"✅ GASA model loaded on {self._device}")

        except Exception as e:
            self._init_error = f"GASA initialization failed: {e}"
            print(f"❌ {self._init_error}")
            import traceback
            traceback.print_exc()
    
    def predict(self, smiles_list: List[str]) -> Optional[Dict[str, Any]]:
        """
        Predict synthetic accessibility for molecules.
        
        Args:
            smiles_list: List of SMILES strings
            
        Returns:
            Dict with predictions or None if failed
        """
        self._initialize()
        
        if not self._initialized:
            print(f"⚠️ GASA not initialized: {self._init_error}")
            return None
        
        try:
            from gasa_model.gasa_utils import generate_graph
            from gasa_model.model import predict_collate
            from torch.utils.data import DataLoader
            from gasa_model.data import pred_data
            
            # Generate graphs
            graph = generate_graph(smiles_list)
            dataset = pred_data(graph=graph, smiles=smiles_list)
            data_loader = DataLoader(
                dataset, 
                batch_size=32, 
                shuffle=False, 
                collate_fn=predict_collate
            )
            
            # Run inference
            predictions = []
            pos_probs = []
            neg_probs = []
            
            with torch.no_grad():
                for batch in data_loader:
                    bg = batch[1].to(self._device)
                    output = self._model(bg)[0]
                    
                    # Get predictions
                    pred = torch.max(output, 1)[1].cpu().numpy().tolist()
                    pos_prob = output[:, 0].cpu().numpy().tolist()  # Easy probability
                    neg_prob = output[:, 1].cpu().numpy().tolist()  # Hard probability
                    
                    predictions.extend(pred)
                    pos_probs.extend(pos_prob)
                    neg_probs.extend(neg_prob)
            
            return {
                "predictions": predictions,
                "easy_probabilities": pos_probs,
                "hard_probabilities": neg_probs,
                "interpretation": [
                    "Easy to synthesize" if p == 0 else "Hard to synthesize"
                    for p in predictions
                ]
            }
            
        except Exception as e:
            print(f"❌ GASA prediction failed: {e}")
            return None
    
    def predict_single(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        Predict for a single molecule.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Dict with prediction or None
        """
        result = self.predict([smiles])
        if not result:
            return None
        
        return {
            "prediction": result["predictions"][0],
            "easy_probability": result["easy_probabilities"][0],
            "hard_probability": result["hard_probabilities"][0],
            "interpretation": result["interpretation"][0]
        }


# Singleton instance
gasa_predictor = GASAPredictor()
