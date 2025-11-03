# Quick Reference: XLSX, CSV, PPTX Support

## Installation
```bash
cd backend && pip install -r requirements.txt
```

## Upload File
```bash
curl -X POST "http://localhost:8000/api/v1/chat/conversations/{id}/documents" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@file.xlsx"
```

## New Formats

| Format | Extension | Features |
|--------|-----------|----------|
| Excel | .xlsx | Multi-sheet, headers, data |
| CSV | .csv | Auto-encoding, headers, data |
| PowerPoint | .pptx | Slides, notes, text |

## Key Files Modified

- `backend/requirements.txt` - Added openpyxl, pandas, unstructured
- `backend/app/services/document_loaders.py` - Added 3 loaders
- `backend/app/api/v1/endpoints/chat.py` - Updated extensions
- `backend/app/api/v1/endpoints/ai.py` - Updated docs

## Testing
```bash
python backend/tests/test_new_formats.py
```

## Documentation

- **README_NEW_FORMATS.md** - Complete guide
- **QUICK_START_NEW_FORMATS.md** - Quick start
- **DEPLOYMENT_CHECKLIST_NEW_FORMATS.md** - Deploy guide
- **IMPLEMENTATION_COMPLETE.md** - Status summary

## Status: ✅ READY FOR DEPLOYMENT
