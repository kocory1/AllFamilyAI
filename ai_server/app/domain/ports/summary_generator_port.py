"""
Summary Generator Port (인터페이스)

주간/월간 요약(헤드라인 스타일) 생성용 Port.
"""

from abc import ABC, abstractmethod


class SummaryGeneratorPort(ABC):
    """
    요약 생성기 인터페이스 (Port)

    구현체: LangChainSummaryGenerator (Infrastructure)
    """

    @abstractmethod
    async def generate_summary(
        self,
        qa_texts: list[str],
        period_label: str,
        answer_count: int,
    ) -> str:
        """
        QA 목록을 [특보] 스타일 헤드라인 요약으로 생성

        Args:
            qa_texts: 임베딩과 동일 포맷의 QA 텍스트 리스트
            period_label: "주간" 또는 "월간"
            answer_count: 해당 기간 답변 건수 (0건일 때 톤 조절용)

        Returns:
            context 문자열 (헤드라인 1개)
        """
        pass
