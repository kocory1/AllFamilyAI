"""
Prompt Loader 유틸리티

책임 분리: YAML 프롬프트 로드 책임만 가짐
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class PromptLoader:
    """YAML 프롬프트 로더"""

    def __init__(self, prompt_dir: str = "prompts"):
        """
        Args:
            prompt_dir: 프롬프트 디렉토리 경로
        """
        self.prompt_dir = Path(prompt_dir)

    def load(self, filename: str) -> dict:
        """
        YAML 프롬프트 로드

        Args:
            filename: YAML 파일명 (예: "personal_generate.yaml")

        Returns:
            프롬프트 데이터 dict

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: YAML 포맷 오류
        """
        prompt_path = self.prompt_dir / filename

        if not prompt_path.exists():
            raise FileNotFoundError(f"프롬프트 파일 없음: {prompt_path}")

        with open(prompt_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if "system" not in data or "user" not in data:
            raise ValueError("프롬프트 포맷 오류: system, user 필드 필요")

        logger.info(f"[PromptLoader] 로드 완료: {filename}")
        return data
