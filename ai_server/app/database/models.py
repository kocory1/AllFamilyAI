from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from app.models.question import QuestionCategory
import enum

class QuestionDB(Base):
    """
    생성된 질문을 저장하는 테이블
    """
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_uuid = Column(String(36), unique=True, index=True, comment="API에서 사용되는 UUID")
    content = Column(Text, nullable=False, comment="질문 내용")
    category = Column(SQLEnum(QuestionCategory), nullable=False, comment="질문 카테고리")
    target_member = Column(String(100), nullable=False, comment="질문 대상 가족 구성원")
    family_context = Column(Text, nullable=True, comment="가족 구성 정보")
    mood = Column(String(100), nullable=True, comment="질문 분위기")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    answers = relationship("AnswerDB", back_populates="question", cascade="all, delete-orphan")
    conversation_history = relationship("ConversationHistoryDB", back_populates="question")

class AnswerDB(Base):
    """
    질문에 대한 답변을 저장하는 테이블
    """
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, comment="질문 ID")
    answer_text = Column(Text, nullable=False, comment="답변 내용")
    answerer_name = Column(String(100), nullable=False, comment="답변자 이름")
    sentiment_score = Column(String(20), nullable=True, comment="답변 감정 점수 (positive/negative/neutral)")
    keywords = Column(JSON, nullable=True, comment="답변에서 추출된 키워드들")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="답변 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    question = relationship("QuestionDB", back_populates="answers")

class FamilyMemberDB(Base):
    """
    가족 구성원 정보를 저장하는 테이블
    """
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="이름/닉네임")
    role = Column(String(50), nullable=True, comment="가족 내 역할 (아빠, 엄마, 형, 누나 등)")
    age_group = Column(String(20), nullable=True, comment="연령대 (child, teen, adult, senior)")
    interests = Column(JSON, nullable=True, comment="관심사 목록")
    personality_traits = Column(JSON, nullable=True, comment="성격 특성")
    preferred_question_types = Column(JSON, nullable=True, comment="선호하는 질문 유형")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ConversationHistoryDB(Base):
    """
    대화 기록을 저장하는 테이블 (MCP 컨텍스트용)
    """
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    conversation_data = Column(JSON, nullable=False, comment="전체 대화 내용")
    participants = Column(JSON, nullable=False, comment="참여자 목록")
    conversation_summary = Column(Text, nullable=True, comment="대화 요약")
    emotional_tone = Column(String(50), nullable=True, comment="대화의 전체적인 감정 톤")
    topics_discussed = Column(JSON, nullable=True, comment="논의된 주제들")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    question = relationship("QuestionDB", back_populates="conversation_history")

class MCPContextDB(Base):
    """
    MCP (Model Context Protocol)를 위한 컨텍스트 데이터 저장
    """
    __tablename__ = "mcp_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(String(100), nullable=False, comment="가족 그룹 식별자")
    context_type = Column(String(50), nullable=False, comment="컨텍스트 유형 (question_pattern, answer_pattern, family_dynamics)")
    context_data = Column(JSON, nullable=False, comment="컨텍스트 데이터")
    confidence_score = Column(String(10), nullable=True, comment="신뢰도 점수")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expiry_date = Column(DateTime(timezone=True), nullable=True, comment="컨텍스트 만료 날짜")