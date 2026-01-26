"""
QA Document Domain Entity

Clean Architecture 원칙:
- 프레임워크 독립 (Pydantic, SQLAlchemy 사용 안 함)
- 순수 Python dataclass
- 비즈니스 로직만 포함
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class QADocument:
    """
    질문-답변 문서 (Domain Entity)

    불변(Immutable) 객체:
    - frozen=True로 생성 후 수정 불가
    - 순수한 비즈니스 개념 표현

    Attributes:
        family_id: 가족 ID (UUID)
        member_id: 멤버 ID (UUID)
        role_label: 역할 레이블 (예: "첫째 딸", "아빠")
        question: 질문 내용
        answer: 답변 내용
        answered_at: 답변 시각 (datetime 객체)
    """

    family_id: str  # UUID
    member_id: str  # UUID
    role_label: str
    question: str
    answer: str
    answered_at: datetime

    def get_date_parts(self) -> tuple[int, int, int]:
        """
        날짜 정보 추출 (년, 월, 일)

        Returns:
            (year, month, day) 튜플
        """
        return self.answered_at.year, self.answered_at.month, self.answered_at.day

    def is_recent(self, days: int = 30) -> bool:
        """
        최근 N일 이내 답변인지 확인

        Args:
            days: 기준 일수 (기본값: 30일)

        Returns:
            True if 최근 N일 이내, False otherwise
        """
        delta = datetime.now() - self.answered_at
        return delta <= timedelta(days=days)
