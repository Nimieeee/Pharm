"""
Slide Generation Service — Research-Grade presentation platform.

Step 1: generate_outline()  — AI creates JSON slide structure with research context
Step 2: refine_content()    — AI writes full prose per slide (with contextual memory + academic review)
Step 3: generate_images()   — Pollinations creates visuals (with art direction)
Step 4: assemble_pptx()     — Design Engine builds the file with technical diagrams
"""

import json
import asyncio
from typing import Optional, Callable, Dict, List, Any
from app.services.multi_provider import MultiProviderService
from app.services.image_gen import ImageGenerationService
from app.services.design_engine import DesignEngine
from app.services.deep_research import ResearchTools

# Phase 1: Premium Quality - Art Direction Styles
ART_DIRECTION_STYLES = {
    "corporate": "Professional corporate vector illustration, minimalist, flat design, white background, unified color palette, clean lines. No text.",
    "photorealistic": "High-quality photorealistic render, professional studio lighting, clean composition, corporate setting, sharp focus. No text.",
    "minimalist": "Ultra-minimalist line art, monochrome, geometric shapes, ample white space, elegant simplicity. No text.",
    "isometric": "Isometric 3D illustration, soft shadows, pastel colors, clean modern style, technical precision. No text.",
    "sketch": "Professional hand-drawn sketch style, blueprint aesthetic, technical drawing, white background. No text."
}

# Research-Grade Content Constraints - Academic Standards
CONTENT_CONSTRAINTS = """
RESEARCH-GRADE CONTENT STANDARDS (ENFORCED):
- Maximum 5-6 bullet points per slide (academic density)
- Maximum 20 words per bullet point
- Include specific citations [Author, Year] or [PMID: XXXXX]
- Use technical terminology appropriate for expert audiences
- Include quantitative data with units where applicable
- Avoid generic phrases - use specific research findings
- Each slide MUST cite at least 1 source from provided research context
"""


