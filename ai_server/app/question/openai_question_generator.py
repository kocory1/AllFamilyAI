from datetime import datetime
from typing import Optional
import logging

from app.core.config import settings
from app.question.base import QuestionGenerator
from app.adapters.openai_client import OpenAIClient
from app.question.models import (
    QuestionGenerateRequest,
    QuestionInstanceResponse,
)

logger = logging.getLogger(__name__)


class OpenAIQuestionGenerator(QuestionGenerator):
    def __init__(self) -> None:
        self.client = OpenAIClient()

    async def generate(
        self, request: QuestionGenerateRequest
    ) -> QuestionInstanceResponse:
        prompt = self._build_prompt(request)
        logger.info(f"[QuestionGen] 프롬프트 생성 완료 - 길이: {len(prompt)}")
        
        response = await self._call_openai(prompt)
        logger.info(f"[QuestionGen] OpenAI 응답 받음 - 길이: {len(response)}, 내용: '{response[:100]}'")
        
        content = self._parse_response(response)
        logger.info(f"[QuestionGen] 파싱 완료 - content: '{content}'")

        confidence, meta = self._evaluate_generation(
            content=content,
            language=request.language or "ko",
            tone=request.tone,
            max_len=settings.max_question_length
        )

        return QuestionInstanceResponse(
            content=content,
            status="draft",
            generated_by="ai",
            generation_model=settings.default_model,
            generation_parameters={"max_completion_tokens": settings.max_tokens},
            generation_prompt=prompt,
            generation_metadata=meta,
            generation_confidence=confidence,
            generated_at=datetime.now()
        )

    def _build_prompt(self, request: QuestionGenerateRequest) -> str:
        lines = []
        lines.append("당신은 가족 유대감을 증진시키는 질문 생성 전문가입니다.")
        lines.append("답변하기 적당한 길이의 질문을 생성해 주세요. 아래 정보가 있다면 참고하여 질문을 생성하세요.")
        lines.append("")
        lines.append("=== 기반 문구 ===")
        lines.append(f"본문: {request.content}")
        lines.append("")
        # 맥락 섹션(존재하는 항목만)
        ctx = []
        if request.category:
            ctx.append(f"카테고리: {request.category}")
        if request.tone:
            ctx.append(f"톤: {request.tone}")
        if request.language:
            ctx.append(f"언어: {request.language}")
        if request.tags:
            ctx.append(f"태그: {', '.join(request.tags)}")
        if request.subject_required is not None:
            ctx.append(f"주제 인물 필요: {request.subject_required}")
        if request.mood:
            ctx.append(f"분위기: {request.mood}")
        if ctx:
            lines.append("=== 맥락 ===")
            lines.extend(ctx)
            lines.append("")

        # 분석 섹션(선택)
        if request.answer_analysis:
            lines.append("=== 답변 분석 힌트(선택) ===")
            summary = request.answer_analysis.summary
            categories = request.answer_analysis.categories
            scores = request.answer_analysis.scores
            keywords = request.answer_analysis.keywords
            if summary:
                # 요약은 '참고용'으로만 제공하고, 문구 재사용 금지 지침을 아래에 명시
                lines.append(f"요약(참고용): {summary}")
            if categories:
                lines.append(f"분류: {', '.join(categories)}")
            if keywords:
                lines.append(f"키워드: {', '.join(keywords)}")
            if scores:
                # 전체 스코어를 JSON 유사 형태로 그대로 노출
                import json
                payload = {}
                if scores.sentiment is not None:
                    payload["sentiment"] = scores.sentiment
                if scores.toxicity is not None:
                    payload["toxicity"] = scores.toxicity
                if scores.relevance_to_question is not None:
                    payload["relevance_to_question"] = scores.relevance_to_question
                if scores.relevance_to_category is not None:
                    payload["relevance_to_category"] = scores.relevance_to_category
                if scores.length is not None:
                    payload["length"] = scores.length
                if scores.emotion is not None:
                    emo = {}
                    if scores.emotion.joy is not None:
                        emo["joy"] = scores.emotion.joy
                    if scores.emotion.sadness is not None:
                        emo["sadness"] = scores.emotion.sadness
                    if scores.emotion.anger is not None:
                        emo["anger"] = scores.emotion.anger
                    if scores.emotion.fear is not None:
                        emo["fear"] = scores.emotion.fear
                    if scores.emotion.neutral is not None:
                        emo["neutral"] = scores.emotion.neutral
                    if emo:
                        payload["emotion"] = emo
                if payload:
                    lines.append("점수(참고용): " + json.dumps(payload, ensure_ascii=False))
            # 요약 활용 방식에 대한 추가 지침(복사 금지, 심화 방향)
            lines.append("참고 지침: 요약과 점수는 맥락 파악용이며, 동일 표현을 복사하지 말고 새로운 심화 질문으로 재구성하세요.")
            lines.append("참고 지침: '요약에 따르면' 같은 메타 언급 없이 자연스러운 질문만 출력하세요.")
            lines.append("")

        # 생성 규칙
        lines.append("=== 생성 규칙 ===")
        lines.append("1) 존댓말 사용, 질문은 단 한 문장")
        lines.append("2) 상투적·일반론 금지, 요약/키워드/점수는 참고만 하며 표현을 그대로 재사용하지 않음")
        lines.append("3) 주어진 내용과 분석을 바탕으로 심화·개인화된 개방형 질문 생성")
        lines.append("4) 제공된 카테고리/톤/태그/분위기와 자연스럽게 일치")
        lines.append(f"5) {settings.max_question_length}자 이내")
        lines.append("6) 설명/접두어 없이 질문만 출력, 불필요한 따옴표·번호 제거")
        lines.append("")
        lines.append("질문:")
        return "\n".join(lines)

    async def _call_openai(self, prompt: str) -> str:
        return await self.client.chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 가족 유대감을 증진시키는 질문 생성 전문가입니다. "
                        "주어진 내용을 바탕으로 더 깊이 파고드는 심화·개인화된 팔로업 질문을 한 문장으로 만듭니다. "
                        "상투적 표현은 피하고, 상대가 스스로를 더 이야기하게 하는 개방형 질문을 선호합니다."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
        )

    def _parse_response(self, response: str) -> str:
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('질문:') and not line.startswith('답변:'):
                return line
        return response.strip()

    def _evaluate_generation(self, content: str, language: str, tone: Optional[str], max_len: int) -> tuple[float, dict]:
        try:
            score = 1.0
            meta: dict = {
                "length": len(content),
                "language": language,
                "tone": tone,
                "rules": {
                    "length_ok": len(content) <= max_len,
                    "ends_question": content.strip().endswith("?") or content.strip().endswith("요") or content.strip().endswith("가요"),
                }
            }
            if not meta["rules"]["length_ok"]:
                score -= 0.2
            if not meta["rules"]["ends_question"]:
                score -= 0.1
            score = max(0.0, min(1.0, score))
            return score, meta
        except Exception:
            return 0.5, {"error": "evaluation_failed"}


