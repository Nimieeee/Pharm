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
- Write 3 to 4 comprehensive bullet points per slide
- Each bullet should clearly explain a specific mechanism, methodology, or outcome
- Use **bold text** for key scientific terms to maintain readability
- Include specific citations [Author, Year] or [PMID: XXXXX]
- Use technical terminology appropriate for expert audiences
- Include quantitative data with units where applicable
- Avoid generic phrases - use specific research findings
- Each slide MUST cite at least 1 source from provided research context

REQUIRED STRUCTURE FOR TECHNICAL SLIDES:
Each technical slide MUST include:
1. CONCEPT bullet: Define the technology/concept (e.g., "**AlphaFold** is a deep learning system developed by DeepMind...")
2. MECHANISM bullet: Explain how it works technically (e.g., "Uses attention-based neural networks to predict 3D protein structures from amino acid sequences...")
3. IMPACT bullet: Explain why it matters and outcomes (e.g., "Reduced protein structure prediction time from years to hours, accelerating drug discovery timelines...")
4. EVIDENCE bullet (optional): Include specific data, metrics, or citations

SPEAKER NOTES REQUIREMENTS:
- Generate detailed, 150 to 200 word presentation scripts
- Include background context on the topic
- Explain the data and findings shown on the slide
- Provide a smooth transition to the next slide
- Use academic language appropriate for university presentations
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
   - subtitle_takeaway: ONE strong sentence summarizing the slide's main point
   - supporting_data: 3-4 comprehensive bullet points following CONCEPT/MECHANISM/IMPACT/EVIDENCE structure
   - speaker_notes: Detailed 150-200 word presentation script with background, explanation, and transition
   - citations: List of [Author, Year] or [PMID: XXXXX] strings cited on this slide
6. Use SPECIFIC named entities - NO generic phrases:
   - Include at least 1 specific research citation per slide
   - Include at least 1 specific technology/AI model name (e.g., "AlphaFold", "GPT-4", "BERT")
   - Include real metrics with numbers and units (e.g., "85% accuracy", "3-month reduction")
   - Use **bold text** for key scientific terms
7. Each slide must advance the narrative - no repetition of concepts
8. Set image_prompt to null if text-heavy or no visual benefit
9. Image prompt should describe professional scientific/medical illustration
10. For data slides: include "chart_data": {{"type": "bar", "labels": ["A", "B"], "values": [10, 20]}}
11. For technical flow diagrams: use layout "diagram" and include "mermaid_code": "flowchart TD..."
12. NEVER create empty slides - every slide must have meaningful content
13. Speaker notes must be substantive enough for a 10-minute presentation segment

