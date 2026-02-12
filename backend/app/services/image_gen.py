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
        Generate an image using Pollinations.ai.
        
        Args:
            prompt: Text description of the image to generate.
            model: Model to use ('flux' for FLUX Schnell, 'zimage' for Z-Image Turbo).
            
        Returns:
            Dict with status, image_base64, and error fields.
        """
        logger.info(f"🎨 Generating image with Pollinations ({model}): {prompt[:80]}...")

        # URL-encode the prompt for the path
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        url = f"{POLLINATIONS_BASE_URL}/{encoded_prompt}"

        params = {
            "model": model,
            "width": 1024,
            "height": 1024,
            "nologo": "true",
            "safe": "true",
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )

                if response.status_code == 200 and response.headers.get("content-type", "").startswith("image/"):
                    image_bytes = response.content
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                    logger.info(f"✅ Image generated ({len(image_bytes)} bytes)")
                    return {
                        "status": "success",
                        "image_base64": image_base64,
                        "error": None,
                    }

                elif response.status_code == 429:
                    logger.warning("⏳ Rate limited by Pollinations")
                    return {
                        "status": "error",
                        "error": "Image generation is temporarily rate-limited. Please try again in a moment.",
                        "image_base64": None,
                    }

                else:
                    error_text = response.text[:500]
                    logger.error(f"❌ Pollinations API error {response.status_code}: {error_text}")
                    return {
                        "status": "error",
                        "error": f"Image generation failed (HTTP {response.status_code})",
                        "image_base64": None,
                    }

        except httpx.TimeoutException:
            logger.error("❌ Image generation timed out (120s)")
            return {
                "status": "error",
                "error": "Image generation timed out. Please try again.",
                "image_base64": None,
            }
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "image_base64": None,
            }
