"""
답변 분석 로직 테스트 (OpenAI Mock)
시니어 피드백 반영: AsyncMock + SimpleNamespace + 안전한 Mocking
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from app.answer.openai_answer_analyzer import OpenAIAnswerAnalyzer
from app.answer.models import AnswerAnalysisRequest


@pytest.mark.unit
class TestAnswerAnalyzer:
    """답변 분석기 테스트 (Mock)"""
    
    @pytest.fixture
    def analyzer(self):
        """
        Analyzer 인스턴스
        실제 API 호출을 막기 위해 client를 AsyncMock으로 교체
        """
        analyzer = OpenAIAnswerAnalyzer()
        # client 전체를 AsyncMock으로 교체 (실제 API 호출 방지)
        analyzer.client = AsyncMock()
        return analyzer
    
    @pytest.fixture
    def mock_openai_response_text(self):
        """OpenAI 응답 텍스트 (JSON 형식) - ScoreSanitizer spec 준수"""
        return """{
  "summary": "가족과 등산을 다녀온 즐거운 경험",
  "categories": ["일상", "가족", "운동"],
  "scores": {
    "sentiment": 0.8,
    "emotion": {
      "joy": 0.9,
      "sadness": 0.1,
      "anger": 0.0,
      "fear": 0.0,
      "neutral": 0.2
    },
    "relevance_to_question": 0.95,
    "relevance_to_category": 0.85,
    "toxicity": 0.0,
    "length": 45
  }
}"""
    
    async def test_analyze_answer_success(
        self, 
        analyzer, 
        mock_openai_response_text,
        sample_answer_request
    ):
        """[성공] 답변 분석 전체 플로우 (AsyncMock)"""
        
        # 1. Mock 응답 직접 설정 (chat_completion 메서드를 Mock)
        analyzer.client.chat_completion.return_value = mock_openai_response_text
        
        # 2. 실행
        request = AnswerAnalysisRequest(**sample_answer_request)
        result = await analyzer.analyze(request)
        
        # 3. 검증
        assert result.summary == "가족과 등산을 다녀온 즐거운 경험"
        assert "일상" in result.categories or "가족" in result.categories
        
        # ScoreSanitizer가 처리한 scores 검증
        assert result.scores["sentiment"] == 0.8
        assert "emotion" in result.scores
        assert result.scores["emotion"]["joy"] == 0.9
        assert result.scores["relevance_to_question"] == 0.95
        
        # 4. 호출 확인 (chat_completion이 한 번 호출되었는지)
        analyzer.client.chat_completion.assert_awaited_once()
    
    async def test_parse_response_json_clean(self, analyzer, mock_openai_response_text):
        """[성공] JSON 파싱 (analyze 내부에서 처리)"""
        # _parse_response 메서드는 존재하지 않으므로, 직접 JSON 파싱 테스트
        analyzer.client.chat_completion.return_value = mock_openai_response_text
        
        # analyze를 통해 파싱이 제대로 되는지 확인
        request = AnswerAnalysisRequest(
            answerText="테스트 답변",
            questionContent="테스트 질문",
            questionCategory="일상",
            userId="test_user"
        )
        result = await analyzer.analyze(request)
        
        assert result.summary == "가족과 등산을 다녀온 즐거운 경험"
        assert len(result.categories) > 0
        assert result.analysis_raw.parseOk is True
    
    async def test_parse_response_with_json_embedded(self, analyzer):
        """[성공] 텍스트 안에 JSON이 포함된 경우 파싱"""
        # 텍스트 중간에 JSON이 있는 경우
        malformed_json = """여기는 설명입니다.
{
  "summary": "테스트 요약",
  "categories": ["테스트"],
  "scores": {
    "sentiment": 0.6,
    "toxicity": 0.1
  }
}
이것도 무시됩니다."""
        
        analyzer.client.chat_completion.return_value = malformed_json
        
        request = AnswerAnalysisRequest(
            answerText="테스트",
            questionContent="질문",
            questionCategory="일상",
            userId="test"
        )
        result = await analyzer.analyze(request)
        
        assert result.summary == "테스트 요약"
        assert result.analysis_raw.parseOk is True
        assert result.scores["sentiment"] == 0.6
    
    def test_build_prompt(self, analyzer, sample_answer_request):
        """프롬프트 생성 테스트"""
        request = AnswerAnalysisRequest(**sample_answer_request)
        prompt = analyzer._build_prompt(request)
        
        # 프롬프트에 질문과 답변이 포함되어 있는지 확인
        assert request.question_content in prompt
        assert request.answer_text in prompt
        assert "summary" in prompt.lower() or "요약" in prompt
        assert "categories" in prompt.lower() or "카테고리" in prompt
    
    async def test_json_parse_failure_handling(self, analyzer, sample_answer_request):
        """[엣지] JSON 파싱 실패 시 빈 값으로 처리"""
        # 완전히 잘못된 JSON
        analyzer.client.chat_completion.return_value = "이것은 JSON이 아닙니다."
        
        request = AnswerAnalysisRequest(**sample_answer_request)
        result = await analyzer.analyze(request)
        
        # 파싱 실패해도 응답 객체는 생성되어야 함
        assert result.summary == ""
        assert result.categories == []
        assert result.analysis_raw.parseOk is False


@pytest.mark.unit
class TestAnswerAnalyzerEdgeCases:
    """답변 분석기 엣지 케이스 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        analyzer = OpenAIAnswerAnalyzer()
        analyzer.client = AsyncMock()
        return analyzer
    
    async def test_analyze_with_empty_categories(self, analyzer, sample_answer_request):
        """[엣지] 카테고리가 빈 배열인 경우"""
        analyzer.client.chat_completion.return_value = '{"summary": "요약", "categories": [], "scores": {}}'
        
        request = AnswerAnalysisRequest(**sample_answer_request)
        result = await analyzer.analyze(request)
        
        assert result.categories == []
        assert result.summary == "요약"
    
    async def test_analyze_with_missing_scores(self, analyzer, sample_answer_request):
        """[엣지] scores가 누락된 경우"""
        analyzer.client.chat_completion.return_value = '{"summary": "테스트", "categories": ["일상"]}'
        
        request = AnswerAnalysisRequest(**sample_answer_request)
        result = await analyzer.analyze(request)
        
        assert result.scores == {}
        assert result.summary == "테스트"
