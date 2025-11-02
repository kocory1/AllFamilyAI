from abc import ABC, abstractmethod

from app.member_profile.models import MemberProfileComputeRequest, MemberProfileSummary


class ProfileUpdater(ABC):
    """프로필 갱신 전략 인터페이스(Strategy).
    다양한 규칙 실험을 위해 구현체를 교체할 수 있습니다.
    """

    @abstractmethod
    def compute(self, request: MemberProfileComputeRequest) -> MemberProfileSummary:
        """분석/현재 프로필/가중치를 입력으로 요약 결과를 계산."""
        ...


