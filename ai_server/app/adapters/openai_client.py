import openai
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


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
        model_name = model or settings.default_model
        logger.info(f"[OpenAI] 호출 시작 - model={model_name}, max_tokens={max_completion_tokens or settings.max_tokens}")
        
        try:
            response = await self._client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_completion_tokens=max_completion_tokens or settings.max_tokens,
                response_format=response_format,
            )
            
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

    async def create_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ):
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
            
            response = await self._client.embeddings.create(
                input=text,
                model=model
            )
            
            logger.debug(f"[OpenAI Embedding] 완료 - dimension={len(response.data[0].embedding)}")
            return response
            
        except Exception as e:
            logger.error(f"[OpenAI Embedding] 실패 - error={str(e)}")
            raise


