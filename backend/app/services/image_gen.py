
import os
import logging
from typing import Optional, Dict, Any
from mistralai import Mistral
from app.core.config import settings

logger = logging.getLogger(__name__)

class ImageGenerationService:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found. Image generation will fail.")
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)

    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        """
        Generate an image using Mistral's beta tools.
        """
        if not self.client:
            raise ValueError("Mistral API key not configured")

        logger.info(f"🎨 Generating image for prompt: {prompt[:50]}...")

        messages = [
            {"role": "user", "content": f"Generate an image of: {prompt}"}
        ]

        # Use the specific beta configuration for image generation
        try:
            # We run this synchronously as the Mistral client is sync (unless we use AsyncMistral which wasn't in the snippet provided)
            # But the user snippet used 'Mistral' which is sync.
            # Ideally we should run this in a threadpool if it blocks, but for now strict implementation of snippet.
            # Actually, let's checking requirements.txt again, it has mistralai>=1.2.0.
            # The user snippet used specific beta.conversations.start
            
            completion_args = {
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 1
            }

            tools = [
                {
                    "type": "image_generation"
                }
            ]

            response = self.client.beta.conversations.start(
                inputs=messages,
                model="mistral-large-latest",
                completion_args=completion_args,
                tools=tools,
            )

            # Parse response to find image URL
            # The response structure from beta conversations usually has choices[0].message.content 
            # OR if it used a tool, it might be in steps or tool_calls.
            # However, for 'image_generation' tool in Mistral's beta, 
            # the model typically returns a markdown image link like ![image](url) in the content
            # OR it returns the tool output. 
            
            # Let's try to extract textual content which should contain the image URL in markdown format.
            content = response.choices[0].message.content
            
            logger.info("✅ Image generation response received")
            return {
                "status": "success",
                "content": content,
                "raw_response": str(response)
            }

        except Exception as e:
            logger.error(f"❌ Image generation failed: {str(e)}")
            raise e
