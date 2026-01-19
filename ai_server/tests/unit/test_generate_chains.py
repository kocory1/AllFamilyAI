"""
Langchain 질문 생성 Chain 테스트 (TDD - Langchain LCEL)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture
def mock_openai_response_json():
    """Mock OpenAI JSON 응답"""
    return {
        "question": "최근에 가장 즐거웠던 순간을 떠올려보면 어떤 감정이 드나요?",
        "level": 2,
        "reasoning": "과거 답변에서 친구들과의 즐거운 경험이 많았으므로, 감정을 더 깊이 탐구하는 후속 질문",
    }


@pytest.fixture
def mock_rag_results():
    """Mock RAG 검색 결과"""
    return [
        {
            "question": "오늘 기분이 어때요?",
            "answer": "친구들이랑 놀아서 기분 좋았어요!",
            "role_label": "첫째 딸",
            "answered_at": "2026-01-10T14:00:00",
            "similarity": 0.92,
        },
        {
            "question": "주말에 뭐 했어요?",
            "answer": "친구들과 공원에서 놀았어요.",
            "role_label": "첫째 딸",
            "answered_at": "2026-01-12T10:00:00",
            "similarity": 0.88,
        },
    ]


def create_mock_ai_message(content: str, usage: dict | None = None):
    """Mock Langchain AIMessage 생성"""
    mock_message = Mock()
    mock_message.content = content
    mock_message.usage_metadata = usage or {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
    }
    mock_message.response_metadata = {"finish_reason": "stop"}
    return mock_message


class TestPromptLoading:
    """프롬프트 로딩 테스트"""

    def test_personal_prompt_file_exists(self):
        """[파일] personal_generate.yaml 존재 확인"""
        prompt_path = Path("prompts/personal_generate.yaml")
        assert prompt_path.exists(), f"{prompt_path} 파일이 존재하지 않습니다"

    def test_family_prompt_file_exists(self):
        """[파일] family_generate.yaml 존재 확인"""
        prompt_path = Path("prompts/family_generate.yaml")
        assert prompt_path.exists(), f"{prompt_path} 파일이 존재하지 않습니다"

    def test_load_personal_prompt(self):
        """[로드] personal 프롬프트 YAML 파싱"""
        import yaml

        with open("prompts/personal_generate.yaml", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)

        assert "system" in prompt_data
        assert "user" in prompt_data
        assert "{role_label}" in prompt_data["system"]
        assert "{rag_context}" in prompt_data["user"]

    def test_load_family_prompt(self):
        """[로드] family 프롬프트 YAML 파싱"""
        import yaml

        with open("prompts/family_generate.yaml", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)

        assert "system" in prompt_data
        assert "user" in prompt_data
        assert "{family_members}" in prompt_data["user"]
        assert "{rag_context}" in prompt_data["user"]


class TestPersonalGenerateChain:
    """개인 파생 질문 생성 Chain 테스트 (Langchain LCEL)"""

    async def test_generate_personal_question_success(
        self, mock_rag_results, mock_openai_response_json
    ):
        """[성공] 개인 파생 질문 생성 (RAG 포함)"""
        with patch("app.question.chains.personal_generate.ChatOpenAI") as mock_chat_openai:
            # Given: Mock Langchain ChatOpenAI
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            # Mock LCEL chain.ainvoke() 응답
            mock_ai_message = create_mock_ai_message(content=json.dumps(mock_openai_response_json))

            # When: Chain 실행
            from app.question.chains.personal_generate import PersonalGenerateChain

            chain = PersonalGenerateChain()

            # chain 객체를 AsyncMock으로 직접 교체
            mock_chain = AsyncMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_ai_message)
            chain.chain = mock_chain

            result = await chain.generate(
                member_id=1,
                role_label="첫째 딸",
                rag_results=mock_rag_results,
                context=None,
            )

            # Then: 결과 확인
            assert "question" in result
            assert "level" in result
            assert "metadata" in result
            assert result["level"] >= 1 and result["level"] <= 4
            assert len(result["question"]) > 0
            assert result["metadata"]["rag_context_count"] == 2

    async def test_generate_personal_question_without_rag(self, mock_openai_response_json):
        """[조건] RAG 결과 없이 생성"""
        with patch("app.question.chains.personal_generate.ChatOpenAI") as mock_chat_openai:
            # Given
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            response_json = {
                "question": mock_openai_response_json["question"],
                "level": 1,
                "reasoning": "일반 질문",
            }
            mock_ai_message = create_mock_ai_message(content=json.dumps(response_json))

            # When
            from app.question.chains.personal_generate import PersonalGenerateChain

            chain = PersonalGenerateChain()

            # chain 객체를 AsyncMock으로 직접 교체
            mock_chain = AsyncMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_ai_message)
            chain.chain = mock_chain

            result = await chain.generate(
                member_id=1, role_label="첫째 딸", rag_results=[], context=None
            )

            # Then
            assert "question" in result
            assert result["level"] == 1  # RAG 없으면 기본 난이도
            assert result["metadata"]["rag_context_count"] == 0

    async def test_generate_personal_with_context(self, mock_rag_results):
        """[추가] context 전달 시 프롬프트 반영"""
        with patch("app.question.chains.personal_generate.ChatOpenAI") as mock_chat_openai:
            # Given
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            response_json = {
                "question": "생일 파티는 어땠어요?",
                "level": 1,
                "reasoning": "생일 컨텍스트 반영",
            }
            mock_ai_message = create_mock_ai_message(content=json.dumps(response_json))

            # When
            from app.question.chains.personal_generate import PersonalGenerateChain

            chain = PersonalGenerateChain()

            # chain 객체를 AsyncMock으로 직접 교체
            mock_chain = AsyncMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_ai_message)
            chain.chain = mock_chain

            result = await chain.generate(
                member_id=1,
                role_label="첫째 딸",
                rag_results=mock_rag_results,
                context="오늘은 생일입니다",
            )

            # Then
            assert "question" in result
            # ainvoke 호출 시 context가 포함되었는지 확인
            call_args = mock_chain.ainvoke.call_args
            assert call_args is not None
            assert "생일" in str(call_args)


class TestFamilyGenerateChain:
    """가족 파생 질문 생성 Chain 테스트 (Langchain LCEL)"""

    async def test_generate_family_question_success(self):
        """[성공] 가족 파생 질문 생성"""
        with patch("app.question.chains.family_generate.ChatOpenAI") as mock_chat_openai:
            # Given
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            response_json = {
                "question": "이번 주말 가족과 함께 하고 싶은 활동은?",
                "level": 2,
                "reasoning": "가족 공통 관심사",
            }
            mock_ai_message = create_mock_ai_message(content=json.dumps(response_json))

            family_rag_results = [
                {
                    "question": "주말에 뭐 했어요?",
                    "answer": "등산 갔어요.",
                    "role_label": "아빠",
                    "member_id": 1,
                    "answered_at": "2026-01-10T10:00:00",
                    "similarity": 0.9,
                },
                {
                    "question": "주말에 뭐 했어요?",
                    "answer": "가족과 등산 갔어요!",
                    "role_label": "첫째 딸",
                    "member_id": 2,
                    "answered_at": "2026-01-10T14:00:00",
                    "similarity": 0.88,
                },
            ]

            members = [
                {"member_id": 1, "role_label": "아빠"},
                {"member_id": 2, "role_label": "첫째 딸"},
                {"member_id": 3, "role_label": "엄마"},
            ]

            # When
            from app.question.chains.family_generate import FamilyGenerateChain

            chain = FamilyGenerateChain()

            # chain 객체를 AsyncMock으로 직접 교체
            mock_chain = AsyncMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_ai_message)
            chain.chain = mock_chain

            result = await chain.generate(
                family_id=10,
                members=members,
                rag_results=family_rag_results,
                context=None,
            )

            # Then
            assert "question" in result
            assert "level" in result
            assert "metadata" in result
            assert result["level"] >= 1 and result["level"] <= 4
            assert result["metadata"]["family_members_count"] == 3
            assert result["metadata"]["rag_context_count"] == 2

    async def test_generate_family_question_with_diverse_members(self):
        """[다양성] 다양한 가족 구성원 대응"""
        with patch("app.question.chains.family_generate.ChatOpenAI") as mock_chat_openai:
            # Given: 4명 가족
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            response_json = {
                "question": "우리 가족만의 특별한 전통은?",
                "level": 3,
                "reasoning": "가족 유대감",
            }
            mock_ai_message = create_mock_ai_message(content=json.dumps(response_json))

            members = [
                {"member_id": 1, "role_label": "아빠"},
                {"member_id": 2, "role_label": "엄마"},
                {"member_id": 3, "role_label": "첫째 딸"},
                {"member_id": 4, "role_label": "둘째 아들"},
            ]

            # When
            from app.question.chains.family_generate import FamilyGenerateChain

            chain = FamilyGenerateChain()

            # chain 객체를 AsyncMock으로 직접 교체
            mock_chain = AsyncMock()
            mock_chain.ainvoke = AsyncMock(return_value=mock_ai_message)
            chain.chain = mock_chain

            result = await chain.generate(
                family_id=10, members=members, rag_results=[], context=None
            )

            # Then
            assert "question" in result
            # ainvoke 호출 시 모든 멤버 포함 확인
            call_args = mock_chain.ainvoke.call_args
            assert call_args is not None
            assert "아빠" in str(call_args)
            assert "첫째 딸" in str(call_args)
