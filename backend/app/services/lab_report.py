"""
Lab Report Generation Service
Generates structured lab reports from experimental data and methodology documents
"""

import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from uuid import UUID
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LabReportSection:
    """A section of the lab report."""
    title: str
    content: str
    subsections: List['LabReportSection'] = field(default_factory=list)


@dataclass
class LabReportState:
    """State for lab report generation."""
    experiment_type: str
    data_context: str  # Extracted from uploaded files
    methodology: str   # From lab manual/methodology document
    user_instructions: Optional[str] = None
    
    # Generated sections
    title: Optional[str] = None
    introduction: Optional[str] = None
    materials_methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None
    references: Optional[List[Dict[str, str]]] = None
    
    error: Optional[str] = None
    status: str = "initialized"


class LabReportService:
    """
    Service for generating structured lab reports from experimental data.
    Uses AI to analyze data, extract methodology, and generate formatted reports.
    """
    
    def __init__(self):
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
    
    async def _call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str,
        json_mode: bool = False
    ) -> str:
        """Call Mistral LLM."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": "mistral-large-latest",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 8000
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
                    logger.error(f"LLM error: {response.status_code} - {response.text}")
                    return ""
                    
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return ""
    
    async def generate_report(
        self,
        experiment_type: str,
        data_context: str,
        methodology: str,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete lab report.
        
        Args:
            experiment_type: Type of experiment (e.g., "Therapeutic Index Determination")
            data_context: Extracted data from uploaded files (tables, images, etc.)
            methodology: Methodology text from lab manual
            user_instructions: Additional user instructions
            
        Returns:
            Dict containing all report sections and metadata
        """
        state = LabReportState(
            experiment_type=experiment_type,
            data_context=data_context,
            methodology=methodology,
            user_instructions=user_instructions
        )
        
        try:
            # Generate all sections
            state = await self._generate_title(state)
            state = await self._generate_introduction(state)
            state = await self._generate_materials_methods(state)
            state = await self._generate_results(state)
            state = await self._generate_discussion(state)
            state = await self._generate_conclusion(state)
            state = await self._generate_references(state)
            
            state.status = "complete"
            
        except Exception as e:
            state.error = str(e)
            state.status = "error"
            logger.error(f"Report generation failed: {e}")
        
        return self._format_report(state)
    
    async def _generate_title(self, state: LabReportState) -> LabReportState:
        """Generate the report title."""
        state.status = "generating_title"
        
        prompt = f"""Based on this experiment type and data, generate a concise, scientific title for the lab report.

Experiment Type: {state.experiment_type}
Data Summary: {state.data_context[:500]}

Return ONLY the title, nothing else."""
        
        response = await self._call_llm(
            "You are a scientific writing expert. Generate precise, professional lab report titles.",
            prompt
        )
        
        state.title = response.strip().strip('"')
        return state
    
    async def _generate_introduction(self, state: LabReportState) -> LabReportState:
        """Generate the introduction section with in-text citations."""
        state.status = "generating_introduction"
        
        system_prompt = """You are a pharmaceutical sciences expert writing lab report introductions.

Guidelines:
- Provide background context for the experiment
- Explain key concepts and their clinical/research significance
- Include in-text citations using [Author et al., Year] format
- End with a clear statement of the experiment's objectives
- Be concise but thorough (2-3 paragraphs)"""

        user_prompt = f"""Write the Introduction section for this lab report:

Experiment Type: {state.experiment_type}
Data Overview: {state.data_context[:800]}
{f"User Instructions: {state.user_instructions}" if state.user_instructions else ""}

Include proper in-text citations for scientific concepts mentioned."""

        state.introduction = await self._call_llm(system_prompt, user_prompt)
        return state
    
    async def _generate_materials_methods(self, state: LabReportState) -> LabReportState:
        """Generate materials and methods section."""
        state.status = "generating_methods"
        
        system_prompt = """You are a pharmaceutical sciences expert writing lab report methodology sections.

Guidelines:
- Divide into Materials and Methodology subsections
- List all materials, equipment, and reagents used
- Describe procedures in past tense, passive voice
- Include specific doses, concentrations, and parameters from the data
- Reference any standard protocols used"""

        user_prompt = f"""Write the Materials and Methods section for this lab report:

Experiment Type: {state.experiment_type}
Methodology from Lab Manual:
{state.methodology}

Experimental Data (extract parameters from here):
{state.data_context}

Format with clear subsections: 3.1 Materials and 3.2 Methodology"""

        state.materials_methods = await self._call_llm(system_prompt, user_prompt)
        return state
    
    async def _generate_results(self, state: LabReportState) -> LabReportState:
        """Generate results section with tables and calculations."""
        state.status = "generating_results"
        
        system_prompt = """You are a pharmaceutical sciences expert analyzing experimental data.

Guidelines:
- Present data in well-formatted markdown tables
- Perform all necessary calculations (e.g., LD50, ED50, Therapeutic Index)
- Show calculation formulas in LaTeX format: $TI = \\frac{LD_{50}}{ED_{50}}$
- Describe trends and patterns in the data
- Do NOT interpret the significance - save that for Discussion"""

        user_prompt = f"""Write the Results section for this lab report:

Experiment Type: {state.experiment_type}

Raw Experimental Data:
{state.data_context}

Tasks:
1. Create properly formatted data tables
2. Perform all calculations (show work)
3. Report calculated values (e.g., LD50, ED50, TI)
4. Describe what the data shows objectively"""

        state.results = await self._call_llm(system_prompt, user_prompt)
        return state
    
    async def _generate_discussion(self, state: LabReportState) -> LabReportState:
        """Generate discussion section."""
        state.status = "generating_discussion"
        
        system_prompt = """You are a pharmaceutical sciences expert writing lab report discussions.

Guidelines:
- Interpret the significance of your results
- Compare to literature values and expected outcomes
- Discuss clinical implications
- Address sources of error and limitations
- Include in-text citations [Author et al., Year]
- Be analytical, not just descriptive"""

        # Include previously generated results for context
        user_prompt = f"""Write the Discussion section for this lab report:

Experiment Type: {state.experiment_type}

Results Summary:
{state.results[:1500] if state.results else state.data_context}

Discuss:
1. What the results mean
2. How they compare to expected/literature values
3. Clinical/research implications
4. Limitations and sources of error
5. Suggestions for improvement"""

        state.discussion = await self._call_llm(system_prompt, user_prompt)
        return state
    
    async def _generate_conclusion(self, state: LabReportState) -> LabReportState:
        """Generate conclusion section."""
        state.status = "generating_conclusion"
        
        prompt = f"""Write a concise Conclusion (1-2 paragraphs) for this lab report:

Experiment: {state.experiment_type}
Key Results: {state.results[:500] if state.results else "See data"}
Main Discussion Points: {state.discussion[:500] if state.discussion else "See discussion"}

The conclusion should:
- Summarize what was achieved
- State the key findings with specific values
- Briefly note clinical/scientific significance
- NOT introduce new information"""

        state.conclusion = await self._call_llm(
            "You are a scientific writer creating concise, impactful conclusions.",
            prompt
        )
        return state
    
    async def _generate_references(self, state: LabReportState) -> LabReportState:
        """Generate references list using Serper API for real academic sources."""
        state.status = "generating_references"
        
        # Import Serper service
        from app.services.serper import SerperService
        serper = SerperService()
        
        # Build search query from experiment type and key terms
        search_query = f"{state.experiment_type} pharmacology methodology"
        
        try:
            # Fetch real academic references from Google Scholar
            references_data = await serper.get_references_for_topic(
                topic=search_query,
                include_scholar=True,
                include_news=False,
                include_patents=False,
                max_total=8
            )
            
            if references_data:
                state.references = [
                    {"text": ref.get("citation_text", ref.get("title", ""))}
                    for ref in references_data
                ]
                logger.info(f"📚 Fetched {len(state.references)} real references from Serper")
            else:
                # Fallback to LLM-generated references if Serper fails
                logger.warning("⚠️ Serper returned no results, using LLM fallback")
                state.references = await self._generate_references_fallback(state)
                
        except Exception as e:
            logger.error(f"Serper reference search failed: {e}")
            # Fallback to LLM-generated references
            state.references = await self._generate_references_fallback(state)
        
        return state
    
    async def _generate_references_fallback(self, state: LabReportState) -> List[Dict[str, str]]:
        """Fallback: Generate references using LLM when Serper is unavailable."""
        all_text = "\n".join([
            state.introduction or "",
            state.discussion or ""
        ])
        
        prompt = f"""Based on the in-text citations used in this text, generate a proper reference list in APA format:

{all_text}

For each [Author et al., Year] citation mentioned, provide the full reference.
If you cited concepts without references, add appropriate pharmacology/toxicology textbook references.

Format each reference on a new line. Include 5-8 references total."""

        response = await self._call_llm(
            "You are a scientific reference librarian. Generate accurate, properly formatted references.",
            prompt
        )
        
        references = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                if line[0].isdigit() and "." in line[:3]:
                    line = line.split(".", 1)[1].strip()
                references.append({"text": line})
        
        return references
    
    def _format_report(self, state: LabReportState) -> Dict[str, Any]:
        """Format the complete report as a dictionary."""
        return {
            "status": state.status,
            "title": state.title or f"Lab Report: {state.experiment_type}",
            "sections": {
                "introduction": state.introduction,
                "materials_methods": state.materials_methods,
                "results": state.results,
                "discussion": state.discussion,
                "conclusion": state.conclusion
            },
            "references": state.references or [],
            "error": state.error,
            # Full markdown report
            "full_report": self._compile_markdown(state)
        }
    
    def _compile_markdown(self, state: LabReportState) -> str:
        """Compile all sections into a complete markdown document."""
        sections = [
            f"# {state.title or 'Lab Report'}\n",
            "## 1. Introduction\n",
            state.introduction or "",
            "\n## 2. Materials and Methods\n",
            state.materials_methods or "",
            "\n## 3. Results\n",
            state.results or "",
            "\n## 4. Discussion\n",
            state.discussion or "",
            "\n## 5. Conclusion\n",
            state.conclusion or "",
            "\n## 6. References\n"
        ]
        
        if state.references:
            for i, ref in enumerate(state.references, 1):
                sections.append(f"{i}. {ref.get('text', '')}\n")
        
        return "\n".join(sections)
