from abc import ABC, abstractmethod

from app.question.models import (
    QuestionInstanceCreateRequest,
    QuestionInstanceResponse,
)


class QuestionGenerator(ABC):
    @abstractmethod
    async def generate_from_template(
        self, request: QuestionInstanceCreateRequest
    ) -> QuestionInstanceResponse:
        ...


