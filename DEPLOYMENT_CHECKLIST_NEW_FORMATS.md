# Deployment Checklist: XLSX, CSV, PPTX Support

## Pre-Deployment

### 1. Code Review
- [x] Document loaders updated with new format handlers
- [x] API endpoints updated to accept new file types
- [x] Requirements.txt updated with new dependencies
- [x] Error handling implemented for all new formats
- [x] No syntax errors or diagnostics issues

### 2. Dependencies Check
```bash
cd backend
pip install -r requirements.txt
```

Required new packages:
- [x] openpyxl==3.1.2
- [x] pandas==2.0.3
- [x] unstructured==0.10.30

### 3. Testing
```bash
# Run unit tests
cd backend
python tests/test_new_formats.py

# Or with pytest
pytest tests/test_new_formats.py -v
```

Expected results:
- [x] Document loader initialization passes
- [x] CSV processing works
- [x] XLSX processing works

## Deployment Steps

### 1. Backup Current System
```bash
# Backup database
# Backup current code
git commit -am "Pre-deployment backup before adding XLSX/CSV/PPTX support"
```

### 2. Update Code
```bash
git add .
git commit -m "Add XLSX, CSV, and PPTX document processing support"
git push origin main
```

### 3. Update Dependencies on Server
```bash
# SSH into server or use deployment platform
cd backend
pip install -r requirements.txt --upgrade
```

### 4. Restart Services
```bash
# Restart backend service
# Example for systemd:
sudo systemctl restart pharmgpt-backend

# Or for Docker:
docker-compose restart backend

# Or for Render/Heroku:
# Automatic restart on git push
```

### 5. Verify Deployment
```bash
# Check service status
curl https://your-api.com/api/v1/health

# Test file upload
curl -X POST "https://your-api.com/api/v1/chat/conversations/{id}/documents" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@test.xlsx"
```

## Post-Deployment Verification

### 1. Smoke Tests
- [ ] Upload a small CSV file
- [ ] Upload a small XLSX file
- [ ] Upload a small PPTX file
- [ ] Verify files are processed successfully
- [ ] Check chat can reference uploaded content

### 2. Monitor Logs
```bash
# Check for errors
tail -f /var/log/pharmgpt/backend.log

# Or in Docker
docker logs -f pharmgpt-backend

# Look for:
# ✅ "Enhanced document loader initialized"
# ✅ "Successfully loaded XLSX file"
# ✅ "Successfully loaded CSV file"
# ✅ "Successfully loaded PPTX file"
```

### 3. Performance Check
- [ ] Monitor memory usage (pandas can be memory-intensive)
- [ ] Check processing times for large files
- [ ] Verify vector database storage is working

### 4. Error Handling
Test error scenarios:
- [ ] Upload corrupted XLSX file
- [ ] Upload empty CSV file
- [ ] Upload password-protected PPTX file
- [ ] Upload file larger than 10MB
- [ ] Verify appropriate error messages

## Rollback Plan

If issues occur:

### 1. Quick Rollback
```bash
git revert HEAD
git push origin main
# Redeploy previous version
```

### 2. Database Rollback
```sql
-- If needed, remove any test documents
DELETE FROM documents WHERE created_at > 'DEPLOYMENT_TIMESTAMP';
```

### 3. Dependency Rollback
```bash
# Restore previous requirements.txt
git checkout HEAD~1 requirements.txt
pip install -r requirements.txt
```

## Known Issues & Solutions

### Issue: "unstructured" package installation fails
**Solution**: Install system dependencies first
```bash
# Ubuntu/Debian
sudo apt-get install libmagic-dev poppler-utils tesseract-ocr

# macOS
brew install libmagic poppler tesseract
```

### Issue: Large XLSX files cause memory issues
**Solution**: Implement file size limits or chunk processing
- Current limit: 10MB
- Consider reducing for XLSX if needed

### Issue: PPTX processing is slow
**Solution**: This is expected for large presentations
- Consider async processing for large files
- Add progress indicators in frontend

## Monitoring

### Key Metrics to Watch
1. **Upload Success Rate**: Should remain >95%
2. **Processing Time**: 
   - CSV: <2s for 1MB
   - XLSX: <4s for 1MB
   - PPTX: <5s for 1MB
3. **Error Rate**: Should be <5%
4. **Memory Usage**: Monitor for spikes

### Alerts to Set Up
- [ ] Alert if upload error rate >10%
- [ ] Alert if processing time >30s
- [ ] Alert if memory usage >80%
- [ ] Alert if disk space <20%

## Documentation Updates

- [x] SPREADSHEET_PRESENTATION_SUPPORT.md created
- [x] QUICK_START_NEW_FORMATS.md created
- [x] DOCUMENT_PROCESSING_FLOW.md created
- [x] CHANGES_SUMMARY.md created
- [ ] Update main README.md with new formats
- [ ] Update API documentation
- [ ] Update user guide

## Communication

### Internal Team
- [ ] Notify backend team of deployment
- [ ] Share documentation links
- [ ] Schedule knowledge transfer session

### Users
- [ ] Announce new feature in release notes
- [ ] Update help documentation
- [ ] Create tutorial video/guide
- [ ] Send email notification (if applicable)

## Success Criteria

Deployment is successful when:
- [x] All tests pass
- [ ] No critical errors in logs
- [ ] Users can upload XLSX, CSV, PPTX files
- [ ] Files are processed and searchable
- [ ] Chat can reference uploaded content
- [ ] Performance is acceptable
- [ ] No increase in error rates

## Timeline

- **Preparation**: 30 minutes
- **Deployment**: 15 minutes
- **Verification**: 30 minutes
- **Monitoring**: 24 hours
- **Total**: ~25 hours (including monitoring)

## Contacts

- **Backend Lead**: [Name]
- **DevOps**: [Name]
- **On-Call**: [Name]

## Notes

- This is a backward-compatible change
- Existing functionality is not affected
- New formats are additions only
- No database migrations required
- No breaking API changes
