"""
TDD Phase 3: Infrastructure Layer 테스트

Port 인터페이스 구현체 테스트:
- ChromaVectorStore (VectorStorePort 구현)
- LangchainPersonalGenerator (QuestionGeneratorPort 구현)
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestChromaVectorStore:
    """ChromaVectorStore 구현체 테스트"""

    @pytest.fixture
    def mock_openai_client(self):
        """OpenAI 클라이언트 Mock"""
        mock = AsyncMock()
        mock.create_embedding = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        )
        return mock

    @pytest.fixture
    def mock_chroma_collection(self):
        """ChromaDB Collection Mock"""
        mock = MagicMock()
        mock.add = MagicMock()
        mock.query = MagicMock(
            return_value={
                "ids": [["doc1", "doc2"]],
                "metadatas": [
                    [
                        {
                            "family_id": 1,
                            "member_id": 10,
                            "role_label": "첫째 딸",
                            "answered_at": "2026-01-15T10:00:00",
                        },
                        {
                            "family_id": 1,
                            "member_id": 10,
                            "role_label": "첫째 딸",
                            "answered_at": "2026-01-14T15:30:00",
                        },
                    ]
                ],
                "documents": [
                    [
                        "2026년 1월 15일에 첫째 딸이(가) 받은 질문: 오늘 학교 어땠어?\n답변: 재미있었어요!",
                        "2026년 1월 14일에 첫째 딸이(가) 받은 질문: 친구들과 뭐 했어?\n답변: 같이 놀았어요",
                    ]
                ],
                "distances": [[0.1, 0.2]],
            }
        )
        mock.count = MagicMock(return_value=10)
        return mock

    def test_chroma_vector_store_implements_port(self):
        """[RED] ChromaVectorStore는 VectorStorePort를 구현해야 함"""
        from app.domain.ports.vector_store_port import VectorStorePort
        from app.infrastructure.vector.chroma_vector_store import ChromaVectorStore

        # VectorStorePort를 상속해야 함
        assert issubclass(ChromaVectorStore, VectorStorePort)

    @pytest.mark.asyncio
    async def test_chroma_vector_store_store_method(
        self, mock_openai_client, mock_chroma_collection
    ):
        """[GREEN] store 메서드 - QA 저장 (Mock 사용)"""
        from app.domain.entities.qa_document import QADocument
        from app.infrastructure.vector.chroma_vector_store import ChromaVectorStore

        # Given: ChromaVectorStore 인스턴스 생성 (Mock 주입)
        vector_store = ChromaVectorStore(
            openai_client=mock_openai_client,
            collection=mock_chroma_collection,
        )

        doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="오늘 뭐 했어?",
            answer="친구들과 놀았어요",
            answered_at=datetime(2026, 1, 20, 14, 30, 0),
        )

        # When: QA 문서 저장
        result = await vector_store.store(doc)

        # Then: 저장 성공 & API 호출 검증
        assert result is True
        mock_openai_client.create_embedding.assert_called_once()
        mock_chroma_collection.add.assert_called_once()

        # ChromaDB add 호출 인자 검증
        call_kwargs = mock_chroma_collection.add.call_args.kwargs
        assert len(call_kwargs["ids"]) == 1
        assert len(call_kwargs["embeddings"]) == 1
        assert len(call_kwargs["documents"]) == 1
        assert len(call_kwargs["metadatas"]) == 1

        # 메타데이터 검증
        metadata = call_kwargs["metadatas"][0]
        assert metadata["family_id"] == 1
        assert metadata["member_id"] == 10
        assert metadata["role_label"] == "첫째 딸"

    @pytest.mark.asyncio
    async def test_chroma_vector_store_search_by_member(
        self, mock_openai_client, mock_chroma_collection
    ):
        """[GREEN] search_by_member 메서드 - 개인 검색 (Mock 사용)"""
        from app.domain.entities.qa_document import QADocument
        from app.infrastructure.vector.chroma_vector_store import ChromaVectorStore

        # Given: ChromaVectorStore 인스턴스 생성 (Mock 주입)
        vector_store = ChromaVectorStore(
            openai_client=mock_openai_client,
            collection=mock_chroma_collection,
        )

        query_doc = QADocument(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            question="테스트",
            answer="테스트",
            answered_at=datetime.now(),
        )

        # When: 개인 QA 검색
        results = await vector_store.search_by_member(10, query_doc, top_k=5)

        # Then: 검색 결과 검증
        assert len(results) == 2
        assert all(isinstance(r, QADocument) for r in results)
        assert results[0].question == "오늘 학교 어땠어?"
        assert results[0].answer == "재미있었어요!"

        # ChromaDB query 호출 검증
        mock_chroma_collection.query.assert_called_once()
        call_kwargs = mock_chroma_collection.query.call_args.kwargs
        assert call_kwargs["n_results"] == 5
        assert call_kwargs["where"] == {"member_id": 10}


class TestLangchainPersonalGenerator:
    """LangchainPersonalGenerator 구현체 테스트"""

    @pytest.fixture
    def mock_langchain_response(self):
        """LangChain 응답 Mock"""
        mock = MagicMock()
        mock.content = (
            '{"question": "친구들과 어떤 놀이를 했나요?", "level": 2, "reasoning": "테스트"}'
        )
        mock.usage_metadata = {
            "input_tokens": 150,
            "output_tokens": 20,
            "total_tokens": 170,
        }
        mock.response_metadata = {
            "finish_reason": "stop",
        }
        return mock

    def test_langchain_personal_generator_implements_port(self):
        """[RED] LangchainPersonalGenerator는 QuestionGeneratorPort를 구현해야 함"""
        from app.domain.ports.question_generator_port import QuestionGeneratorPort
        from app.infrastructure.llm.langchain_personal_generator import LangchainPersonalGenerator

        # QuestionGeneratorPort를 상속해야 함
        assert issubclass(LangchainPersonalGenerator, QuestionGeneratorPort)

    @pytest.mark.asyncio
    async def test_langchain_personal_generator_generate_question(self, mock_langchain_response):
        """[RED] generate_question 메서드 - 질문 생성"""
        from app.domain.entities.qa_document import QADocument
        from app.domain.value_objects.question_level import QuestionLevel
        from app.infrastructure.llm.langchain_personal_generator import LangchainPersonalGenerator

        # Given
        with patch("app.infrastructure.llm.langchain_personal_generator.ChatOpenAI"):
            with patch("app.infrastructure.llm.langchain_personal_generator.ChatPromptTemplate"):
                mock_chain = AsyncMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_langchain_response)

                generator = LangchainPersonalGenerator(
                    prompt_data={"system": "test", "user": "test"},
                    model="gpt-4o-mini",
                    temperature=0.2,
                )
                generator.chain = mock_chain

                base_qa = QADocument(
                    family_id=1,
                    member_id=10,
                    role_label="첫째 딸",
                    question="오늘 뭐 했어?",
                    answer="친구들과 놀았어요",
                    answered_at=datetime(2026, 1, 20, 14, 30, 0),
                )

                # When
                question, level = await generator.generate_question(base_qa, [])

                # Then
                assert question == "친구들과 어떤 놀이를 했나요?"
                assert isinstance(level, QuestionLevel)
                assert level.value == 2

                # LangChain 호출 검증
                mock_chain.ainvoke.assert_called_once()


class TestPromptLoader:
    """PromptLoader 유틸리티 테스트"""

    def test_prompt_loader_load_yaml(self, tmp_path):
        """[RED] YAML 프롬프트 로드"""
        from app.infrastructure.llm.prompt_loader import PromptLoader

        # Given: 임시 YAML 파일 생성
        yaml_content = """
