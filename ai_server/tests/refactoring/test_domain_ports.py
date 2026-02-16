"""
TDD Phase 1-2: Domain Ports (인터페이스) 테스트

의존성 역전을 위한 추상 인터페이스 정의
"""

from abc import ABC
from datetime import datetime

import pytest


class TestVectorStorePort:
    """VectorStorePort 인터페이스 테스트"""

    def test_vector_store_port_is_abstract(self):
        """[RED] VectorStorePort는 추상 클래스여야 함"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # ABC를 상속해야 함
        assert issubclass(VectorStorePort, ABC)

    def test_vector_store_port_has_store_method(self):
        """[RED] store 메서드 시그니처 확인"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # store 메서드가 존재해야 함
        assert hasattr(VectorStorePort, "store")

    def test_vector_store_port_has_search_by_member_method(self):
        """[RED] search_by_member 메서드 시그니처 확인"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # search_by_member 메서드가 존재해야 함
        assert hasattr(VectorStorePort, "search_by_member")

    def test_vector_store_port_has_search_by_family_method(self):
        """[RED] search_by_family 메서드 시그니처 확인"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # search_by_family 메서드가 존재해야 함
        assert hasattr(VectorStorePort, "search_by_family")

    def test_vector_store_port_has_get_recent_questions_by_member_method(self):
        """[RED] get_recent_questions_by_member 메서드 시그니처 확인"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # get_recent_questions_by_member 메서드가 존재해야 함
        assert hasattr(VectorStorePort, "get_recent_questions_by_member")

    def test_vector_store_port_has_delete_by_member_method(self):
        """[RED] delete_by_member 메서드 시그니처 확인"""
        from app.domain.ports.vector_store_port import VectorStorePort

        assert hasattr(VectorStorePort, "delete_by_member")

    def test_vector_store_port_cannot_be_instantiated(self):
        """[RED] 추상 클래스는 직접 인스턴스화 불가"""
        from app.domain.ports.vector_store_port import VectorStorePort

        # 추상 클래스는 인스턴스화 시 에러
        with pytest.raises(TypeError):
            VectorStorePort()


class TestQuestionGeneratorPort:
    """QuestionGeneratorPort 인터페이스 테스트"""

    def test_question_generator_port_is_abstract(self):
        """[RED] QuestionGeneratorPort는 추상 클래스여야 함"""
        from app.domain.ports.question_generator_port import QuestionGeneratorPort

        assert issubclass(QuestionGeneratorPort, ABC)

    def test_question_generator_port_has_generate_question_method(self):
        """[RED] generate_question 메서드 시그니처 확인"""
        from app.domain.ports.question_generator_port import QuestionGeneratorPort

        # generate_question 메서드가 존재해야 함
        assert hasattr(QuestionGeneratorPort, "generate_question")

    def test_question_generator_port_cannot_be_instantiated(self):
        """[RED] 추상 클래스는 직접 인스턴스화 불가"""
        from app.domain.ports.question_generator_port import QuestionGeneratorPort

        with pytest.raises(TypeError):
            QuestionGeneratorPort()


class TestPortContracts:
    """Port 인터페이스 계약 테스트 (Mock 구현체로 검증)"""

    @pytest.mark.asyncio
    async def test_vector_store_port_contract(self):
        """[RED] VectorStorePort 인터페이스 계약 검증"""
        from app.domain.entities.qa_document import QADocument
        from app.domain.ports.vector_store_port import VectorStorePort

        # Mock 구현체
        class MockVectorStore(VectorStorePort):
            async def store(self, doc: QADocument) -> bool:
                return True

            async def search_by_member(
                self, member_id: str, query_doc: QADocument, top_k: int = 5
            ) -> list[QADocument]:
                return []

            async def search_by_family(
                self, family_id: str, query_doc: QADocument, top_k: int = 5
            ) -> list[QADocument]:
                return []

            async def search_similar_questions(self, question_text: str, member_id: str) -> float:
                return 0.0

            async def get_recent_questions_by_member(
                self, member_id: str, limit: int = 2
            ) -> list[QADocument]:
                return []

            async def get_recent_questions_by_family(
                self, family_id: str, limit_per_member: int = 3
            ) -> list[QADocument]:
                return []

            async def get_qa_by_family_in_range(
                self, family_id: str, start, end
            ) -> list[QADocument]:
                return []

            async def delete_by_member(self, member_id: str) -> int:
                return 0

        # 인스턴스 생성 가능 (모든 메서드 구현)
        mock_store = MockVectorStore()

        # store 호출
        doc = QADocument(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=datetime.now(),
        )
        result = await mock_store.store(doc)
        assert result is True

        # search_by_member 호출
        results = await mock_store.search_by_member("member-10", doc, top_k=5)
        assert results == []

        # get_recent_questions_by_member 호출
        recent = await mock_store.get_recent_questions_by_member("member-uuid", limit=2)
        assert recent == []

        # get_recent_questions_by_family 호출
        family_recent = await mock_store.get_recent_questions_by_family(
            "family-1", limit_per_member=3
        )
        assert family_recent == []

    @pytest.mark.asyncio
    async def test_question_generator_port_contract(self):
        """[RED] QuestionGeneratorPort 인터페이스 계약 검증"""
        from app.domain.entities.qa_document import QADocument
        from app.domain.ports.question_generator_port import QuestionGeneratorPort
        from app.domain.value_objects.question_level import QuestionLevel

        # Mock 구현체
        class MockQuestionGenerator(QuestionGeneratorPort):
            async def generate_question(
                self, base_qa: QADocument, rag_context: list[QADocument]
            ) -> tuple[str, QuestionLevel]:
                return "테스트 질문", QuestionLevel(2)

            async def generate_question_for_target(
                self,
                target_member_id: str,
                target_role_label: str,
                context: list[QADocument],
            ) -> tuple[str, QuestionLevel]:
                return "타겟 질문", QuestionLevel(3)

        # 인스턴스 생성 가능
        mock_generator = MockQuestionGenerator()

        # generate_question 호출
        base_qa = QADocument(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=datetime.now(),
        )
        question, level = await mock_generator.generate_question(base_qa, [])

        assert question == "테스트 질문"
        assert level.value == 2
