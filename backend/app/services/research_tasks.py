import asyncio
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.core.container import container
from app.models.conversation import MessageCreate
from app.core.database import async_db_execute

logger = logging.getLogger(__name__)

class BackgroundResearchService:
    """
    Manages background research tasks, providing concurrency control
    and task queue management via Supabase.
    
    Uses ServiceContainer for all dependencies - NO direct instantiation.
    """

    def __init__(self, db=None, max_concurrent: int = 5):
        self._container = None
        self._db = db
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    @property
    def container(self):
        """Get container - should be initialized at app startup"""
        if self._container is None:
            # Don't try to initialize - should already be initialized at app startup
            self._container = container
        return self._container
    
    @property
    def research_service(self):
        """Get deep research service from container"""
        return self.container.get('deep_research_service')
    
    @property
    def chat_service(self):
        """Get chat service from container"""
        return self.container.get('chat_service')

    @property
    def db(self):
        """Get database connection from container"""
        return self.container.get_db()

    async def create_task(self, user_id: UUID, conversation_id: UUID, question: str, metadata: Dict[str, Any] = None) -> str:
        """Submit a new research task to the queue"""
        task_data = {
            "user_id": str(user_id),
            "conversation_id": str(conversation_id),
            "research_question": question,
            "status": "PENDING",
            "metadata": metadata or {}
        }
        
        result = await async_db_execute(
            lambda: self.db.table("research_tasks").insert(task_data).execute()
        )
        
        if not result.data:
            raise Exception("Failed to create research task")
            
        return result.data[0]["id"]
        
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch task status and results"""
        result = await async_db_execute(
            lambda: self.db.table("research_tasks").select("*").eq("id", task_id).single().execute()
        )
        return result.data if result and result.data else None
        
    async def get_user_tasks(self, user_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent tasks for a user"""
        result = await async_db_execute(
            lambda: self.db.table("research_tasks")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
        )
        return result.data if result and result.data else []

    async def worker_loop(self):
        """
        Background worker that polls for PENDING tasks and executes them.
        Managed by the main application lifecycle or scheduler.
        """
        logger.info("👷 Research worker loop started")
        while True:
            try:
                # 1. Poll for a pending task
                result = await async_db_execute(
                    lambda: self.db.table("research_tasks")
                        .select("*")
                        .eq("status", "PENDING")
                        .order("created_at", desc=False)
                        .limit(1)
                        .execute()
                )
                
                if not result.data:
                    # No tasks, sleep and retry
                    await asyncio.sleep(10)
                    continue
                    
                task = result.data[0]
                task_id = task["id"]
                
                # 2. Execute task with concurrency limit
                # We don't 'await' the process_task here to allow the worker 
                # to pick up multiple tasks up to the semaphore limit.
                asyncio.create_task(self._run_task_with_semaphore(task))
                
                # Small delay before picking next task to avoid tight loop
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Worker loop error: {e}")
                await asyncio.sleep(30) # Longer sleep on error

    async def _run_task_with_semaphore(self, task: Dict[str, Any]):
        """Run a task constrained by the global semaphore"""
        async with self.semaphore:
            await self._process_task(task)

    async def _process_task(self, task: Dict[str, Any]):
        """Execute the actual research for a task"""
        task_id = task["id"]
        user_id = task["user_id"]
        conversation_id = task["conversation_id"]
        question = task["research_question"]
        
        logger.info(f"🧪 Processing research task {task_id} for user {user_id}")
        
        try:
            # 1. Mark as RUNNING
            await async_db_execute(
                lambda: self.db.table("research_tasks")
                    .update({"status": "RUNNING", "started_at": datetime.utcnow().isoformat()})
                    .eq("id", task_id)
                    .execute()
            )
            
            # 2. Execute Research
            # We use the service's non-streaming run_research
            state = await self.research_service.run_research(
                question=question,
                user_id=UUID(user_id)
            )
            
            # 3. Save result to conversation
            if state.final_report and conversation_id:
                try:
                    assistant_message = MessageCreate(
                        conversation_id=UUID(conversation_id),
                        role="assistant",
                        content=state.final_report,
                        metadata={
                            "mode": "deep_research",
                            "task_id": task_id,
                            "citations_count": len(state.citations)
                        }
                    )
                    await self.chat_service.add_message(assistant_message, UUID(user_id))
                except Exception as msg_err:
                    logger.error(f"⚠️ Failed to save task result to conversation: {msg_err}")

            # 4. Mark as COMPLETED
            await async_db_execute(
                lambda: self.db.table("research_tasks")
                    .update({
                        "status": "COMPLETED", 
                        "result_report": state.final_report,
                        "finished_at": datetime.utcnow().isoformat()
                    })
                    .eq("id", task_id)
                    .execute()
            )
            logger.info(f"✅ Research task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Research task {task_id} failed: {e}")
            # Mark as FAILED
            await async_db_execute(
                lambda: self.db.table("research_tasks")
                    .update({
                        "status": "FAILED", 
                        "error_detail": str(e),
                        "finished_at": datetime.utcnow().isoformat()
                    })
                    .eq("id", task_id)
                    .execute()
            )
