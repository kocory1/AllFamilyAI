"""가족 파생 질문 생성 Chain (P3) - Langchain LCEL 사용"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.question.utils import validate_question_level

logger = logging.getLogger(__name__)


class FamilyGenerateChain:
    """가족 파생 질문 생성 Chain (RAG 기반) - Langchain LCEL"""

    def __init__(self):
        """Chain 초기화"""
        self.prompt_data = self._load_prompt()

        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.default_model,
            temperature=settings.temperature,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        # 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_data["system"]),
                ("user", self.prompt_data["user"]),
            ]
        )

        # 파서
        self.parser = JsonOutputParser()

        # LCEL Chain 구성: prompt | llm
        self.chain = self.prompt_template | self.llm

    def _load_prompt(self) -> dict:
        """YAML 프롬프트 로드 (에러 처리 강화)"""
        try:
            prompt_path = Path("prompts/family_generate.yaml")

            if not prompt_path.exists():
                logger.error(f"프롬프트 파일 없음: {prompt_path}")
                raise FileNotFoundError(f"필수 프롬프트 파일 없음: {prompt_path}")

            with open(prompt_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if "system" not in data or "user" not in data:
                raise ValueError("프롬프트 포맷 오류: system, user 필드 필요")

            return data

        except Exception as e:
            logger.error(f"프롬프트 로드 실패: {e}")
            raise

    async def generate(
        self,
        family_id: int,
        members: list[dict[str, Any]],
        rag_results: list[dict[str, Any]],
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        가족 파생 질문 생성

        Args:
            family_id: 가족 ID
            members: 가족 구성원 목록 [{"member_id": int, "role_label": str}, ...]
            rag_results: RAG 검색 결과 (가족 전체)
            context: 추가 컨텍스트 (선택)

        Returns:
            {
                "question": str,
                "level": int,
                "metadata": dict
            }
        """
        start_time = datetime.now()

        try:
            logger.info(
                f"[가족 질문 생성 시작] family_id={family_id}, "
                f"members_count={len(members)}, rag_count={len(rag_results)}"
            )

            # 1. 가족 구성원 포맷팅
            family_members_str = self._format_family_members(members)

            # 2. RAG 컨텍스트 포맷팅
            rag_context = self._format_rag_context(rag_results)

            # 3. 컨텍스트 프롬프트 생성
            context_prompt = (
                f"**추가 컨텍스트:** {context}" if context else "**추가 컨텍스트:** 없음"
            )

            # 4. LCEL Chain 실행 (Langsmith 자동 트레이싱)
            response = await self.chain.ainvoke(
                {
                    "family_members": family_members_str,
                    "rag_context": rag_context,
                    "context_prompt": context_prompt,
                }
            )

            # 5. JSON 파싱 (JsonOutputParser 사용)
            parsed_result = self.parser.parse(response.content)

            # 6. 필수 필드 검증
            if "question" not in parsed_result or "level" not in parsed_result:
                raise ValueError(
                    f"LLM 응답에 필수 필드가 없습니다. " f"받은 필드: {list(parsed_result.keys())}"
                )

            # 7. 메타데이터 구성
            total_latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Langchain의 usage_metadata 접근
            usage = response.usage_metadata or {}

            result = {
                "question": parsed_result["question"],
                "level": validate_question_level(parsed_result["level"]),
                "metadata": {
                    "generated_by": "ai",
                    "model": settings.default_model,
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "finish_reason": response.response_metadata.get("finish_reason", "stop"),
                    "total_latency_ms": total_latency_ms,
                    "rag_context_count": len(rag_results),
                    "family_members_count": len(members),
                    "reasoning": parsed_result.get("reasoning", ""),
                },
            }

            logger.info(
                f"[가족 질문 생성 완료] question='{result['question'][:30]}...', "
                f"level={result['level']}, latency={total_latency_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(f"[가족 질문 생성 실패] error={str(e)}", exc_info=True)
            raise

    def _format_family_members(self, members: list[dict[str, Any]]) -> str:
        """가족 구성원 목록 포맷팅"""
        if not members:
            return "구성원 정보 없음"

        member_labels = [m.get("role_label", "알 수 없음") for m in members]
        return ", ".join(member_labels)

    def _format_rag_context(self, rag_results: list[dict[str, Any]]) -> str:
        """RAG 검색 결과를 프롬프트용 텍스트로 포맷팅"""
        if not rag_results:
            return "과거 답변 기록이 없습니다."

        formatted_lines = []
        for idx, result in enumerate(rag_results[:10], 1):  # 최대 10개 (가족은 더 많이)
            line = (
                f"{idx}. [{result['answered_at'][:10]}] "
                f"{result['role_label']} - "
                f"Q: {result['question']} / A: {result['answer']}"
            )
            formatted_lines.append(line)

        return "\n".join(formatted_lines)
