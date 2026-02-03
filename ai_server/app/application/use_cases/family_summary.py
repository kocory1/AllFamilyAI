"""
가족 주간/월간 요약 Use Case

- GET /api/v1/summary?familyId=xxx&period=weekly|monthly
- period: weekly = 최근 7일, monthly = 최근 30일 (API 스펙)
- 응답: context만 ([특보] 스타일 헤드라인 1개)
"""

import logging
from datetime import datetime, timedelta

from app.application.dto.summary_dto import SummaryInput, SummaryOutput
from app.domain.entities.qa_document import QADocument
from app.domain.ports.summary_generator_port import SummaryGeneratorPort
from app.domain.ports.vector_store_port import VectorStorePort

logger = logging.getLogger(__name__)

PERIOD_DAYS = {"weekly": 7, "monthly": 30}
PERIOD_LABEL = {"weekly": "주간", "monthly": "월간"}


class FamilySummaryUseCase:
    """
    가족 주간/월간 요약 Use Case

    - vector_store.get_qa_by_family_in_range 로 기간 내 QA 조회
    - 임베딩과 동일 포맷으로 문자열화 후 LLM 요약
    - context만 반환 (메타 없음)
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        summary_generator: SummaryGeneratorPort,
    ):
        self.vector_store = vector_store
        self.summary_generator = summary_generator

    async def execute(self, input_dto: SummaryInput) -> SummaryOutput:
        days = PERIOD_DAYS.get(input_dto.period, 7)
        period_label = PERIOD_LABEL.get(input_dto.period, "주간")

        end = datetime.now()
        start = end - timedelta(days=days)

        docs = await self.vector_store.get_qa_by_family_in_range(
            family_id=input_dto.family_id,
            start=start,
            end=end,
        )

        qa_texts = [_to_embedding_style(d) for d in docs]
        context = await self.summary_generator.generate_summary(
            qa_texts=qa_texts,
            period_label=period_label,
            answer_count=len(docs),
        )

        return SummaryOutput(context=context)


def _to_embedding_style(doc: QADocument) -> str:
    """임베딩과 동일 포맷 (ChromaVectorStore._to_embedding_text와 동일)"""
    y, m, d = doc.get_date_parts()
    return (
        f"{y}년 {m}월 {d}일에 {doc.role_label}이(가) 받은 질문: {doc.question}\n"
        f"답변: {doc.answer}"
    )
