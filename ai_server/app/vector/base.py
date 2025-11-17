"""벡터 DB 서비스 인터페이스"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class VectorService(ABC):
    """벡터 DB 서비스 추상 클래스 (전략 패턴)"""
    
    @abstractmethod
    async def store_answer(
        self,
        answer_id: str,
        user_id: str,
        question_text: str,
        answer_text: str,
        category: Optional[str] = None,
        sentiment: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        답변을 벡터 DB에 저장
        
        Args:
            answer_id: 답변 고유 ID (AI 서버에서 생성)
            user_id: 사용자 ID (필수, 다른 사용자 데이터 분리용)
            question_text: 질문 내용 (맥락 제공)
            answer_text: 원본 답변 텍스트 (임베딩 대상)
            category: 질문 카테고리 (선택)
            sentiment: 감정 점수 (선택, 답변 분석 결과)
            timestamp: 답변 시간 (선택, 기본값: 현재 시간)
        
        Returns:
            bool: 저장 성공 여부
        """
        pass
    
    @abstractmethod
    async def search_similar_answers(
        self,
        user_id: str,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None
    ) -> List[dict]:
        """
        유사한 과거 답변 검색 (RAG용)
        
        Args:
            user_id: 사용자 ID (필수, 해당 사용자의 답변만 검색)
            query: 검색 쿼리 (현재 질문 또는 카테고리)
            top_k: 반환할 최대 결과 수
            category: 카테고리 필터 (선택)
        
        Returns:
            List[dict]: 유사 답변 리스트
                [
                    {
                        "question": "질문 내용",
                        "answer": "답변 내용",
                        "category": "카테고리",
                        "timestamp": "2025-11-16T...",
                        "similarity": 0.85
                    },
                    ...
                ]
        """
        pass

