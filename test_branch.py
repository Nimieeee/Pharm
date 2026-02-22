import asyncio
from uuid import uuid4

class MockDB:
    def execute(self):
        class Data:
            data = [
                {"id": "msg1", "parent_id": None},
                {"id": "msg2", "parent_id": None},
                {"id": "msg3", "parent_id": "msg1"}
            ]
        return Data()

def mock_execute(func):
    return func()

async def test():
    class Service:
        class Table:
            def select(self, *args): return self
            def eq(self, *args): return self
            def order(self, *args): return self
            def execute(self):
                class Data:
                    data = [
                        {"id": "msg1", "parent_id": None, "created_at": 1},
                        {"id": "msg2", "parent_id": None, "created_at": 2},
                        {"id": "msg3", "parent_id": "msg1", "created_at": 3}
                    ]
                return Data()
        db = type('DB', (), {'table': lambda self, name: Service.Table()})()
    
    chat_service = Service()
    
    result = await asyncio.sleep(0) or chat_service.db.table("messages").execute()
    all_rows = [r for r in result.data]

    from collections import defaultdict
    parent_groups = defaultdict(list)
    for row in all_rows:
        pid = row.get("parent_id")
        parent_groups[pid].append(row["id"])

    branch_map = {}
    for pid, sibling_ids in parent_groups.items():
        if len(sibling_ids) > 1:
            for idx, mid in enumerate(sibling_ids):
                branch_map[mid] = {
                    "branchIndex": idx + 1,
                    "branchCount": len(sibling_ids),
                    "siblingIds": sibling_ids,
                }
    
    import json
    print(json.dumps(branch_map, indent=2))

asyncio.run(test())
