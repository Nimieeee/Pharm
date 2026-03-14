"""
Slide Generation Service — Kimi-style agentic pipeline.

Step 1: generate_outline()  — AI creates JSON slide structure
Step 2: refine_content()    — AI writes full prose per slide
Step 3: generate_images()   — Pollinations creates visuals
Step 4: assemble_pptx()     — Design Engine builds the file
"""

import json
import asyncio
from typing import Optional, Callable, Dict, List, Any
from app.services.multi_provider import MultiProviderService
from app.services.image_gen import ImageGenerationService
from app.services.design_engine import DesignEngine


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
        
        prompt = f"""Create a presentation outline on: "{topic}"
Number of slides: {num_slides}
{source_context}

Return ONLY valid JSON with this exact schema:
{{
  "title": "Presentation Title",
  "subtitle": "Subtitle",
  "theme": "ocean_gradient",
  "slides": [
    {{
      "slide_number": 1,
      "layout": "title",
      "title": "Slide Title",
      "subtitle": "Optional subtitle",
      "bullets": ["Point 1", "Point 2"],
      "speaker_notes": "What to say...",
      "image_prompt": "description of image to generate, or null for no image",
      "data": null
    }}
  ]
}}

Layout options: "title", "two_column", "bullets_only", "data_callout", "image_full"
Theme options: "ocean_gradient", "forest_moss", "coral_energy", "warm_terracotta",
               "charcoal_minimal", "teal_trust", "berry_cream", "sage_calm",
               "cherry_bold", "midnight_executive"

Rules:
- First slide MUST be layout "title"
- Last slide should be "title" (conclusion/thank you)
- Never have 3 consecutive slides with the same layout
- Max 6 bullets per slide (split if more needed)
- set image_prompt to null if the slide is text-heavy or doesn't benefit from a visual illustration. No generic placeholders.
- image_prompt should describe a professional, high-fidelity scientific illustration or medical diagram.
- For data_callout: include "data": {{"value": "85%", "label": "Patient Response Rate"}}
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
        """
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
            
            # Refine bullet points into fuller content
            refined = await self._refine_slide_content(slide, outline["title"])
            content_results.append(refined)
        
        # Step 3: Generate images via Pollinations
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
                    img_bytes = await self.image_gen.fetch_image_from_pollinations(
                        prompt=prompt,
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
    
    async def _refine_slide_content(self, slide: dict, deck_title: str) -> dict:
        """Use detailed AI to expand bullet points into polished content"""
        if slide["layout"] == "title":
            return slide  # Title slides don't need expansion
        
        bullets_json = json.dumps(slide.get("bullets", []))
        
        prompt = f"""Refine this slide content for the presentation "{deck_title}".

Slide title: {slide['title']}
Bullets: {bullets_json}

Rules:
- Keep each bullet under 15 words
- Make language active and concrete
- Add a 2-sentence speaker note
- Return as JSON: {{"bullets": [...], "speaker_notes": "..."}}"""
        
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
            slide["bullets"] = refined.get("bullets", slide.get("bullets", []))
            slide["speaker_notes"] = refined.get("speaker_notes", slide.get("speaker_notes", ""))
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
