# CORS Issue Fix for Render Deployment

## Problem
Getting CORS errors and 520 errors when accessing the backend from Vercel:
```
Access to XMLHttpRequest at 'https://pharmgpt-backend.onrender.com/api/v1/chat/conversations/.../documents' 
from origin 'https://pharmgpt.vercel.app' has been blocked by CORS policy
```

## Root Cause
**Render Free Tier Cold Starts**: The 520 error is caused by Render's free tier spinning down after 15 minutes of inactivity. When a request comes in:
1. Backend is asleep (spun down)
2. Request arrives → 520 error during 30-60 second wake-up period
3. After wake-up, backend works normally until next idle period

This is NOT a CORS configuration issue - the CORS headers are correct, but they can't be sent when the backend is waking up.

## Solutions Implemented

### ✅ Automatic Retry Logic (Already Added)
The frontend now automatically retries failed requests with intelligent backoff:
- Detects 520 errors and network failures
- Waits 45 seconds on first retry (cold start time)
- Waits 15 seconds on second retry
- Shows user-friendly messages: "Backend is waking up..."

### ✅ User Feedback (Already Added)
- Toast notification: "Uploading document... (Backend may take 30-60s to wake up if idle)"
- Better error messages for 520 errors
- Automatic retry happens in background

## Additional Solutions (Optional)

### Option 1: Keep Backend Awake (Free)
Set up a free ping service to prevent cold starts:

**Using UptimeRobot (Recommended):**
1. Sign up at https://uptimerobot.com (free)
2. Create new monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://pharmgpt-backend.onrender.com/health`
   - Monitoring Interval: 10 minutes
3. This keeps your backend awake 24/7

**Using Cron-Job.org:**
1. Sign up at https://cron-job.org (free)
2. Create new cron job:
   - URL: `https://pharmgpt-backend.onrender.com/health`
   - Schedule: Every 10 minutes
   - Method: GET

### Option 2: Upgrade Render Plan ($7/month)
- No cold starts
- Always-on backend
- Better performance
- More memory/CPU

### Option 3: Accept Cold Starts (Current Setup)
- Free tier with automatic retry
- Users wait 30-60s on first request after idle
- Subsequent requests are fast
- Good for low-traffic apps

## Current CORS Configuration
The backend is configured to allow:
- `http://localhost:3000` - Local development
- `http://localhost:5173` - Vite dev server
- `https://*.netlify.app` - Netlify deployments (via regex)
- `https://pharmgpt.netlify.app` - Production Netlify
- `https://*.vercel.app` - Vercel deployments (via regex)
- `https://pharmgpt.vercel.app` - Production Vercel
- `https://pharmgpt-frontend.vercel.app` - Alternative Vercel domain

## Troubleshooting

### If 520 errors persist:
1. Check Render service logs for memory issues
2. Consider upgrading Render plan if on free tier (free tier has limitations)
3. Check if Mistral API calls are timing out or failing
4. Verify Supabase connection is working

### If CORS errors persist after 520 is fixed:
1. Verify the Origin header in the request matches exactly
2. Check if there are any proxy/CDN issues with Vercel
3. Try adding explicit ALLOWED_ORIGINS environment variable on Render

## Quick Test
After deploying, test with:
```bash
# Test health endpoint
curl https://pharmgpt-backend.onrender.com/health

# Test with CORS headers
curl https://pharmgpt-backend.onrender.com/health \
  -H "Origin: https://pharmgpt.vercel.app"
```
