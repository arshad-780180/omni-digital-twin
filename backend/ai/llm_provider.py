import os
import google.generativeai as genai
from abc import ABC, abstractmethod
from utils.logger import get_logger

logger = get_logger("llm_provider")


class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass


class GeminiProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not configured.")

        model_name = os.getenv("GEMINI_MODEL")
        if not model_name:
            raise RuntimeError("GEMINI_MODEL environment variable is not configured.")

        logger.info(f"Initializing GeminiProvider with model '{model_name}'")
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            logger.info(f"GeminiProvider initialized successfully for model '{model_name}'")
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini model '{model_name}'")
            raise RuntimeError(
                f"Failed to initialize Gemini model '{model_name}': {e}"
            ) from e

    async def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            response = await self.model.generate_content_async(prompt, **kwargs)
            return response.text
        except Exception as e:
            logger.exception("GeminiProvider.generate_text failed")
            raise RuntimeError(f"Gemini text generation failed: {e}") from e


_provider_singleton: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Returns a singleton LLM provider configured from environment variables."""
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = GeminiProvider()
    return _provider_singleton
