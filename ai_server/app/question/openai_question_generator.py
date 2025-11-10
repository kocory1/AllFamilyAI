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
        lines.append("당신은 가족과의 자연스러운 대화를 돕는 질문 생성 전문가입니다.")
        lines.append("아래 정보를 참고하여, 친구처럼 부담 없이 물어보는 짧고 간단한 질문을 만드세요.")
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
        lines.append("1) 짧고 간결하게: 한 문장, 50자 이내 권장")
        lines.append("2) 자연스러운 말투: '~나요?', '~어요?', '~있어요?' 같은 편안한 의문형")
        lines.append("3) 금지 표현: '떠올리시고', '말씀해 주세요', '자세히 설명', '조금 더' 같은 형식적 표현")
        lines.append("4) 직접적으로: 친구에게 묻듯이 핵심만 물어보기")
        lines.append("5) 상투적 표현 금지: 일상 대화처럼 자연스럽게")
        lines.append("")
        lines.append("좋은 예시:")
        lines.append("- 최근 가족과 함께한 소소한 기쁨이 있었나요?")
        lines.append("- 요즘 가족과 어떤 시간을 보내고 있어요?")
        lines.append("- 가족 중에 가장 닮고 싶은 사람이 있나요?")
        lines.append("")
        lines.append("나쁜 예시:")
        lines.append("- 가족과 함께한 최근의 작은 기쁨을 떠올리시고, 그때 느낀 감정을 조금 더 자세히 말씀해 주세요.")
        lines.append("- 가족 구성원 중 본인이 가장 닮고 싶어하는 사람에 대해 구체적으로 설명해 주실 수 있나요?")
        lines.append("")
        lines.append("질문:")
        return "\n".join(lines)

    async def _call_openai(self, prompt: str) -> str:
        return await self.client.chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 가족과의 자연스러운 대화를 돕는 질문 생성 전문가입니다. "
                        "친구에게 묻듯이 짧고 간단하며 부담 없는 질문을 만듭니다. "
                        "'~나요?', '~어요?' 같은 자연스러운 의문형을 사용하고, "
                        "'떠올리시고', '말씀해 주세요', '자세히' 같은 형식적 표현은 절대 사용하지 않습니다."
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


