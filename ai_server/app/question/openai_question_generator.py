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
        
        # 답변 분석이 있으면 팔로업 모드, 없으면 새 질문 모드
        if request.answer_analysis:
            lines.append("사용자가 답변한 내용을 바탕으로, 더 깊이 파고드는 자연스러운 팔로업 질문을 만드세요.")
            lines.append("⚠️ 중요: 이전 질문을 반복하거나 패러프레이징하지 마세요. 답변 내용에서 새로운 질문을 만드세요.")
        else:
            lines.append("아래 주제로 친구처럼 부담 없이 물어보는 짧고 간단한 질문을 만드세요.")
        
        lines.append("")
        lines.append("=== 이전 질문 ===")
        lines.append(f"{request.content}")
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

        # 답변 분석 섹션 (팔로업 모드)
        if request.answer_analysis:
            lines.append("=== 📌 사용자의 답변 내용 (핵심!) ===")
            summary = request.answer_analysis.summary
            categories = request.answer_analysis.categories
            scores = request.answer_analysis.scores
            keywords = request.answer_analysis.keywords
            
            if summary:
                lines.append(f"답변 요약: {summary}")
            if keywords:
                lines.append(f"🔑 핵심 키워드: {', '.join(keywords)}")
            if categories:
                lines.append(f"주제: {', '.join(categories)}")
            if scores and scores.emotion:
                # 감정 분석 - 가장 높은 감정만 표시
                emo = scores.emotion
                emotions = []
                if emo.sadness and emo.sadness > 0.4:
                    emotions.append("슬픔/그리움")
                if emo.joy and emo.joy > 0.4:
                    emotions.append("기쁨")
                if emo.anger and emo.anger > 0.4:
                    emotions.append("분노")
                if emotions:
                    lines.append(f"💭 감정: {', '.join(emotions)}")
            
            lines.append("")
            lines.append("👉 팔로업 방향:")
            lines.append("- 위 키워드와 감정을 활용하여 더 깊이 들어가는 질문 만들기")
            lines.append("- 이전 질문과 완전히 다른 각도로 접근하기")
            lines.append("- 구체적인 경험이나 감정을 물어보기")
            lines.append("")

        # 생성 규칙
        lines.append("=== 생성 규칙 ===")
        lines.append("1) 짧고 간결하게: 한 문장, 50자 이내 권장")
        lines.append("2) 자연스러운 말투: '~나요?', '~어요?', '~있어요?' 같은 편안한 의문형")
        lines.append("3) 금지 표현: '떠올리시고', '말씀해 주세요', '자세히 설명', '조금 더' 같은 형식적 표현")
        lines.append("4) 직접적으로: 친구에게 묻듯이 핵심만 물어보기")
        lines.append("5) ⚠️ 이전 질문 반복 금지: 같은 내용을 다시 묻지 말고, 답변에서 새로운 각도 찾기")
        lines.append("")
        
        if request.answer_analysis:
            lines.append("좋은 팔로업 예시:")
            lines.append("- 이전: '요즘 가족과 어떤 하루를 보내나요?' / 답변: '본가에 못 가서 그립다'")
            lines.append("  → 좋음: '본가의 어떤 모습이 가장 그리운가요?'")
            lines.append("  → 나쁨: '가족과 함께 보내는 요즘 하루가 어때요?' (이전 질문 반복!)")
            lines.append("")
        else:
            lines.append("좋은 예시:")
            lines.append("- 최근 가족과 함께한 소소한 기쁨이 있었나요?")
            lines.append("- 요즘 가족과 어떤 시간을 보내고 있어요?")
            lines.append("- 가족 중에 가장 닮고 싶은 사람이 있나요?")
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
                        "답변 내용을 기반으로 더 깊이 파고드는 팔로업 질문을 만들 때는 "
                        "절대 이전 질문을 반복하거나 패러프레이징하지 마세요. "
                        "답변에서 나온 키워드, 감정, 구체적 상황을 활용해서 완전히 새로운 각도로 질문하세요. "
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


