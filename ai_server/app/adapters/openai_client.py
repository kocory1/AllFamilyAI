import openai
from typing import List, Dict, Any, Optional

from app.core.config import settings


class OpenAIClient:
    """Thin adapter over openai.Chat Completions API (async)."""

    def __init__(self) -> None:
        openai.api_key = settings.openai_api_key
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        # gpt-5-nano 등 reasoning 모델은 temperature 커스텀 값을 지원하지 않으므로
        # temperature 파라미터를 전달하지 않고 모델 기본값 사용
        response = await self._client.chat.completions.create(
            model=model or settings.default_model,
            messages=messages,
            max_completion_tokens=max_completion_tokens or settings.max_tokens,
            response_format=response_format,
        )
        return response.choices[0].message.content.strip()


