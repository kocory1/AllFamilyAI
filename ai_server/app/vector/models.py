"""
벡터 DB용 Pydantic 모델
"""

from datetime import datetime

from pydantic import BaseModel, Field


class QADocument(BaseModel):
    """
    ChromaDB에 저장할 QA 문서

    DB_SCHEMA2.md의 MEMBER_QUESTION 테이블 구조와 연동:
    - family_id, member_id: 관계 식별
    - role_label: FAMILY_MEMBER.label (예: "첫째 딸", "아빠")
    - question, answer: 질문/답변 텍스트
    - answered_at: MEMBER_QUESTION.answered_at (ISO 문자열)
    """

    family_id: int = Field(..., description="가족 ID")
    member_id: int = Field(..., description="멤버 ID")
    role_label: str = Field(..., description="멤버 역할 레이블 (예: 첫째 딸, 아빠)")
    question: str = Field(..., description="질문 내용")
    answer: str = Field(..., description="답변 내용")
    answered_at: str = Field(..., description="답변 시간 (ISO 8601 문자열)")

    def to_embedding_text(self) -> str:
        """
        임베딩용 텍스트 생성 (연/월/일 포함)

        포맷: "{year}년 {month}월 {day}일에 {role_label}이(가) 받은 질문: {question}\n답변: {answer}"

        예시:
            "2026년 1월 15일에 첫째 딸이(가) 받은 질문: 오늘 기분이 어때요?\n답변: 친구들이랑 놀아서 기분 좋았어요!"

        이유:
            - LLM이 시간 흐름 인지 ("최근 1월에는..., 2월에는...")
            - RAG 검색 품질 향상 ("겨울에 뭐 했어?" → "1월, 2월 답변" 높은 유사도)
            - 프롬프트 단순화 (시간 정렬 로직 불필요)

        Returns:
            str: 임베딩용 텍스트
        """
        # ISO 문자열 파싱
        dt = datetime.fromisoformat(self.answered_at.replace("Z", "+00:00"))

        # 연/월/일 추출 (앞의 0 제거)
        year = dt.year
        month = dt.month  # 1~12
        day = dt.day  # 1~31

        # 포맷팅
        return (
            f"{year}년 {month}월 {day}일에 {self.role_label}이(가) 받은 질문: {self.question}\n"
            f"답변: {self.answer}"
        )

    def to_metadata(self) -> dict:
        """
        ChromaDB 메타데이터 생성 (검색 필터용)

        포함 필드:
            - family_id: 가족 단위 검색
            - member_id: 개인 단위 검색
            - role_label: 역할별 검색
            - answered_at: 시간별 필터링

        제외 필드:
            - question, answer: 임베딩 텍스트에만 사용 (메타데이터 중복 방지)

        Returns:
            dict: ChromaDB 메타데이터
        """
        return {
            "family_id": self.family_id,
            "member_id": self.member_id,
            "role_label": self.role_label,
            "answered_at": self.answered_at,
        }
