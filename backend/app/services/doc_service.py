"""
Document Generation Service

Structured document generation with outline-first workflow.
Similar to slide_service.py but for DOCX documents.

Supported document types:
- report: Executive Summary, Introduction, Findings, Discussion, Conclusion
- manuscript: Abstract, Introduction, Methods, Results, Discussion, References
- whitepaper: Problem Statement, Solution, Technical Details, Case Studies
- case_report: Case Presentation, Investigations, Treatment, Outcome
"""

import json
import asyncio
from typing import Optional, Callable, Dict, List, Any
from app.services.multi_provider import MultiProviderService
from app.services.manuscript_formatter import ManuscriptFormatter


class DocService:
    """
    Document generation orchestrator.
    
    Features:
    - AI-powered outline generation
    - Section content refinement
    - Professional DOCX assembly via ManuscriptFormatter
    - Table of Contents auto-generation
    """
    
    DOC_TYPES = {
        "report": {
            "sections": ["Executive Summary", "Introduction", "Findings", "Discussion", "Conclusion"],
            "citation_style": "apa"
        },
        "manuscript": {
            "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion"],
            "citation_style": "vancouver"
        },
        "whitepaper": {
            "sections": ["Executive Summary", "Problem Statement", "Proposed Solution", "Technical Details", "Case Studies", "Implementation", "Conclusion"],
            "citation_style": "apa"
        },
        "case_report": {
            "sections": ["Abstract", "Introduction", "Case Presentation", "Investigations", "Treatment", "Outcome", "Discussion"],
            "citation_style": "vancouver"
        }
    }
    
    def __init__(self, multi_provider: MultiProviderService):
        self.ai = multi_provider
        self.formatter = ManuscriptFormatter(multi_provider)
    
    async def generate_outline(
        self,
        topic: str,
        doc_type: str = "report",
        context: str = None,
        uploaded_text: str = None
    ) -> dict:
        """
        Step 1: Generate editable document outline.
        
        Uses Groq fast mode for speed (~2-3 seconds).
        """
        doc_config = self.DOC_TYPES.get(doc_type, self.DOC_TYPES["report"])
        sections = doc_config["sections"]
        
        source_context = ""
        if uploaded_text:
            source_context = f"\n\nSource material to distill:\n{uploaded_text[:8000]}"
        elif context:
            source_context = f"\n\nAdditional context:\n{context}"
        
        sections_list = "\n".join([f"- {s}" for s in sections])
        
        prompt = f"""Create a structured {doc_type} document outline on: "{topic}"
{source_context}

Required sections:
{sections_list}

Return ONLY valid JSON with this exact schema:
{{
  "title": "Document Title",
  "subtitle": "Optional subtitle",
  "doc_type": "{doc_type}",
  "sections": [
    {{
      "heading": "Section Name",
      "key_points": ["Point 1", "Point 2"],
      "subsections": [
        {{"heading": "Subsection", "key_points": ["Point"]}}
      ]
    }}
  ]
}}

Rules:
- Each section should have 3-5 key points
- Subsections are optional
- Key points should be concise (under 15 words)
- Maintain logical flow between sections
"""
        
        response = await self.ai.chat_completion(
            mode="fast",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3
        )
        
        # Extract JSON from response
        json_str = response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        
        outline = json.loads(json_str)
        outline["doc_type"] = doc_type
        
        return outline
    
    async def generate_document(
        self,
        outline: dict,
        on_progress: Optional[Callable] = None
    ) -> bytes:
        """
        Step 2: Generate full DOCX from approved outline.
        
        For each section:
        1. AI generates full prose (NOT bullets - paragraph format)
        2. Build DOCX with python-docx
        """
        total_sections = len(outline.get("sections", []))
        
        # Build structured content for formatter
        structured = {
            "title": outline.get("title", "Document"),
            "subtitle": outline.get("subtitle", ""),
            "sections": []
        }
        
        # Generate content for each section
        for i, section in enumerate(outline.get("sections", [])):
            if on_progress:
                await on_progress({
                    "step": "content",
                    "current": i + 1,
                    "total": total_sections,
                    "message": f"Writing section: {section.get('heading', 'Section')}"
                })
            
            # Generate full prose for this section
            section_content = await self._generate_section_content(
                section,
                outline.get("title", "Document"),
                outline.get("doc_type", "report")
            )
            structured["sections"].append(section_content)
        
        # Build DOCX
        if on_progress:
            await on_progress({
                "step": "assembly",
                "current": total_sections,
                "total": total_sections,
                "message": "Assembling document..."
            })
        
        docx_bytes = self.formatter.build_docx(
            structured,
            style=outline.get("doc_type", "report")
        )
        
        if on_progress:
            await on_progress({
                "step": "complete",
                "current": total_sections,
                "total": total_sections,
                "message": "Document ready!"
            })
        
        return docx_bytes
    
    async def _generate_section_content(
        self,
        section: dict,
        document_title: str,
        doc_type: str
    ) -> dict:
        """Use AI to expand section key points into full prose"""
        heading = section.get("heading", "Section")
        key_points = section.get("key_points", [])
        subsections = section.get("subsections", [])
        
        points_str = "\n".join([f"- {p}" for p in key_points])
        
        prompt = f"""Expand these key points into professional prose for a {doc_type} document titled "{document_title}".

Section: {heading}
Key Points:
{points_str}

Rules:
- Write in paragraph form (NOT bullet points)
- Use academic/professional tone
- 200-400 words per section
- Include transitions between ideas
- Cite evidence where appropriate
- Return as JSON: {{"content": "Full prose text...", "subsections": [{{"heading": "...", "content": "..."}}]}}
"""
        
        try:
            response = await self.ai.chat_completion(
                mode="detailed",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.4
            )
            
            expanded = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            result = {
                "heading": heading,
                "content": expanded.get("content", ""),
                "subsections": expanded.get("subsections", [])
            }
            
            # Process subsections recursively
            for sub in subsections:
                sub_content = await self._generate_section_content(
                    sub, document_title, doc_type
                )
                result["subsections"].append(sub_content)
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: use key points as content
            return {
                "heading": heading,
                "content": "\n\n".join(key_points),
                "subsections": []
            }


# Factory function for dependency injection
def get_doc_service(multi_provider: MultiProviderService = None) -> DocService:
    """Get DocService with injected dependencies"""
    if not multi_provider:
        from app.services.multi_provider import get_multi_provider
        multi_provider = get_multi_provider()
    
    return DocService(multi_provider)
