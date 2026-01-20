"""
Member Assignment DTOs

Use Case 입출력 전용 DTO
"""

from dataclasses import dataclass


@dataclass
class AssignMembersInput:
    """멤버 할당 Use Case 입력 DTO"""

    family_id: int
    member_ids: list[str]  # UUID
    pick_count: int


@dataclass
class AssignMembersOutput:
    """멤버 할당 Use Case 출력 DTO"""

    selected_member_ids: list[str]  # UUID
    metadata: dict
