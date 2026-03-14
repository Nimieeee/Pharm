"""
Slide Generation Service — Premium presentation platform.

Step 1: generate_outline()  — AI creates JSON slide structure
Step 2: refine_content()    — AI writes full prose per slide (with contextual memory)
Step 3: generate_images()   — Pollinations creates visuals (with art direction)
Step 4: assemble_pptx()     — Design Engine builds the file
"""

import json
import asyncio
from typing import Optional, Callable, Dict, List, Any
from app.services.multi_provider import MultiProviderService
from app.services.image_gen import ImageGenerationService
from app.services.design_engine import DesignEngine

# Phase 1: Premium Quality - Art Direction Styles
ART_DIRECTION_STYLES = {
    "corporate": "Professional corporate vector illustration, minimalist, flat design, white background, unified color palette, clean lines. No text.",
    "photorealistic": "High-quality photorealistic render, professional studio lighting, clean composition, corporate setting, sharp focus. No text.",
    "minimalist": "Ultra-minimalist line art, monochrome, geometric shapes, ample white space, elegant simplicity. No text.",
    "isometric": "Isometric 3D illustration, soft shadows, pastel colors, clean modern style, technical precision. No text.",
    "sketch": "Professional hand-drawn sketch style, blueprint aesthetic, technical drawing, white background. No text."
}

# Phase 1: Content Constraints - Rule of Three
CONTENT_CONSTRAINTS = """
STRICT CONTENT LIMITS (ENFORCED):
- Maximum 3 bullet points per slide
- Maximum 12 words per bullet point
- Maximum 1 sentence per bullet point
- No paragraph text - single concise statements only
- Focus on ONE key concept per slide
- Avoid generic buzzwords: use specific metrics, names, and data
"""


