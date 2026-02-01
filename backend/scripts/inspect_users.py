
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
        response = db.table("users").select("*").limit(1).execute()
        if response.data:
            print("Existing columns:", list(response.data[0].keys()))
        else:
            print("No users found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
