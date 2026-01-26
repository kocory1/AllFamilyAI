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
        mock.search_similar_questions.return_value = 0.3  # 유사도 낮음 (중복 아님)
        mock.search_by_member.return_value = [
            QADocument(
                family_id="family-1",
                member_id="member-10",
                role_label="첫째 딸",
                question="오늘 학교 어땠어?",
                answer="재미있었어요!",
                answered_at=datetime(2026, 1, 15, 10, 0, 0),
            ),
            QADocument(
                family_id="family-1",
                member_id="member-10",
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

        플로우 (옵션 B):
        1. Input DTO 받음
        2. Domain Entity 생성
        3. RAG 검색 (Port 호출)
        4. 질문 생성 (Port 호출)
        5. 벡터 스토어에 저장 (Port 호출)
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
            family_id="family-1",
            member_id="member-10",
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
        assert output.metadata["member_id"] == "member-10"

        # Then: Mock 호출 검증 (순서: RAG → 생성 → 저장)
        mock_vector_store.search_by_member.assert_called_once()
        mock_question_generator.generate_question.assert_called_once()
        mock_vector_store.store.assert_called_once()

        # Then: 검색 파라미터 검증
        search_call = mock_vector_store.search_by_member.call_args
        assert search_call.kwargs["member_id"] == "member-10"
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
            family_id="family-1",
            member_id="member-10",
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
    async def test_generate_personal_question_vector_store_failure_raises_error(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 벡터 스토어 저장 실패 시 예외 발생 (옵션 B)"""
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
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            base_question="테스트",
            base_answer="테스트",
            answered_at=datetime.now(),
        )

        # When/Then: 저장 실패 시 예외 발생
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(input_dto)

        assert "저장 실패" in str(exc_info.value)

        # 질문 생성은 호출됨 (저장 전에 실행되므로)
        mock_question_generator.generate_question.assert_called_once()


class TestGenerateFamilyQuestionUseCase:
    """가족 질문 생성 Use Case 테스트"""

    @pytest.fixture
    def mock_vector_store(self):
        """VectorStorePort Mock"""
        from app.domain.entities.qa_document import QADocument

        mock = AsyncMock()
        mock.store.return_value = True
        mock.search_similar_questions.return_value = 0.3  # 유사도 낮음 (중복 아님)
        mock.search_by_family.return_value = [
            QADocument(
                family_id="family-1",
                member_id="member-10",
                role_label="첫째 딸",
                question="오늘 저녁 뭐 먹을까?",
                answer="치킨 먹고 싶어요",
                answered_at=datetime(2026, 1, 15, 18, 0, 0),
            ),
            QADocument(
                family_id="family-1",
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
        """[RED] 가족 질문 생성 Use Case - 성공 케이스 (옵션 B)"""
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
            family_id="family-1",
            member_id="member-10",
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

        # Then: Mock 호출 검증 (순서: RAG → 생성 → 저장)
        mock_vector_store.search_by_family.assert_called_once()
        mock_question_generator.generate_question.assert_called_once()
        mock_vector_store.store.assert_called_once()

        # Then: 검색 파라미터 검증 (top_k=10)
        search_call = mock_vector_store.search_by_family.call_args
        assert search_call.kwargs["family_id"] == "family-1"
        assert search_call.kwargs["top_k"] == 10


class TestDuplicateQuestionCheck:
    """중복 질문 체크 테스트"""

    @pytest.fixture
    def mock_vector_store(self):
        """VectorStorePort Mock"""
        from app.domain.entities.qa_document import QADocument

        mock = AsyncMock()
        mock.store.return_value = True
        mock.search_by_member.return_value = [
            QADocument(
                family_id="family-1",
                member_id="member-10",
                role_label="첫째 딸",
                question="오늘 학교 어땠어?",
                answer="재미있었어요!",
                answered_at=datetime(2026, 1, 15, 10, 0, 0),
            ),
        ]
        return mock

    @pytest.fixture
    def mock_question_generator(self):
        """QuestionGeneratorPort Mock"""
        from app.domain.value_objects.question_level import QuestionLevel

        mock = AsyncMock()
        mock.generate_question.return_value = ("새로운 질문입니다", QuestionLevel(2))
        return mock

    @pytest.mark.asyncio
    async def test_regenerate_when_similarity_over_threshold(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 유사도 0.9 이상이면 재생성"""
        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )
        from app.domain.value_objects.question_level import QuestionLevel

        # Given: 첫 번째 질문은 유사도 높음, 두 번째는 OK
        mock_question_generator.generate_question.side_effect = [
            ("오늘 학교 어땠어?", QuestionLevel(2)),  # 중복 (기존 질문과 동일)
            ("새로운 친구 사귀었어?", QuestionLevel(2)),  # 고유
        ]
        mock_vector_store.search_similar_questions.side_effect = [
            0.95,  # 첫 번째: 유사도 높음 → 재생성
            0.30,  # 두 번째: 유사도 낮음 → OK
        ]

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            base_question="오늘 뭐 했어?",
            base_answer="친구랑 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 재생성 후 고유 질문 반환
        assert output.question == "새로운 친구 사귀었어?"
        assert mock_question_generator.generate_question.call_count == 2
        assert output.metadata["regeneration_count"] == 1

    @pytest.mark.asyncio
    async def test_max_regeneration_limit(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 최대 3회 재생성 후 마지막 질문 반환"""
        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )
        from app.domain.value_objects.question_level import QuestionLevel

        # Given: 모든 질문이 유사함
        mock_question_generator.generate_question.return_value = (
            "계속 유사한 질문", QuestionLevel(2)
        )
        mock_vector_store.search_similar_questions.return_value = 0.95  # 항상 유사

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            base_question="오늘 뭐 했어?",
            base_answer="친구랑 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 3번 시도 후 마지막 질문 반환
        assert mock_question_generator.generate_question.call_count == 3
        assert output.question == "계속 유사한 질문"
        assert output.metadata["regeneration_count"] == 2
        assert output.metadata["similarity_warning"] is True

    @pytest.mark.asyncio
    async def test_no_regeneration_when_unique(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 처음부터 고유하면 재생성 없음"""
        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionInput,
            GeneratePersonalQuestionUseCase,
        )

        # Given: 유사도 낮음
        mock_vector_store.search_similar_questions.return_value = 0.30

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            base_question="오늘 뭐 했어?",
            base_answer="친구랑 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 1번만 호출
        assert mock_question_generator.generate_question.call_count == 1
        assert output.metadata["regeneration_count"] == 0


class TestFamilyRecentQuestionUseCase:
    """가족 최근 질문 기반 Use Case 테스트 (신규 API)"""

    @pytest.fixture
    def mock_vector_store(self):
        """VectorStorePort Mock"""
        from app.domain.entities.qa_document import QADocument

        mock = AsyncMock()
        mock.search_similar_questions.return_value = 0.3  # 유사도 낮음

        # 가족 전체 최근 질문 반환
        mock.get_recent_questions_by_family.return_value = [
            QADocument(
                family_id="family-1",
                member_id="member-1",
                role_label="아빠",
                question="오늘 회사 어땠어?",
                answer="바빴어",
                answered_at=datetime(2026, 1, 19, 18, 0, 0),
            ),
            QADocument(
                family_id="family-1",
                member_id="member-1",
                role_label="아빠",
                question="점심 뭐 먹었어?",
                answer="김치찌개",
                answered_at=datetime(2026, 1, 18, 12, 0, 0),
            ),
            QADocument(
                family_id="family-1",
                member_id="member-2",
                role_label="엄마",
                question="오늘 뭐 했어?",
                answer="집 청소했어",
                answered_at=datetime(2026, 1, 19, 15, 0, 0),
            ),
        ]
        return mock

    @pytest.fixture
    def mock_question_generator(self):
        """QuestionGeneratorPort Mock"""
        from app.domain.value_objects.question_level import QuestionLevel

        mock = AsyncMock()
        mock.generate_question_for_target.return_value = (
            "아빠, 요즘 회사에서 어떤 프로젝트 하고 계세요?",
            QuestionLevel(3),
        )
        return mock

    @pytest.mark.asyncio
    async def test_family_recent_question_success(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 가족 최근 질문 기반 생성 - 성공 케이스"""
        # Given
        from app.application.dto.question_dto import (
            FamilyRecentQuestionInput,
        )
        from app.application.use_cases.family_recent_question import (
            FamilyRecentQuestionUseCase,
        )

        use_case = FamilyRecentQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = FamilyRecentQuestionInput(
            family_id="family-1",
            target_member_id="member-1",
            target_role_label="아빠",
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 응답 검증
        assert output.question == "아빠, 요즘 회사에서 어떤 프로젝트 하고 계세요?"
        assert output.level.value == 3
        assert output.metadata["context_count"] == 3
        assert output.metadata["target_member_id"] == "member-1"

        # Then: 가족 전체 최근 질문 조회 확인
        mock_vector_store.get_recent_questions_by_family.assert_called_once_with(
            family_id="family-1",
            limit_per_member=3,
        )

        # Then: 질문 생성 확인
        mock_question_generator.generate_question_for_target.assert_called_once()

        # Then: 저장 안 함 확인
        mock_vector_store.store.assert_not_called()

    @pytest.mark.asyncio
    async def test_family_recent_question_regenerate_on_high_similarity(
        self, mock_vector_store, mock_question_generator
    ):
        """[RED] 유사도 높으면 재생성"""
        from app.application.dto.question_dto import FamilyRecentQuestionInput
        from app.application.use_cases.family_recent_question import (
            FamilyRecentQuestionUseCase,
        )
        from app.domain.value_objects.question_level import QuestionLevel

        # Given: 첫 번째 질문은 유사도 높음
        mock_question_generator.generate_question_for_target.side_effect = [
            ("중복 질문입니다", QuestionLevel(2)),
            ("새로운 질문입니다", QuestionLevel(3)),
        ]
        mock_vector_store.search_similar_questions.side_effect = [0.95, 0.30]

        use_case = FamilyRecentQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = FamilyRecentQuestionInput(
            family_id="family-1",
            target_member_id="member-1",
            target_role_label="아빠",
        )

        # When
        output = await use_case.execute(input_dto)

        # Then
        assert output.question == "새로운 질문입니다"
        assert mock_question_generator.generate_question_for_target.call_count == 2
        assert output.metadata["regeneration_count"] == 1

    @pytest.mark.asyncio
    async def test_family_recent_question_empty_context(
        self, mock_question_generator
    ):
        """[RED] 최근 질문이 없어도 생성 가능"""
        from app.application.dto.question_dto import FamilyRecentQuestionInput
        from app.application.use_cases.family_recent_question import (
            FamilyRecentQuestionUseCase,
        )

        # Given: 가족의 최근 질문이 없음 (새로운 mock 생성)
        empty_vector_store = AsyncMock()
        empty_vector_store.get_recent_questions_by_family.return_value = []
        empty_vector_store.search_similar_questions.return_value = 0.3

        use_case = FamilyRecentQuestionUseCase(
            vector_store=empty_vector_store,
            question_generator=mock_question_generator,
        )

        input_dto = FamilyRecentQuestionInput(
            family_id="family-1",
            target_member_id="member-1",
            target_role_label="아빠",
        )

        # When
        output = await use_case.execute(input_dto)

        # Then: 컨텍스트 없이도 질문 생성
        assert output.question is not None
        assert output.metadata["context_count"] == 0


class TestUseCaseDTO:
    """Use Case DTO 테스트"""

    def test_generate_personal_question_input_dto(self):
        """[RED] Input DTO 생성 및 검증"""
        # Given/When
        from app.application.dto.question_dto import GeneratePersonalQuestionInput

        input_dto = GeneratePersonalQuestionInput(
            family_id="family-1",
            member_id="member-10",
            role_label="첫째 딸",
            base_question="테스트",
            base_answer="테스트",
            answered_at=datetime.now(),
        )

        # Then
        assert input_dto.family_id == "family-1"
        assert input_dto.member_id == "member-10"
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
