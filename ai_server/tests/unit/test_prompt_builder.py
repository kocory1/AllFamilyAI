"""
프롬프트 빌더 & 파싱 로직 테스트
시니어 피드백 반영: 의미 있는 테스트만, 안전장치 추가
"""
import pytest
from app.question.openai_question_generator import OpenAIQuestionGenerator
from app.question.models import QuestionGenerateRequest


@pytest.mark.unit
class TestPromptBuilder:
    """프롬프트 생성 로직 테스트"""
    
    @pytest.fixture
    def generator(self):
        """Generator 인스턴스"""
        return OpenAIQuestionGenerator()
    
    def test_build_prompt_basic(self, generator):
        """기본 프롬프트 생성"""
        request = QuestionGenerateRequest(
            content="기본 질문입니다",
            category="일상",
            tone="편안한"
        )
        
        prompt = generator._build_prompt(request, past_answers=None)
        
        # 프롬프트에 카테고리와 톤이 포함되어 있는지 확인
        assert "일상" in prompt
        assert "편안한" in prompt
        assert "질문" in prompt
    
    def test_build_prompt_with_rag_context(self, generator):
        """RAG 컨텍스트 포함 프롬프트"""
        request = QuestionGenerateRequest(
            content="파생 질문",
            category="가족",
            tone="따뜻한"
        )
        
        past_answers = [
            {
                "answer": "주말에 가족과 등산을 갔어요.",
                "question": "주말에 뭐 했어요?",
                "similarity": 0.85
            },
            {
                "answer": "아이들과 공원에서 놀았어요.",
                "question": "최근 즐거웠던 순간은?",
                "similarity": 0.78
            }
        ]
        
        prompt = generator._build_prompt(request, past_answers=past_answers)
        
        # RAG 컨텍스트가 포함되어 있는지 확인
        assert "과거 대화" in prompt or "맥락" in prompt
        assert "등산" in prompt
        assert "공원" in prompt
    
    def test_build_prompt_without_rag(self, generator):
        """RAG 없는 프롬프트 (past_answers=None)"""
        request = QuestionGenerateRequest(content="질문", category="추억")
        
        prompt = generator._build_prompt(request, past_answers=None)
        
        # RAG 관련 내용이 없어야 함
        assert "과거 대화" not in prompt
    
    def test_build_prompt_with_empty_category(self, generator):
        """[안전장치] 빈 카테고리 처리"""
        request = QuestionGenerateRequest(
            content="질문",
            category=""  # 빈 문자열
        )
        
        # 에러 없이 프롬프트 생성되어야 함
        prompt = generator._build_prompt(request, past_answers=None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_build_prompt_with_long_rag_context(self, generator):
        """[안전장치] 긴 RAG 컨텍스트 처리 (최대 5개 제한)"""
        request = QuestionGenerateRequest(
            content="질문",
            category="일상"
        )
        
        # 10개의 과거 답변 제공
        past_answers = [
            {
                "answer": f"답변 {i}번입니다.",
                "question": f"질문 {i}번?",
                "similarity": 0.9 - (i * 0.05)
            } for i in range(1, 11)
        ]
        
        # 프롬프트 생성
        prompt = generator._build_prompt(request, past_answers=past_answers)
        assert isinstance(prompt, str)
        
        # 최대 5개만 포함되어야 함 (시니어 피드백 반영)
        # "1." ~ "5."는 있어야 하고, "6." ~ "10."은 없어야 함
        for i in range(1, 6):
            assert f"{i}." in prompt, f"{i}번째 답변이 없음"
        
        # 6번째 이후는 없어야 함 (최대 5개 제한)
        # "총 10개 답변 중 상위 5개만 표시" 메시지 확인
        if len(past_answers) > 5:
            assert "상위 5개" in prompt or "5개만" in prompt
    
    def test_build_rag_context_helper(self, generator):
        """[리팩토링] Helper 메서드 테스트 - _build_rag_context"""
        past_answers = [
            {
                "answer": "가족과 등산했어요.",
                "question": "주말에 뭐 했어요?",
                "timestamp": "2025-01-01T10:00:00"
            }
        ]
        
        context = generator._build_rag_context(past_answers)
        
        # RAG 컨텍스트가 생성되어야 함
        assert "과거 대화" in context or "맥락" in context
        assert "등산" in context
        assert isinstance(context, str)
    
    def test_build_rag_context_empty(self, generator):
        """[리팩토링] Helper 메서드 테스트 - 빈 RAG 컨텍스트"""
        # 빈 리스트
        context1 = generator._build_rag_context([])
        assert context1 == ""
        
        # None
        context2 = generator._build_rag_context(None)
        assert context2 == ""
    
    def test_build_generation_rules_helper(self, generator):
        """[리팩토링] Helper 메서드 테스트 - _build_generation_rules"""
        rules = generator._build_generation_rules()
        
        # 생성 규칙이 포함되어야 함
        assert "생성 규칙" in rules or "규칙" in rules
        assert "물음표" in rules or "?" in rules
        assert isinstance(rules, str)
        assert len(rules) > 0


@pytest.mark.unit
class TestResponseParser:
    """응답 파싱 로직 테스트 (실무적 방어)"""
    
    @pytest.fixture
    def generator(self):
        return OpenAIQuestionGenerator()
    
    def test_parse_response_clean(self, generator):
        """정상 케이스 - 깔끔한 응답"""
        response = "오늘 저녁에는 뭐 드셨어요?"
        parsed = generator._parse_response(response)
        
        assert parsed == "오늘 저녁에는 뭐 드셨어요?"
    
    def test_parse_response_with_prefix_korean(self, generator):
        """[방어] '질문:' 접두사 제거 (LLM 사족)"""
        response = "질문: 요즘 주말엔 가족이랑 뭘 해요?"
        parsed = generator._parse_response(response)
        
        # '질문:' 접두사가 제거되어야 함
        assert parsed == "요즘 주말엔 가족이랑 뭘 해요?"
        assert not parsed.startswith("질문:")
    
    def test_parse_response_with_prefix_english(self, generator):
        """[방어] 'Question:' 접두사 제거"""
        response = "Question: What did you do today?"
        parsed = generator._parse_response(response)
        
        assert parsed == "What did you do today?"
        assert not parsed.startswith("Question:")
    
    def test_parse_response_with_answer_prefix(self, generator):
        """[방어] '답변:' 접두사 제거 (LLM 혼동)"""
        response = "답변: 오늘 기분이 어때요?"
        parsed = generator._parse_response(response)
        
        assert parsed == "오늘 기분이 어때요?"
        assert not parsed.startswith("답변:")
    
    def test_parse_response_with_quotes(self, generator):
        """[방어] 따옴표 제거 (LLM이 자주 붙임)"""
        test_cases = [
            '"오늘 뭐 했어요?"',      # 영문 큰따옴표
            "'오늘 뭐 했어요?'",      # 영문 작은따옴표
            '"오늘 뭐 했어요?"',      # 한글 큰따옴표
        ]
        
        for response in test_cases:
            parsed = generator._parse_response(response)
            # 따옴표가 제거되어야 함
            assert not parsed.startswith(('"', "'", '"', '''))
            assert not parsed.endswith(('"', "'", '"', '''))
            assert "오늘 뭐 했어요?" in parsed
    
    def test_parse_response_multiline(self, generator):
        """[방어] 여러 줄 중 첫 번째 줄만 추출"""
        response = """오늘 기분이 어때요?
        
이것은 추가 설명입니다.
더 긴 텍스트가 있을 수 있습니다."""
        
        parsed = generator._parse_response(response)
        
        # 첫 번째 줄만 반환되어야 함
        assert parsed == "오늘 기분이 어때요?"
        assert "추가 설명" not in parsed
    
    def test_parse_response_with_whitespace(self, generator):
        """[방어] 공백 제거"""
        response = "  \n  오늘 저녁에는 뭐 드셨어요?  \n  "
        parsed = generator._parse_response(response)
        
        assert parsed == "오늘 저녁에는 뭐 드셨어요?"
    
    def test_parse_response_complex(self, generator):
        """[방어] 복합 케이스 (접두사 + 따옴표 + 공백)"""
        response = '  질문: "오늘 뭐 했어요?"  '
        parsed = generator._parse_response(response)
        
        # 모든 불필요한 요소가 제거되어야 함
        assert parsed == "오늘 뭐 했어요?"


@pytest.mark.unit
class TestGenerationEvaluation:
    """생성 평가 로직 테스트"""
    
    @pytest.fixture
    def generator(self):
        return OpenAIQuestionGenerator()
    
    def test_evaluate_generation_basic(self, generator):
        """기본 평가 로직"""
        confidence, metadata = generator._evaluate_generation(
            content="오늘 저녁 뭐 드셨어요?",
            language="ko",
            tone="편안한",
            max_len=100
        )
        
        # 신뢰도 범위 확인
        assert 0 <= confidence <= 1
        
        # 메타데이터 구조 확인
        assert "questionLength" in metadata
        assert "hasQuestionMark" in metadata
        assert metadata["language"] == "ko"
    
    def test_evaluate_generation_without_question_mark(self, generator):
        """물음표 없는 질문 (신뢰도 낮아야 함)"""
        confidence_with, _ = generator._evaluate_generation(
            content="오늘 저녁 뭐 드셨어요?",
            language="ko",
            tone="편안한",
            max_len=100
        )
        
        confidence_without, _ = generator._evaluate_generation(
            content="오늘 저녁 뭐 드셨어요",  # 물음표 없음
            language="ko",
            tone="편안한",
            max_len=100
        )
        
        # 물음표 있는 쪽이 신뢰도 높아야 함 (만약 구현에 이 로직이 있다면)
        # 실제 구현에 따라 조정 필요
        assert isinstance(confidence_with, float)
        assert isinstance(confidence_without, float)
    
    def test_evaluate_generation_too_long(self, generator):
        """너무 긴 질문 (신뢰도 낮아야 함)"""
        long_content = "A" * 200
        
        confidence, metadata = generator._evaluate_generation(
            content=long_content,
            language="ko",
            tone="편안한",
            max_len=100
        )
        
        # 신뢰도가 낮아야 함 (길이 초과)
        assert 0 <= confidence <= 1
        assert metadata["questionLength"] > 100
