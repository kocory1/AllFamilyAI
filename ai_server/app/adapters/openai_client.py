import logging
from typing import Any

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Thin adapter over openai.Chat Completions API (async)."""

    def __init__(self) -> None:
        openai.api_key = settings.openai_api_key
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_completion_tokens: int | None = None,
        temperature: float | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        model_name = model or settings.default_model
        logger.info(
            f"[OpenAI] 호출 시작 - model={model_name}, "
            f"max_tokens={max_completion_tokens or settings.max_tokens}, "
            f"temperature={temperature}"
        )

        try:
            # reasoning 모델(gpt-5-*, o1-* 등)은 temperature 미지원
            is_reasoning_model = model_name.startswith(("gpt-5", "o1"))

            # API 호출 파라미터 구성
            call_params = {
                "model": model_name,
                "messages": messages,
                "max_completion_tokens": max_completion_tokens or settings.max_tokens,
            }

            # 일반 모델일 때만 temperature 전달
            if not is_reasoning_model and temperature is not None:
                call_params["temperature"] = temperature

            if response_format is not None:
                call_params["response_format"] = response_format

            response = await self._client.chat.completions.create(**call_params)

            content = response.choices[0].message.content
            logger.info(f"[OpenAI] 응답 받음 - content_length={len(content) if content else 0}")
            logger.debug(f"[OpenAI] 응답 내용: {content}")

            if not content:
                logger.warning(f"[OpenAI] 빈 응답 받음 - response={response}")
                return ""

            return content.strip()

        except Exception as e:
            logger.error(f"[OpenAI] API 호출 실패 - error={str(e)}")
            raise

    async def create_embedding(self, text: str, model: str = "text-embedding-3-small"):
        """
        텍스트를 벡터 임베딩으로 변환

        Args:
            text: 임베딩할 텍스트
            model: 임베딩 모델 (기본값: text-embedding-3-small)

        Returns:
            OpenAI Embedding Response
        """
        try:
            logger.debug(f"[OpenAI Embedding] 요청 - model={model}, text_length={len(text)}")

            response = await self._client.embeddings.create(input=text, model=model)

            logger.debug(f"[OpenAI Embedding] 완료 - dimension={len(response.data[0].embedding)}")
            return response

        except Exception as e:
            logger.error(f"[OpenAI Embedding] 실패 - error={str(e)}")
            raise