class SlideService:
    """
    Research-grade slide generation orchestrator.
    
    Features:
    - AI-powered outline generation with PubMed/Tavily research integration
    - Content refinement with academic reviewer validation
    - Pollinations image generation per slide
    - Professional PPTX assembly via Design Engine with technical diagrams
    """
    
    def __init__(self, multi_provider: MultiProviderService,
                 image_gen: ImageGenerationService):
        self.ai = multi_provider
        self.image_gen = image_gen
        self.design = DesignEngine()
        self.research_tools = ResearchTools()
        self._slide_context = []  # Track content to prevent repetition
        self._used_phrases = set()  # Track used key phrases
        self._vibe = "corporate"  # Default art direction style
        self._research_context = []  # Store research abstracts for citations
    
    async def _fetch_research_context(self, topic: str) -> List[Dict[str, Any]]:
        """
        Fetch research abstracts from PubMed for citation support.
        
        Returns list of research papers with abstracts, citations, and metadata.
        """
        try:
            # Search PubMed for relevant research
            pubmed_results = await self.research_tools.search_pubmed(topic, max_results=10)
            
            if not pubmed_results:
                # Fallback to web search via Tavily
                web_results = await self.research_tools.search_web(topic, max_results=5)
                return web_results
            
            return pubmed_results
        except Exception as e:
            print(f"⚠️ Research fetch failed: {e}")
            return []
    
    async def generate_outline(
        self,
        topic: str,
        context: str = None,
        num_slides: int = 12,
        uploaded_text: str = None,
        use_research: bool = True,
        theme: str = "ocean_gradient"
    ) -> dict:
        """
        Step 1: AI generates editable JSON outline with research backing.
        
        Features:
        - Fetches 5-10 PubMed abstracts for citation support
        - Uses Groq fast mode for speed (~2-3 seconds)
        - Includes slide-level citations in output schema
        """
        source_context = ""
        research_context_str = ""
        
        # Fetch research abstracts if enabled
        if use_research and not uploaded_text:
            print(f"🔬 Fetching research context for: {topic}")
            research_papers = await self._fetch_research_context(topic)
            self._research_context = research_papers
            
            if research_papers:
                # Format research context for prompt
                research_summaries = []
                for i, paper in enumerate(research_papers[:8], 1):  # Use top 8 papers
                    citation = paper.get('apa_citation', f"[{i}]")
                    abstract = paper.get('abstract', 'No abstract available')[:500]
                    research_summaries.append(
                        f"[{i}] {citation}\nAbstract: {abstract}\n"
                    )
                
                research_context_str = "\n\nRESEARCH CONTEXT (Cite these in slides):\n" + "\n".join(research_summaries)
        
        if uploaded_text:
            # Truncate to 8000 chars for fast mode token limit
            source_context = f"\n\nSource material to distill:\n{uploaded_text[:8000]}"
        elif context:
            source_context = f"\n\nAdditional context:\n{context}"
        
        prompt = f"""Create a RESEARCH-GRADE presentation outline on: "{topic}"
Number of slides: {num_slides}
{source_context}
{research_context_str}

{CONTENT_CONSTRAINTS}

Return ONLY valid JSON with this exact schema:
{{
  "title": "Presentation Title",
  "subtitle": "Subtitle",
  "theme": "{theme}",
  "vibe": "corporate",
  "slides": [
    {{
      "slide_number": 1,
      "layout": "title",
      "title": "Slide Title",
      "subtitle_takeaway": "One strong sentence summarizing this slide's main point",
      "supporting_data": [
        {{
          "bullet": "Specific stat or fact with numbers [Author, Year]",
          "context": "Brief explanation of why this matters"
        }}
      ],
      "speaker_notes": "Full conversational paragraph explaining the why and how with citations. Should be 3-4 sentences minimum.",
      "bullets": ["Point 1 with citation", "Point 2 with citation"],
      "image_prompt": "description of professional scientific illustration",
      "chart_data": null,
      "data": null,
      "citations": ["Author et al., Year (Journal)"]
    }}
  ]
}}

Layout options: "title", "two_column", "bullets_only", "data_callout", "image_full", "comparison", "timeline", "diagram"
Theme options: "ocean_gradient", "forest_moss", "coral_energy", "warm_terracotta",
               "charcoal_minimal", "teal_trust", "berry_cream", "sage_calm",
               "cherry_bold", "midnight_executive"
Vibe options: "corporate", "photorealistic", "minimalist", "isometric", "sketch"

MANDATORY RULES:
1. First slide MUST be layout "title" - only presentation title and subtitle
2. Last slide MUST be layout "title" - simple "Thank You" with contact placeholder ONLY, NO bullets, NO content
3. Second-to-last slide MUST be "conclusion" layout with exactly 3-5 high-level thematic takeaways summarizing entire presentation
4. Never have 3 consecutive slides with the same layout
5. Each slide MUST have:
   - subtitle_takeaway: ONE strong sentence (max 25 words) summarizing the slide's main point
   - supporting_data: 3-5 specific data points with NUMBERS and CITATIONS (e.g., "85% accuracy [Smith, 2023]")
   - speaker_notes: 3-4 sentence conversational paragraph explaining context and implications
   - citations: List of [Author, Year] or [PMID: XXXXX] strings cited on this slide
6. Use SPECIFIC named entities - NO generic phrases:
   - Include at least 1 specific research citation per slide
   - Include at least 1 specific technology/AI model name (e.g., "AlphaFold", "GPT-4", "BERT")
   - Include real metrics with numbers and units (e.g., "85% accuracy", "3-month reduction")
7. Each slide must advance the narrative - no repetition of concepts
8. Set image_prompt to null if text-heavy or no visual benefit
9. Image prompt should describe professional scientific/medical illustration
10. For data slides: include "chart_data": {{"type": "bar", "labels": ["A", "B"], "values": [10, 20]}}
11. For technical flow diagrams: use layout "diagram" and include "mermaid_code": "flowchart TD..."

EXAMPLE GOOD SLIDE:
{{
  "slide_number": 3,
  "layout": "two_column",
  "title": "AI in Clinical Trials",
  "subtitle_takeaway": "Machine learning reduces trial costs by 40% through automated patient screening [Johnson et al., 2023].",
  "supporting_data": [
    {{"bullet": "BERT predicts dropouts with 95% accuracy [Chen et al., 2022]", "context": "Early identification prevents costly late-stage failures"}},
    {{"bullet": "NLP screening cuts recruitment by 40% [Smith et al., 2023]", "context": "Automated eligibility matching speeds enrollment"}},
    {{"bullet": "$2.3B annual savings industry-wide [McKinsey, 2023]", "context": "Economic impact of AI adoption"}}
  ],
  "speaker_notes": "Traditional clinical trials face two major bottlenecks: patient recruitment and dropout prediction. As Chen et al. (2022) demonstrated, AI models like BERT can predict patient dropout with 95% accuracy by analyzing electronic health records. Meanwhile, Smith et al. (2023) showed NLP-powered screening reduces recruitment timelines by 40%. This translates to $2.3B in annual industry savings (McKinsey, 2023).",
  "citations": ["Chen et al., 2022", "Smith et al., 2023", "McKinsey, 2023"]
}}

EXAMPLE BAD SLIDE (DO NOT CREATE):
{{
  "slide_number": 3,
  "title": "AI in Clinical Trials",
  "bullets": ["AI helps trials", "Reduces costs", "Faster screening"]
}}
"""
        
        response = await self.ai.generate(
            mode="fast",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3
        )
        
        # Extract JSON from response (handle markdown code blocks and loose text)
        json_str = response.strip()
        try:
            # Look for JSON block if it's wrapped in markdown
            if "```" in json_str:
                # Try to find content between ```json and ``` or just ``` and ```
                import re
                blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
                if blocks:
                    json_str = blocks[0]
                else:
                    # Fallback: just strip the markers
                    json_str = json_str.split("```")[1]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
            
            # Final attempt: find the first { and last } to isolate the JSON object
            if not (json_str.strip().startswith("{") and json_str.strip().endswith("}")):
                import re
                match = re.search(r"(\{.*\})", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)
            
            outline = json.loads(json_str)
        except (json.JSONDecodeError, IndexError, Exception) as e:
            import logging
            logger = logging.getLogger("app.slide_service")
            logger.error(f"Failed to parse slide outline JSON. Error: {str(e)}")
            logger.error(f"Raw AI Response: {response}")
            raise Exception(f"AI response was not valid JSON. {str(e)}")
        
        # Apply design intelligence adjustments
        outline = self.design.analyze_and_adjust(outline)
        
        return outline
    
    async def generate_slides(
        self,
        outline: dict,
        generate_images: bool = True,
        on_progress: Optional[Callable] = None
    ) -> bytes:
        """
        Steps 2-4: Generate content, images, assemble PPTX.

        Reports progress via on_progress callback (for SSE).
        Returns PPTX file as bytes.

        Phase 1 Improvements:
        - Contextual Memory: Pass previous slide summary to prevent repetition
        - Global Art Direction: Wrap all image prompts with style definition
        """
        # Phase 1: Reset context tracking for new presentation
        self._slide_context = []

        total_slides = len(outline["slides"])
        theme = self.design.get_theme(outline.get("theme", "ocean_gradient"))
        content_results = []
        image_results = {}

        # Step 2: Generate full content per slide (parallel where possible)
        for i, slide in enumerate(outline["slides"]):
            if on_progress:
                await on_progress({
                    "step": "content",
                    "current": i + 1,
                    "total": total_slides,
                    "message": f"Writing slide {i+1}: {slide['title']}"
                })

            # Phase 1: Get previous slide summary for contextual memory
            prev_summary = None
            if self._slide_context:
                prev_summary = self._slide_context[-1]["summary"]

            # Refine bullet points into fuller content with contextual memory
            refined = await self._refine_slide_content(slide, outline["title"], prev_summary)
            content_results.append(refined)

        # Step 3: Generate images via Pollinations with Global Art Direction Wrapper
        if generate_images:
            image_tasks = []
            for i, slide in enumerate(outline["slides"]):
                if slide.get("image_prompt"):
                    image_tasks.append((i, slide["image_prompt"]))

            for idx, (slide_idx, prompt) in enumerate(image_tasks):
                if on_progress:
                    await on_progress({
                        "step": "images",
                        "current": idx + 1,
                        "total": len(image_tasks),
                        "message": f"Generating image {idx+1}/{len(image_tasks)}"
                    })

                try:
                    # Phase 1: Global Art Direction Wrapper
                    # Wrap user prompt with strict style definition
                    wrapped_prompt = self._wrap_image_prompt(prompt, outline.get("vibe", "corporate"))

                    img_bytes = await self.image_gen.fetch_image_from_pollinations(
                        prompt=wrapped_prompt,
                        model="flux",
                        width=1024,
                        height=768,
                        seed=42 + slide_idx
                    )
                    image_results[slide_idx] = img_bytes
                except Exception as e:
                    # Image failure is non-fatal — slide works without image
                    print(f"⚠️ Image generation failed for slide {slide_idx}: {e}")
                    image_results[slide_idx] = None

        # Step 4: Assemble PPTX with Design Engine
        if on_progress:
            await on_progress({
                "step": "assembly",
                "current": total_slides,
                "total": total_slides,
                "message": "Assembling presentation..."
            })

        pptx_bytes = self.design.assemble_pptx(
            outline=outline,
            content=content_results,
            images=image_results,
            theme=theme
        )

        if on_progress:
            await on_progress({
                "step": "complete",
                "current": total_slides,
                "total": total_slides,
                "message": "Presentation ready!"
            })

        return pptx_bytes

    def _wrap_image_prompt(self, prompt: str, vibe: str = "corporate") -> str:
        """
        Phase 1: Global Art Direction Wrapper

        Wraps user's image prompt with strict style definition to ensure
        visual consistency across all slides.
        """
        # Style definitions by vibe
        style_wrappers = {
            "corporate": "Professional corporate vector illustration, minimalist, flat design, white background, unified blue and gray color palette. No text, no labels, no watermarks.",
            "photorealistic": "Photorealistic scientific photograph, professional lighting, clean background, high detail, natural colors. No text, no labels.",
            "minimalist": "Minimalist line art, simple geometric shapes, single color on white background, clean and modern. No text, no shading.",
            "isometric": "Isometric 3D illustration, clean vector style, soft shadows, pastel colors on white background. No text, no labels.",
            "sketch": "Hand-drawn scientific sketch, pencil style, clean lines, white background, academic illustration style. No text, no shading."
        }

        # Get style wrapper (default to corporate)
        style = style_wrappers.get(vibe, style_wrappers["corporate"])

        # Combine user prompt with style wrapper
        return f"{prompt}. {style}"
    
    async def _refine_slide_content(self, slide: dict, deck_title: str, prev_slide_summary: str = None) -> dict:
        """
        Multi-Agent Research Refinement: Researcher-Writer + Academic Reviewer.

        Phase 3 Improvements:
        - Researcher-Writer: Generates technically dense content with citations
        - Academic Reviewer: Validates accuracy, suggests improvements
        - Relaxed constraints: 5-6 bullets, 20 words/bullet for academic depth
        """
        if slide["layout"] == "title":
            return slide  # Title slides don't need expansion

        # Extract existing content
        subtitle_takeaway = slide.get("subtitle_takeaway", "")
        supporting_data = slide.get("supporting_data", [])
        existing_citations = slide.get("citations", [])

        # Convert supporting_data to bullets
        bullets = [item.get("bullet", "") for item in supporting_data] if supporting_data else slide.get("bullets", [])
        bullets_json = json.dumps(bullets)
        citations_json = json.dumps(existing_citations)

        # Contextual memory - prevent repetition
        context_note = ""
        if prev_slide_summary:
            context_note = f"\n\nPREVIOUS SLIDE SUMMARY: {prev_slide_summary}\nDo NOT repeat concepts or phrases from the previous slide."

        # AGENT 1: Researcher-Writer - Generate technically dense content
        researcher_prompt = f"""You are a Researcher-Writer creating technically dense slide content for: "{deck_title}"

Slide title: {slide['title']}
Current subtitle takeaway: {subtitle_takeaway}
Current supporting data: {bullets_json}
Existing citations: {citations_json}
{context_note}

RESEARCHER-WRITER INSTRUCTIONS:
1. Write for an EXPERT scientific audience (PhD-level researchers, industry scientists)
2. Use technical terminology and domain-specific language
3. Include 4-6 supporting data points (relaxed from 3 for academic density)
4. Each bullet: 15-20 words with specific numbers, units, and citations [Author, Year]
5. Include methodology details where relevant (e.g., "using 10-fold cross-validation on n=1,247 samples")
6. Cite specific research papers using the existing citations or add new ones if needed
7. Subtitle takeaway: ONE strong sentence (max 25 words) with key finding + citation
8. Speaker notes: 4-5 sentence technical explanation including:
   - Experimental methodology
   - Statistical significance
   - Clinical or practical implications
   - Comparison to prior work

Return as JSON:
{{
  "subtitle_takeaway": "...with citation",
  "supporting_data": [
    {{"bullet": "Technical finding with numbers [Citation]", "context": "Technical explanation"}}
  ],
  "speaker_notes": "Technical 4-5 sentence explanation...",
  "citations": ["Author et al., Year"]
}}"""

        try:
            # Step 1: Researcher-Writer generates content
            draft_response = await self.ai.generate(
                mode="detailed",
                messages=[{"role": "user", "content": researcher_prompt}],
                max_tokens=800,
                temperature=0.3
            )

            # Extract JSON from researcher output
            json_str = draft_response.strip()
            if "```" in json_str:
                import re
                blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
                if blocks:
                    json_str = blocks[0]

            if not (json_str.strip().startswith("{") and json_str.strip().endswith("}")):
                import re
                match = re.search(r"(\{.*\})", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)

            draft_content = json.loads(json_str)

            # AGENT 2: Academic Reviewer - Validate and improve
            reviewer_prompt = f"""You are an Academic Reviewer validating slide content for: "{deck_title}"

Slide title: {slide['title']}
DRAFT CONTENT:
- Subtitle: {draft_content.get('subtitle_takeaway', '')}
- Supporting data: {json.dumps(draft_content.get('supporting_data', []))}
- Speaker notes: {draft_content.get('speaker_notes', '')}

ACADEMIC REVIEWER CRITERIA:
1. ACCURACY: Are the technical claims accurate and well-supported?
2. PRECISION: Are numbers, units, and statistics correct?
3. CITATIONS: Are citations properly formatted [Author, Year]?
4. METHODOLOGY: Are experimental methods described accurately?
5. SIGNIFICANCE: Are clinical/practical implications clear?

Provide IMPROVED version as JSON:
{{
  "subtitle_takeaway": "Improved version with citation",
  "supporting_data": [{{"bullet": "...", "context": "..."}}],
  "speaker_notes": "Improved technical explanation",
  "citations": ["Author et al., Year"],
  "reviewer_notes": "Brief note on key improvements made"
}}"""

            # Step 2: Academic Reviewer validates and refines
            review_response = await self.ai.generate(
                mode="detailed",
                messages=[{"role": "user", "content": reviewer_prompt}],
                max_tokens=800,
                temperature=0.2
            )

            # Extract JSON from reviewer output
            json_str = review_response.strip()
            if "```" in json_str:
                import re
                blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
                if blocks:
                    json_str = blocks[0]

            if not (json_str.strip().startswith("{") and json_str.strip().endswith("}")):
                import re
                match = re.search(r"(\{.*\})", json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)

            final_content = json.loads(json_str)

            # Update slide with refined content
            slide["subtitle_takeaway"] = final_content.get("subtitle_takeaway", subtitle_takeaway)
            slide["supporting_data"] = final_content.get("supporting_data", supporting_data)
            slide["speaker_notes"] = final_content.get("speaker_notes", slide.get("speaker_notes", ""))
            slide["citations"] = final_content.get("citations", existing_citations)

            # Backward compatibility: convert supporting_data to bullets
            if slide["supporting_data"]:
                slide["bullets"] = [item.get("bullet", "") for item in slide["supporting_data"]]

            # Store slide summary for next slide's context
            self._slide_context.append({
                "title": slide['title'],
                "subtitle_takeaway": slide["subtitle_takeaway"],
                "bullets": slide["bullets"],
                "summary": f"Slide '{slide['title']}': {slide['subtitle_takeaway']}"
            })

        except (json.JSONDecodeError, Exception) as e:
            import logging
            logging.getLogger("app.slide_service").warning(f"Multi-agent refinement failed: {e}. Using original content.")
            # Keep original content if refinement fails

        return slide


# Factory function for dependency injection
def get_slide_service(multi_provider: MultiProviderService = None,
                      image_gen: ImageGenerationService = None) -> SlideService:
    """Get SlideService with injected dependencies"""
    if not multi_provider:
        from app.services.multi_provider import get_multi_provider
        multi_provider = get_multi_provider()
    
    if not image_gen:
        from app.services.image_gen import get_image_gen
        image_gen = get_image_gen()
    
    return SlideService(multi_provider, image_gen)
