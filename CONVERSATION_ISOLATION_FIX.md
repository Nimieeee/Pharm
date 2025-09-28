# Fix: Documents Appearing in Wrong Conversations

## Problem
Documents uploaded in one conversation are appearing in other conversations, breaking conversation isolation.

## Root Cause
The database schema is missing the `user_session_id` columns that are required for proper conversation isolation. The application code is correctly trying to isolate documents by both `conversation_id` and `user_session_id`, but the database doesn't have these columns yet.

## Solution

### Step 1: Update Database Schema
1. Go to your **Supabase Dashboard**
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste the contents of `user_session_schema_update.sql`
5. Click **Run** to execute the schema update

### Step 2: Verify Fix
1. Restart your Streamlit app
2. Click the "🔍 Check Conversation Isolation" button in the app
3. Verify that the isolation is working correctly

### Step 3: Re-upload Documents (Optional)
If you have existing documents that were uploaded before the fix:
- They will have the default `user_session_id = 'anonymous'`
- Consider re-uploading important documents in their specific conversations for better isolation

## What the Fix Does

The schema update adds:
- `user_session_id` column to `conversations`, `messages`, and `document_chunks` tables
- Proper indexes for efficient filtering
- Updated database functions that respect conversation and user session boundaries

## Verification

After applying the fix:
- Documents uploaded in Conversation A will ONLY appear in Conversation A
- Documents uploaded in Conversation B will ONLY appear in Conversation B
- Each conversation maintains its own isolated knowledge base

## Files Involved
- `user_session_schema_update.sql` - The schema update to run
- `fix_conversation_isolation.py` - Diagnostic script (optional)
- `simple_app.py` - Updated with isolation check button