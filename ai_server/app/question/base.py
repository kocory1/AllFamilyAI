from abc import ABC, abstractmethod

from app.question.models import QuestionGenerateRequest, QuestionInstanceResponse


class QuestionGenerator(ABC):
    @abstractmethod
    async def generate(
        self, request: QuestionGenerateRequest
    ) -> QuestionInstanceResponse:
        ...


