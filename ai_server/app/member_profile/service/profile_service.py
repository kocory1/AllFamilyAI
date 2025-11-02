from app.member_profile.base import ProfileUpdater
from app.member_profile.models import MemberProfileComputeRequest, MemberProfileSummary


class ProfileService:
    """오케스트레이션 서비스: 규칙 구현체 주입/호출만 담당."""
    def __init__(self, updater: ProfileUpdater) -> None:
        self.updater = updater

    def compute(self, request: MemberProfileComputeRequest) -> MemberProfileSummary:
        return self.updater.compute(request)


