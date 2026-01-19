"""FastAPI 의존성 주입 (Dependency Injection)"""

import logging

from app.question.chains.family_generate import FamilyGenerateChain
from app.question.chains.personal_generate import PersonalGenerateChain
from app.vector.chroma_service import ChromaVectorService

logger = logging.getLogger(__name__)

# 싱글톤 인스턴스
_vector_service_instance: ChromaVectorService | None = None
_personal_chain_instance: PersonalGenerateChain | None = None
_family_chain_instance: FamilyGenerateChain | None = None


def get_vector_service() -> ChromaVectorService:
    """
    ChromaVectorService 싱글톤 인스턴스 반환

    FastAPI Depends를 통해 주입되며, 앱 전체에서 하나의 인스턴스만 사용됩니다.

    Returns:
        ChromaVectorService: 벡터 서비스 싱글톤 인스턴스
    """
    global _vector_service_instance

    if _vector_service_instance is None:
        logger.info("[의존성 주입] ChromaVectorService 싱글톤 생성 중...")
        _vector_service_instance = ChromaVectorService()
        logger.info("[의존성 주입] ChromaVectorService 싱글톤 생성 완료")

    return _vector_service_instance


def get_personal_chain() -> PersonalGenerateChain:
    """
    PersonalGenerateChain 싱글톤 인스턴스 반환

    FastAPI Depends를 통해 주입되며, 앱 전체에서 하나의 인스턴스만 사용됩니다.
    프롬프트 YAML 파일을 1회만 로드하여 성능을 최적화합니다.

    Returns:
        PersonalGenerateChain: 개인 질문 생성 Chain 싱글톤 인스턴스
    """
    global _personal_chain_instance

    if _personal_chain_instance is None:
        logger.info("[의존성 주입] PersonalGenerateChain 싱글톤 생성 중...")
        _personal_chain_instance = PersonalGenerateChain()
        logger.info("[의존성 주입] PersonalGenerateChain 싱글톤 생성 완료")

    return _personal_chain_instance


def get_family_chain() -> FamilyGenerateChain:
    """
    FamilyGenerateChain 싱글톤 인스턴스 반환

    FastAPI Depends를 통해 주입되며, 앱 전체에서 하나의 인스턴스만 사용됩니다.
    프롬프트 YAML 파일을 1회만 로드하여 성능을 최적화합니다.

    Returns:
        FamilyGenerateChain: 가족 질문 생성 Chain 싱글톤 인스턴스
    """
    global _family_chain_instance

    if _family_chain_instance is None:
        logger.info("[의존성 주입] FamilyGenerateChain 싱글톤 생성 중...")
        _family_chain_instance = FamilyGenerateChain()
        logger.info("[의존성 주입] FamilyGenerateChain 싱글톤 생성 완료")

    return _family_chain_instance
