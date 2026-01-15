"""OpenAI를 활용한 질문 생성 전략 구현체

시니어 피드백 반영:
- Helper 메서드로 _build_prompt 리팩토링 (가독성/유지보수성)
- RAG 컨텍스트 길이 제한 (최대 5개)
- System Prompt 강화 (가족 대화 맥락)
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.question.base import QuestionGenerator
from app.question.models import QuestionGenerateRequest, QuestionInstanceResponse
from app.adapters.openai_client import OpenAIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIQuestionGenerator(QuestionGenerator):
    def __init__(self):
        self.client = OpenAIClient()

    async def generate(
        self,
        request: QuestionGenerateRequest,
        past_answers: Optional[List[dict]] = None
    ) -> QuestionInstanceResponse:
        """질문 생성"""
        # RAG 활성화 여부
        rag_enabled = past_answers is not None and len(past_answers) > 0
        
        # 프롬프트 생성
        prompt = self._build_prompt(request, past_answers)
        
        # OpenAI 호출
        response = await self._call_openai(prompt)
        
        # 응답 파싱
        content = self._parse_response(response)

        # 신뢰도 평가
        confidence, meta = self._evaluate_generation(
            content=content,
            language=request.language or "ko",
            tone=request.tone,
            max_len=settings.max_question_length
        )

        # RAG 메타데이터 추가
        meta["ragEnabled"] = rag_enabled
        meta["ragContextCount"] = len(past_answers) if past_answers else 0
        if rag_enabled:
            meta["ragVersion"] = "v1"
        
        return QuestionInstanceResponse(
            content=content,
            generated_by="ai",
            generation_model=settings.default_model,
            generation_parameters={
                "max_completion_tokens": settings.max_tokens
            },
            generation_prompt=prompt,
            generation_metadata=meta,
            generation_confidence=confidence
        )
    
    def _build_rag_context(self, past_answers: List[dict]) -> str:
        """
        RAG 컨텍스트 섹션 생성
        
        개선:
        - 최대 5개로 제한 (토큰/비용 절감, Lost in the Middle 방지)
        - 명확한 주석 추가
        """
        if not past_answers or len(past_answers) == 0:
            return ""
        
        lines = []
        lines.append("=== 📚 과거 대화 맥락 (참고용) ===")
        lines.append("사용자가 이전에 답변한 내용입니다. 이를 참고하여 더 개인화된 질문을 만드세요.")
        lines.append("")
        
        # 최대 5개로 제한 (비용/성능 최적화)
        # 서비스 레이어에서 top_k로 이미 필터링했지만, 추가 보호
        limited_answers = past_answers[:5]
        
        for idx, item in enumerate(limited_answers, 1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            timestamp = item.get("timestamp", "")
            
            # 상대적 시간 표시
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
                except Exception:
                    pass
            
            lines.append(f"{idx}. {time_str}")
            lines.append(f"   Q: {question}")
            lines.append(f"   A: {answer}")
            lines.append("")
        
        # 5개 초과 시 알림
        if len(past_answers) > 5:
            lines.append(f"💡 (총 {len(past_answers)}개 답변 중 상위 5개만 표시)")
            lines.append("")
        
        lines.append("👉 위 맥락을 참고하여:")
        lines.append("- 사용자가 관심 있어하는 주제를 반영하세요")
        lines.append("- 이전 답변에서 언급된 구체적인 상황을 활용하세요")
        lines.append("- 단, 과거 질문을 그대로 반복하지 마세요")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_answer_analysis_context(self, request: QuestionGenerateRequest) -> str:
        """답변 분석 컨텍스트 섹션 생성 (팔로업 모드)"""
        if not request.answer_analysis:
            return ""
        
        lines = []
        lines.append("=== 📌 사용자의 답변 내용 (핵심!) ===")
        
        analysis = request.answer_analysis
        summary = analysis.summary
        categories = analysis.categories
        scores = analysis.scores
        keywords = analysis.keywords
        
        if summary:
            lines.append(f"답변 요약: {summary}")
        if keywords:
            lines.append(f"🔑 핵심 키워드: {', '.join(keywords)}")
        if categories:
            lines.append(f"주제: {', '.join(categories)}")
        
        # 감정 분석
        if scores and scores.emotion:
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
        lines.append("- 답변에 구체적인 고유명사(영화/노래 제목, 장소, 브랜드 등)가 있다면 반드시 그것에 대해 구체적으로 물어보세요.")
        lines.append("- 예: '헌터헌터 오프닝' -> '오, 그 애니 재밌나요?' 또는 '어떤 버전 오프닝 좋아하세요?'")
        lines.append("- ❌ 절대 금지: 구체적인 답변을 무시하고 다시 '노래'나 '취미' 같은 큰 범주로 질문하기")
        lines.append("- 긍정적 감정이면 그 주제를 더 깊이 파고드세요.")
        lines.append("- 부정적 감정이면 화제를 자연스럽게 전환하세요.")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_generation_rules(self) -> str:
        """질문 생성 규칙 섹션"""
        lines = []
        lines.append("=== 생성 규칙 ===")
        lines.append("1) 짧고 간결하게: 한 문장, 40자 이내 권장")
        lines.append("2) 자연스러운 말투: '~나요?', '~어요?', '~있어요?' 같은 편안한 의문형")
        lines.append("3) ⚠️ 금지 표현:")
        lines.append("   - 형식적: '떠올리시고', '말씀해 주세요', '자세히', '구체적으로'")
        lines.append("   - 무거움: '순간', '기억', '떠오르나요', '느꼈나요'")
        lines.append("   - 앵무새 화법: 답변을 단순히 따라하지 마세요. (단, 구체적인 고유명사는 언급해도 좋습니다)")
        lines.append("4) 물음표(?)로 끝나야 합니다")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_prompt(
        self,
        request: QuestionGenerateRequest,
        past_answers: Optional[List[dict]] = None
    ) -> str:
        """
        질문 생성 프롬프트 조립
        
        리팩토링: Helper 메서드로 섹션 분리 (가독성/유지보수성 향상)
        """
        lines = []
        lines.append("=== 🎯 미션 ===")
        lines.append("가족 간의 대화를 이어주는 자연스러운 질문을 만들어주세요.")
        lines.append("")
        
        # RAG 컨텍스트 (최대 5개)
        rag_context = self._build_rag_context(past_answers or [])
        if rag_context:
            lines.append(rag_context)
        
        # 이전 질문 (베이스)
        lines.append("=== 이전 질문 ===")
        lines.append(f"{request.content}")
        lines.append("")
        
        # 맥락 정보
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
        
        if ctx:
            lines.append("=== 맥락 ===")
            lines.extend(ctx)
            lines.append("")

        # 답변 분석 (팔로업 모드)
        answer_context = self._build_answer_analysis_context(request)
        if answer_context:
            lines.append(answer_context)

        # 생성 규칙
        lines.append(self._build_generation_rules())
        
        # 예시 (팔로업 모드일 때만)
        if request.answer_analysis and request.answer_analysis.keywords:
            lines.append("📝 변환 예시:")
            lines.append("  → 답변: '헌터헌터 오프닝 듣는 중'")
            lines.append("  → ❌ 나쁨: '가장 좋아하는 노래가 뭔가요?' (구체적 내용 무시)")
            lines.append("  → ✅ 좋음: '오, 헌터헌터! 구작이랑 신작 중에 어떤 거 보세요?' (구체적 관심)")
        lines.append("")
        
        lines.append("위 가이드라인을 따라 자연스러운 질문 1개만 생성하세요:")
        
        return "\n".join(lines)

    async def _call_openai(self, prompt: str) -> str:
        """
        OpenAI API 호출
        
        개선: System Prompt 강화 (가족 대화 맥락 명확화)
        """
        return await self.client.chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 가족 간의 대화를 이어주는 AI 어시스턴트입니다. "
                        "사용자가 부모님이나 자녀와 대화할 거리를 만들어주는 것이 목표입니다. "
                        "\n\n"
                        "친구처럼 자연스럽게 대화하되, 가족 관계에 적합한 따뜻하고 편안한 톤을 유지하세요. "
                        "카톡으로 가족에게 '요즘 어때?', '재밌는 일 있어?' 묻듯이 가볍고 자연스럽게 질문하세요. "
                        "\n\n"
                        "절대 하지 말아야 할 것: "
                        "1) 구체적인 고유명사가 나왔는데 뜬금없이 포괄적인 질문으로 돌아가기 "
                        "2) 앵무새처럼 답변 내용을 그대로 읊기 "
                        "3) 무겁거나 형식적인 표현 ('순간', '기억', '떠오르나요') "
                        "4) 심리상담 같은 질문 ('어떤 감정이', '어떤 의미가') "
                        "5) 부정적 감정을 계속 파고들기"
                    ),
                },
                {"role": "user", "content": prompt},
            ]
        )

    def _parse_response(self, response: str) -> str:
        """
        LLM 응답 파싱 (방어 로직 포함)
        - 접두사 제거: '질문:', '답변:', 'Question:', 'Answer:'
        - 따옴표 제거: ", ', ", ', ', ' 등
        - 공백 제거
        - 첫 번째 유효한 줄만 반환
        """
        text = response.strip()
        
        # 접두사 제거
        prefixes = ['질문:', '답변:', 'Question:', 'Answer:', '질문 :', '답변 :']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        # 따옴표 제거 (영문, 한글)
        quotes = ['"', "'", '"', '"', ''', ''']
        while text and text[0] in quotes:
            text = text[1:]
        while text and text[-1] in quotes:
            text = text[:-1]
        
        text = text.strip()
        
        # 첫 번째 유효한 줄 반환
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                return line
        
        return text

    def _evaluate_generation(
        self,
        content: str,
        language: str,
        tone: Optional[str],
        max_len: int
    ) -> tuple[float, dict]:
        """생성 품질 평가"""
        try:
            score = 1.0
            
            meta = {
                "questionLength": len(content),
                "hasQuestionMark": "?" in content or content.endswith("요") or content.endswith("가요"),
                "language": language,
                "tone": tone
            }
            
            # 길이 체크
            if len(content) > max_len:
                score -= 0.2
            
            # 물음표/어미 체크
            if not meta["hasQuestionMark"]:
                score -= 0.1
            
            score = max(0.0, min(1.0, score))
            return score, meta
        
        except Exception:
            return 0.5, {"error": "evaluation_failed"}
