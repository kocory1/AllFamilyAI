"""FastAPI 의존성 주입 (Dependency Injection)"""
import logging
from typing import Optional

from app.vector.chroma_service import ChromaVectorService

logger = logging.getLogger(__name__)

# 싱글톤 인스턴스
_vector_service_instance: Optional[ChromaVectorService] = None


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

