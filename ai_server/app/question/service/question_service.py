from app.question.base import QuestionGenerator
from app.question.models import QuestionInstanceCreateRequest, QuestionInstanceResponse


class QuestionService:
    """
    질문 생성 오케스트레이션 서비스.
    구체 구현체(QuestionGenerator)를 주입 받아 실행합니다.
    """

    def __init__(self, generator: QuestionGenerator) -> None:
        self.generator = generator

    async def generate_from_template(self, request: QuestionInstanceCreateRequest) -> QuestionInstanceResponse:
        return await self.generator.generate_from_template(request)


