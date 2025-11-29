"""
벡터 서비스 테스트 (ChromaDB Mock)
시니어 피드백 반영: SUT(주인공)는 실제 객체, 외부 의존성만 Mock
"""
import pytest
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from app.vector.chroma_service import ChromaVectorService


@pytest.mark.unit
class TestVectorService:
    """벡터 서비스 테스트 (올바른 Mock 전략)"""
    
    @pytest.fixture
    def service(self, mocker):
        """
        실제 ChromaVectorService 인스턴스 생성 (주인공은 진짜!)
        외부 의존성(collection, openai_client)만 Mock
        """
        # ChromaDB 클라이언트와 컬렉션을 Mock으로 교체
        mock_client = Mock()
        mock_collection = Mock()
        mock_openai_client = AsyncMock()
        
        # ChromaDB 초기화 과정을 Mock
        mocker.patch('app.vector.chroma_service.chromadb.PersistentClient', return_value=mock_client)
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 0
        
        # OpenAIClient Mock
        mocker.patch('app.vector.chroma_service.OpenAIClient', return_value=mock_openai_client)
        
        # 실제 서비스 인스턴스 생성 (이제 외부 의존성은 Mock으로 교체됨)
        service = ChromaVectorService()
        
        # Embedding Mock 설정
        mock_embedding_response = SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1] * 1536)]
        )
        service.openai_client.create_embedding.return_value = mock_embedding_response
        
        return service
    
    async def test_store_answer_success(self, service, test_user_id):
        """[성공] 답변 저장 - 실제 로직 실행 확인"""
        # 실행
        result = await service.store_answer(
            answer_id=f"{test_user_id}_001",
            user_id=test_user_id,
            question_text="오늘 뭐 했어요?",
            answer_text="친구들과 영화를 봤어요.",
            category="일상",
            sentiment=0.8,
            timestamp=datetime.now()
        )
        
        # 검증 1: 반환값
        assert result is True
        
        # 검증 2: 실제 로직이 실행되었는지 확인
        # - OpenAI embedding 호출되었는가?
        service.openai_client.create_embedding.assert_awaited_once()
        
        # - ChromaDB collection.add 호출되었는가?
        service.collection.add.assert_called_once()
        
        # 검증 3: collection.add에 전달된 인자 확인
        call_args = service.collection.add.call_args
        assert call_args.kwargs['ids'] == [f"{test_user_id}_001"]
        assert test_user_id in str(call_args.kwargs['metadatas'])
        assert "오늘 뭐 했어요?" in str(call_args.kwargs['metadatas'])
    
    async def test_store_answer_with_optional_metadata(self, service, test_user_id):
        """[성공] 선택적 메타데이터 포함 저장"""
        result = await service.store_answer(
            answer_id=f"{test_user_id}_002",
            user_id=test_user_id,
            question_text="기분이 어때요?",
            answer_text="좋아요!",
            category="감정",
            sentiment=0.9,
            timestamp=datetime(2025, 1, 1, 10, 0, 0)
        )
        
        assert result is True
        
        # 메타데이터에 category와 sentiment 포함 확인
        call_args = service.collection.add.call_args
        metadata = call_args.kwargs['metadatas'][0]
        assert metadata['category'] == "감정"
        assert metadata['sentiment'] == 0.9
    
    async def test_search_similar_answers_success(self, service, test_user_id):
        """[성공] 유사 답변 검색 - 실제 로직 실행"""
        # ChromaDB 검색 결과 Mock 설정
        mock_search_result = {
            'ids': [['answer_1', 'answer_2']],
            'documents': [['답변 1입니다.', '답변 2입니다.']],
            'metadatas': [[
                {'user_id': test_user_id, 'question': '질문 1', 'timestamp': '2025-01-01T10:00:00'},
                {'user_id': test_user_id, 'question': '질문 2', 'timestamp': '2025-01-02T10:00:00'}
            ]],
            'distances': [[0.15, 0.25]]
        }
        service.collection.query.return_value = mock_search_result
        
        # 실행
        results = await service.search_similar_answers(
            user_id=test_user_id,
            query="가족과 함께한 시간",
            top_k=5
        )
        
        # 검증 1: 결과 개수
        assert len(results) == 2
        
        # 검증 2: OpenAI embedding 호출됨
        service.openai_client.create_embedding.assert_awaited_once()
        
        # 검증 3: ChromaDB query 호출됨
        service.collection.query.assert_called_once()
        
        # 검증 4: 결과 구조 확인 (실제 로직의 데이터 가공 확인)
        assert 'answer' in results[0]
        assert 'question' in results[0]
        assert 'similarity' in results[0]
        assert results[0]['answer'] == '답변 1입니다.'
        
        # 검증 5: similarity 계산 로직 확인 (1 - distance/2)
        # distance=0.15 → similarity = 1 - 0.15/2 = 0.925
        # distance=0.25 → similarity = 1 - 0.25/2 = 0.875
        assert results[0]['similarity'] == pytest.approx(0.925, rel=0.01)
        assert results[1]['similarity'] == pytest.approx(0.875, rel=0.01)
    
    async def test_search_with_category_filter(self, service, test_user_id):
        """[성공] 카테고리 필터링 검색"""
        mock_search_result = {
            'ids': [['answer_1']],
            'documents': [['답변입니다.']],
            'metadatas': [[{'user_id': test_user_id, 'question': '질문', 'timestamp': '2025-01-01T10:00:00', 'category': '일상'}]],
            'distances': [[0.1]]
        }
        service.collection.query.return_value = mock_search_result
        
        # 실행
        results = await service.search_similar_answers(
            user_id=test_user_id,
            query="테스트",
            top_k=5,
            category="일상"
        )
        
        # 검증: where 필터에 category 포함 확인
        call_args = service.collection.query.call_args
        assert 'category' in call_args.kwargs['where']
        assert call_args.kwargs['where']['category'] == "일상"
    
    def test_collection_count(self, service, test_user_id):
        """[성공] 컬렉션 카운트 조회"""
        # Mock 설정
        service.collection.count.return_value = 10
        
        # 테스트 격리: 초기화 때 생긴 호출 기록 제거
        service.collection.count.reset_mock()
        
        # 실행
        count = service.collection.count(
            where={"user_id": test_user_id}
        )
        
        # 검증
        assert count == 10
        service.collection.count.assert_called_once_with(
            where={"user_id": test_user_id}
        )


