from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI API 설정
    openai_api_key: str
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8001
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 