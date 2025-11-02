"""프로필 갱신 규칙 기본 파라미터.
필요 시 BE에서 weights로 override 가능.
Settings에서 기본값을 가져오되, 여기서 fallback 제공.
"""

from app.core.config import settings

DECAY_DEFAULT = settings.profile_decay
CATEGORY_GAIN_DEFAULT = settings.profile_category_gain
TAG_GAIN_DEFAULT = settings.profile_tag_gain
TONE_GAIN_DEFAULT = settings.profile_tone_gain
TABOO_THRESHOLD_DEFAULT = settings.profile_taboo_threshold
TABOO_PENALTY_DEFAULT = settings.profile_taboo_penalty
ALPHA_LENGTH_DEFAULT = settings.profile_alpha_length
TOP_N = settings.profile_top_n_prune
MIN_WEIGHT_PRUNE = 0.05  # 절삭 임계값은 여기서만 관리