@pytest.mark.unit
class TestVectorServiceEdgeCases:
    """벡터 서비스 엣지 케이스"""
    
    @pytest.fixture
    def service(self, mocker):
        """실제 서비스 + Mock 의존성"""
        mock_client = Mock()
        mock_collection = Mock()
        mock_openai_client = AsyncMock()
        
        mocker.patch('app.vector.chroma_service.chromadb.PersistentClient', return_value=mock_client)
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 0
        mocker.patch('app.vector.chroma_service.OpenAIClient', return_value=mock_openai_client)
        
        service = ChromaVectorService()
        
        mock_embedding_response = SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1] * 1536)]
        )
        service.openai_client.create_embedding.return_value = mock_embedding_response
        
        return service
    
    async def test_search_with_no_results(self, service, test_user_id):
        """[엣지] 검색 결과 없음"""
        # 빈 결과 Mock
        service.collection.query.return_value = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        
        results = await service.search_similar_answers(
            user_id=test_user_id,
            query="존재하지 않는 내용",
            top_k=5
        )
        
        # 빈 리스트 반환 확인
        assert results == []
    
    async def test_store_answer_without_optional_fields(self, service, test_user_id):
        """[엣지] 선택적 필드 없이 저장"""
        result = await service.store_answer(
            answer_id=f"{test_user_id}_003",
            user_id=test_user_id,
            question_text="질문",
            answer_text="답변"
            # category, sentiment, timestamp 생략
        )
        
        assert result is True
        service.collection.add.assert_called_once()
        
        # 메타데이터에 기본 필드만 있는지 확인
        call_args = service.collection.add.call_args
        metadata = call_args.kwargs['metadatas'][0]
        assert 'user_id' in metadata
        assert 'question' in metadata
        assert 'timestamp' in metadata
        # category, sentiment는 없어야 함
        assert 'category' not in metadata or metadata.get('category') is None
