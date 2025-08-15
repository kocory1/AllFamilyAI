from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI API 설정
    openai_api_key: str
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8001
    
    # 데이터베이스 설정
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/family_questions"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/family_questions"
    
    # 로깅 설정
    log_level: str = "INFO"
    
    # AI 모델 설정
    default_model: str = "gpt-4.1-nano"  # gpt-4.1-nano, gpt-4o-mini, gpt-3.5-turbo, gpt-4o
    max_tokens: int = 100
    temperature: float = 0.8
    
    # 질문 생성 설정
    max_question_length: int = 100
    question_categories: list = [
        "가족", "추억", "일상", "꿈", "관계", "감정", "취미", "미래"
    ]
    
    # MCP 설정
    mcp_context_window: int = 10  # 참고할 과거 대화 수
    mcp_similarity_threshold: float = 0.7  # 유사도 임계값
    mcp_analysis_depth: str = "deep"  # shallow, medium, deep
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 