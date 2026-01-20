"""
멤버 할당 Use Case

Clean Architecture 원칙:
- 순수 비즈니스 로직만 포함
- 프레임워크 독립
"""

import logging
import random

from app.application.dto.assignment_dto import AssignMembersInput, AssignMembersOutput

logger = logging.getLogger(__name__)


class AssignMembersUseCase:
    """
    멤버 할당 Use Case

    비즈니스 규칙:
    - 주어진 멤버 중에서 pick_count명 선택
    - 현재: 랜덤 선택
    - 추후: DB 통계 기반 가중치 선택 (최근 30회 기준)
    """

    async def execute(self, input_dto: AssignMembersInput) -> AssignMembersOutput:
        """
        멤버 할당 실행

        Args:
            input_dto: 입력 DTO

        Returns:
            출력 DTO (선택된 멤버 ID 리스트)
        """
        logger.info(
            f"[Use Case] 멤버 할당 시작: family_id={input_dto.family_id}, "
            f"candidates={len(input_dto.member_ids)}, pick={input_dto.pick_count}"
        )

        # 비즈니스 로직: 랜덤 선택
        # TODO: DB 통계 기반 가중치 선택으로 개선
        selected = self._select_members_randomly(input_dto.member_ids, input_dto.pick_count)

        output = AssignMembersOutput(
            selected_member_ids=selected,
            metadata={
                "family_id": input_dto.family_id,
                "total_candidates": len(input_dto.member_ids),
                "selected_count": len(selected),
                "method": "random",  # 추후 "weighted" 변경
            },
        )

        logger.info(f"[Use Case] 멤버 할당 완료: selected={selected}")
        return output

    def _select_members_randomly(self, member_ids: list[str], pick_count: int) -> list[str]:
        """
        랜덤 선택 (비즈니스 로직)

        Args:
            member_ids: 선택 가능한 멤버 ID 리스트 (UUID)
            pick_count: 선택할 개수

        Returns:
            선택된 멤버 ID 리스트 (UUID)
        """
        # Validation
        if pick_count <= 0:
            raise ValueError(f"pick_count는 1 이상이어야 합니다: {pick_count}")

        if not member_ids:
            raise ValueError("member_ids가 비어있습니다")

        # 요청보다 후보가 적으면 모두 선택
        actual_pick = min(pick_count, len(member_ids))

        # 랜덤 선택
        return random.sample(member_ids, actual_pick)
