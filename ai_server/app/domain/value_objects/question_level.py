"""
Question Level Value Object

Clean Architecture 원칙:
- 불변(Immutable) 값 객체
- 검증 로직 캡슐화
- 비즈니스 의미 명확화
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionLevel:
    """
    질문 난이도 Value Object (1-4)

    불변 객체:
    - frozen=True로 생성 후 수정 불가
    - 유효성 검증 내장

    Level 정의:
    - 1: 쉬움 (간단한 사실 확인)
    - 2: 보통 (일반적인 대화)
    - 3: 어려움 (깊이 있는 질문)
    - 4: 매우 어려움 (철학적, 감정적 질문)
    """

    value: int

    def __post_init__(self):
        """생성 시 유효성 검증"""
        if not 1 <= self.value <= 4:
            raise ValueError(f"질문 난이도는 1-4 사이여야 합니다: {self.value}")

    @classmethod
    def from_int(cls, level: int | str) -> "QuestionLevel":
        """
        안전한 생성 팩토리 메서드

        파싱 실패 시 기본값(2) 반환

        Args:
            level: 레벨 값 (int 또는 str)

        Returns:
            QuestionLevel 인스턴스
        """
        try:
            level_int = int(level)
            if 1 <= level_int <= 4:
                return cls(level_int)
            else:
                # 범위 초과 시 기본값
                return cls(2)
        except (ValueError, TypeError):
            # 파싱 실패 시 기본값
            return cls(2)

    @property
    def description(self) -> str:
        """
        난이도 설명

        Returns:
            한글 설명 문자열
        """
        descriptions = {
            1: "쉬움",
            2: "보통",
            3: "어려움",
            4: "매우 어려움",
        }
        return descriptions[self.value]
