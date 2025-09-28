# SentenceTransformers PyTorch Tensor Fix

## Problem Fixed
```
Error initializing embeddings: Cannot copy out of meta tensor; no data! 
Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() 
when moving module from meta to a different device.
```

This PyTorch meta tensor error was preventing SentenceTransformers from initializing properly.

## Solution Implemented

### ✅ PyTorch Meta Tensor Fix
- **Safe Tensor Handling**: Properly handles PyTorch meta tensors
- **Device Management**: Forces CPU device to avoid tensor issues
- **Multiple Strategies**: 4 different initialization approaches for SentenceTransformers
- **Tensor Migration**: Uses `to_empty()` for meta tensors when needed

## Technical Changes

### rag.py
1. **`_initialize_sentence_transformers()`**: New method with PyTorch tensor fixes
2. **`_create_sentence_transformer_safe()`**: Safe tensor handling with device management
3. **`_create_sentence_transformer_with_torch_fix()`**: Explicit meta tensor handling
4. **Prioritized SentenceTransformers**: Primary choice over OpenAI embeddings

## Initialization Strategies

### Strategy 1: Safe Device Management
```python
torch.set_default_device('cpu')
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
model = model.to('cpu')
```

### Strategy 2: Meta Tensor Fix
```python
# Handle meta tensors explicitly
for param in model.parameters():
    if param.is_meta:
        param.data = torch.empty_like(param, device='cpu')
```

### Strategy 3: Alternative Model Paths
- `sentence-transformers/all-MiniLM-L6-v2`
- `all-MiniLM-L12-v2`

## Status Messages

### Success:
- "✅ SentenceTransformer initialized successfully (method X)"

### Failure:
- "❌ No embeddings available"
- "💡 Fix with: pip install --upgrade sentence-transformers torch"

## Key Features

1. **Keeps SentenceTransformers**: No fallback to text search
2. **Proper Vector Search**: Full semantic similarity when working
3. **Clean Error Handling**: Clear messages without spam
4. **Device Safety**: Ensures CPU usage to avoid tensor issues

## Requirements

For best results, ensure you have compatible versions:
```bash
pip install --upgrade sentence-transformers torch
```

The fix specifically addresses the PyTorch meta tensor issue while maintaining full SentenceTransformer functionality.