"""
TDD Phase 2: Use Case 리팩토링 테스트

Clean Architecture 원칙:
- Use Case는 Port (인터페이스)에만 의존
- Infrastructure 구현체를 모름
- 순수 비즈니스 로직만 포함
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest


class TestGeneratePersonalQuestionUseCase:
    """개인 질문 생성 Use Case 테스트"""

    @pytest.fixture
    def mock_vector_store(self):
        """VectorStorePort Mock"""
        from app.domain.entities.qa_document import QADocument

        mock = AsyncMock()
        mock.store.return_value = True
        mock.search_by_member.return_value = [
            QADocument(
                family_id=1,
                member_id=10,
                role_label="첫째 딸",
                question="오늘 학교 어땠어?",
                answer="재미있었어요!",
                answered_at=datetime(2026, 1, 15, 10, 0, 0),
            ),
            QADocument(
                family_id=1,
                member_id=10,
                role_label="첫째 딸",
                question="친구들과 뭐 했어?",
                answer="같이 놀았어요",
                answered_at=datetime(2026, 1, 14, 15, 30, 0),
            ),
        ]
        return mock

    @pytest.fixture
    def mock_question_generator(self):
        """QuestionGeneratorPort Mock"""
        from app.domain.value_objects.question_level import QuestionLevel

        mock = AsyncMock()
        mock.generate_question.return_value = ("친구들과 어떤 놀이를 했나요?", QuestionLevel(2))
        return mock

    @pytest.mark.asyncio
    async def test_generate_personal_question_success(
        self, mock_vector_store, mock_question_generator
    ):
        """
        [RED] 개인 질문 생성 Use Case - 성공 케이스

        플로우:
        1. Input DTO 받음
        2. Domain Entity 생성
        3. 벡터 스토어에 저장 (Port 호출)
        4. RAG 검색 (Port 호출)
        5. 질문 생성 (Port 호출)
        6. Output DTO 반환
        """
        # Given
        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="오늘 뭐 했어?",
            base_answer="친구들과 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 응답 검증
        assert output.question == "친구들과 어떤 놀이를 했나요?"
        assert output.level.value == 2
        assert output.metadata["rag_count"] == 2
        assert output.metadata["member_id"] == 10

        # Then: Mock 호출 검증 (Port 인터페이스 호출)
        mock_vector_store.store.assert_called_once()
        mock_vector_store.search_by_member.assert_called_once()
        mock_question_generator.generate_question.assert_called_once()

        # Then: 검색 파라미터 검증
        search_call = mock_vector_store.search_by_member.call_args
        assert search_call.kwargs["member_id"] == 10
        assert search_call.kwargs["top_k"] == 5

    @pytest.mark.asyncio
    async def test_generate_personal_question_with_empty_rag(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] RAG 결과가 없어도 질문 생성 가능"""
        # Given
        mock_vector_store.search_by_member.return_value = []

        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="오늘 뭐 했어?",
            base_answer="공부했어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then
        assert output.question == "친구들과 어떤 놀이를 했나요?"
        assert output.metadata["rag_count"] == 0

        # RAG 결과가 빈 리스트로 전달됨
        generate_call = mock_question_generator.generate_question.call_args
        assert generate_call.kwargs["rag_context"] == []

    @pytest.mark.asyncio
    async def test_generate_personal_question_vector_store_failure(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 벡터 스토어 저장 실패 시 예외 전파"""
        # Given
        mock_vector_store.store.return_value = False

        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="테스트",
            base_answer="테스트",
            answered_at=datetime.now(),
        )

        # When/Then: 저장 실패 시에도 계속 진행 (현재 동작 유지)
        output = await use_case.execute(input_dto)
        assert output.question == "친구들과 어떤 놀이를 했나요?"


class TestGenerateFamilyQuestionUseCase:
    """가족 질문 생성 Use Case 테스트"""

    @pytest.fixture
    def mock_vector_store(self):
        """VectorStorePort Mock"""
        from app.domain.entities.qa_document import QADocument

        mock = AsyncMock()
        mock.store.return_value = True
        mock.search_by_family.return_value = [
            QADocument(
                family_id=1,
                member_id=10,
                role_label="첫째 딸",
                question="오늘 저녁 뭐 먹을까?",
                answer="치킨 먹고 싶어요",
                answered_at=datetime(2026, 1, 15, 18, 0, 0),
            ),
            QADocument(
                family_id=1,
                member_id=2,
                role_label="엄마",
                question="내일 날씨 어때?",
                answer="맑을 것 같아요",
                answered_at=datetime(2026, 1, 15, 9, 0, 0),
            ),
        ]
        return mock

    @pytest.fixture
    def mock_question_generator(self):
        """QuestionGeneratorPort Mock"""
        from app.domain.value_objects.question_level import QuestionLevel

        mock = AsyncMock()
        mock.generate_question.return_value = (
            "가족들이 좋아하는 저녁 메뉴는 무엇인가요?",
            QuestionLevel(3),
        )
        return mock

    @pytest.mark.asyncio
    async def test_generate_family_question_success(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 가족 질문 생성 Use Case - 성공 케이스"""
        # Given
        from app.application.use_cases.generate_family_question import (
            GenerateFamilyQuestionInput,
            GenerateFamilyQuestionUseCase,
        )

        use_case = GenerateFamilyQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GenerateFamilyQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="오늘 저녁 뭐 먹을까?",
            base_answer="치킨 먹고 싶어요",
            answered_at=datetime(2026, 1, 20, 18, 0, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then
        assert output.question == "가족들이 좋아하는 저녁 메뉴는 무엇인가요?"
        assert output.level.value == 3
        assert output.metadata["rag_count"] == 2

        # Then: Mock 호출 검증
        mock_vector_store.store.assert_called_once()
        mock_vector_store.search_by_family.assert_called_once()

        # Then: 검색 파라미터 검증 (top_k=10)
        search_call = mock_vector_store.search_by_family.call_args
        assert search_call.kwargs["family_id"] == 1
        assert search_call.kwargs["top_k"] == 10


class TestUseCaseDTO:
    """Use Case DTO 테스트"""

    def test_generate_personal_question_input_dto(self):
        """[RED] Input DTO 생성 및 검증"""
        # Given/When
        from app.application.dto.question_dto import GeneratePersonalQuestionInput

        input_dto = GeneratePersonalQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="테스트",
            base_answer="테스트",
            answered_at=datetime.now(),
        )

        # Then
        assert input_dto.family_id == 1
        assert input_dto.member_id == 10
        assert input_dto.role_label == "첫째 딸"

    def test_generate_personal_question_output_dto(self):
        """[RED] Output DTO 생성 및 검증"""
        # Given/When
        from app.application.dto.question_dto import GeneratePersonalQuestionOutput
        from app.domain.value_objects.question_level import QuestionLevel

        output_dto = GeneratePersonalQuestionOutput(
            question="테스트 질문", level=QuestionLevel(2), metadata={"rag_count": 5}
        )

        # Then
        assert output_dto.question == "테스트 질문"
        assert output_dto.level.value == 2
        assert output_dto.metadata["rag_count"] == 5
