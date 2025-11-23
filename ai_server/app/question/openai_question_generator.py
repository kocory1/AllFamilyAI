from typing import Optional, List
import logging
from datetime import datetime
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
        self,
        request: QuestionGenerateRequest,
        past_answers: Optional[List[dict]] = None  # 🆕 RAG 맥락
    ) -> QuestionInstanceResponse:
        # RAG 활성화 여부 판단
        rag_enabled = past_answers is not None and len(past_answers) > 0
        
        prompt = self._build_prompt(request, past_answers)
        logger.info(
            f"[질문 생성] 프롬프트 생성 완료 - "
            f"length={len(prompt)}, rag_enabled={rag_enabled}, "
            f"context_count={len(past_answers) if past_answers else 0}"
        )
        
        response = await self._call_openai(prompt)
        logger.info(f"[질문 생성] OpenAI 응답 받음 - length={len(response)}, preview='{response[:100]}'")
        
        content = self._parse_response(response)
        logger.info(f"[질문 생성] 파싱 완료 - content='{content}'")

        confidence, meta = self._evaluate_generation(
            content=content,
            language=request.language or "ko",
            tone=request.tone,
            max_len=settings.max_question_length
        )
        
        # 🆕 RAG 정보 추가 (camelCase로 BE 호환)
        meta["ragEnabled"] = rag_enabled
        meta["ragContextCount"] = len(past_answers) if past_answers else 0
        if rag_enabled:
            meta["ragVersion"] = "v1"  # RAG 버전 (추후 개선 추적용)

        return QuestionInstanceResponse(
            content=content,
            generated_by="ai",
            generation_model=settings.default_model,
            generation_parameters={"max_completion_tokens": settings.max_tokens},
            generation_prompt=prompt,
            generation_metadata=meta,  # RAG 정보 포함!
            generation_confidence=confidence
        )

    def _build_prompt(
        self,
        request: QuestionGenerateRequest,
        past_answers: Optional[List[dict]] = None  # 🆕 RAG 맥락
    ) -> str:
        lines = []
        lines.append("당신은 가족과의 자연스러운 대화를 돕는 질문 생성 전문가입니다.")
        
        # 답변 분석이 있으면 팔로업 모드, 없으면 새 질문 모드
        if request.answer_analysis:
            lines.append("사용자가 답변한 내용을 바탕으로, 더 깊이 파고드는 자연스러운 팔로업 질문을 만드세요.")
            lines.append("⚠️ 중요: 이전 질문을 반복하거나 패러프레이징하지 마세요. 답변 내용에서 새로운 질문을 만드세요.")
        else:
            lines.append("아래 주제로 친구처럼 부담 없이 물어보는 짧고 간단한 질문을 만드세요.")
        
        lines.append("")
        
        # 🆕 과거 대화 맥락 (RAG)
        if past_answers and len(past_answers) > 0:
            lines.append("=== 📚 과거 대화 맥락 (참고용) ===")
            lines.append("사용자가 이전에 답변한 내용입니다. 이를 참고하여 더 개인화된 질문을 만드세요.")
            lines.append("")
            
            for idx, item in enumerate(past_answers, 1):
                question = item.get("question", "")
                answer = item.get("answer", "")
                timestamp = item.get("timestamp", "")
                
                # 상대적 시간 표시 (선택)
                time_str = ""
                if timestamp:
                    try:
                        past_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        now = datetime.now(past_time.tzinfo)
                        delta = now - past_time
                        if delta.days > 0:
                            time_str = f"({delta.days}일 전)"
                        else:
                            time_str = "(오늘)"
                    except:
                        pass
                
                lines.append(f"{idx}. {time_str}")
                lines.append(f"   Q: {question}")
                lines.append(f"   A: {answer}")
                lines.append("")
            
            lines.append("👉 위 맥락을 참고하여:")
            lines.append("- 사용자가 관심 있어하는 주제를 반영하세요")
            lines.append("- 이전 답변에서 언급된 구체적인 상황을 활용하세요")
            lines.append("- 단, 과거 질문을 그대로 반복하지 마세요")
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
            lines.append("👉 팔로업 전략:")
            lines.append("- 키워드를 직접 언급하지 말고 자연스럽게 우회하기")
            lines.append("- 부정적 감정이면 긍정적 주제로 전환하기 (그리움 → 현재 즐거운 일)")
            lines.append("- 긍정적이면 살짝만 더 파고드는 심화 질문 생성")
            lines.append("- 무겁거나 형식적인 질문 금지 ('떠오르나요', '기억', '순간' 같은 표현 피하기)")
            lines.append("- 가볍고 일상적인 질문으로 대화 이어가기")
            lines.append("")

        # 생성 규칙
        lines.append("=== 생성 규칙 ===")
        lines.append("1) 짧고 간결하게: 한 문장, 40자 이내 권장")
        lines.append("2) 자연스러운 말투: '~나요?', '~어요?', '~있어요?' 같은 편안한 의문형")
        lines.append("3) ⚠️ 금지 표현:")
        lines.append("   - 형식적: '떠올리시고', '말씀해 주세요', '자세히', '구체적으로', '조금 더'")
        lines.append("   - 무거움: '순간', '기억', '떠오르나요', '느꼈나요', '생각하나요'")
        lines.append("   - 키워드 직접 언급: 답변에 나온 단어를 그대로 질문에 넣지 말기")
        lines.append("4) 감정 전환: 부정적 답변이면 긍정적/가벼운 주제로 바꾸기")
        lines.append("5) 친구처럼: 카톡하듯이 가볍게 물어보기")
        lines.append("")
        
        if request.answer_analysis:
            lines.append("좋은 팔로업 예시:")
            lines.append("- 답변: '요새 본가에 못간지 좀 되어서 그립다' (그리움, 부정적)")
            lines.append("  → ❌ 나쁨: '그리움이 가장 강해지는 순간은 언제예요?' (무겁고 형식적)")
            lines.append("  → ❌ 나쁨: '유학 중 그리움이 생길 때 어떤 기억이 떠오르나요?' (키워드 직접 언급, AI같음)")
            lines.append("  → ✅ 좋음: '요즘 주말에는 어떻게 지내고 있어요?' (주제 전환, 가벼움)")
            lines.append("  → ✅ 좋음: '유학에서 재밌었던 일 있어요?' (주제에 대한 긍정적 전환)")
            lines.append("")
        else:
            lines.append("좋은 예시:")
            lines.append("- 최근 가족과 함께한 소소한 기쁨이 있었나요?")
            lines.append("- 요즘 가족과 어떤 시간을 보내고 있어요?")
            lines.append("- 가족 중에 가장 닮고 싶은 사람이 있나요?")
            lines.append("")
        
        lines.append("위 가이드라인을 따라 자연스러운 질문 1개만 생성하세요:")
        return "\n".join(lines)

    async def _call_openai(self, prompt: str) -> str:
        return await self.client.chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 친구처럼 자연스럽게 대화하는 질문 생성 전문가입니다. "
                        "카톡으로 친구에게 '요즘 어때?', '재밌는 일 있어?' 묻듯이 가볍고 자연스럽게 질문하세요. "
                        "절대 하지 말아야 할 것: "
                        "1) 답변의 키워드를 그대로 질문에 넣기 (예: 답변에 '유학'이 나왔다고 '유학 중...'이라고 묻지 마세요) "
                        "2) 무겁거나 형식적인 표현 ('순간', '기억', '떠오르나요', '느꼈나요') "
                        "3) 심리상담 같은 질문 ('어떤 감정이', '어떤 의미가') "
                        "4) 부정적 감정을 계속 파고들기 (답변이 '그립다'면 '그리움'을 또 묻지 말고 현재 즐거운 일로 전환)"
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
            # camelCase로 BE 호환
            meta: dict = {
                "length": len(content),
                "language": language,
                "tone": tone,
                "rules": {
                    "lengthOk": len(content) <= max_len,
                    "endsQuestion": content.strip().endswith("?") or content.strip().endswith("요") or content.strip().endswith("가요"),
                }
            }
            if not meta["rules"]["lengthOk"]:
                score -= 0.2
            if not meta["rules"]["endsQuestion"]:
                score -= 0.1
            score = max(0.0, min(1.0, score))
            return score, meta
        except Exception:
            return 0.5, {"error": "evaluation_failed"}


