from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.question import QuestionCategory

# === 답변 관련 모델 ===
class AnswerRequest(BaseModel):
    question_uuid: str = Field(description="질문 고유 ID")
    answer_text: str = Field(description="답변 내용")
    answerer_name: str = Field(description="답변자 이름")

class AnswerResponse(BaseModel):
    id: int = Field(description="답변 DB ID")
    question_uuid: str = Field(description="질문 고유 ID")
    answer_text: str = Field(description="답변 내용")
    answerer_name: str = Field(description="답변자 이름")
    sentiment_score: Optional[str] = Field(description="감정 점수")
    keywords: Optional[List[str]] = Field(description="키워드 목록")
    created_at: datetime = Field(description="답변 시간")

# === 가족 구성원 관련 모델 ===
class FamilyMemberRequest(BaseModel):
    name: str = Field(description="이름/닉네임")
    role: Optional[str] = Field(default=None, description="가족 내 역할")
    age_group: Optional[str] = Field(default=None, description="연령대")
    interests: Optional[List[str]] = Field(default=None, description="관심사 목록")
    personality_traits: Optional[List[str]] = Field(default=None, description="성격 특성")

class FamilyMemberResponse(BaseModel):
    id: int = Field(description="구성원 DB ID")
    name: str = Field(description="이름/닉네임")
    role: Optional[str] = Field(description="가족 내 역할")
    age_group: Optional[str] = Field(description="연령대")
    interests: Optional[List[str]] = Field(description="관심사 목록")
    personality_traits: Optional[List[str]] = Field(description="성격 특성")
    preferred_question_types: Optional[List[str]] = Field(description="선호 질문 유형")
    created_at: datetime = Field(description="등록 시간")

# === MCP 강화 질문 생성 관련 모델 ===
class MCPQuestionRequest(BaseModel):
    target_member: str = Field(description="질문 대상 가족 구성원")
    family_id: str = Field(default="default", description="가족 그룹 식별자")
    category: Optional[QuestionCategory] = Field(default=None, description="질문 카테고리")
    family_context: Optional[str] = Field(default=None, description="가족 구성 정보")
    mood: Optional[str] = Field(default=None, description="원하는 분위기")
    use_mcp: bool = Field(default=True, description="MCP 사용 여부")

class FollowUpQuestionRequest(BaseModel):
    target_member: str = Field(description="질문 대상 가족 구성원")
    previous_answer: str = Field(description="이전 답변 내용")
    original_question: str = Field(description="원래 질문 내용")
    family_id: str = Field(default="default", description="가족 그룹 식별자")

class ThemedQuestionsRequest(BaseModel):
    target_member: str = Field(description="질문 대상 가족 구성원")
    theme: str = Field(description="테마 (예: 어린시절, 꿈, 취미 등)")
    count: int = Field(default=5, description="생성할 질문 수", ge=1, le=10)
    family_id: str = Field(default="default", description="가족 그룹 식별자")

# === 대화 분석 관련 모델 ===
class ConversationAnalysisRequest(BaseModel):
    question_uuid: str = Field(description="질문 고유 ID")
    conversation_data: Dict[str, Any] = Field(description="대화 데이터")
    participants: List[str] = Field(description="참여자 목록")

class ConversationAnalysisResponse(BaseModel):
    participation: Dict[str, Any] = Field(description="참여도 분석")
    emotional_connection: Dict[str, Any] = Field(description="감정 교류 분석")
    information_sharing: Dict[str, Any] = Field(description="정보 공유 분석")
    conversation_flow: Dict[str, Any] = Field(description="대화 흐름 분석")
    satisfaction: Dict[str, Any] = Field(description="만족도 분석")
    overall_score: float = Field(description="전체 점수")
    recommendations: List[str] = Field(description="개선 추천사항")

