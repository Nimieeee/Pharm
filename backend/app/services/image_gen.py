"""
Image Generation Service
Uses Hugging Face Inference API with Z-Image-Turbo for high-quality image generation.
"""

import io
import base64
import logging
from typing import Dict, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Z-Image-Turbo via HF Inference API
HF_MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"
HF_INFERENCE_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}"


class ImageGenerationService:
    def __init__(self):
        self.api_key = settings.HF_API_KEY
        if not self.api_key:
            logger.warning("HF_API_KEY not found. Image generation will be unavailable.")

    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        """
        Generate an image using Z-Image-Turbo via Hugging Face Inference API.
        
        Returns a dict with:
          - status: 'success' or 'error'
          - image_base64: base64-encoded PNG (on success)
          - error: error message (on failure)
        """
        if not self.api_key:
            return {
                "status": "error",
                "error": "HF_API_KEY not configured. Image generation is unavailable.",
                "image_base64": None,
            }

        logger.info(f"🎨 Generating image with Z-Image-Turbo: {prompt[:80]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 8,
                "guidance_scale": 0.0,
                "width": 1024,
                "height": 1024,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    HF_INFERENCE_URL,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    # HF Inference API returns raw image bytes
                    image_bytes = response.content
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                    logger.info("✅ Image generated successfully")
                    return {
                        "status": "success",
                        "image_base64": image_base64,
                        "error": None,
                    }

                elif response.status_code == 503:
                    # Model is loading
                    try:
                        body = response.json()
                        wait_time = body.get("estimated_time", 30)
                    except Exception:
                        wait_time = 30
                    logger.warning(f"⏳ Model loading, estimated wait: {wait_time}s")
                    return {
                        "status": "error",
                        "error": f"Model is loading. Please try again in ~{int(wait_time)} seconds.",
                        "image_base64": None,
                    }

                else:
                    error_text = response.text[:500]
                    logger.error(f"❌ HF API error {response.status_code}: {error_text}")
                    return {
                        "status": "error",
                        "error": f"Image generation failed (HTTP {response.status_code}): {error_text}",
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
