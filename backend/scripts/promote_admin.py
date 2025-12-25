
import os
import sys
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path to import config if needed, but we'll specific vars directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file in parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Prefer service role key for admin actions, fallback to anon
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"Error: Supabase credentials not found. URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}")
    print(f"Checked .env at: {env_path}")
    sys.exit(1)

def promote(email: str):
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. Check if user exists
        print(f"Checking for user {email}...")
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if not response.data:
            print(f"❌ User with email {email} not found.")
            return

        user = response.data[0]
        print(f"✅ Found user: {user.get('first_name', 'No Name')} {user.get('last_name', '')} (ID: {user['id']})")
        print(f"Current Admin Status: {user.get('is_admin', False)}")

        if user.get('is_admin'):
            print("INFO: User is already an admin.")
            return

        # 2. Update is_admin -> True
        print(f"Promoting user to admin...")
        update_response = supabase.table("users").update({"is_admin": True}).eq("id", user['id']).execute()
        
        if update_response.data:
            print(f"✅ Successfully promoted {email} to Admin!")
            print(f"New data: {update_response.data[0]}")
        else:
            print("❌ Failed to update user. Check if the table has 'is_admin' column or if permissions allow update.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email>")
        sys.exit(1)
        
    email = sys.argv[1]
    promote(email)
