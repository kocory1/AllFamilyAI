"""벡터 DB 서비스 인터페이스"""

from abc import ABC, abstractmethod

from app.vector.models import QADocument


class VectorService(ABC):
    """벡터 DB 서비스 추상 클래스 (전략 패턴)"""

    @abstractmethod
    async def store_qa(self, doc: QADocument) -> bool:
        """
        QA 문서를 벡터 DB에 저장

        Args:
            doc: QADocument Pydantic 모델

        Returns:
            bool: 저장 성공 여부
        """
        pass

    @abstractmethod
    async def search_for_personal(self, member_id: int, query: str, top_k: int = 5) -> list[dict]:
        """
        개인 QA 검색 (member_id 필터)

        Args:
            member_id: 멤버 ID (해당 멤버의 답변만 검색)
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            List[dict]: 유사 QA 리스트
                [
                    {
                        "question": "질문 내용",
                        "answer": "답변 내용",
                        "role_label": "첫째 딸",
                        "answered_at": "2026-01-15T10:30:00",
                        "similarity": 0.85
                    },
                    ...
                ]
        """
        pass

    @abstractmethod
    async def search_for_family(self, family_id: int, query: str, top_k: int = 5) -> list[dict]:
        """
        가족 QA 검색 (family_id 필터)

        Args:
            family_id: 가족 ID (해당 가족의 모든 답변 검색)
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수

        Returns:
            List[dict]: 유사 QA 리스트
                [
                    {
                        "question": "질문 내용",
                        "answer": "답변 내용",
                        "role_label": "엄마",
                        "member_id": 2,
                        "answered_at": "2026-01-15T14:20:00",
                        "similarity": 0.92
                    },
                    ...
                ]
        """
        pass
