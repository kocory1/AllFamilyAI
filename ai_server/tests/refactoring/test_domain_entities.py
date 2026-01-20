"""
TDD Phase 1: Domain Entities 테스트

RED → GREEN → REFACTOR 사이클로 Domain Layer 구축
"""

from datetime import datetime

import pytest


class TestQADocumentEntity:
    """QADocument Entity 테스트 (순수 Python 도메인 객체)"""

    def test_create_qa_document_with_valid_data(self):
        """[RED] QA Document 생성 - 유효한 데이터"""
        # Given
        from app.domain.entities.qa_document import QADocument

        # When
        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="오늘 뭐 했어?",
            answer="친구들과 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # Then
        assert doc.family_id == 1
        assert doc.member_id == 10
        assert doc.role_label == "첫째 딸"
        assert doc.question == "오늘 뭐 했어?"
        assert doc.answer == "친구들과 놀았어요"
        assert doc.answered_at == datetime(2026, 1, 20, 14, 30, 0)

    def test_get_date_parts(self):
        """[RED] 날짜 정보 추출 메서드"""
        # Given
        from app.domain.entities.qa_document import QADocument

        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When
        year, month, day = doc.get_date_parts()

        # Then
        assert year == 2026
        assert month == 1
        assert day == 20

    def test_is_recent_within_30_days(self):
        """[RED] 최근 답변 여부 확인 - 30일 이내"""
        # Given
        from datetime import timedelta

        from app.domain.entities.qa_document import QADocument

        recent_date = datetime.now() - timedelta(days=15)

        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=recent_date,
        )

        # When/Then
        assert doc.is_recent(days=30) is True

    def test_is_recent_beyond_30_days(self):
        """[RED] 최근 답변 여부 확인 - 30일 초과"""
        # Given
        from datetime import timedelta

        from app.domain.entities.qa_document import QADocument

        old_date = datetime.now() - timedelta(days=45)

        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=old_date,
        )

        # When/Then
        assert doc.is_recent(days=30) is False

    def test_qa_document_immutability(self):
        """[RED] QADocument는 dataclass(frozen=True)로 불변이어야 함"""
        # Given
        from app.domain.entities.qa_document import QADocument

        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=datetime.now(),
        )

        # When/Then: 속성 변경 시도 시 에러 발생
        with pytest.raises(AttributeError):
            doc.question = "변경 시도"


class TestQuestionLevelValueObject:
    """QuestionLevel Value Object 테스트"""

    def test_create_question_level_valid(self):
        """[RED] 유효한 레벨로 QuestionLevel 생성"""
        # Given/When
        from app.domain.value_objects.question_level import QuestionLevel

        level = QuestionLevel(value=2)

        # Then
        assert level.value == 2

    def test_create_question_level_invalid_range(self):
        """[RED] 범위 밖 레벨 생성 시 에러"""
        # Given/When/Then
        from app.domain.value_objects.question_level import QuestionLevel

        with pytest.raises(ValueError, match="질문 난이도는 1-4 사이여야 합니다"):
            QuestionLevel(value=0)

        with pytest.raises(ValueError, match="질문 난이도는 1-4 사이여야 합니다"):
            QuestionLevel(value=5)

    def test_from_int_with_valid_value(self):
        """[RED] from_int 팩토리 메서드 - 정상 값"""
        # Given/When
        from app.domain.value_objects.question_level import QuestionLevel

        level = QuestionLevel.from_int(3)

        # Then
        assert level.value == 3

    def test_from_int_with_string(self):
        """[RED] from_int 팩토리 메서드 - 문자열 파싱"""
        # Given/When
        from app.domain.value_objects.question_level import QuestionLevel

        level = QuestionLevel.from_int("2")

        # Then
        assert level.value == 2

    def test_from_int_with_invalid_value_returns_default(self):
        """[RED] from_int 팩토리 메서드 - 실패 시 기본값"""
        # Given/When
        from app.domain.value_objects.question_level import QuestionLevel

        level = QuestionLevel.from_int("invalid")

        # Then
        assert level.value == 2  # 기본값

    def test_question_level_description(self):
        """[RED] 레벨 설명 속성"""
        # Given/When
        from app.domain.value_objects.question_level import QuestionLevel

        level1 = QuestionLevel(value=1)
        level2 = QuestionLevel(value=2)
        level3 = QuestionLevel(value=3)
        level4 = QuestionLevel(value=4)

        # Then
        assert level1.description == "쉬움"
        assert level2.description == "보통"
        assert level3.description == "어려움"
        assert level4.description == "매우 어려움"

    def test_question_level_immutability(self):
        """[RED] QuestionLevel은 불변(frozen=True)이어야 함"""
        # Given
        from app.domain.value_objects.question_level import QuestionLevel

        level = QuestionLevel(value=2)

        # When/Then
        with pytest.raises(AttributeError):
            level.value = 3
