import os
import google.generativeai as genai
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash as the default model for text tasks
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_text(self, prompt: str) -> str:
        # Note: the python SDK for gemini has generate_content_async but generate_content is also fine if used correctly in async.
        # We will use generate_content_async.
        response = await self.model.generate_content_async(prompt)
        return response.text

# Factory function to easily swap out providers later
def get_llm_provider() -> LLMProvider:
    return GeminiProvider()
