from __future__ import annotations

from typing import Dict, Any, List

from app.member_profile.base import ProfileUpdater
from app.member_profile.models import (
    MemberProfileComputeRequest,
    MemberProfileSummary,
)
from app.member_profile import rules


class DefaultProfileUpdater(ProfileUpdater):
    """기본 프로필 갱신 로직 구현체.
    - 선호: 카테고리/태그 가중치 갱신(감쇠+가산), taboo 처리
    - 톤: 간단 warm 톤 가중치
    - 참여도: 평균 글자수 EMA(α=0.5 기본)
    - 저장은 BE가 담당(본 클래스는 요약만 반환)
    """
    def compute(self, request: MemberProfileComputeRequest) -> MemberProfileSummary:
        prefs = (request.current_profile.preferences.dict() if request.current_profile else {}) or {}
        eng = (request.current_profile.engagement_stats.dict() if request.current_profile else {}) or {}
        w = (request.weights.dict() if request.weights else {}) or {}

        decay = w.get("decay", rules.DECAY_DEFAULT)
        g_cat = w.get("category_gain", rules.CATEGORY_GAIN_DEFAULT)
        g_tag = w.get("tag_gain", rules.TAG_GAIN_DEFAULT)
        taboo_threshold = w.get("taboo_threshold", rules.TABOO_THRESHOLD_DEFAULT)
        taboo_penalty = w.get("taboo_penalty", rules.TABOO_PENALTY_DEFAULT)
        alpha_L = w.get("alpha_length", rules.ALPHA_LENGTH_DEFAULT)

        liked_categories: Dict[str, float] = dict(prefs.get("liked_categories", {}))
        liked_tags: Dict[str, float] = dict(prefs.get("liked_tags", {}))
        preferred_tone_map: Dict[str, float] = dict(prefs.get("preferred_tone", {}))
        taboo_topics: List[str] = list(prefs.get("taboo_topics", []))

        # decay: 기존 가중치에 시간 감쇠 적용
        for m in (liked_categories, liked_tags, preferred_tone_map):
            for k in list(m.keys()):
                m[k] = m[k] * decay

        ana = request.analysis
        categories = (ana.categories or [])
        keywords = (ana.keywords or [])
        scores = (ana.scores.dict() if ana.scores else {})
        s = float(scores.get("sentiment") or 0.0)
        s = max(-1.0, min(1.0, s))
        joy = 0.0
        emo = scores.get("emotion") or {}
        try:
            joy = float(getattr(emo, "joy", None) if not isinstance(emo, dict) else emo.get("joy")) or 0.0
        except Exception:
            joy = 0.0
        joy = max(0.0, min(1.0, joy))
        r_q = float(scores.get("relevance_to_question") or 0.5)
        r_q = max(0.0, min(1.0, r_q))
        r_c = float(scores.get("relevance_to_category") or 0.5)
        r_c = max(0.0, min(1.0, r_c))
        tox = float(scores.get("toxicity") or 0.0)
        tox = max(0.0, min(1.0, tox))
        L = scores.get("length")
        try:
            L = int(L) if L is not None else None
        except Exception:
            L = None
        if L is not None and L < 0:
            L = 0

        # gains: 현재 분석을 기반으로 가중치 가산
        pos = max(s, 0.0)
        for c in categories:
            delta = g_cat * pos * (r_c or 0.5) * (1.0 + joy / 2.0)
            liked_categories[c] = liked_categories.get(c, 0.0) + delta
        for k in keywords:
            delta = g_cat * 0  # placeholder kept zero; tags use tag gain below
        for k in keywords:
            delta = g_tag * (((r_q or 0.5) + joy) / 2.0)
            liked_tags[k] = liked_tags.get(k, 0.0) + delta

        # taboo: 독성이 높으면 금기 추가 및 페널티 적용
        if tox >= taboo_threshold:
            for c in categories:
                liked_categories[c] = max(0.0, liked_categories.get(c, 0.0) - taboo_penalty)
                if c not in taboo_topics:
                    taboo_topics.append(c)
            for k in keywords:
                liked_tags[k] = max(0.0, liked_tags.get(k, 0.0) - taboo_penalty)
                if k not in taboo_topics:
                    taboo_topics.append(k)

        # preferred tone (simple warm boost): joy/긍정 비율에 비례
        warm_delta = 0.10 * ((joy + max(s, 0.0)) / 2.0)
        preferred_tone_map["따뜻한"] = preferred_tone_map.get("따뜻한", 0.0) + warm_delta
        preferred_tone = max(preferred_tone_map, key=preferred_tone_map.get) if preferred_tone_map else "따뜻한"

        # prune & normalize top-N: 상위 N만 남기고 0~1 정규화
        def topn_norm(m: Dict[str, float]) -> Dict[str, float]:
            items = sorted(m.items(), key=lambda x: x[1], reverse=True)[: rules.TOP_N]
            items = [(k, v) for k, v in items if v >= rules.MIN_WEIGHT_PRUNE]
            if not items:
                return {}
            mx = max(v for _, v in items)
            return {k: (v / mx if mx > 0 else 0.0) for k, v in items}

        liked_categories = topn_norm(liked_categories)
        liked_tags = topn_norm(liked_tags)

        # engagement avg_length EMA (alpha=0.5 default): 길이 기반 참여도
        prev_avg_L = eng.get("avg_length")
        if L is not None:
            if prev_avg_L is None:
                avg_length = float(L)
            else:
                avg_length = (1.0 - alpha_L) * float(prev_avg_L) + alpha_L * float(L)
        else:
            avg_length = prev_avg_L

        return MemberProfileSummary(
            preferences={
                "liked_categories": liked_categories,
                "liked_tags": liked_tags,
                "preferred_tone": preferred_tone,
                "taboo_topics": taboo_topics,
            },
            engagement_stats={
                "avg_length": avg_length,
            },
            meta={
                "applied_decay": decay,
                "alpha_length": alpha_L,
            },
        )