class SlideService:
    """
    Slide generation orchestrator.
    
    Features:
    - AI-powered outline generation
    - Content refinement with detailed mode
    - Pollinations image generation per slide
    - Professional PPTX assembly via Design Engine
    """
    
    def __init__(self, multi_provider: MultiProviderService,
                 image_gen: ImageGenerationService):
        self.ai = multi_provider
        self.image_gen = image_gen
        self.design = DesignEngine()
        self._slide_context = []  # Phase 1: Track content to prevent repetition
        self._used_phrases = set()  # Track used key phrases
        self._vibe = "corporate"  # Phase 1: Default art direction style
    
    async def generate_outline(
        self,
        topic: str,
        context: str = None,
        num_slides: int = 12,
        uploaded_text: str = None
    ) -> dict:
        """
        Step 1: AI generates editable JSON outline.
        
        Uses Groq fast mode for speed (~2-3 seconds).
        If uploaded_text is provided, the AI distills it into slides.
        """
        source_context = ""
        if uploaded_text:
            # Truncate to 8000 chars for fast mode token limit
            source_context = f"\n\nSource material to distill:\n{uploaded_text[:8000]}"
        elif context:
            source_context = f"\n\nAdditional context:\n{context}"
        
        prompt = f"""Create a PREMIUM presentation outline on: "{topic}"
Number of slides: {num_slides}
{source_context}

{CONTENT_CONSTRAINTS}

Return ONLY valid JSON with this exact schema:
{{
  "title": "Presentation Title",
  "subtitle": "Subtitle",
  "theme": "ocean_gradient",
  "vibe": "corporate",
  "slides": [
    {{
      "slide_number": 1,
      "layout": "title",
      "title": "Slide Title",
      "subtitle": "Optional subtitle",
      "bullets": ["Point 1", "Point 2"],
      "speaker_notes": "What to say...",
      "image_prompt": "description of image to generate, or null for no image",
      "chart_data": null,
      "data": null
    }}
  ]
}}

Layout options: "title", "two_column", "bullets_only", "data_callout", "image_full", "comparison", "timeline"
Theme options: "ocean_gradient", "forest_moss", "coral_energy", "warm_terracotta",
               "charcoal_minimal", "teal_trust", "berry_cream", "sage_calm",
               "cherry_bold", "midnight_executive"
Vibe options: "corporate", "photorealistic", "minimalist", "isometric", "sketch"

MANDATORY RULES:
1. First slide MUST be layout "title" - only presentation title and subtitle
2. Last slide MUST be layout "title" - simple "Thank You" with contact placeholder, NO bullet points
3. Never have 3 consecutive slides with the same layout
4. MAXIMUM 3 bullets per slide - NEVER more
5. Each bullet MAXIMUM 12 words
6. Use SPECIFIC named entities - NO generic phrases like "many companies" or "various tools":
   - Include at least 1 specific company name per slide (e.g., "Pfizer", "DeepMind", "Novartis")
   - Include at least 1 specific technology/AI model name (e.g., "AlphaFold", "GPT-4", "BERT")
   - Include real metrics with numbers (e.g., "85% accuracy", "3-month reduction")
7. Each slide must advance the narrative - no repetition of concepts
8. Closing slides (last 2 slides) should be minimal: title + brief subtitle only
9. set image_prompt to null if text-heavy or no visual benefit
10. image_prompt should describe professional scientific/medical illustration
11. For data slides: include "chart_data": {{"type": "bar", "labels": ["A", "B"], "values": [10, 20]}}
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
        Use detailed AI to expand bullet points into polished content.

        Phase 1 Improvements:
        - Contextual Memory: Pass previous slide summary to prevent repetition
        - Rule of Three: Max 3 bullets, 12 words each
        - Named Entities: Require specific company/technology names
        """
        if slide["layout"] == "title":
            return slide  # Title slides don't need expansion

        bullets_json = json.dumps(slide.get("bullets", []))

        # Phase 1: Contextual memory - prevent repetition
        context_note = ""
        if prev_slide_summary:
            context_note = f"\n\nPREVIOUS SLIDE SUMMARY: {prev_slide_summary}\nDo NOT repeat concepts or phrases from the previous slide."

        prompt = f"""Refine this slide content for the presentation "{deck_title}".

Slide title: {slide['title']}
Bullets: {bullets_json}
{context_note}

CRITICAL RULES:
1. MAXIMUM 3 bullet points - remove any extras
2. Each bullet MAXIMUM 12 words - truncate if longer
3. Include at least ONE specific named entity:
   - Company name (e.g., "Pfizer", "DeepMind", "Novartis")
   - Technology/model name (e.g., "AlphaFold", "GPT-4", "BERT")
   - Real metric with number (e.g., "85% accuracy", "3-month reduction")
4. NO generic phrases like "many companies", "various tools", "AI accelerates"
5. Make language active and concrete
6. Add a 2-sentence speaker note
7. Return as JSON: {{"bullets": [...], "speaker_notes": "..."}}

Example good bullet: "DeepMind's AlphaFold predicted 200M protein structures with 85% accuracy"
Example bad bullet: "AI accelerates drug discovery through various tools" (generic, no named entities)"""

        try:
            response = await self.ai.generate(
                mode="detailed",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.4
            )

            # Extract JSON cleanly
            json_str = response.strip()
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

            refined = json.loads(json_str)

            # Enforce Rule of Three
            bullets = refined.get("bullets", slide.get("bullets", []))
            if len(bullets) > 3:
                bullets = bullets[:3]

            # Enforce 12-word limit per bullet
            bullets = [
                ' '.join(b.split()[:12]) + ('...' if len(b.split()) > 12 else '')
                for b in bullets
            ]

            slide["bullets"] = bullets
            slide["speaker_notes"] = refined.get("speaker_notes", slide.get("speaker_notes", ""))

            # Phase 1: Store slide summary for next slide's context
            self._slide_context.append({
                "title": slide['title'],
                "bullets": bullets,
                "summary": f"Slide '{slide['title']}': {'; '.join(bullets)}"
            })

        except (json.JSONDecodeError, Exception):
            import logging
            logging.getLogger("app.slide_service").warning(f"Refinement JSON parse failed, using original. Response: {response[:100]}...")
            pass  # Keep original content if parsing fails

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
