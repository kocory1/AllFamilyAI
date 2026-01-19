from __future__ import annotations

import random

from app.question.models import (
    MemberAssignRequest,
    MemberAssignResponse,
)


class AssignmentService:
    """멤버 할당 서비스(경량, DB 미사용).

    - 최근 30회 기반 가중치: w_i = (1/N) * (1 - c_i / S)
    - 제외/쿨다운 적용 후 비복원 가중 샘플링
    """

    async def assign_members(self, request: MemberAssignRequest) -> MemberAssignResponse:
        candidates = []

        opts = request.options or None
        epsilon = float(getattr(opts, "epsilon", 0.0) or 0.0)

        # 후보 필터링(제외/쿨다운)
        for m in request.members:
            candidates.append(m)

        n = len(candidates)
        if n == 0:
            return MemberAssignResponse(member_ids=[], version="assign-v1")

        base = 1.0 / n
        S = sum(m.assigned_count_30 for m in candidates)

        # 가중치 계산
        if S <= 0:
            weights = [base for _ in candidates]
        else:
            weights = [max(epsilon, base * (1.0 - (m.assigned_count_30 / S))) for m in candidates]

        # 정규화
        total_w = sum(weights)
        if total_w <= 0:
            weights = [1.0 / n for _ in candidates]
            total_w = 1.0
        probs = [w / total_w for w in weights]

        # 샘플링
        rng = random.Random()

        pick = min(request.pick_count, n)
        selected_ids: list[str | int] = []

        cand_list = candidates[:]  # shallow copy
        prob_list = probs[:]

        for _ in range(pick):
            u = rng.random()
            acc = 0.0
            chosen_j = None
            for j, p in enumerate(prob_list):
                acc += p
                if u <= acc:
                    chosen_j = j
                    break
            if chosen_j is None:
                chosen_j = len(prob_list) - 1

            selected_ids.append(cand_list[chosen_j].member_id)

            # 비복원 처리
            del cand_list[chosen_j]
            del prob_list[chosen_j]
            if not prob_list:
                break
            s = sum(prob_list)

            # [BugFix] 남은 확률의 합이 0이면 균등 분배 (ZeroDivisionError 방지)
            if s <= 0:
                remain_n = len(prob_list)
                prob_list = [1.0 / remain_n for _ in prob_list]
            else:
                prob_list = [p / s for p in prob_list]

        return MemberAssignResponse(member_ids=selected_ids, version="assign-v1")
