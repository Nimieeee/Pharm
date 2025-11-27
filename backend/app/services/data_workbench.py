"""
Data Analysis Workbench Service
LangGraph-style agent for data visualization and analysis
"""

import os
import json
import httpx
import asyncio
import subprocess
import tempfile
import base64
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from uuid import UUID
from pathlib import Path

from app.core.config import settings


# ============================================================================
# STATE DEFINITION
# ============================================================================

@dataclass
class StyleConfig:
    """Visual style configuration extracted from reference image."""
    figure_facecolor: str = "#ffffff"
    axes_facecolor: str = "#ffffff"
    palette: List[str] = field(default_factory=lambda: ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
    font_family: str = "sans-serif"
    grid: Dict[str, Any] = field(default_factory=lambda: {"visible": True, "style": "--", "alpha": 0.3})


@dataclass
class WorkbenchState:
    """State for the data analysis workbench."""
    file_path: str
    file_name: str
    style_description: Optional[str] = None
    style_image_base64: Optional[str] = None
    style_config: Optional[StyleConfig] = None
    plotting_code: Optional[str] = None
    result_image_base64: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    analysis_report: Optional[str] = None
    error: Optional[str] = None
    status: str = "initialized"


# ============================================================================
# DATA WORKBENCH SERVICE
# ============================================================================

class DataWorkbenchService:
    """
    LangGraph-style agent for data analysis and visualization.
    Nodes: StyleExtractor -> Coder -> Executor -> Analyst
    """
    
    def __init__(self):
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.python_script_path = Path(__file__).parent.parent.parent / "scripts" / "analysis_worker.py"
    
    async def _call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        json_mode: bool = False,
        image_base64: Optional[str] = None
    ) -> str:
        """Call Mistral LLM with optional vision support."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Handle image input for vision
                if image_base64:
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    })
                    model = "pixtral-large-latest"  # Vision model
                else:
                    messages.append({"role": "user", "content": user_prompt})
                    model = "mistral-small-latest"
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3 if json_mode else 0.7,
                    "max_tokens": 4000
                }
                
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                
                response = await client.post(
                    f"{self.mistral_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.mistral_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"LLM error: {response.status_code} - {response.text}")
                    return ""
                    
        except Exception as e:
            print(f"LLM call error: {e}")
            return ""
    
    # ========================================================================
    # NODE A: STYLE EXTRACTOR (Vision Node)
    # ========================================================================
    
    async def _node_style_extractor(self, state: WorkbenchState) -> WorkbenchState:
        """Extract visual style from reference image or description."""
        state.status = "extracting_style"
        
        system_prompt = """You are a Design System Expert for Scientific Publishing.
Your task is to extract visual style parameters from charts so they can be replicated in Matplotlib.

If given an image, analyze it carefully. If given a text description, interpret the style.

Output ONLY valid JSON with these exact keys:
{
    "figure_facecolor": "#hex_color",
    "axes_facecolor": "#hex_color", 
    "palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
    "font_family": "serif" or "sans-serif",
    "grid": {"visible": true/false, "style": "--" or "-" or ":", "alpha": 0.0-1.0}
}"""

        if state.style_image_base64:
            # Use vision to extract style from image
            user_prompt = "Analyze this chart image and extract its visual style parameters."
            response = await self._call_llm(
                system_prompt, 
                user_prompt, 
                json_mode=True,
                image_base64=state.style_image_base64
            )
        elif state.style_description:
            # Use text description
            user_prompt = f"""Extract style parameters for this description: "{state.style_description}"

