"""
주간/월간 요약 Use Case DTO

- period: weekly(최근 7일), monthly(최근 30일)
- 응답: context만 (헤드라인 1개)
"""

from dataclasses import dataclass


@dataclass
class SummaryInput:
    """요약 Use Case 입력 DTO"""

    family_id: str  # UUID
    period: str  # "weekly" | "monthly"


@dataclass
class SummaryOutput:
    """요약 Use Case 출력 DTO (context만)"""

    context: str
