## 온식구 AI 데이터베이스 스키마 문서

본 문서는 `ai_server/app/database/schema.sql`에 정의된 PostgreSQL 스키마를 기준으로, 각 테이블의 목적과 컬럼/제약/인덱스를 설명합니다.

문서 버전: 2025-08-20

---

### FAMILY
가족 단위 엔터티의 루트 테이블

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 가족 고유 ID |
| name | TEXT | NOT NULL | 가족 이름 |
| timezone | TEXT |  | 가족 기준 타임존 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정 시각 |

---

### MEMBER
가족 구성원 정보

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 구성원 ID |
| family_id | BIGINT | NOT NULL, FK → family(id) ON DELETE CASCADE | 소속 가족 |
| name | TEXT | NOT NULL | 이름/닉네임 |
| role | TEXT |  | 가족 내 역할(예: 아빠, 엄마) |
| birthdate | DATE |  | 생일 |
| timezone | TEXT |  | 개인 타임존 |
| preferred_language | TEXT |  | 선호 언어 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 수정 시각 |

인덱스
- idx_member_family(family_id): 가족별 조회 최적화

---

### MEMBER_PROFILE
구성원 선호/참여도 등 부가 프로필(0..1 관계)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| member_id | BIGINT | PK, FK → member(id) ON DELETE CASCADE | 구성원 ID(=PK) |
| preferences | JSONB |  | 선호(주제/톤/금기 등) |
| engagement_stats | JSONB |  | 참여도(응답률/길이/감정 평균 등) |
| last_ai_update_at | TIMESTAMPTZ |  | 마지막 AI 업데이트 시각 |
| updated_at | TIMESTAMPTZ |  | 수정 시각 |

---

### MEMBER_AFFINITY
구성원 간 친밀도(주체 → 대상)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 레코드 ID |
| family_id | BIGINT | NOT NULL, FK → family(id) ON DELETE CASCADE | 가족 범위 |
| subject_member_id | BIGINT | NOT NULL, FK → member(id) ON DELETE CASCADE | 주체 구성원 |
| target_member_id | BIGINT | NOT NULL, FK → member(id) ON DELETE CASCADE | 대상 구성원 |
| affinity_score | REAL | NOT NULL | 친밀도 점수 (0~1) |
| last_updated_at | TIMESTAMPTZ |  | 갱신 시각 |

제약/인덱스
- chk_affinity_self: subject_member_id <> target_member_id
- chk_affinity_range: 0 ≤ affinity_score ≤ 1
- uq_affinity(family_id, subject_member_id, target_member_id): 중복 방지
- idx_affinity_family_subject(family_id, subject_member_id)

---

### QUESTION_TEMPLATE
질문 템플릿(재사용 기준)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 템플릿 ID |
| owner_family_id | BIGINT | FK → family(id) ON DELETE CASCADE | 소유 가족(글로벌은 NULL 허용) |
| content | TEXT | NOT NULL | 템플릿 본문(치환 전) |
| category | TEXT |  | 카테고리 |
| tags | JSONB |  | 태그 |
| subject_required | BOOLEAN | DEFAULT FALSE | 주제 인물 필요 여부 |
| reuse_scope | TEXT |  | global|per_family|per_subject |
| cooldown_days | INT |  | 재사용 쿨다운 일수 |
| language | TEXT |  | 언어 |
| tone | TEXT |  | 톤 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 여부 |
| archived_at | TIMESTAMPTZ |  | 보관 시각 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |

제약/인덱스
- chk_reuse_scope: reuse_scope ∈ {global, per_family, per_subject} 또는 NULL
- idx_template_owner_family(owner_family_id)
- idx_template_tags_gin USING GIN(tags)

---

### QUESTION_INSTANCE
발송/스케줄용 최종 질문 인스턴스(치환 완료)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 인스턴스 ID |
| family_id | BIGINT | NOT NULL, FK → family(id) ON DELETE CASCADE | 가족 ID |
| template_id | BIGINT | FK → question_template(id) ON DELETE SET NULL | 원 템플릿 참조(옵션) |
| subject_member_id | BIGINT | FK → member(id) ON DELETE SET NULL | 주제 인물(옵션) |
| content | TEXT | NOT NULL | 최종 질문 본문(고정 스냅샷) |
| planned_date | DATE | NOT NULL | 진행 날짜 |
| status | TEXT | NOT NULL | draft|scheduled|sent|canceled |
| generated_by | TEXT |  | ai|manual |
| generation_model | TEXT |  | 생성 모델명 |
| generation_parameters | JSONB |  | 생성 파라미터 |
| generation_prompt | TEXT |  | 사용 프롬프트(옵션) |
| generation_metadata | JSONB |  | 생성 메타(분석 요약 등) |
| generation_confidence | REAL |  | 신뢰도(0~1 가정) |
| generated_at | TIMESTAMPTZ |  | 생성 시각 |
| scheduled_at | TIMESTAMPTZ |  | 스케줄 시각 |
| sent_at | TIMESTAMPTZ |  | 발송 시각 |
| canceled_at | TIMESTAMPTZ |  | 취소 시각 |

