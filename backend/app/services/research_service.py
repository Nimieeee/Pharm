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
                # Pass current host environment variables to ensure API keys are present
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            # Yield initial status
            yield self._format_sse({"type": "status", "status": "started", "message": "Initializing research agent..."})

            full_stdout = []
            last_activity = asyncio.get_event_loop().time()

            # Read stdout line by line
            if process.stdout:
                while True:
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Send keep-alive if no output for 5 seconds
                        if process.returncode is not None:
                            break # Process finished
                        yield self._format_sse({"type": "ping", "message": "Researching..."})
                        continue

                    if not line:
                        break

                    decoded = line.decode().strip()
                    if not decoded:
                        continue
                    
                    full_stdout.append(decoded)
                    logger.debug(f"RESEARCH STDOUT: {decoded}")
                    last_activity = asyncio.get_event_loop().time() # Update activity timestamp

                    # Heuristic parsing for UI feedback
                    if "Thinking" in decoded or "Action" in decoded:
                        safe_msg = decoded[:150] + "..." if len(decoded) > 150 else decoded
                        yield self._format_sse({
                             "type": "progress", 
                             "message": safe_msg 
                         })
                    elif "Answer" in decoded or "Final" in decoded:
                         yield self._format_sse({
                             "type": "progress", 
                             "message": "Generating final report..." 
                         })

            # Wait for completion
            await process.wait()
            
            # Read any stderr
            if process.stderr:
                err = await process.stderr.read()
                if err:
                    logger.error(f"RESEARCH STDERR: {err.decode()}")

            if process.returncode == 0:
                # Attempt to extract the final markdown report from the accumulated stdout
                # MiroFlow usually prints the final answer at the end
                final_report = "\n".join(full_stdout)  # Fallback to everything
                
                # Simple heuristic: try to find the last large block of text or specific marker
                # For now, we return the full log which might be messy, but debuggable.
                # Ideally, MiroFlow updates should write to a known output file we can read.
                
                yield self._format_sse({
                    "type": "complete", 
                    "report": final_report
                })
            else:
                 yield self._format_sse({"type": "error", "message": f"Research process failed with code {process.returncode}"})

        except Exception as e:
            logger.error(f"Research logging error: {e}", exc_info=True)
            yield self._format_sse({"type": "error", "message": f"Internal error: {str(e)}"})

    def _format_sse(self, data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"
