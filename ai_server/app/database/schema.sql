-- 온식구 AI - 초기 스키마 (PostgreSQL)
-- 적용 방법 예시:
--   psql "$DATABASE_URL" -f ai_server/app/database/schema.sql

BEGIN;

-- =====================
-- 기본 테이블
-- =====================
CREATE TABLE IF NOT EXISTS family (
  id            BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  timezone      TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS member (
  id                   BIGSERIAL PRIMARY KEY,
  family_id            BIGINT NOT NULL REFERENCES family(id) ON DELETE CASCADE,
  name                 TEXT NOT NULL,
  role                 TEXT,
  birthdate            DATE,
  timezone             TEXT,
  preferred_language   TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_member_family ON member(family_id);

CREATE TABLE IF NOT EXISTS member_profile (
  member_id          BIGINT PRIMARY KEY REFERENCES member(id) ON DELETE CASCADE,
  preferences        JSONB,
  engagement_stats   JSONB,
  last_ai_update_at  TIMESTAMPTZ,
  updated_at         TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS member_affinity (
  id                 BIGSERIAL PRIMARY KEY,
  family_id          BIGINT NOT NULL REFERENCES family(id) ON DELETE CASCADE,
  subject_member_id  BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE,
  target_member_id   BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE,
  affinity_score     REAL NOT NULL,
  last_updated_at    TIMESTAMPTZ,
  CONSTRAINT chk_affinity_self  CHECK (subject_member_id <> target_member_id),
  CONSTRAINT chk_affinity_range CHECK (affinity_score >= 0 AND affinity_score <= 1),
  CONSTRAINT uq_affinity UNIQUE (family_id, subject_member_id, target_member_id)
);

CREATE INDEX IF NOT EXISTS idx_affinity_family_subject ON member_affinity(family_id, subject_member_id);

-- =====================
-- 질문 템플릿/인스턴스
-- =====================
CREATE TABLE IF NOT EXISTS question_template (
  id                BIGSERIAL PRIMARY KEY,
  owner_family_id   BIGINT REFERENCES family(id) ON DELETE CASCADE,
  content           TEXT NOT NULL,
  category          TEXT,
  tags              JSONB,
  subject_required  BOOLEAN DEFAULT FALSE,
  reuse_scope       TEXT,
  cooldown_days     INT,
  language          TEXT,
  tone              TEXT,
  is_active         BOOLEAN DEFAULT TRUE,
  archived_at       TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_reuse_scope CHECK (
    reuse_scope IS NULL OR reuse_scope IN ('global','per_family','per_subject')
  )
);

CREATE INDEX IF NOT EXISTS idx_template_owner_family ON question_template(owner_family_id);
CREATE INDEX IF NOT EXISTS idx_template_tags_gin ON question_template USING GIN (tags);

CREATE TABLE IF NOT EXISTS question_instance (
  id                     BIGSERIAL PRIMARY KEY,
  family_id              BIGINT NOT NULL REFERENCES family(id) ON DELETE CASCADE,
  template_id            BIGINT REFERENCES question_template(id) ON DELETE SET NULL,
  subject_member_id      BIGINT REFERENCES member(id) ON DELETE SET NULL,
  content                TEXT NOT NULL,
  planned_date           DATE NOT NULL,
  status                 TEXT NOT NULL,
  generated_by           TEXT,
  generation_model       TEXT,
  generation_parameters  JSONB,
  generation_prompt      TEXT,
  generation_metadata    JSONB,
  generation_confidence  REAL,
  generated_at           TIMESTAMPTZ,
  scheduled_at           TIMESTAMPTZ,
  sent_at                TIMESTAMPTZ,
  canceled_at            TIMESTAMPTZ,
  CONSTRAINT uq_instance_per_day UNIQUE (family_id, planned_date),
  CONSTRAINT chk_instance_status CHECK (status IN ('draft','scheduled','sent','canceled')),
  CONSTRAINT chk_generated_by CHECK (
    generated_by IS NULL OR generated_by IN ('ai','manual')
  )
);

CREATE INDEX IF NOT EXISTS idx_instance_family_planned ON question_instance(family_id, planned_date);
CREATE INDEX IF NOT EXISTS idx_instance_template ON question_instance(template_id);
CREATE INDEX IF NOT EXISTS idx_instance_subject ON question_instance(subject_member_id);
CREATE INDEX IF NOT EXISTS idx_instance_params_gin ON question_instance USING GIN (generation_parameters);
CREATE INDEX IF NOT EXISTS idx_instance_meta_gin ON question_instance USING GIN (generation_metadata);

-- =====================
-- 배포 대상/응답/분석/댓글
-- =====================
CREATE TABLE IF NOT EXISTS question_assignment (
  id                  BIGSERIAL PRIMARY KEY,
  instance_id         BIGINT NOT NULL REFERENCES question_instance(id) ON DELETE CASCADE,
  recipient_member_id BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE,
  due_at              TIMESTAMPTZ,
  sent_at             TIMESTAMPTZ,
  delivered_at        TIMESTAMPTZ,
  read_at             TIMESTAMPTZ,
  answered_at         TIMESTAMPTZ,
  expired_at          TIMESTAMPTZ,
  state               TEXT NOT NULL DEFAULT 'pending',
  delivery_channel    TEXT,
  delivery_status     TEXT,
  delivery_error      TEXT,
  last_delivered_at   TIMESTAMPTZ,
  reminder_count      INT NOT NULL DEFAULT 0,
  last_reminded_at    TIMESTAMPTZ,
  CONSTRAINT uq_assignment UNIQUE (instance_id, recipient_member_id),
  CONSTRAINT chk_assignment_state CHECK (
    state IN ('pending','delivered','read','answered','expired','failed')
  ),
  CONSTRAINT chk_delivery_channel CHECK (
    delivery_channel IS NULL OR delivery_channel IN ('push','sms','kakao','email','other')
  )
);

CREATE INDEX IF NOT EXISTS idx_assignment_inbox ON question_assignment(recipient_member_id, state);
CREATE INDEX IF NOT EXISTS idx_assignment_instance ON question_assignment(instance_id);

CREATE TABLE IF NOT EXISTS answer (
  id                BIGSERIAL PRIMARY KEY,
  assignment_id     BIGINT NOT NULL REFERENCES question_assignment(id) ON DELETE CASCADE,
  author_member_id  BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE,
  content           TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_answer_assignment ON answer(assignment_id);

-- author_member_id = assignment.recipient_member_id 무결성 보장 트리거
CREATE OR REPLACE FUNCTION ensure_answer_author_matches_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.author_member_id <> (
    SELECT recipient_member_id FROM question_assignment WHERE id = NEW.assignment_id
  ) THEN
    RAISE EXCEPTION 'author_member_id must equal recipient_member_id for assignment %', NEW.assignment_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_answer_author_check ON answer;
CREATE TRIGGER trg_answer_author_check
BEFORE INSERT OR UPDATE ON answer
FOR EACH ROW EXECUTE FUNCTION ensure_answer_author_matches_assignment();

CREATE TABLE IF NOT EXISTS answer_analysis (
  id                   BIGSERIAL PRIMARY KEY,
  answer_id            BIGINT NOT NULL REFERENCES answer(id) ON DELETE CASCADE,
  analysis_model       TEXT,
  analysis_parameters  JSONB,
  analysis_prompt      TEXT,
  analysis_raw         JSONB,
  analysis_version     TEXT,
  summary              TEXT,
  categories           JSONB,
  scores               JSONB,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_answer_analysis_version UNIQUE (answer_id, analysis_version)
);

CREATE INDEX IF NOT EXISTS idx_analysis_answer ON answer_analysis(answer_id);
CREATE INDEX IF NOT EXISTS idx_analysis_params_gin ON answer_analysis USING GIN (analysis_parameters);
CREATE INDEX IF NOT EXISTS idx_analysis_categories_gin ON answer_analysis USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_analysis_scores_gin ON answer_analysis USING GIN (scores);

-- COMMENT는 키워드 충돌을 피하기 위해 comments 테이블명 사용
CREATE TABLE IF NOT EXISTS comments (
  id                    BIGSERIAL PRIMARY KEY,
  answer_id             BIGINT NOT NULL REFERENCES answer(id) ON DELETE CASCADE,
  commenter_member_id   BIGINT NOT NULL REFERENCES member(id) ON DELETE CASCADE,
  parent_comment_id     BIGINT REFERENCES comments(id) ON DELETE CASCADE,
  content               TEXT NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  edited_at             TIMESTAMPTZ,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_comments_answer ON comments(answer_id);
CREATE INDEX IF NOT EXISTS idx_comments_commenter ON comments(commenter_member_id);

COMMIT;


