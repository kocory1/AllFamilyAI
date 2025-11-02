from __future__ import annotations

from typing import Any, Dict


class ScoreSanitizer:
    """
    Utility to clamp and round analysis scores to expected ranges.

    - sentiment: [-1, 1] → round(2)
    - emotion.{joy,sadness,anger,fear,neutral}: [0, 1] → round(2)
    - relevance_to_question/relevance_to_category/toxicity: [0, 1] → round(2)
    - length: int ≥ 0
    - keywords: passthrough
    """

    @staticmethod
    def sanitize(scores: Dict[str, Any] | None) -> Dict[str, Any]:
        if not isinstance(scores, dict):
            return {}

        sanitized: Dict[str, Any] = {}

        # sentiment
        s = scores.get("sentiment")
        try:
            s = float(s)
        except Exception:
            s = None
        if s is not None:
            s = max(-1.0, min(1.0, s))
            sanitized["sentiment"] = round(s, 2)

        # emotion
        emo_in = scores.get("emotion") or {}
        if isinstance(emo_in, dict):
            emo_out: Dict[str, Any] = {}
            for k in ["joy", "sadness", "anger", "fear", "neutral"]:
                v = emo_in.get(k)
                try:
                    v = float(v)
                except Exception:
                    v = None
                if v is not None:
                    v = max(0.0, min(1.0, v))
                    emo_out[k] = round(v, 2)
            if emo_out:
                sanitized["emotion"] = emo_out

        # relevance/toxicity
        for key in ["relevance_to_question", "relevance_to_category", "toxicity"]:
            v = scores.get(key)
            try:
                v = float(v)
            except Exception:
                v = None
            if v is not None:
                v = max(0.0, min(1.0, v))
                sanitized[key] = round(v, 2)

        # length
        L = scores.get("length")
        try:
            L = int(L)
        except Exception:
            L = None
        if L is not None:
            if L < 0:
                L = 0
            sanitized["length"] = L

        # keywords passthrough
        if "keywords" in scores:
            sanitized["keywords"] = scores["keywords"]

        return sanitized


