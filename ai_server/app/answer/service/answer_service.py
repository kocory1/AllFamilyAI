from typing import Optional
from app.answer.base import AnswerAnalyzer
from app.answer.models import AnswerAnalysisRequest, AnswerAnalysisResponse


class AnswerService:
    """
    오케스트레이션 서비스.
    구체 구현체(예: OpenAIAnswerAnalyzer)를 주입하여 실행만 담당.
    """

    def __init__(self, analyzer: AnswerAnalyzer) -> None:
        self.analyzer = analyzer

    async def analyze(self, request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
        return await self.analyzer.analyze(request)


