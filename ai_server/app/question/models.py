from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str = Field(description="에러 메시지")
    detail: str | None = Field(default=None, description="상세 에러 정보")


# === 답변 분석 힌트(요청 내 구조화 스키마) ===
class EmotionScores(BaseModel):
    joy: float | None = Field(default=None, description="0~1")
    sadness: float | None = Field(default=None, description="0~1")
    anger: float | None = Field(default=None, description="0~1")
    fear: float | None = Field(default=None, description="0~1")
    neutral: float | None = Field(default=None, description="0~1")


class AnalysisScores(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sentiment: float | None = Field(default=None, description="-1.0~1.0")
    emotion: EmotionScores | None = Field(default=None, description="감정 스코어")
    relevance_to_question: float | None = Field(
        default=None, alias="relevanceToQuestion", description="0~1"
    )
    relevance_to_category: float | None = Field(
        default=None, alias="relevanceToCategory", description="0~1"
    )
    toxicity: float | None = Field(default=None, description="0~1")
    length: int | None = Field(default=None, description="답변 길이")


class AnswerAnalysisHint(BaseModel):
    summary: str | None = Field(default=None, description="요약")
    categories: list[str] | None = Field(default=None, description="분류 라벨")
    scores: AnalysisScores | None = Field(default=None, description="점수 집합")
    keywords: list[str] | None = Field(default=None, description="키워드")


# === 질문 생성(최신) 요청 스키마 ===
class QuestionGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(description="질문 생성의 기반이 되는 베이스 문구")
    language: str | None = Field(default="ko", description="언어 코드(기본 ko)")
    tone: str | None = Field(default=None, description="톤/스타일")
    category: str | None = Field(default=None, description="카테고리")
    tags: list[str] | None = Field(default=None, description="태그 목록")
    subject_required: bool | None = Field(
        default=False, alias="subjectRequired", description="주제 인물 필요 여부"
    )
    subject_member_id: str | None = Field(
        default=None, alias="subjectMemberId", description="질문 대상 멤버 ID"
    )
    # 답변 분석 힌트(선택): summary/categories/scores/keywords 등 일부 또는 전부 포함 가능
    answer_analysis: AnswerAnalysisHint | None = Field(
        default=None, alias="answerAnalysis", description="답변 분석 힌트"
    )

    # RAG 사용 여부 (선택적)
    use_rag: bool = Field(
        default=True,
        alias="useRag",
        description="RAG(과거 답변 맥락) 사용 여부. true(기본): 자동 판단, false: 기존 방식",
    )


class QuestionInstanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(description="생성된 질문 내용")
    generated_by: str = Field(alias="generatedBy", description="생성 주체: ai|manual")
    generation_model: str = Field(alias="generationModel", description="사용 모델명")
    generation_parameters: dict[str, Any] = Field(
        alias="generationParameters", description="모델 호출 파라미터"
    )
    generation_prompt: str = Field(alias="generationPrompt", description="프롬프트 원문")
    generation_metadata: dict[str, Any] = Field(
        alias="generationMetadata", description="생성 메타데이터"
    )
    generation_confidence: float = Field(
        alias="generationConfidence", description="생성 신뢰도(0~1)"
    )


# === 멤버 할당 스키마 ===
class AssignMemberInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    member_id: int | str = Field(alias="memberId", description="멤버 ID")
    assigned_count_30: int = Field(
        ge=0, alias="assignedCount30", description="최근 30회 내 할당 횟수(0 이상)"
    )


class AssignOptions(BaseModel):
    epsilon: float | None = Field(default=1e-9, description="가중치 하한값")


class MemberAssignRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    family_id: int | str = Field(alias="familyId", description="가족 ID")
    members: list[AssignMemberInput] = Field(description="후보 멤버 목록")
    pick_count: int = Field(ge=1, alias="pickCount", description="선정할 멤버 수")
    options: AssignOptions | None = Field(default=None, description="선정 옵션")


class MemberAssignResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    member_ids: list[int | str] = Field(alias="memberIds", description="선정된 멤버 ID 목록")
    version: str = Field(default="assign-v1", description="로직 버전")


# === Phase 3: 파생 질문 생성 스키마 ===


class MemberRole(BaseModel):
    """멤버 역할 정보 (BE로부터 받는 구조)"""

    model_config = ConfigDict(populate_by_name=True)

    member_id: int = Field(alias="memberId", description="멤버 ID")
    role_label: str = Field(alias="roleLabel", description="역할 레이블 (예: 첫째 딸, 아빠)")


class PersonalQuestionRequest(BaseModel):
    """개인 파생 질문 생성 요청 (P2)"""

    model_config = ConfigDict(populate_by_name=True)

    family_id: int = Field(alias="familyId", description="가족 ID")
    member_id: int = Field(alias="memberId", description="대상 멤버 ID")
    role_label: str = Field(alias="roleLabel", description="역할 레이블 (예: 첫째 딸)")
    context: str | None = Field(default=None, description="추가 컨텍스트 (선택)")


class FamilyQuestionRequest(BaseModel):
    """가족 파생 질문 생성 요청 (P3)"""

    model_config = ConfigDict(populate_by_name=True)

    family_id: int = Field(alias="familyId", description="가족 ID")
    members: list[MemberRole] = Field(description="가족 구성원 목록")
    context: str | None = Field(default=None, description="추가 컨텍스트 (선택)")


class GenerateQuestionResponse(BaseModel):
    """질문 생성 응답 (공통)"""

    model_config = ConfigDict(populate_by_name=True)

    question: str = Field(description="생성된 질문")
    level: int = Field(description="질문 난이도 (1-4)", ge=1, le=4)
    metadata: dict[str, Any] = Field(description="생성 메타데이터")
