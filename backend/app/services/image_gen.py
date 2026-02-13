"""
Image Generation Service
Uses Pollinations.ai API with FLUX Schnell for high-quality image generation.
Free tier: 5,000 images/day with secret API key (no rate limit).
"""

import base64
import logging
import urllib.parse
from typing import Dict, Any

import httpx
import random

from app.core.config import settings

logger = logging.getLogger(__name__)

# Pollinations.ai API
POLLINATIONS_BASE_URL = "https://gen.pollinations.ai/image"


class ImageGenerationService:
    def __init__(self):
        self.api_key = settings.POLLINATIONS_API_KEY
        if not self.api_key:
            logger.warning("POLLINATIONS_API_KEY not found. Image generation will use anonymous tier (rate-limited).")

    async def generate_image(self, prompt: str, model: str = "zimage") -> Dict[str, Any]:
        """
        Generate an image URL proxy (Internal API).
        """
        # We now use a proxy endpoint in our own backend to hide the API key
        # The URL points to OUR backend, which fetches from Pollinations
        base_url = "/api/v1/ai/image-proxy"
        
        # Enforce Biomedical/Scientific Style
        # Context-aware prompting for better accuracy
        lower_prompt = prompt.lower()
        
        # Default style for general scientific images
        style_keywords = "scientific illustration, detailed, 8k resolution, professional biomedical rendering, white background, anatomically accurate, photorealistic"
        
        # Enhanced style for Diagrams/Cross-sections (triggers "Textbook Mode")
        diagram_triggers = ["cross section", "cross-section", "diagram", "anatomy", "structure", "labeled", "schematic", "cutaway"]
        if any(trigger in lower_prompt for trigger in diagram_triggers):
            # Stronger emphasis on educational/diagrammatic accuracy
            # Added "accurate text", "legible labels" to fight gibberish
            style_keywords = "medical textbook diagram, anatomically correct cross-section, correct physiological structure, clearly labeled parts, proper spelling, legible annotations, schematic, educational infographic, high detail, white background, vector style, clean lines, encyclopaedia britannica style"

        final_prompt = f"{prompt}, {style_keywords}"
        
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        seed = random.randint(0, 999999)
        # Construct query parameters - use list to avoid encoding issues with pre-encoded prompt
        # We construct the query string manually to ensure the prompt is handled correctly
        query = f"prompt={encoded_prompt}&model={model}&width=512&height=512&seed={seed}"
        
        # Return relative URL to our proxy
        # Frontend will treat this as https://api.domain.com/api/v1/ai/image-proxy?...
        image_url = f"{base_url}?{query}"
        
        return {
            "status": "success",
            "image_url": image_url,
            "image_base64": None,
            "error": None,
        }

    async def fetch_image_from_pollinations(self, prompt: str, model: str, width: int, height: int, seed: int) -> bytes:
        """
        Fetch actual image bytes from Gen.Pollinations.AI (Secure).
        """
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        url = f"{POLLINATIONS_BASE_URL}/{encoded_prompt}" # https://gen.pollinations.ai/image/...
        
        params = {
            "model": model,
            "width": width,
            "height": height,
            "nologo": "true",
            "safe": "true",
            "seed": seed
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.content
            else:
                logger.error(f"Pollinations Error {resp.status_code}: {resp.text}")
                # Fallback to public if auth fails? No, public is dead.
                raise Exception(f"Pollinations API Error: {resp.status_code}")
