"""
질문 생성 Use Case 추상 클래스

Clean Architecture 원칙:
- 공통 비즈니스 로직 추출
- Template Method 패턴 적용
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from app.core.config import settings
from app.domain.entities.qa_document import QADocument
from app.domain.ports.question_generator_port import QuestionGeneratorPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.domain.value_objects.question_level import QuestionLevel

logger = logging.getLogger(__name__)

# 제네릭 타입 정의
InputDTO = TypeVar("InputDTO")
OutputDTO = TypeVar("OutputDTO")


class QuestionGenerationUseCase(ABC):
    """
    질문 생성 Use Case 최상위 추상 클래스

    공통 기능:
    - 의존성 주입 (vector_store, question_generator)
    - 중복 질문 재생성 로직

    Template Method 패턴:
    - execute()가 전체 흐름 정의
    - 서브클래스가 특정 단계 구현
    """

    # 설정값 (config에서 로드)
    MAX_REGENERATION = settings.max_regeneration
    SIMILARITY_THRESHOLD = settings.similarity_threshold

    def __init__(
        self,
        vector_store: VectorStorePort,
        question_generator: QuestionGeneratorPort,
    ):
        """의존성 주입"""
        self.vector_store = vector_store
        self.question_generator = question_generator

    async def _generate_with_retry(
        self,
        base_qa: QADocument,
        rag_context: list[QADocument],
        member_id: str,
    ) -> tuple[str, QuestionLevel, int, bool]:
        """
        중복 체크를 포함한 질문 생성 (공통 로직)

        Args:
            base_qa: 기준 QA Document
            rag_context: RAG 컨텍스트
            member_id: 유사도 체크 대상 멤버 ID

        Returns:
            (question, level, regeneration_count, similarity_warning)
        """
        regeneration_count = 0
        similarity_warning = False

        for attempt in range(self.MAX_REGENERATION):
            question, level = await self.question_generator.generate_question(
                base_qa=base_qa,
                rag_context=rag_context,
            )
            logger.info(f"[Use Case] 질문 생성 (시도 {attempt + 1}): {question[:30]}...")

            # 유사도 검색
            similarity = await self.vector_store.search_similar_questions(
                question_text=question,
                member_id=member_id,
            )

            # 유사도가 임계값 미만이면 성공
            if similarity < self.SIMILARITY_THRESHOLD:
                logger.info(f"[Use Case] 고유 질문 확인 (유사도: {similarity:.2f})")
                break

            # 마지막 시도면 경고 플래그 설정하고 탈출
            if attempt == self.MAX_REGENERATION - 1:
                similarity_warning = True
                logger.warning("[Use Case] 최대 재생성 횟수 도달, 마지막 질문 사용")
                break

            # 재생성 필요 (마지막 제외)
            regeneration_count += 1
            logger.warning(
                f"[Use Case] 중복 질문 감지 (유사도: {similarity:.2f}), "
                f"재생성 {regeneration_count}/{self.MAX_REGENERATION - 1}"
            )

        return question, level, regeneration_count, similarity_warning

    async def _generate_for_target_with_retry(
        self,
        member_id: str,
        role_label: str,
        context: list[QADocument],
    ) -> tuple[str, QuestionLevel, int, bool]:
        """
        타겟 멤버용 질문 생성 + 중복 체크 (재생성 로직)

        Args:
            member_id: 타겟 멤버 ID
            role_label: 타겟 멤버 역할 레이블
            context: 컨텍스트 QA 목록

        Returns:
            (question, level, regeneration_count, similarity_warning)
        """
        regeneration_count = 0
        similarity_warning = False

        for attempt in range(self.MAX_REGENERATION):
            question, level = await self.question_generator.generate_question_for_target(
                target_member_id=member_id,
                target_role_label=role_label,
                context=context,
            )
            logger.info(f"[Use Case] 질문 생성 (시도 {attempt + 1}): {question[:30]}...")

            # 유사도 검색
            similarity = await self.vector_store.search_similar_questions(
                question_text=question,
                member_id=member_id,
            )

            # 유사도가 임계값 미만이면 성공
            if similarity < self.SIMILARITY_THRESHOLD:
                logger.info(f"[Use Case] 고유 질문 확인 (유사도: {similarity:.2f})")
                break

            # 마지막 시도면 경고 플래그 설정하고 탈출
            if attempt == self.MAX_REGENERATION - 1:
                similarity_warning = True
                logger.warning("[Use Case] 최대 재생성 횟수 도달, 마지막 질문 사용")
                break

            # 재생성 필요 (마지막 제외)
            regeneration_count += 1
            logger.warning(
                f"[Use Case] 중복 질문 감지 (유사도: {similarity:.2f}), "
                f"재생성 {regeneration_count}/{self.MAX_REGENERATION - 1}"
            )

        return question, level, regeneration_count, similarity_warning

    @abstractmethod
    async def execute(self, input_dto: Any) -> Any:
        """
        Use Case 실행 (서브클래스에서 구현)
        """
        pass


class RAGQuestionUseCase(QuestionGenerationUseCase):
    """
    RAG 기반 질문 생성 Use Case 추상 클래스

    공통 기능 (QuestionGenerationUseCase 상속):
    - 중복 질문 재생성 로직

    추가 공통 기능:
    - base_qa 기반 플로우
    - 벡터 스토어 저장

    서브클래스에서 구현:
    - _search_rag_context(): RAG 검색 방식
    """

    async def execute(self, input_dto: Any) -> Any:
        """
        RAG 기반 Use Case 실행

        비즈니스 플로우:
        1. role_label 조회 (memberId로)
        2. base_qa 생성
        3. RAG 검색 (서브클래스 구현)
        4. 질문 생성 + 중복 체크
        5. 벡터 스토어 저장
        6. Output DTO 반환
        """
        log_prefix = self._get_log_prefix()
        logger.info(f"[Use Case] {log_prefix} 시작")

        # 1. role_label 조회 (memberId로 최근 질문에서 추출)
        role_label = await self._get_role_label(input_dto.member_id)
        if not role_label:
            logger.warning(
                f"[Use Case] role_label을 찾을 수 없음: member_id={input_dto.member_id}, "
                "기본값 '멤버' 사용"
            )
            role_label = "멤버"

        # 2. Domain Entity 생성
        base_qa = self._create_base_qa(input_dto, role_label)

        # 3. RAG 검색 (서브클래스에서 구현)
        rag_context = await self._search_rag_context(input_dto, base_qa)
        logger.info(f"[Use Case] RAG 검색 완료: {len(rag_context)}개")

        # 3. 질문 생성 + 중복 체크
        question, level, regeneration_count, similarity_warning = (
            await self._generate_with_retry(
                base_qa=base_qa,
                rag_context=rag_context,
                member_id=input_dto.member_id,
            )
        )

        # 4. 저장 (다음 RAG를 위해)
        stored = await self.vector_store.store(base_qa)
        if not stored:
            raise Exception("벡터 DB 저장 실패")
        logger.info("[Use Case] 벡터 스토어 저장 완료")

        # 5. Output DTO 구성
        return self._create_output_dto(
            question=question,
            level=level,
            input_dto=input_dto,
            rag_count=len(rag_context),
            regeneration_count=regeneration_count,
            similarity_warning=similarity_warning,
        )

    async def _get_role_label(self, member_id: str) -> str | None:
        """
        memberId로 role_label 조회

        Args:
            member_id: 멤버 ID

        Returns:
            role_label 또는 None (찾지 못한 경우)
        """
        try:
            recent = await self.vector_store.get_recent_questions_by_member(
                member_id=member_id,
                limit=1,
            )
            if recent:
                return recent[0].role_label
            return None
        except Exception as e:
            logger.error(f"[Use Case] role_label 조회 실패: {e}")
            return None

    def _create_base_qa(self, input_dto: Any, role_label: str) -> QADocument:
        """base_qa 생성 (공통)"""
        return QADocument(
            family_id=input_dto.family_id,
            member_id=input_dto.member_id,
            role_label=role_label,
            question=input_dto.base_question,
            answer=input_dto.base_answer,
            answered_at=input_dto.answered_at,
        )

    @abstractmethod
    async def _search_rag_context(
        self, input_dto: Any, base_qa: QADocument
    ) -> list[QADocument]:
        """RAG 검색 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def _get_log_prefix(self) -> str:
        """로그 prefix (서브클래스에서 구현)"""
        pass

    @abstractmethod
    def _create_output_dto(
        self,
        question: str,
        level: QuestionLevel,
        input_dto: Any,
        rag_count: int,
        regeneration_count: int,
        similarity_warning: bool,
    ) -> Any:
        """Output DTO 생성 (서브클래스에서 구현)"""
        pass
