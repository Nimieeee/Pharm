import asyncio
import time
from uuid import UUID
from datetime import datetime

# Build a mock payload similar to what the DB returns
num_messages = 500
all_messages = []
for i in range(num_messages):
    pid = f"msg_{i-1}" if i > 0 else None
    all_messages.append({
        "id": f"msg_{i}",
        "conversation_id": "conv_1",
        "role": "user" if i % 2 == 0 else "assistant",
        "content": "test",
        "parent_id": pid,
        "created_at": f"2026-02-21T10:00:0{i%10}.000Z"
    })

def test_downward_walk():
    start = time.time()
    
    children_map = {}
    for m in all_messages:
        pid = m.get("parent_id")
        if pid:
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(m)
    
    current_id = "msg_0"
    thread = []
    
    for _ in range(100):
        children = children_map.get(current_id, [])
        if not children:
            break
        
        def get_created_at_timestamp(child):
            created_at = child["created_at"]
            if isinstance(created_at, str):
                try:
                    return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    return created_at
            return created_at

        latest_child = max(children, key=get_created_at_timestamp)
        thread.append(latest_child)
        current_id = latest_child["id"]
        
    print(f"Time taken: {(time.time() - start) * 1000:.2f}ms")

test_downward_walk()
