import openai
from typing import List, Dict, Any, Optional

from app.core.config import settings


class OpenAIClient:
    """Thin adapter over openai.Chat Completions API."""

    def __init__(self) -> None:
        openai.api_key = settings.openai_api_key
        self._client = openai.OpenAI(api_key=settings.openai_api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        response = self._client.chat.completions.create(
            model=model or settings.default_model,
            messages=messages,
            max_tokens=max_tokens or settings.max_tokens,
            temperature=temperature if temperature is not None else settings.temperature,
            response_format=response_format,
        )
        return response.choices[0].message.content.strip()


