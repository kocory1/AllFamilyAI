"""
LangChain 기반 개인 질문 생성기 (Infrastructure)

Clean Architecture:
- QuestionGeneratorPort 인터페이스 구현
- Domain Entity 입출력
- LangChain 구체 구현 세부사항 캡슐화
"""

import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domain.entities.qa_document import QADocument
from app.domain.ports.question_generator_port import QuestionGeneratorPort
from app.domain.value_objects.question_level import QuestionLevel

logger = logging.getLogger(__name__)


class LangchainPersonalGenerator(QuestionGeneratorPort):
    """
    LangChain 기반 개인 질문 생성기 (Port 구현)

    책임:
    - LangChain LCEL Chain 구성
    - LLM 호출
    - 응답 파싱
    - Domain Entity ↔ LangChain 형식 변환
    """

    def __init__(self, prompt_data: dict, model: str, temperature: float):
        """
        Args:
            prompt_data: 프롬프트 데이터 (system, user)
            model: LLM 모델명
            temperature: 온도 파라미터
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_data["system"]),
                ("user", prompt_data["user"]),
            ]
        )

        self.parser = JsonOutputParser()
        self.chain = self.prompt_template | self.llm

        logger.info(f"[LangchainPersonalGenerator] 초기화 완료: model={model}")

    async def generate_question(
        self, base_qa: QADocument, rag_context: list[QADocument]
    ) -> tuple[str, QuestionLevel]:
        """
        질문 생성 (Port 인터페이스 구현)

        Args:
            base_qa: 기준 QA (Domain Entity)
            rag_context: RAG 검색 결과 (Domain Entities)

        Returns:
            (생성된 질문, 난이도) 튜플
        """
        logger.info(f"[LangchainPersonalGenerator] 질문 생성 시작: member_id={base_qa.member_id}")

        # Domain Entity → LangChain 입력 포맷 변환
        rag_text = self._format_rag_context(rag_context)
        base_qa_text = self._format_base_qa(base_qa)

        # LangChain 호출
        response = await self.chain.ainvoke(
            {
                "role_label": base_qa.role_label,
                "rag_context": rag_text,
                "base_qa": base_qa_text,
            }
        )

        # JSON 파싱
        parsed = self.parser.parse(response.content)

        # 필수 필드 검증
        if "question" not in parsed or "level" not in parsed:
            raise ValueError(f"LLM 응답에 필수 필드 없음: {list(parsed.keys())}")

        question = parsed["question"]
        level = QuestionLevel.from_int(parsed["level"])

        logger.info(f"[LangchainPersonalGenerator] 질문 생성 완료: {question[:30]}...")

        return question, level

    def _format_rag_context(self, docs: list[QADocument]) -> str:
        """RAG 컨텍스트 포맷팅 (Infrastructure 세부사항)"""
        if not docs:
            return "과거 답변 기록이 없습니다."

        lines = []
        for idx, doc in enumerate(docs[:5], 1):
            year, month, day = doc.get_date_parts()
            line = f"{idx}. [{year}-{month:02d}-{day:02d}] Q: {doc.question} / A: {doc.answer}"
            lines.append(line)

        return "\n".join(lines)

    def _format_base_qa(self, doc: QADocument) -> str:
        """기준 QA 포맷팅"""
        year, month, day = doc.get_date_parts()
        return f"""**기준 QA:**
- 질문: {doc.question}
- 답변: {doc.answer}
- 답변 시각: {year}년 {month}월 {day}일
- 답변자: {doc.role_label}"""
