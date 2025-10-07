# CORS Fix for Vercel Deployment

## What Was Fixed

Updated the backend to allow requests from your Vercel deployment:

1. **backend/app/core/config.py** - Added Vercel domains to `ALLOWED_ORIGINS`
2. **backend/main.py** - Updated CORS regex to include both Netlify and Vercel domains

## Changes Made

### Config (backend/app/core/config.py)
```python
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://*.netlify.app",
    "https://pharmgpt.netlify.app",
    "https://*.vercel.app",  # NEW
    "https://pharmgpt-frontend.vercel.app",  # NEW
]
```

### CORS Middleware (backend/main.py)
```python
allow_origin_regex=r"https://.*\.(netlify|vercel)\.app"
```

This regex now matches:
- `https://anything.netlify.app`
- `https://anything.vercel.app`

## Deploy the Backend Fix

You need to redeploy your backend for the CORS changes to take effect.

### Option 1: Git Push (Recommended)
```bash
git add backend/app/core/config.py backend/main.py
git commit -m "Add CORS support for Vercel deployment"
git push
```

Render will automatically redeploy your backend.

### Option 2: Manual Deploy on Render
1. Go to your Render dashboard
2. Find your backend service
3. Click "Manual Deploy" → "Deploy latest commit"

## Verify the Fix

After backend redeployment:

1. Wait for Render deployment to complete (~2-3 minutes)
2. Refresh your Vercel frontend
3. Try logging in again

The CORS error should be resolved.

## Alternative: Environment Variable Approach

If you want more flexibility without code changes, you can also set CORS origins via environment variable on Render:

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://pharmgpt.netlify.app,https://pharmgpt-frontend.vercel.app
```

Add this in Render Dashboard → Environment → Add Environment Variable

Then redeploy.

## Troubleshooting

If you still see CORS errors:

1. **Check backend logs** on Render to confirm it restarted
2. **Clear browser cache** or try incognito mode
3. **Verify the exact Vercel URL** matches what you added
4. **Check browser console** for the exact origin being blocked
