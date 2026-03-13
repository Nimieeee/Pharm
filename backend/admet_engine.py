"""
ADMET Engine Microservice

FastAPI wrapper for the ADMET-AI (Chemprop v2) model.
Provides prediction endpoint for 104 ADMET properties.

Runs on Port 7861, registered in PM2 as 'admet-engine'.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import uvicorn

# Global model instance
_model = None


def get_model():
    """Lazy-load the ADMET model"""
    global _model
    if _model is None:
        print("Loading ADMET-AI model...")
        from admet_ai import ADMETModel
        _model = ADMETModel()
        print("ADMET-AI model loaded successfully")
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting ADMET Engine Microservice...")
    get_model()  # Pre-load model
    yield
    # Shutdown
    print("Shutting down ADMET Engine...")


app = FastAPI(
    title="ADMET Engine",
    description="Local ADMET prediction service using Chemprop v2 (ADMET-AI)",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictRequest(BaseModel):
    """Request model for predictions"""
    smiles: List[str]
    include_percentiles: bool = True


class PredictResponse(BaseModel):
    """Response model for predictions"""
    success: bool
    count: int
    predictions: List[Dict[str, Any]]
    engine: str = "admet-ai (Chemprop v2)"
    endpoints: int = 104


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine": "admet-ai",
        "model_loaded": _model is not None
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Predict ADMET properties for molecules.
    
    Args:
        smiles: List of SMILES strings
        
    Returns:
        Predictions for 104 ADMET endpoints + DrugBank percentiles
    """
    try:
        model = get_model()
        
        # Validate input
        if not request.smiles:
            raise HTTPException(status_code=400, detail="No SMILES provided")
        
        if len(request.smiles) > 25:
            raise HTTPException(status_code=400, detail="Maximum 25 molecules per request")
        
        # Run predictions
        print(f"Predicting ADMET for {len(request.smiles)} molecules...")
        predictions_df = model.predict(request.smiles)
        
        # Convert to list of dicts
        predictions = predictions_df.to_dict(orient="records")
        
        return {
            "success": True,
            "count": len(predictions),
            "predictions": predictions,
            "engine": "admet-ai (Chemprop v2)",
            "endpoints": 104
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ADMET-AI model not available: {str(e)}"
        )
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/predict-single")
async def predict_single(smiles: str):
    """
    Predict ADMET properties for a single molecule (GET endpoint).
    
    Args:
        smiles: SMILES string
        
    Returns:
        Predictions for 104 ADMET endpoints
    """
    try:
        model = get_model()
        
        if not smiles:
            raise HTTPException(status_code=400, detail="No SMILES provided")
        
        predictions_df = model.predict([smiles])
        prediction = predictions_df.iloc[0].to_dict()
        
        return {
            "success": True,
            "smiles": smiles,
            "prediction": prediction,
            "engine": "admet-ai (Chemprop v2)",
            "endpoints": 104
        }
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7861))
    uvicorn.run(
        "admet_engine:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1,
    )
