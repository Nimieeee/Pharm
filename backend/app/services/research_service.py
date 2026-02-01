import asyncio
import os
import logging
from typing import AsyncGenerator
import json

logger = logging.getLogger(__name__)

class ResearchService:
    def __init__(self):
        # Path to MiroFlow on VPS
        self.miroflow_path = "/var/www/MiroFlow"
        self.venv_python = "/home/ubuntu/.local/bin/uv"  # Using uv to run

    async def stream_deep_research(self, task: str, conversation_id: str) -> AsyncGenerator[str, None]:
        """
        Runs MiroFlow deep research and yields output line by line as SSE events.
        """
        cmd = [
            "uv", "run", "main.py", "trace",
            "--config_file_name=agent_quickstart_reading", # Default config
            f"--task={task}"
        ]
        
        # We need to run this command INSIDE the MiroFlow directory
        # effectively: cd /var/www/MiroFlow && uv run ...
        
        logger.info(f"🚀 Starting Deep Research: {task} for conv {conversation_id}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "uv", "run", "main.py", "trace",
                f"--config_file_name=agent_quickstart_reading",
                f"--task={task}",
                cwd=self.miroflow_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ} # Pass current env (with API keys hopefully)
            )

            # Yield initial status
            yield self._format_sse({"type": "status", "status": "started", "message": "Initializing research agent..."})

            if process.stdout:
                async for line in process.stdout:
                    decoded = line.decode().strip()
                    if not decoded:
                        continue
                        
                    logger.debug(f"RESEARCH STDOUT: {decoded}")
                    
                    # Parse MiroFlow output to user-friendly messages
                    # MiroFlow outputs logs. We can try to heuristic parse them.
                    # For now, just forward relevant lines or generic "Thinking"
                    
                    if "Thinking" in decoded or "Action" in decoded:
                         yield self._format_sse({
                             "type": "progress", 
                             "message": decoded[:100] + "..." 
                         })
                    elif "Answer" in decoded:
                        # This might be the final answer
                         yield self._format_sse({
                             "type": "progress", 
                             "message": "Generating final answer..." 
                         })

            # Wait for completion
            await process.wait()
            
            # Read any stderr
            if process.stderr:
                err = await process.stderr.read()
                if err:
                    logger.error(f"RESEARCH STDERR: {err.decode()}")

            if process.returncode == 0:
                # In a real impl, we'd parse the actual output file or the final stdout block
                # For this MVP, we might assume the last stdout was the answer or check the log file
                yield self._format_sse({
                    "type": "complete", 
                    "report": "Research completed. (Output parsing to be implemented based on actual log format)"
                })
            else:
                 yield self._format_sse({"type": "error", "message": "Research process failed."})

        except Exception as e:
            logger.error(f"Research failed: {e}")
            yield self._format_sse({"type": "error", "message": str(e)})

    def _format_sse(self, data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"