# === 가족 패턴 분석 관련 모델 ===
class FamilyAnalysisResponse(BaseModel):
    target_member: str = Field(description="분석 대상 구성원")
    analysis_timestamp: str = Field(description="분석 시간")
    recent_conversations: List[Dict[str, Any]] = Field(description="최근 대화 기록")
    answer_patterns: Dict[str, Any] = Field(description="답변 패턴 분석")
    preferred_categories: List[Dict[str, Any]] = Field(description="선호 카테고리")
    emotional_patterns: Dict[str, Any] = Field(description="감정 패턴")
    time_patterns: Dict[str, Any] = Field(description="시간대별 패턴")
    recommendations: List[str] = Field(description="추천사항")

# === 통계 관련 모델 ===
class QuestionStatisticsResponse(BaseModel):
    total_questions: int = Field(description="전체 질문 수")
    category_distribution: Dict[str, int] = Field(description="카테고리별 분포")
    member_distribution: Dict[str, int] = Field(description="구성원별 분포")
    recent_week_count: int = Field(description="최근 7일 질문 수")
    generated_at: str = Field(description="통계 생성 시간")

class AnswerStatisticsResponse(BaseModel):
    total_answers: int = Field(description="전체 답변 수")
    answerer_distribution: Dict[str, int] = Field(description="답변자별 분포")
    sentiment_distribution: Dict[str, int] = Field(description="감정별 분포")
    average_answer_length: float = Field(description="평균 답변 길이")
    generated_at: str = Field(description="통계 생성 시간")

# === 대화 기록 관련 모델 ===
class ConversationHistoryRequest(BaseModel):
    question_uuid: str = Field(description="질문 고유 ID")
    conversation_data: Dict[str, Any] = Field(description="전체 대화 내용")
    participants: List[str] = Field(description="참여자 목록")
    conversation_summary: Optional[str] = Field(default=None, description="대화 요약")
    emotional_tone: Optional[str] = Field(default=None, description="감정 톤")
    topics_discussed: Optional[List[str]] = Field(default=None, description="논의된 주제들")

class ConversationHistoryResponse(BaseModel):
    id: int = Field(description="대화 기록 ID")
    question_content: Optional[str] = Field(description="질문 내용")
    conversation_summary: Optional[str] = Field(description="대화 요약")
    emotional_tone: Optional[str] = Field(description="감정 톤")
    topics_discussed: Optional[List[str]] = Field(description="논의된 주제들")
    participants: List[str] = Field(description="참여자 목록")
    created_at: str = Field(description="대화 시간")

# === 질문 목록 관련 모델 ===
class QuestionListRequest(BaseModel):
    target_member: Optional[str] = Field(default=None, description="특정 구성원 필터")
    category: Optional[QuestionCategory] = Field(default=None, description="카테고리 필터")
    limit: int = Field(default=50, description="조회할 질문 수", ge=1, le=100)
    include_answers: bool = Field(default=False, description="답변 포함 여부")

class DetailedQuestionResponse(BaseModel):
    id: str = Field(description="질문 고유 ID")
    content: str = Field(description="질문 내용")
    category: QuestionCategory = Field(description="질문 카테고리")
    target_member: str = Field(description="질문 대상 가족 구성원")
    created_at: datetime = Field(description="생성 시간")
    family_context: Optional[str] = Field(description="가족 구성 정보")
    mood: Optional[str] = Field(description="분위기")
    answers: Optional[List[AnswerResponse]] = Field(description="답변 목록")

# === 에러 응답 모델 ===
class MCPErrorResponse(BaseModel):
    error: str = Field(description="에러 메시지")
    error_code: str = Field(description="에러 코드")
    detail: Optional[str] = Field(default=None, description="상세 에러 정보")
    timestamp: str = Field(description="에러 발생 시간")

# === 성공 응답 모델 ===
class SuccessResponse(BaseModel):
    success: bool = Field(description="성공 여부")
    message: str = Field(description="성공 메시지")
    data: Optional[Dict[str, Any]] = Field(default=None, description="추가 데이터")