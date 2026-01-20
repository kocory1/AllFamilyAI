"""
Vector Store Port (인터페이스)

Clean Architecture - 의존성 역전 원칙:
- Domain Layer가 정의하는 인터페이스
- Infrastructure Layer가 구현
- Use Case는 이 인터페이스에만 의존
"""

from abc import ABC, abstractmethod

from app.domain.entities.qa_document import QADocument


class VectorStorePort(ABC):
    """
    벡터 DB 인터페이스 (Port)

    구현체는 Infrastructure Layer에 위치:
    - ChromaVectorStore (ChromaDB 구현)
    - PineconeVectorStore (Pinecone 구현)
    - MockVectorStore (테스트용)

    의존성 방향: Domain ← Infrastructure (역전)
    """

    @abstractmethod
    async def store(self, doc: QADocument) -> bool:
        """
        QA 문서 저장

        Args:
            doc: QADocument Domain Entity

        Returns:
            저장 성공 여부
        """
        pass

    @abstractmethod
    async def search_by_member(
        self,
        member_id: str,  # UUID
        query_doc: QADocument,
        top_k: int = 5,
    ) -> list[QADocument]:
        """
        개인 QA 검색 (member_id 필터)

        Args:
            member_id: 검색 대상 멤버 ID (UUID)
            query_doc: 검색 쿼리로 사용할 QA Document
            top_k: 반환할 최대 결과 수

        Returns:
            Domain Entity 리스트 (Infrastructure 세부사항 숨김)
        """
        pass

    @abstractmethod
    async def search_by_family(
        self,
        family_id: int,
        query_doc: QADocument,
        top_k: int = 5,
    ) -> list[QADocument]:
        """
        가족 QA 검색 (family_id 필터)

        Args:
            family_id: 검색 대상 가족 ID
            query_doc: 검색 쿼리로 사용할 QA Document
            top_k: 반환할 최대 결과 수

        Returns:
            Domain Entity 리스트 (member_id 포함)
        """
        pass
