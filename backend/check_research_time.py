import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env explicitly
# Try to load from pharmgpt-backend.env in the root project folder
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmgpt-backend.env')
if os.path.exists(root_env_path):
    print(f"Loading env from {root_env_path}")
    load_dotenv(root_env_path)
else:
    # Fallback to local .env
    print("Loading env from local .env")
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from app.core.config import settings
from supabase import create_client

def main():
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        print("Error: Supabase credentials not found in settings.")
        return

    # Use service role key if available for better access, else anon key
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    supabase = create_client(settings.SUPABASE_URL, key)

    print("Checking database for recent activity...")
    
    # Check for ANY conversations first (ordered by updated_at)
    try:
        conv_response = supabase.table("conversations")\
            .select("*")\
            .order("updated_at", desc=True)\
            .limit(5)\
            .execute()
            
        conversations = conv_response.data
        print(f"Found {len(conversations)} recent conversations.")
        
        if not conversations:
            print("❌ No conversations found. This database might be empty or different from production.")
            return

        for conv in conversations:
            print(f"\n--- Conversation: {conv.get('title', 'Untitled')} ({conv['id']}) ---")
            print(f"Last Updated: {conv['updated_at']}")
            
            # Get messages for this conversation
            msg_response = supabase.table("messages")\
                .select("*")\
                .eq("conversation_id", conv['id'])\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
                
            msgs = msg_response.data
            for m in msgs:
                role = m['role']
                content_preview = m['content'][:50].replace('\n', ' ') + "..." if m['content'] else "No content"
                meta = m.get('metadata') or {}
                print(f"  [{m['created_at']}] {role}: {content_preview} (Meta: {meta})")
                
                # Check if this is the deep research we are looking for
                if role == 'assistant' and meta.get('mode') == 'deep_research':
                    # Find the user prompt (next message in this reversed list, or previous in time)
                    # Since we only fetched 5, it might be here.
                    created_at = datetime.fromisoformat(m["created_at"].replace('Z', '+00:00'))
                    print(f"  >>> FOUND DEEP RESEARCH generated at {created_at}")
                    
                    # Look for the user message in this small batch
                    # The user message should be *after* this in the list (older time)
                    # We are iterating desc time.
                    
                    # Let's simple iterate the msgs list to find the user match
                    current_idx = msgs.index(m)
                    if current_idx + 1 < len(msgs):
                         prev_msg = msgs[current_idx + 1]
                         if prev_msg['role'] == 'user':
                             user_time = datetime.fromisoformat(prev_msg["created_at"].replace('Z', '+00:00'))
                             duration = created_at - user_time
                             print(f"  >>> DURATION: {duration.total_seconds():.2f} seconds")
                    
    except Exception as e:
        print(f"❌ Error querying conversations: {e}")
        return

    last_research = deep_research_msgs[0]
    conversation_id = last_research["conversation_id"]
    research_end_time = datetime.fromisoformat(last_research["created_at"].replace('Z', '+00:00'))
    
    print(f"Found Deep Research output from: {research_end_time}")
    print(f"Conversation ID: {conversation_id}")
    
    # Now find the user message that triggered this
    # It should be the user message immediately preceding this one in the same conversation
    
    msgs_response = supabase.table("messages")\
        .select("*")\
        .eq("conversation_id", conversation_id)\
        .order("created_at", desc=True)\
        .execute()
        
    conversation_msgs = msgs_response.data
    
    # Find the index of the research message
    research_idx = -1
    for i, msg in enumerate(conversation_msgs):
        if msg["id"] == last_research["id"]:
            research_idx = i
            break
            
    if research_idx != -1 and research_idx + 1 < len(conversation_msgs):
        user_msg = conversation_msgs[research_idx + 1]
        if user_msg["role"] == "user":
            user_time = datetime.fromisoformat(user_msg["created_at"].replace('Z', '+00:00'))
            duration = research_end_time - user_time
            print(f"Start time (User Request): {user_time}")
            print(f"End time (Research Output): {research_end_time}")
            print(f"Duration: {duration}")
            print(f"Duration (seconds): {duration.total_seconds():.2f}")
        else:
            print("Preceding message was not from user. Could not calculate duration.")
    else:
        print("Could not find preceding user message.")

if __name__ == "__main__":
    main()
