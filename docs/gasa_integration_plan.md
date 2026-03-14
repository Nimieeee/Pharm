# GASA + SAS Integration Plan for ADMET Lab

## Research Summary

### GASA (Graph Attention-based Synthetic Accessibility)
- **Purpose**: Binary classification (Easy-to-Synthesize [0] vs Hard-to-Synthesize [1])
- **Input**: SMILES string → Graph representation
- **Output**: 
  - `pred`: [0] or [1] (ES or HS)
  - `pos`: Probability of easy-to-synthesize (0.0-1.0)
  - `neg`: Probability of hard-to-synthesize (0.0-1.0)
- **Model**: Graph Neural Network with attention mechanism
- **Training**: 800K compounds from ChEMBL, GDBChEMBL, ZINC15
- **Paper**: J. Chem. Inf. Model. 2022, DOI: 10.1021/acs.jcim.2c00038

### RDKit SAS (Synthetic Accessibility Score)
- **Purpose**: Continuous score (1-10)
- **Scale**: 1 = easy, 10 = difficult
- **Method**: Fragment contribution + molecular complexity
- **Computation**: Fast, no ML model required

### Complementary Value
| Aspect | RDKit SAS | GASA |
|--------|-----------|------|
| **Type** | Continuous (1-10) | Binary (0/1) + probabilities |
| **Method** | Fragment-based | Graph Neural Network |
| **Speed** | Fast (<1ms) | Slower (requires GNN inference) |
| **Interpretation** | Lower = easier | 0 = easy, 1 = hard |
| **Use Case** | Quick screening | ML-based assessment |

## Implementation Strategy

### Phase 1: Backend Service (gasa_service.py)
```python
class GASAService:
    - Load pretrained GASA model (gasa.pth)
    - Convert SMILES to graph (gasa_utils.py)
    - Run inference
    - Return pred, pos, neg
```

### Phase 2: ADMET Integration
```python
# In admet_service.py
async def predict_synthetic_accessibility(smiles: str) -> dict:
    rdkit_sas = calculate_rdkit_sas(smiles)
    gasa_pred, gasa_pos, gasa_neg = await gasa_service.predict(smiles)
    
    return {
        "rdkit_sas": rdkit_sas,
        "rdkit_interpretation": interpret_sas(rdkit_sas),
        "gasa_prediction": gasa_pred[0],
        "gasa_easy_probability": gasa_pos[0],
        "gasa_hard_probability": gasa_neg[0],
        "consensus": get_consensus(rdkit_sas, gasa_pred[0])
    }
```

### Phase 3: Frontend Display
```tsx
// In LabDashboard.tsx
<div className="mt-4 p-4 rounded-xl bg-purple-50 dark:bg-purple-950/20 border border-purple-200">
  <h3 className="font-semibold mb-3">Synthetic Accessibility</h3>
  
  {/* RDKit SAS */}
  <div className="mb-3">
    <div className="flex justify-between text-sm mb-1">
      <span>RDKit SAS Score</span>
      <span className="font-medium">{sas.rdkit_sas.toFixed(1)}</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full ${getSASColor(sas.rdkit_sas)}`}
        style={{ width: `${(sas.rdkit_sas / 10) * 100}%` }}
      />
    </div>
    <p className="text-xs mt-1">{sas.rdkit_interpretation}</p>
  </div>
  
  {/* GASA */}
  <div>
    <div className="flex justify-between text-sm mb-1">
      <span>GASA Prediction</span>
      <span className="font-medium">{gasa.gasa_prediction === 0 ? 'Easy' : 'Hard'}</span>
    </div>
    <div className="flex gap-2 text-xs">
      <span className="text-green-600">Easy: {(gasa.gasa_easy_probability * 100).toFixed(1)}%</span>
      <span className="text-red-600">Hard: {(gasa.gasa_hard_probability * 100).toFixed(1)}%</span>
    </div>
  </div>
  
  {/* Consensus */}
  {sas.consensus && (
    <p className="text-xs mt-3 font-medium text-purple-700">
      Consensus: {sas.consensus}
    </p>
  )}
</div>
```

## Deployment Considerations

### Model Files Required
- `model/gasa.pth` (pretrained weights, ~50MB)
- `model/gasa.json` (hyperparameters)
- `model/gasa_utils.py` (graph generation)
- `model/model.py` (GASA model definition)

### Dependencies
- torch (already installed)
- dgl 0.7.0+ (needs installation)
- dgllife 0.2.6+ (needs installation)
- RDKit (already installed)
- hyperopt (for model loading)

### RAM Impact
- Model size: ~50MB
- Inference memory: ~200MB peak
- Acceptable for VPS (8GB RAM, ~2GB free)

## Decision

**RECOMMENDATION**: Implement both SAS and GASA as complementary metrics.

**Rationale**:
1. RDKit SAS provides fast, interpretable baseline
2. GASA adds ML-based assessment with attention mechanism
3. Consensus between both increases confidence
4. Minimal RAM impact (~200MB peak)
5. Adds unique value vs other ADMET platforms

**Implementation Priority**: P1 (High value, moderate complexity)
