from abc import ABC, abstractmethod

from app.answer.models import (
    AnswerAnalysisRequest,
    AnswerAnalysisResponse,
)


class AnswerAnalyzer(ABC):
    name: str = "base"

    @abstractmethod
    async def analyze(self, request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
        ...


