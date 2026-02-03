"""
LangChain 기반 주간/월간 요약 생성기 (Infrastructure)

[특보] 스타일 헤드라인 1개 생성.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domain.ports.summary_generator_port import SummaryGeneratorPort

logger = logging.getLogger(__name__)


class LangChainSummaryGenerator(SummaryGeneratorPort):
    """
    요약 생성 Port 구현 (LangChain)

    - prompt: summary_headline.yaml
    - 출력: [특보] 스타일 헤드라인 1개 (context)
    """

    def __init__(self, prompt_data: dict, model: str, temperature: float):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_data["system"]),
                ("user", prompt_data["user"]),
            ]
        )
        self.chain = self.prompt_template | self.llm
        logger.info(f"[LangChainSummaryGenerator] 초기화 완료: model={model}")

    async def generate_summary(
        self,
        qa_texts: list[str],
        period_label: str,
        answer_count: int,
    ) -> str:
        qa_list = "\n".join(qa_texts) if qa_texts else "(없음)"
        response = await self.chain.ainvoke(
            {
                "period_label": period_label,
                "answer_count": answer_count,
                "qa_list": qa_list,
            }
        )
        context = (response.content or "").strip()
        logger.info(f"[LangChainSummaryGenerator] 요약 생성 완료: {context[:50]}...")
        return context
