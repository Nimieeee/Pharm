
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env before importing app
load_dotenv("/opt/pharmgpt-backend/.env")

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db

async def inspect():
    db = get_db()
    try:
        # Get specific user seen in logs
        response = db.table("users").select("*").eq("id", "bef05b9e-7f4a-422f-8f77-c88af779e9aa").execute()
        if response.data:
            user = response.data[0]
            print(f"User found: {user.get('email')}")
            print(f"First Name: '{user.get('first_name')}'")
            print(f"Last Name: '{user.get('last_name')}'")
        else:
            print("User not found, listing first 5 users:")
            response = db.table("users").select("id,email,first_name").limit(5).execute()
            for u in response.data:
                print(u)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
