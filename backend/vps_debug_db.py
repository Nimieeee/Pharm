
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

def check_db():
    print("Checking database from VPS perspective...")
    # Load env from the deploy folder
    env_path = "/root/pharmgpt-backend-deploy/.env"
    if not os.path.exists(env_path):
        print(f"❌ Env file not found at {env_path}")
        return

    with open(env_path) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Credentials missing")
        return

    supabase = create_client(url, key)
    
    # The user ID we saw in the logs
    target_user_id = "bef05b9e-7f4a-422f-8f77-c88af779e9aa"
    
    print(f"Querying conversations for user: {target_user_id}")
    result = supabase.table("conversations").select("*").eq("user_id", target_user_id).execute()
    
    print(f"Result count: {len(result.data)}")
    for c in result.data[:3]:
        print(f" - {c['id']}: {c['title']}")

if __name__ == "__main__":
    check_db()