제약/인덱스
- uq_instance_per_day(family_id, planned_date): 가족/하루 1건 보장
- chk_instance_status: status ∈ {draft, scheduled, sent, canceled}
- chk_generated_by: generated_by ∈ {ai, manual} 또는 NULL
- 인덱스: (family_id, planned_date), template_id, subject_member_id, GIN(generation_parameters), GIN(generation_metadata)

---

### QUESTION_ASSIGNMENT
질문 인스턴스의 개별 수신자 배정/상태

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 배정 ID |
| instance_id | BIGINT | NOT NULL, FK → question_instance(id) ON DELETE CASCADE | 질문 인스턴스 |
| recipient_member_id | BIGINT | NOT NULL, FK → member(id) ON DELETE CASCADE | 수신자 |
| due_at | TIMESTAMPTZ |  | 응답 기한 |
| sent_at | TIMESTAMPTZ |  | 표시/발송 시각 |
| read_at | TIMESTAMPTZ |  | 읽음 시각 |
| answered_at | TIMESTAMPTZ |  | 답변 시각 |
| expired_at | TIMESTAMPTZ |  | 만료 시각 |
| state | TEXT | NOT NULL DEFAULT 'pending' | pending|delivered|read|answered|expired|failed |
| reminder_count | INT | NOT NULL DEFAULT 0 | 리마인드 횟수 |
| last_reminded_at | TIMESTAMPTZ |  | 마지막 리마인드 시각 |

제약/인덱스
- uq_assignment(instance_id, recipient_member_id): 중복 배정 방지
- chk_assignment_state: state ∈ {pending, delivered, read, answered, expired, failed}
- 인덱스: (recipient_member_id, state), (instance_id)

---

### ANSWER
개별 배정에 대한 실제 답변 (텍스트 및 미디어 확장 지원)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 답변 ID |
| assignment_id | BIGINT | NOT NULL, FK → question_assignment(id) ON DELETE CASCADE | 관련 배정 |
| author_member_id | BIGINT | NOT NULL, FK → member(id) ON DELETE CASCADE | 작성자(=수신자) |
| answer_type | answer_type(ENUM) | NOT NULL DEFAULT 'text' | 답변 유형: 'text','image','audio','video','file','mixed' |
| content | JSONB | NOT NULL | 답변 본문/메타. text일 때 {"text":"..."}, 미디어일 때 {"url":"...", "mime":"...", ...} |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |

인덱스/트리거
- idx_answer_assignment(assignment_id)
- idx_answer_type(answer_type)
- idx_answer_content_gin USING GIN(content)
- 트리거 `trg_answer_author_check`: `author_member_id` = 해당 배정의 `recipient_member_id` 무결성 보장
- 트리거 `trg_answer_content_check`: 타입별 필수 키 검사
  - text: `content.text` 필수
  - mixed: `content.text` + `content.url`(또는 `content.primary_url`) 필수
  - 그 외(media): `content.url` 필수

---

### ANSWER_ANALYSIS
답변 분석 결과(버전 관리)

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 분석 ID |
| answer_id | BIGINT | NOT NULL, FK → answer(id) ON DELETE CASCADE | 대상 답변 |
| analysis_model | TEXT |  | 분석 모델명 |
| analysis_parameters | JSONB |  | 분석 파라미터 |
| analysis_prompt | TEXT |  | 분석 프롬프트 |
| analysis_raw | JSONB |  | 원문/원데이터(옵션) |
| analysis_version | TEXT |  | 분석 버전 태그 |
| summary | TEXT |  | 요약 |
| categories | JSONB |  | 감정/주제 등 분류 |
| scores | JSONB |  | 점수/지표 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |

제약/인덱스
- uq_answer_analysis_version(answer_id, analysis_version): 버전 중복 방지
- 인덱스: answer_id, GIN(analysis_parameters), GIN(categories), GIN(scores)

---

### COMMENTS
답변에 대한 댓글/스레드

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 댓글 ID |
| answer_id | BIGINT | NOT NULL, FK → answer(id) ON DELETE CASCADE | 대상 답변 |
| commenter_member_id | BIGINT | NOT NULL, FK → member(id) ON DELETE CASCADE | 댓글 작성자 |
| parent_comment_id | BIGINT | FK → comments(id) ON DELETE CASCADE | 부모 댓글(대댓글) |
| content | TEXT | NOT NULL | 댓글 본문 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 생성 시각 |
| edited_at | TIMESTAMPTZ |  | 수정 시각 |
| deleted_at | TIMESTAMPTZ |  | 소프트 삭제 시각 |

인덱스
- idx_comments_answer(answer_id)
- idx_comments_commenter(commenter_member_id)

---

### 비고
- 가족당 하루 한 건: `QUESTION_INSTANCE (family_id, planned_date)` 유니크로 강제
- 상태/스코프 제한: CHECK 제약으로 문자열 상태를 통제
- JSONB 컬럼: GIN 인덱스로 유연한 질의 성능 확보
- FK ON DELETE: 상위 삭제 시 하위 정리/NULL 처리 전략 명시


