# Fixing "Failed to delete conversation" Error

## Problem
You're seeing "Failed to delete conversation" because:
1. Row Level Security (RLS) is enabled on your Supabase database
2. The backend needs the Service Role Key to bypass RLS for trusted operations

## Solution

### Step 1: Get Your Service Role Key
1. Go to your **Supabase Dashboard**: https://app.supabase.com
2. Select your project
3. Go to **Settings** → **API**
4. Find the **service_role** key (click "Reveal" to see it)
5. **Copy the entire key** (starts with `eyJ...`)

### Step 2: Add to Backend Environment

#### If running locally:
Add to `/Users/mac/Desktop/phhh/backend/.env`:
```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-actual-key-here
```

Then restart your backend:
```bash
cd /Users/mac/Desktop/phhh/backend
# Kill existing process
# Restart with: uvicorn app.main:app --reload
```

#### If deployed on Render:
1. Go to your **Render Dashboard**: https://dashboard.render.com
2. Select your **backend service**
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Add:
   - **Key**: `SUPABASE_SERVICE_ROLE_KEY`
   - **Value**: `eyJ...` (your service role key)
6. Click **Save Changes**
7. Render will automatically redeploy

### Step 3: Verify It's Working

Check your backend logs. You should see:
```
✅ Database client initialized (using Service Role Key)
```

Instead of:
```
✅ Database client initialized (using Anon Key)
```

### Step 4: Test Delete Again
Try deleting a conversation from the frontend. It should now work!

## Why This Is Needed

**Row Level Security (RLS)** in Supabase works like this:
- **Anon Key**: Limited access, can only see data that matches `auth.uid()`
- **Service Role Key**: Full access, bypasses RLS (used by trusted backends)

Your backend is trusted (it does its own auth via JWT), so it should use the Service Role Key to perform operations on behalf of authenticated users.

## Security Note
⚠️ **Never expose the Service Role Key in your frontend!** 
- Frontend uses Anon Key ✅
- Backend uses Service Role Key ✅
- Never commit Service Role Key to Git ✅ (it's in `.env` which is gitignored)
