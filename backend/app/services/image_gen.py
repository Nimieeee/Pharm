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

from app.core.config import settings

logger = logging.getLogger(__name__)

# Pollinations.ai API
POLLINATIONS_BASE_URL = "https://gen.pollinations.ai/image"


class ImageGenerationService:
    def __init__(self):
        self.api_key = settings.POLLINATIONS_API_KEY
        if not self.api_key:
            logger.warning("POLLINATIONS_API_KEY not found. Image generation will use anonymous tier (rate-limited).")

    async def generate_image(self, prompt: str, model: str = "flux") -> Dict[str, Any]:
        """
        Generate an image URL using Pollinations.ai (Public API).
        """
        logger.info(f"🎨 Generating image URL with Pollinations ({model}): {prompt[:80]}...")

        # URL-encode the prompt
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        base_url = "https://image.pollinations.ai/prompt"
        
        # Construct parameters
        params = [
            f"model={model}",
            "width=1024",
            "height=1024",
            "nologo=true",
            "safe=true"
        ]
        query_string = "&".join(params)
        
        # Final URL
        image_url = f"{base_url}/{encoded_prompt}?{query_string}"
        
        logger.info(f"✅ Image URL generated: {image_url}")
        
        return {
            "status": "success",
            "image_url": image_url,
            "image_base64": None, # Not used
            "error": None,
        }
