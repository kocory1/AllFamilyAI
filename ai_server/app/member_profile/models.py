from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

# 사용자 프로필 계산에 사용되는 요청/응답 DTO 정의
# - BE가 저장은 담당하고, AI 서버는 계산(요약)만 수행


class EmotionScoresInput(BaseModel):
    """답변 감정 분포(0~1). 일부 키만 올 수도 있음."""
    joy: Optional[float] = Field(default=None)
    sadness: Optional[float] = Field(default=None)
    anger: Optional[float] = Field(default=None)
    fear: Optional[float] = Field(default=None)
    neutral: Optional[float] = Field(default=None)


class AnalysisScoresInput(BaseModel):
    """답변 분석 점수(사전 클램프 권장). 길이(length)는 문자 수 기준."""
    model_config = ConfigDict(populate_by_name=True)
    
    sentiment: Optional[float] = Field(default=None)
    emotion: Optional[EmotionScoresInput] = Field(default=None)
    relevance_to_question: Optional[float] = Field(default=None, alias="relevanceToQuestion")
    relevance_to_category: Optional[float] = Field(default=None, alias="relevanceToCategory")
    toxicity: Optional[float] = Field(default=None)
    length: Optional[int] = Field(default=None)


class AnswerAnalysisLite(BaseModel):
    """프로필 갱신에 필요한 최소 분석 입력."""
    categories: Optional[List[str]] = Field(default=None)
    scores: Optional[AnalysisScoresInput] = Field(default=None)
    keywords: Optional[List[str]] = Field(default=None)


class PreferencesMap(BaseModel):
    """선호 맵(가중치 기반).
    - liked_*: {라벨: 가중치}
    - preferred_tone: {톤: 가중치}
    - taboo_topics: 금기 라벨 목록
    """
    model_config = ConfigDict(populate_by_name=True)
    
    liked_categories: Dict[str, float] = Field(default_factory=dict, alias="likedCategories")
    liked_tags: Dict[str, float] = Field(default_factory=dict, alias="likedTags")
    preferred_tone: Dict[str, float] = Field(default_factory=dict, alias="preferredTone")
    taboo_topics: List[str] = Field(default_factory=list, alias="tabooTopics")


class EngagementStats(BaseModel):
    """참여도 요약. 현재는 평균 글자수(EMA)만 사용."""
    model_config = ConfigDict(populate_by_name=True)
    
    avg_length: Optional[float] = Field(default=None, alias="avgLength")
    answer_rate_30d: Optional[float] = Field(default=None, alias="answerRate30d")


class CurrentProfileInput(BaseModel):
    """현재 저장되어 있는 프로필(없으면 빈 값으로 처리)."""
    model_config = ConfigDict(populate_by_name=True)
    
    preferences: PreferencesMap = Field(default_factory=PreferencesMap)
    engagement_stats: EngagementStats = Field(default_factory=EngagementStats, alias="engagementStats")


class Weights(BaseModel):
    """갱신 규칙 하이퍼파라미터. 필요 시 BE에서 조정 가능."""
    model_config = ConfigDict(populate_by_name=True)
    
    decay: float = 0.9
    category_gain: float = Field(default=0.25, alias="categoryGain")
    tag_gain: float = Field(default=0.15, alias="tagGain")
    tone_gain: float = Field(default=0.10, alias="toneGain")
    taboo_threshold: float = Field(default=0.6, alias="tabooThreshold")
    taboo_penalty: float = Field(default=0.2, alias="tabooPenalty")
    alpha_length: float = Field(default=0.5, alias="alphaLength")


class MemberProfileComputeRequest(BaseModel):
    """프로필 계산 요청. 단일 분석 입력 + 현재 프로필 + 가중치."""
    model_config = ConfigDict(populate_by_name=True)
    
    analysis: AnswerAnalysisLite = Field(description="단일 답변 분석 요약")
    current_profile: Optional[CurrentProfileInput] = Field(default=None, alias="currentProfile")
    weights: Optional[Weights] = Field(default=None)


class MemberProfileSummary(BaseModel):
    """프로필 계산 결과 요약(저장은 BE 책임)."""
    model_config = ConfigDict(populate_by_name=True)
    
    preferences: Dict[str, Any] = Field(description="선호 요약")
    engagement_stats: Dict[str, Any] = Field(alias="engagementStats", description="참여도 요약")
    meta: Dict[str, Any] = Field(default_factory=dict, description="갱신 메타")


