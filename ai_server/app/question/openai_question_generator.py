from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.question.base import QuestionGenerator
from app.adapters.openai_client import OpenAIClient
from app.question.models import (
    QuestionInstanceCreateRequest,
    QuestionInstanceResponse,
)


class OpenAIQuestionGenerator(QuestionGenerator):
    def __init__(self) -> None:
        self.client = OpenAIClient()

    async def generate_from_template(
        self, request: QuestionInstanceCreateRequest
    ) -> QuestionInstanceResponse:
        prompt = self._build_template_prompt(request)
        response = await self._call_openai(prompt)
        content = self._parse_response(response)

        confidence, meta = self._evaluate_generation(
            content=content,
            language=request.template.language or "ko",
            tone=request.template.tone,
            max_len=50
        )

        return QuestionInstanceResponse(
            template_id=request.template.id,
            family_id=request.template.owner_family_id,
            subject_member_id=request.subject_member_id,
            content=content,
            planned_date=request.planned_date,
            status="draft",
            generated_by="ai",
            generation_model=settings.default_model,
            generation_parameters={
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature
            },
            generation_prompt=prompt,
            generation_metadata=meta,
            generation_confidence=confidence,
            generated_at=datetime.now()
        )

    def _build_template_prompt(self, request: QuestionInstanceCreateRequest) -> str:
        template = request.template
        base = f"""
당신은 가족 유대감을 증진시키는 질문 생성 전문가입니다.
아래 템플릿과 조건을 반영하여 질문 한 개만 한국어로 생성해주세요.

=== 템플릿 ===
본문: {template.content}
카테고리: {template.category or '미지정'}
톤: {template.tone or '미지정'}
언어: {template.language or 'ko'}
태그: {', '.join(template.tags) if template.tags else '없음'}
주제 인물 필요: {template.subject_required}

=== 조건 ===
주제 인물 ID: {request.subject_member_id if request.subject_member_id is not None else '없음'}
분위기: {request.mood or '기본'}
추가 컨텍스트: {request.extra_context or {}}
이전 답변 분석: {request.answer_analysis or '없음'}

=== 생성 규칙 ===
1) 존댓말 사용
2) 템플릿의 카테고리({template.category or '미지정'})에 부합하는 질문 생성
3) 50자 이내
4) 설명 없이 질문만 출력
5) 불필요한 따옴표/번호/접두어 제거

질문:"""
        return base

    async def _call_openai(self, prompt: str) -> str:
        return self.client.chat_completion(
            [
                {"role": "system", "content": "당신은 가족 유대감 증진을 위한 질문 생성 전문가입니다. 따뜻하고 진정성 있는 질문을 만드는 것이 목표입니다."},
                {"role": "user", "content": prompt}
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


