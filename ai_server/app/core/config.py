from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    # OpenAI API 설정
    openai_api_key: str
    
    # 서버 설정
    host: str = "127.0.0.1"  # nginx 리버스 프록시 사용 시 localhost만 리스닝
    port: int = 8000  # nginx가 80/443 포트에서 리스닝하고 8000으로 프록시
    
    # 로깅 설정
    log_level: str = "INFO"
    
    # AI 모델 설정
    default_model: str = "gpt-5-nano"  
    max_tokens: int = 2000  # reasoning 모델은 내부 사고에 토큰을 많이 사용하므로 여유있게 설정
    temperature: float = 0.8
    
    # 질문 생성 설정
    max_question_length: int = 100
    question_categories: list = [
        "가족", "추억", "일상", "꿈", "관계", "감정", "취미", "미래"
    ]
    
    # 프로필 갱신 설정 (member_profile 업데이트 기본값)
    profile_decay: float = 0.9  # 기존 가중치 감쇠율
    profile_category_gain: float = 0.25  # 카테고리 가산치
    profile_tag_gain: float = 0.15  # 태그 가산치
    profile_tone_gain: float = 0.1  # 톤 가산치
    profile_taboo_threshold: float = 0.6  # 독성 점수 금기 임계값
    profile_taboo_penalty: float = 0.2  # 금기 주제 감점
    profile_alpha_length: float = 0.5  # 평균 답변 길이 EMA 계수
    profile_top_n_prune: int = 10  # 선호 카테고리/태그 유지 상위 N개
    
    # ChromaDB 설정 (RAG용 벡터 DB)
    chroma_persist_directory: str = "/home/ubuntu/onsikgu_data/chroma"  # 파일 기반 저장 경로 (배포 환경)
    chroma_collection_name: str = "family_answers"  # 컬렉션 이름
    embedding_model: str = "text-embedding-3-small"  # OpenAI 임베딩 모델
    rag_top_k: int = 5  # RAG 검색 시 반환할 최대 결과 수 (초기 단계: 풍부한 맥락 제공)
    rag_min_answers: int = 5  # RAG 활성화를 위한 최소 답변 개수
    
settings = Settings() 