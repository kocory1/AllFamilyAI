import logging

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API 클라이언트 (임베딩 전용)"""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

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
