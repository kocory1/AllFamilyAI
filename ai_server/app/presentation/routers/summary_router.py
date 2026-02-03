"""
주간/월간 요약 API Router

GET /api/v1/summary?familyId=xxx&period=weekly|monthly
- period: weekly = 최근 7일, monthly = 최근 30일 (API 스펙)
- 응답: context만
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.dto.summary_dto import SummaryInput, SummaryOutput
from app.presentation.dependencies import SummaryUC, get_family_summary_use_case
from app.presentation.schemas.question_schemas import SummaryResponseSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["요약"])


@router.get(
    "",
    response_model=SummaryResponseSchema,
    summary="주간/월간 요약",
    description="가족 ID 기준으로 기간 내 질문·답변을 [특보] 스타일 헤드라인으로 요약. period: weekly=최근 7일, monthly=최근 30일. context만 반환.",
)
async def get_family_summary(
    familyId: str = Query(..., alias="familyId", description="가족 ID (UUID)"),
    period: str = Query(
        ...,
        description="weekly(최근 7일) 또는 monthly(최근 30일)",
        pattern="^(weekly|monthly)$",
    ),
    use_case: SummaryUC = Depends(get_family_summary_use_case),
) -> SummaryResponseSchema:
    try:
        input_dto = SummaryInput(family_id=familyId, period=period)
        output: SummaryOutput = await use_case.execute(input_dto)
        return SummaryResponseSchema(context=output.context)
    except ValueError as e:
        logger.error(f"[API] 요약 생성 실패 (잘못된 입력): {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"잘못된 요청: {str(e)}") from e
    except Exception as e:
        logger.error(f"[API] 요약 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 생성 실패: {str(e)}") from e