Common styles:
- "Nature" style: Clean, minimal, blue/gray palette
- "Financial Times" style: Pink/salmon background (#fff1e5), dark text
- "The Economist" style: Red accent (#e3120b), clean sans-serif
- "Dark mode": Dark background (#1a1a2e), bright accent colors"""
            
            response = await self._call_llm(system_prompt, user_prompt, json_mode=True)
        else:
            # Default scientific style
            state.style_config = StyleConfig()
            return state
        
        try:
            style_data = json.loads(response)
            state.style_config = StyleConfig(
                figure_facecolor=style_data.get("figure_facecolor", "#ffffff"),
                axes_facecolor=style_data.get("axes_facecolor", "#ffffff"),
                palette=style_data.get("palette", ["#1f77b4", "#ff7f0e", "#2ca02c"]),
                font_family=style_data.get("font_family", "sans-serif"),
                grid=style_data.get("grid", {"visible": True, "style": "--", "alpha": 0.3})
            )
        except json.JSONDecodeError:
            state.style_config = StyleConfig()
        
        return state

    # ========================================================================
    # NODE B: THE CODER (Logic Node)
    # ========================================================================
    
    async def _node_coder(self, state: WorkbenchState) -> WorkbenchState:
        """Generate Python visualization code based on data and style."""
        state.status = "generating_code"
        
        # First, get data preview
        preview = await self._get_data_preview(state.file_path)
        
        style_json = json.dumps({
            "figure_facecolor": state.style_config.figure_facecolor,
            "axes_facecolor": state.style_config.axes_facecolor,
            "palette": state.style_config.palette,
            "font_family": state.style_config.font_family,
            "grid": state.style_config.grid
        }, indent=2) if state.style_config else "{}"
        
        system_prompt = """You are a Python Data Visualization Expert using Matplotlib and Seaborn.

Context: You have a pandas DataFrame called `df` already loaded.

Goal: Write Python code to create an insightful visualization of the data.

Style Instructions:
- Apply the provided style_config using plt.rcParams and sns.set_palette
- If background is dark (luminance < 0.5), use white text colors
- Create publication-quality figures

CRITICAL CONSTRAINTS:
- NEVER use plt.show()
- Save the final plot to a BytesIO object named `buf` using: plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
- Return ONLY the Python code block, no explanations
- The code must be self-contained and executable"""

        user_prompt = f"""Data Preview:
{preview}

Style Configuration:
{style_json}

Generate Python visualization code for this data. Choose appropriate chart types based on the columns."""

        response = await self._call_llm(system_prompt, user_prompt, json_mode=False)
        
        # Extract code from response (handle markdown code blocks)
        code = response.strip()
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        state.plotting_code = code.strip()
        return state
    
    async def _get_data_preview(self, file_path: str) -> str:
        """Get a preview of the data file."""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=5)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, nrows=5)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
                df = df.head(5)
            else:
                df = pd.read_csv(file_path, nrows=5)
            
            preview = f"Columns: {list(df.columns)}\n"
            preview += f"Data types: {df.dtypes.to_dict()}\n"
            preview += f"Sample rows:\n{df.to_string()}"
            return preview
        except Exception as e:
            return f"Error reading file: {e}"
    
    # ========================================================================
    # NODE C: THE EXECUTOR (Bridge to Python)
    # ========================================================================
    
    async def _node_executor(self, state: WorkbenchState) -> WorkbenchState:
        """Execute Python code via subprocess."""
        state.status = "executing"
        
        try:
            # Prepare payload for Python worker
            payload = {
                "file_path": state.file_path,
                "plotting_code": state.plotting_code,
                "style_config": {
                    "figure_facecolor": state.style_config.figure_facecolor,
                    "axes_facecolor": state.style_config.axes_facecolor,
                    "palette": state.style_config.palette,
                    "font_family": state.style_config.font_family,
                    "grid": state.style_config.grid
                } if state.style_config else {}
            }
            
            # Run Python worker
            process = await asyncio.create_subprocess_exec(
                "python", str(self.python_script_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=json.dumps(payload).encode())
            
            if process.returncode != 0:
                state.error = f"Python execution failed: {stderr.decode()}"
                return state
            
            # Parse result
            result = json.loads(stdout.decode())
            
            if result.get("error"):
                state.error = result["error"]
            else:
                state.result_image_base64 = result.get("image")
                state.statistics = result.get("stats")
            
        except Exception as e:
            state.error = f"Executor error: {str(e)}"
        
        return state
    
    # ========================================================================
    # NODE D: THE ANALYST (Reviewer)
    # ========================================================================
    
    async def _node_analyst(self, state: WorkbenchState) -> WorkbenchState:
        """Generate scientific analysis of the data."""
        state.status = "analyzing"
        
        if not state.statistics:
            state.analysis_report = "No statistics available for analysis."
            return state
        
        system_prompt = """You are a Senior Biostatistician reviewing experimental data.

Task: Write a professional scientific analysis report in Markdown format.

Guidelines:
- Highlight significant correlations (if any)
- Point out anomalies or outliers
- Describe data distributions
- Use scientific language (variance, distribution, trend, significance)
- Be concise but thorough
- Format with headers and bullet points"""

        stats_summary = json.dumps(state.statistics, indent=2, default=str)
        
        user_prompt = f"""Analyze this statistical summary and write a scientific report:

{stats_summary}

Focus on:
1. Data quality (missing values, outliers)
2. Key distributions and trends
3. Correlations between variables
4. Recommendations for further analysis"""

        response = await self._call_llm(system_prompt, user_prompt, json_mode=False)
        state.analysis_report = response
        state.status = "complete"
        
        return state
    
    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================
    
    async def analyze(
        self,
        file_path: str,
        file_name: str,
        style_description: Optional[str] = None,
        style_image_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the full analysis workflow."""
        
        state = WorkbenchState(
            file_path=file_path,
            file_name=file_name,
            style_description=style_description,
            style_image_base64=style_image_base64
        )
        
        try:
            # Node A: Extract style
            state = await self._node_style_extractor(state)
            
            # Node B: Generate code
            state = await self._node_coder(state)
            
            # Node C: Execute
            state = await self._node_executor(state)
            
            # Node D: Analyze
            if not state.error:
                state = await self._node_analyst(state)
            
        except Exception as e:
            state.error = str(e)
            state.status = "error"
        
        return {
            "status": state.status,
            "image": state.result_image_base64,
            "statistics": state.statistics,
            "analysis": state.analysis_report,
            "style_config": {
                "figure_facecolor": state.style_config.figure_facecolor,
                "axes_facecolor": state.style_config.axes_facecolor,
                "palette": state.style_config.palette,
                "font_family": state.style_config.font_family,
                "grid": state.style_config.grid
            } if state.style_config else None,
            "code": state.plotting_code,
            "error": state.error
        }
