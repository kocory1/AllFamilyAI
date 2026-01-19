"""질문 생성 관련 유틸리티 함수"""

import logging

logger = logging.getLogger(__name__)


def validate_question_level(level: int | str) -> int:
    """
    질문 난이도 검증 (1-4)

    Args:
        level: 검증할 레벨 값

    Returns:
        int: 유효한 레벨 (1-4), 실패 시 기본값
    """
    try:
        level_int = int(level)
        if 1 <= level_int <= 4:
            return level_int
        logger.warning(f"[레벨 범위 초과] level={level}, 기본값 2 사용")
        return 2
    except (ValueError, TypeError):
        logger.warning(f"[레벨 파싱 실패] level={level}, 기본값 1 사용")
        return 1
