import json
from datetime import datetime
from app.adapters.openai_client import OpenAIClient
from app.core.config import settings
from app.answer.base import AnswerAnalyzer
from app.answer.models import (
    AnswerAnalysisRequest,
    AnswerAnalysisResponse,
    AnswerAnalysisRaw,
)


class OpenAIAnswerAnalyzer(AnswerAnalyzer):
    name = "openai"

    def __init__(self) -> None:
        self.client = OpenAIClient()

    async def analyze(self, request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
        prompt = self._build_prompt(request)

        params = {
            "model": settings.default_model,
            "temperature": 0.2,
            "max_tokens": 600,
            "language": request.language,
            "top_k": 5,
            "thresholds": {"toxicity": 0.6},
            "tasks": [
                "sentiment",
                "summary",
                "keywords",
                "emotion",
                "relevance",
                "toxicity",
            ],
            "context": {
                "question_category": request.question_category,
                "question_tags": request.question_tags,
                "question_tone": request.question_tone,
            },
            "response_format": "json_object",
        }

        raw_text = await self._call_openai_json(prompt, params)

        parse_ok = False
        summary = ""
        categories = []
        scores = {}

        try:
            data = json.loads(raw_text)
            parse_ok = True
            summary = data.get("summary") or ""
            categories = data.get("categories") or []
            scores = data.get("scores") or {}
        except json.JSONDecodeError:
            try:
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    data = json.loads(raw_text[start:end+1])
                    parse_ok = True
                    summary = data.get("summary") or ""
                    categories = data.get("categories") or []
                    scores = data.get("scores") or {}
            except Exception:
                pass

        version = f"ans-v1.0:{settings.default_model}:{datetime.now().date().isoformat()}"

        return AnswerAnalysisResponse(
            analysis_prompt=prompt,
            analysis_parameters=params,
            analysis_raw=AnswerAnalysisRaw(text=raw_text, parseOk=parse_ok),
            analysis_version=version,
            summary=summary,
            categories=categories,
            scores=scores,
            created_at=datetime.now(),
        )

    def _build_prompt(self, request: AnswerAnalysisRequest) -> str:
        tags_line = ", ".join(request.question_tags) if request.question_tags else "없음"
        tone = request.question_tone or "미지정"
        return f"""
당신은 가족 대화 답변을 정량/정성적으로 분석하는 전문가입니다.
다음 JSON 스키마로만 출력하세요(불필요한 텍스트 금지). 반드시 유효한 JSON 객체 1개만 출력하세요.

입력 정보:
- 언어: {request.language}
- 질문 카테고리: {request.question_category}
- 질문 태그: {tags_line}
- 질문 톤: {tone}
- 질문: {request.question_content}
- 답변: {request.answer_text}

출력(JSON) 스키마:
{{
  "summary": "string",  
  "categories": ["string"],
  "scores": {{
    "sentiment": -1.0_to_1.0,
    "emotion": {{"joy": 0_to_1, "sadness": 0_to_1, "anger": 0_to_1, "fear": 0_to_1, "neutral": 0_to_1}},
    "relevance_to_question": 0_to_1,
    "relevance_to_category": 0_to_1,
    "toxicity": 0_to_1,
    "length": int,
    "keywords": ["string"]
  }}
}}

지침:
1) 질문/카테고리/태그/톤 맥락에 맞춰 분석하세요.
2) 한국어로 간결히 요약(summary) 작성.
3) JSON 외의 텍스트를 출력하지 마세요.
"""

    async def _call_openai_json(self, prompt: str, params: dict) -> str:
        return self.client.chat_completion(
            [
                {
                    "role": "system",
                    "content": "당신은 JSON만 출력하는 분석기입니다. 어떤 경우에도 유효한 JSON 객체만 반환하세요.",
                },
                {"role": "user", "content": prompt},
            ],
            model=params["model"],
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            response_format={"type": "json_object"},
        )


