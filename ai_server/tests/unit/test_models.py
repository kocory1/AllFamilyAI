"""
Pydantic 모델 검증 테스트
"""
import pytest
from pydantic import ValidationError
from app.question.models import (
    QuestionGenerateRequest,
    QuestionInstanceResponse
)
from app.answer.models import (
    AnswerAnalysisRequest,
    AnswerAnalysisResponse
)


class TestQuestionModels:
    """질문 모델 테스트"""
    
    def test_question_generate_request_valid(self):
        """유효한 질문 생성 요청"""
        data = {
            "content": "오늘 하루 어땠어요?",
            "category": "일상",
            "tone": "편안한",
            "subjectMemberId": "user_123",
            "useRag": True
        }
        request = QuestionGenerateRequest(**data)
        
        assert request.content == "오늘 하루 어땠어요?"
        assert request.category == "일상"
        assert request.tone == "편안한"
        assert request.subject_member_id == "user_123"
        assert request.use_rag is True
    
    def test_question_generate_request_camel_case_alias(self):
        """camelCase 필드 alias 검증"""
        data = {
            "content": "최근 기억에 남는 일이 있나요?",
            "category": "추억",
            "subjectMemberId": "user_456"
        }
        request = QuestionGenerateRequest(**data)
        
        # 내부는 snake_case
        assert request.content == "최근 기억에 남는 일이 있나요?"
        assert request.subject_member_id == "user_456"
        
        # 직렬화는 camelCase
        json_data = request.model_dump(by_alias=True)
        assert "subjectMemberId" in json_data
        assert "subject_member_id" not in json_data
    
    def test_question_generate_request_defaults(self):
        """기본값 검증"""
        request = QuestionGenerateRequest(
            content="오늘 기분이 어때요?",
            category="감정"
        )
        
        assert request.content == "오늘 기분이 어때요?"
        assert request.use_rag is True  # 기본값
        assert request.subject_member_id is None
        assert request.tone is None
    
    def test_question_instance_response_camel_case(self):
        """QuestionInstanceResponse camelCase 변환"""
        data = {
            "content": "오늘 기분이 어때요?",
            "generatedBy": "ai",
            "generationModel": "gpt-4o-mini",
            "generationParameters": {"max_tokens": 100},
            "generationPrompt": "test prompt",
            "generationMetadata": {"ragEnabled": True},
            "generationConfidence": 0.95
        }
        response = QuestionInstanceResponse(**data)
        
        assert response.content == "오늘 기분이 어때요?"
        assert response.generated_by == "ai"
        assert response.generation_confidence == 0.95
        
        # 직렬화 검증
        json_data = response.model_dump(by_alias=True)
        assert "generatedBy" in json_data
        assert "generated_by" not in json_data


class TestAnswerModels:
    """답변 모델 테스트"""
    
    def test_answer_analysis_request_valid(self):
        """유효한 답변 분석 요청"""
        data = {
            "userId": "user_789",
            "questionContent": "오늘 뭐 하셨어요?",
            "answerText": "친구들과 저녁을 먹었어요.",
            "questionCategory": "일상"
        }
        request = AnswerAnalysisRequest(**data)
        
        assert request.user_id == "user_789"
        assert request.question_content == "오늘 뭐 하셨어요?"
        assert request.answer_text == "친구들과 저녁을 먹었어요."
    
    def test_answer_analysis_request_missing_required(self):
        """필수 필드 누락 시 ValidationError"""
        data = {
            "userId": "user_123"
            # questionContent, answerText 누락
        }
        
        with pytest.raises(ValidationError):
            AnswerAnalysisRequest(**data)
    
    def test_answer_analysis_response_structure(self):
        """답변 분석 응답 구조 검증"""
        from datetime import datetime
        data = {
            "analysisPrompt": "test prompt",
            "analysisParameters": {"model": "gpt-4o-mini"},
            "analysisRaw": {
                "text": '{"summary": "test"}',
                "parseOk": True
            },
            "analysisVersion": "ans-v1.0",
            "summary": "친구와의 저녁 식사",
            "categories": ["일상", "식사"],
            "keywords": ["친구", "저녁"],
            "scores": {
                "sentiment": 0.8,
                "toxicity": 0.1
            },
            "createdAt": datetime.now().isoformat()
        }
        response = AnswerAnalysisResponse(**data)
        
        assert response.summary == "친구와의 저녁 식사"
        assert len(response.categories) == 2
        assert response.scores["sentiment"] == 0.8
        assert response.analysis_raw.parseOk is True

