"""
의존성 주입 컨테이너 (Clean Architecture)

Clean Architecture 의존성 흐름:
Presentation → Application → Domain ← Infrastructure
"""

import logging
from typing import Annotated, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from fastapi import Depends

from app.adapters.openai_client import OpenAIClient
from app.application.use_cases.family_recent_question import FamilyRecentQuestionUseCase
from app.application.use_cases.family_summary import FamilySummaryUseCase
from app.application.use_cases.generate_family_question import GenerateFamilyQuestionUseCase
from app.application.use_cases.generate_personal_question import (
    GeneratePersonalQuestionUseCase,
)
from app.core.config import settings
from app.domain.ports.question_generator_port import QuestionGeneratorPort
from app.domain.ports.summary_generator_port import SummaryGeneratorPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.infrastructure.llm.langchain_family_generator import LangchainFamilyGenerator
from app.infrastructure.llm.langchain_personal_generator import LangchainPersonalGenerator
from app.infrastructure.llm.langchain_summary_generator import LangChainSummaryGenerator
from app.infrastructure.llm.prompt_loader import PromptLoader
from app.infrastructure.vector.chroma_vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)

# === 싱글톤 인스턴스 ===
_openai_client: OpenAIClient | None = None
_chroma_collection = None
_vector_store: VectorStorePort | None = None
_personal_generator: QuestionGeneratorPort | None = None
_family_generator: QuestionGeneratorPort | None = None
_summary_generator: SummaryGeneratorPort | None = None


# === Infrastructure Layer ===


def get_openai_client() -> OpenAIClient:
    """OpenAI 클라이언트 싱글톤"""
    global _openai_client
    if _openai_client is None:
        logger.info("[DI] OpenAI 클라이언트 생성")
        _openai_client = OpenAIClient()
    return _openai_client


def get_chroma_collection() -> Any:
    """ChromaDB Collection 싱글톤 (chromadb 공식 Collection 타입 스텁 없음 → Any)"""
    global _chroma_collection
    if _chroma_collection is None:
        logger.info("[DI] ChromaDB Collection 생성")
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
        )
        _chroma_collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={
                "description": "가족 QA 히스토리",
                "embedding_model": settings.embedding_model,
            },
        )
        logger.info(
            f"[DI] ChromaDB Collection 준비 완료: " f"기존 데이터={_chroma_collection.count()}개"
        )
    return _chroma_collection


def get_vector_store() -> VectorStorePort:
    """
    벡터 스토어 싱글톤 (인터페이스 반환)

    Clean Architecture:
    - VectorStorePort 인터페이스 반환
    - 구체 구현(ChromaVectorStore)은 숨김
    """
    global _vector_store
    if _vector_store is None:
        logger.info("[DI] ChromaVectorStore 생성")
        _vector_store = ChromaVectorStore(
            openai_client=get_openai_client(),
            collection=get_chroma_collection(),
        )
    return _vector_store


def get_personal_generator() -> QuestionGeneratorPort:
    """
    개인 질문 생성기 싱글톤 (인터페이스 반환)

    Clean Architecture:
    - QuestionGeneratorPort 인터페이스 반환
    - 구체 구현(LangchainPersonalGenerator)은 숨김
    """
    global _personal_generator
    if _personal_generator is None:
        logger.info("[DI] LangchainPersonalGenerator 생성")
        prompt_loader = PromptLoader(prompt_dir="prompts")
        prompt_data = prompt_loader.load("personal_generate.yaml")

        _personal_generator = LangchainPersonalGenerator(
            prompt_data=prompt_data,
            model=settings.default_model,
            temperature=settings.temperature,
        )
    return _personal_generator


def get_family_generator() -> QuestionGeneratorPort:
    """
    가족 질문 생성기 싱글톤 (인터페이스 반환)

    Clean Architecture:
    - QuestionGeneratorPort 인터페이스 반환
    - 구체 구현(LangchainFamilyGenerator)은 숨김
    """
    global _family_generator
    if _family_generator is None:
        logger.info("[DI] LangchainFamilyGenerator 생성")
        prompt_loader = PromptLoader(prompt_dir="prompts")
        prompt_data = prompt_loader.load("family_generate.yaml")

        _family_generator = LangchainFamilyGenerator(
            prompt_data=prompt_data,
            model=settings.default_model,
            temperature=settings.temperature,
        )
    return _family_generator


def get_summary_generator() -> SummaryGeneratorPort:
    """주간/월간 요약 생성기 싱글톤 (SummaryGeneratorPort 반환)"""
    global _summary_generator
    if _summary_generator is None:
        logger.info("[DI] LangChainSummaryGenerator 생성")
        prompt_loader = PromptLoader(prompt_dir="prompts")
        prompt_data = prompt_loader.load("summary_headline.yaml")
        _summary_generator = LangChainSummaryGenerator(
            prompt_data=prompt_data,
            model=settings.default_model,
            temperature=settings.temperature,
        )
    return _summary_generator


# === Application Layer (Use Cases) ===


def get_personal_question_use_case() -> GeneratePersonalQuestionUseCase:
    """
    개인 질문 생성 Use Case

    Clean Architecture 의존성 흐름:
    Presentation → Application → Domain ← Infrastructure

    Use Case는 Port (인터페이스)에만 의존
    """
    return GeneratePersonalQuestionUseCase(
        vector_store=get_vector_store(),  # ← Port (인터페이스)
        question_generator=get_personal_generator(),  # ← Port (인터페이스)
    )


def get_family_question_use_case() -> GenerateFamilyQuestionUseCase:
    """
    가족 질문 생성 Use Case

    Clean Architecture 의존성 흐름:
    Presentation → Application → Domain ← Infrastructure
    """
    return GenerateFamilyQuestionUseCase(
        vector_store=get_vector_store(),  # ← Port (인터페이스)
        question_generator=get_family_generator(),  # ← Port (인터페이스)
    )


def get_family_recent_question_use_case() -> FamilyRecentQuestionUseCase:
    """
    가족 최근 질문 기반 생성 Use Case (신규 API)

    Clean Architecture 의존성 흐름:
    Presentation → Application → Domain ← Infrastructure
    """
    return FamilyRecentQuestionUseCase(
        vector_store=get_vector_store(),  # ← Port (인터페이스)
        question_generator=get_family_generator(),  # ← Port (인터페이스, 가족용 프롬프트)
    )


def get_family_summary_use_case() -> FamilySummaryUseCase:
    """
    가족 주간/월간 요약 Use Case

    GET /api/v1/summary?familyId=xxx&period=weekly|monthly
    - period: weekly=최근 7일, monthly=최근 30일
    - 응답: context만
    """
    return FamilySummaryUseCase(
        vector_store=get_vector_store(),
        summary_generator=get_summary_generator(),
    )


# === Annotated 의존성 (라우터에서 타입으로 사용, dependency_overrides 용이) ===

PersonalQuestionUC = Annotated[
    GeneratePersonalQuestionUseCase, Depends(get_personal_question_use_case)
]
FamilyQuestionUC = Annotated[
    GenerateFamilyQuestionUseCase, Depends(get_family_question_use_case)
]
FamilyRecentQuestionUC = Annotated[
    FamilyRecentQuestionUseCase, Depends(get_family_recent_question_use_case)
]
SummaryUC = Annotated[FamilySummaryUseCase, Depends(get_family_summary_use_case)]
