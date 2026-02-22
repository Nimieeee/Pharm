import asyncio
from supabase import create_client

def get_supabase():
    url = ""
    key = ""
    with open('/var/www/pharmgpt-backend/backend/.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_URL='): url = line.split('=')[1].strip()
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='): key = line.split('=')[1].strip()
    return create_client(url, key)

def run():
    supabase = get_supabase()
    # Get the last 10 messages from any user to see the parent_id state
    res = supabase.table("messages").select("id, role, content, parent_id, created_at").order('created_at', desc=True).limit(10).execute()
    import json
    for msg in res.data:
        msg["content"] = msg["content"][:20] + "..." if msg["content"] else ""
    print(json.dumps(res.data, indent=2))

run()
