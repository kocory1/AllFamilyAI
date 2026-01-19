from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    # OpenAI API 설정
    openai_api_key: str

    # Langsmith 설정 (AI 추적 및 디버깅)
    langchain_tracing_v2: str = "false"  # Langsmith 추적 활성화 ("true" or "false")
    langchain_api_key: str = ""  # Langsmith API 키
    langchain_project: str = "onsikgu-ai"  # Langsmith 프로젝트 이름

    # 서버 설정
    host: str = "127.0.0.1"  # nginx 리버스 프록시 사용 시 localhost만 리스닝
    port: int = 8000  # nginx가 80/443 포트에서 리스닝하고 8000으로 프록시

    # 로깅 설정
    log_level: str = "INFO"

    # AI 모델 설정
    default_model: str = "gpt-4o-mini"
    max_tokens: int = 10000
    temperature: float = 0.2

    # ChromaDB 설정 (RAG용 벡터 DB)
    chroma_persist_directory: str = (
        "/home/ubuntu/onsikgu_data/chroma"  # 파일 기반 저장 경로 (배포 환경)
    )
    chroma_collection_name: str = "qa_history"  # 컬렉션 이름 (QA 히스토리 단일 컬렉션)
    embedding_model: str = "text-embedding-3-small"  # OpenAI 임베딩 모델
    rag_top_k: int = 5  # RAG 검색 시 반환할 최대 결과 수 (초기 단계: 풍부한 맥락 제공)
    rag_min_answers: int = 5  # RAG 활성화를 위한 최소 답변 개수


settings = Settings()