EXAMPLE GOOD SLIDE (follow this structure):
{{
  "slide_number": 3,
  "layout": "two_column",
  "title": "AlphaFold: Revolutionizing Protein Structure Prediction",
  "subtitle_takeaway": "DeepMind's AlphaFold has solved the 50-year protein folding problem, accelerating drug discovery by predicting structures in hours rather than years.",
  "supporting_data": [
    {{"bullet": "**AlphaFold** is a deep learning system developed by DeepMind that predicts 3D protein structures from amino acid sequences with near-experimental accuracy", "context": "Represents a fundamental breakthrough in computational biology"}},
    {{"bullet": "Uses **attention-based neural networks** and evolutionary sequence analysis to model spatial relationships between amino acids, achieving CASP14 scores above 90 GDT", "context": "Technical mechanism enabling unprecedented prediction accuracy"}},
    {{"bullet": "Has predicted structures for over 200 million proteins, bypassing traditional methods like X-ray crystallography that require months or years of laboratory work", "context": "Democratizing access to structural biology data"}},
    {{"bullet": "Enabled identification of novel drug targets for COVID-19 within weeks, demonstrating 92% accuracy compared to experimental structures [Jumper et al., 2021]", "context": "Real-world impact on therapeutic development timelines"}}
  ],
  "speaker_notes": "For decades, determining protein structures was one of biology's grand challenges. Experimental methods like X-ray crystallography and cryo-EM, while accurate, are time-consuming and expensive. AlphaFold represents a paradigm shift in structural biology. By training on known protein structures and using attention mechanisms similar to those in natural language processing, AlphaFold can predict protein folding patterns with remarkable accuracy. The system's impact extends beyond academia - pharmaceutical companies are now using AlphaFold predictions to identify drug binding sites and design targeted therapies. During the COVID-19 pandemic, AlphaFold predictions helped researchers understand the spike protein structure within weeks rather than months. As we move to the next slide, we'll explore how these predicted structures are being integrated into drug discovery pipelines and what this means for future therapeutic development.",
  "citations": ["Jumper et al., 2021"]
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
        
        # Step 2.5: Retry empty slides
        for i, slide in enumerate(outline["slides"]):
            refined = content_results[i]
            # Check if slide is effectively empty
            has_no_content = (
                not refined.get("bullets") or 
                len(refined.get("bullets", [])) == 0 or
                all(not bullet.strip() for bullet in refined.get("bullets", []))
            ) and not refined.get("chart_data") and not refined.get("mermaid_code")
            
            if has_no_content and slide.get("layout") != "title":
                print(f"⚠️ Slide {i+1} is empty. Retrying content generation...")
                if on_progress:
                    await on_progress({
                        "step": "content_retry",
                        "current": i + 1,
                        "total": total_slides,
                        "message": f"Retrying slide {i+1} (empty content detected)"
                    })
                
                # Force retry with stronger prompt
                retry_slide = slide.copy()
                retry_slide["title"] = slide["title"] + " (RETRY)"
                prev_summary = self._slide_context[-1]["summary"] if self._slide_context else None
                refined_retry = await self._refine_slide_content(retry_slide, outline["title"], prev_summary)
                
                # If retry succeeded, use it
                if refined_retry.get("bullets") and len(refined_retry.get("bullets", [])) > 0:
                    content_results[i] = refined_retry
                    print(f"✅ Slide {i+1} retry successful")
                else:
                    print(f"❌ Slide {i+1} retry failed - will be removed during assembly")

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
                    
                    # BAN: Skip image generation for diagram/flowchart/text-heavy prompts
                    # FLUX cannot generate readable text or logical diagrams
                    if self._is_diagram_prompt(prompt):
                        print(f"⚠️ Skipping image generation for slide {slide_idx}: Diagram/flowchart detected (FLUX cannot render text)")
                        image_results[slide_idx] = None
                        continue

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
    
    def _is_diagram_prompt(self, prompt: str) -> bool:
        """
        Detect if prompt is asking for diagrams, flowcharts, or text-heavy images.
        FLUX and other diffusion models cannot generate readable text or logical diagrams.
        
        Returns True if image generation should be skipped for this prompt.
        """
        if not prompt:
            return False
        
        prompt_lower = prompt.lower()
        
        # Keywords that indicate diagram/flowchart/text content
        diagram_keywords = [
            'diagram', 'flowchart', 'flow chart', 'flow diagram',
            'process map', 'workflow', 'decision tree', 'org chart',
            'organizational chart', 'hierarchy chart', 'mind map',
            'text', 'label', 'caption', 'title', 'word', 'phrase',
            'chart with labels', 'annotated', 'with text', 'showing text',
            'step 1', 'step 2', 'step 3', 'labeled', 'callout',
            'arrow with text', 'box with text', 'containing text'
        ]
        
        # Check for diagram-related keywords
        for keyword in diagram_keywords:
            if keyword in prompt_lower:
                return True
        
        return False
    
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
3. Write 3 to 4 comprehensive bullet points per slide following this REQUIRED structure:
   - CONCEPT bullet: Define the technology/concept with bold key terms (e.g., "**AlphaFold** is a deep learning system...")
   - MECHANISM bullet: Explain how it works technically with specific methods
   - IMPACT bullet: Explain why it matters with quantitative outcomes
   - EVIDENCE bullet (optional): Include specific data, metrics, and citations
4. Use **bold text** for key scientific terms to maintain readability
5. Each bullet should be comprehensive - clearly explain the mechanism, methodology, or outcome
6. Include specific research citations [Author, Year] in every bullet
7. Subtitle takeaway: ONE strong sentence summarizing the slide's main contribution
8. Speaker notes: Generate detailed 150-200 word presentation scripts including:
   - Background context on the topic
   - Explanation of the data and findings shown on the slide
   - Smooth transition to the next slide
   - Academic language appropriate for university presentations

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