system: "당신은 질문 생성 AI입니다."
user: "다음 정보를 바탕으로 질문을 생성하세요: {base_qa}"
"""
        yaml_file = tmp_path / "test_prompt.yaml"
        yaml_file.write_text(yaml_content)

        loader = PromptLoader(prompt_dir=str(tmp_path))

        # When
        prompt_data = loader.load("test_prompt.yaml")

        # Then
        assert "system" in prompt_data
        assert "user" in prompt_data
        assert prompt_data["system"] == "당신은 질문 생성 AI입니다."

    def test_prompt_loader_file_not_found(self):
        """[RED] 파일 없을 시 에러"""
        from app.infrastructure.llm.prompt_loader import PromptLoader

        loader = PromptLoader(prompt_dir="/nonexistent")

        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.yaml")


class TestInfrastructureIntegration:
    """Infrastructure 통합 테스트 (E2E with Mocks)"""

    @pytest.mark.asyncio
    async def test_full_flow_with_infrastructure(self):
        """[RED] Use Case → Infrastructure 전체 플로우 (Mocks 사용)"""
        from app.application.dto.question_dto import GeneratePersonalQuestionInput
        from app.application.use_cases.generate_personal_question import (
            GeneratePersonalQuestionUseCase,
        )
        from app.domain.ports.question_generator_port import QuestionGeneratorPort
        from app.domain.ports.vector_store_port import VectorStorePort
        from app.domain.value_objects.question_level import QuestionLevel

        # Given: Mock Infrastructure
        mock_vector_store = AsyncMock(spec=VectorStorePort)
        mock_vector_store.store.return_value = True
        mock_vector_store.search_by_member.return_value = []
        mock_vector_store.search_similar_questions.return_value = 0.3  # 유사도 낮음

        mock_generator = AsyncMock(spec=QuestionGeneratorPort)
        mock_generator.generate_question.return_value = ("테스트 질문", QuestionLevel(2))

        use_case = GeneratePersonalQuestionUseCase(
            vector_store=mock_vector_store,
            question_generator=mock_generator,
        )

        input_dto = GeneratePersonalQuestionInput(
            family_id=1,
            member_id=10,
            role_label="첫째 딸",
            base_question="테스트",
            base_answer="테스트",
            answered_at=datetime.now(),
        )

        # When
        output = await use_case.execute(input_dto)

        # Then
        assert output.question == "테스트 질문"
        assert output.level.value == 2

        # Infrastructure 호출 검증
        mock_vector_store.store.assert_called_once()
        mock_vector_store.search_by_member.assert_called_once()
        mock_generator.generate_question.assert_called_once()
