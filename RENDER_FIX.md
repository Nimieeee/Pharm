# Fix for Render Deployment Error

## Problem
The deployment is failing with:
```
pydantic_settings.exceptions.SettingsError: error parsing value for field "ALLOWED_ORIGINS" from source "EnvSettingsSource"
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

## Root Cause
The `ALLOWED_ORIGINS` environment variable is not set or is empty in your Render environment variables, causing Pydantic Settings to fail when trying to parse it.

## Solution

### Step 1: Update Code (✅ DONE)
The code has been updated to:
- Use Pydantic v2 syntax (`field_validator` instead of `validator`)
- Handle empty `ALLOWED_ORIGINS` gracefully with fallback defaults
- Accept both comma-separated strings and JSON arrays

### Step 2: Set Environment Variable in Render

Go to your Render dashboard and add/update the `ALLOWED_ORIGINS` environment variable:

**Option 1: Comma-separated string (Recommended)**
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://pharmgpt.netlify.app,https://pharmgpt.vercel.app,https://pharmgpt-frontend.vercel.app
```

**Option 2: If you want to add more origins**
Add your production frontend URL(s):
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://pharmgpt.netlify.app,https://pharmgpt.vercel.app,https://pharmgpt-frontend.vercel.app,https://your-production-frontend.com
```

### Step 3: Redeploy
After setting the environment variable:
1. Commit and push the updated `config.py` file
2. Render will automatically redeploy
3. Or manually trigger a redeploy in the Render dashboard

## What Changed

### Updated `backend/app/core/config.py`:
1. ✅ Migrated from Pydantic v1 `@validator` to v2 `@field_validator`
2. ✅ Added `model_config` using `SettingsConfigDict`
3. ✅ Changed `ALLOWED_ORIGINS` type to `Union[List[str], str]` to accept both formats
4. ✅ Added robust fallback handling for empty/missing `ALLOWED_ORIGINS`
5. ✅ Updated all validators to use Pydantic v2 syntax

## Testing Locally
To test that the changes work:

```bash
cd backend
# Test with no ALLOWED_ORIGINS set
unset ALLOWED_ORIGINS
python -c "from app.core.config import settings; print(settings.ALLOWED_ORIGINS)"

# Test with comma-separated string
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"
python -c "from app.core.config import settings; print(settings.ALLOWED_ORIGINS)"
```

Both should work without errors now!

## Notes
- The code now has sensible defaults if `ALLOWED_ORIGINS` is not set
- The validator handles empty strings gracefully
- Works with both comma-separated strings and JSON arrays for maximum flexibility
