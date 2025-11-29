"""
pytest fixtures 및 테스트 설정
"""
import pytest
import time
from types import SimpleNamespace
from typing import Optional
from dotenv import load_dotenv

# Mock 데이터 임포트
from tests.mocks import (
    MOCK_OPENAI_ANSWER_ANALYSIS,
    MOCK_OPENAI_QUESTION_GENERATION,
    MOCK_OPENAI_EMBEDDING_RESPONSE,
    MOCK_FORMATTED_SEARCH_RESULTS,
    SAMPLE_QUESTION_REQUEST,
    SAMPLE_ANSWER_REQUEST
)

# 환경 변수 로드 (.env 파일)
load_dotenv()


# ====================
# Fixtures: Mock 객체 (개선됨)
# ====================

@pytest.fixture
def mock_openai_client(mocker):
    """
    OpenAI 클라이언트 Mock (AsyncMock + SimpleNamespace)
    실제 OpenAI API 응답 구조를 정확히 흉내냄
    """
    mock_client = mocker.AsyncMock()
    
    # chat.completions.create Mock
    async def mock_create(*args, **kwargs):
        # SimpleNamespace로 실제 객체 구조 재현
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="오늘 저녁에는 뭐 드셨어요?"
                    )
                )
            ]
        )
    
    mock_client.chat.completions.create = mock_create
    
    # embeddings.create Mock
    async def mock_embedding(*args, **kwargs):
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    embedding=[0.1] * 1536  # 1536차원 벡터
                )
            ]
        )
    
    mock_client.embeddings.create = mock_embedding
    
    return mock_client


@pytest.fixture
def mock_vector_service(mocker):
    """
    VectorService Mock (ChromaDB)
    실무 레벨: 의존성 주입 안전하게 처리
    """
    mock_service = mocker.AsyncMock()
    
    # store_answer Mock
    async def mock_store(*args, **kwargs):
        return True
    
    mock_service.store_answer = mock_store
    
    # search_similar_answers Mock
    async def mock_search(*args, **kwargs):
        return MOCK_FORMATTED_SEARCH_RESULTS[:2]  # 상위 2개만 반환
    
    mock_service.search_similar_answers = mock_search
    
    # collection.count Mock
    mock_service.collection.count = mocker.Mock(return_value=10)
    
    return mock_service


@pytest.fixture
def mock_openai_answer_response():
    """OpenAI 답변 분석 응답 상수 (mocks.py에서 임포트)"""
    return MOCK_OPENAI_ANSWER_ANALYSIS


@pytest.fixture
def mock_openai_question_response():
    """OpenAI 질문 생성 응답 상수 (mocks.py에서 임포트)"""
    return MOCK_OPENAI_QUESTION_GENERATION


# ====================
# Fixtures: 테스트 데이터
# ====================

@pytest.fixture
def test_user_id():
    """테스트 유저 ID 생성 (타임스탬프 기반, 충돌 방지)"""
    return f"test_user_{int(time.time() * 1000)}"


@pytest.fixture
def sample_question_request():
    """질문 생성 요청 샘플 (mocks.py에서 임포트)"""
    return SAMPLE_QUESTION_REQUEST.copy()


@pytest.fixture
def sample_answer_request():
    """답변 분석 요청 샘플 (mocks.py에서 임포트)"""
    return SAMPLE_ANSWER_REQUEST.copy()


# ====================
# Fixtures: Integration 테스트용
# ====================

@pytest.fixture
async def cleanup_test_data(test_user_id):
    """
    테스트 데이터 자동 정리 (Teardown)
    Integration 테스트 후 벡터 DB에서 테스트 데이터 삭제
    
    ⚠️ 중요: Integration 테스트에서만 사용!
    유닛 테스트에서는 이 fixture를 사용하지 않으므로,
    ChromaDB 초기화가 시도되지 않음.
    
    지원 패턴:
    - test_user_{timestamp}
    - test_rag_{timestamp}
    
    안전 장치:
    - 환경변수 체크
    - import 실패 처리
    - DB 연결 실패 처리
    """
    yield  # 테스트 실행
    
    # 테스트 종료 후 cleanup (Integration 테스트만)
    try:
        # 원격 테스트 감지 (EC2 등 원격 서버 테스트 시 cleanup 스킵)
        import os
        test_api_url = os.getenv('TEST_API_URL', 'http://localhost:8000/api/v1')
        if 'localhost' not in test_api_url and '127.0.0.1' not in test_api_url:
            print(f"\n[Cleanup 스킵] 원격 테스트 환경 감지: {test_api_url}")
            print("   💡 Tip: 테스트 데이터는 'test_user_', 'test_rag_' 접두사로 구분됩니다.")
            return
        
        # 환경 체크 (유닛 테스트 환경 회피)
        chroma_dir = os.getenv('CHROMA_PERSIST_DIRECTORY')
        if not chroma_dir or chroma_dir == '/tmp/chroma_test':
            # 유닛 테스트 환경 (Mock 환경) - cleanup 스킵
            print(f"\n⏭️  유닛 테스트 환경 감지 - cleanup 스킵")
            return
        
        # 실제 VectorService 임포트
        try:
            from app.vector.chroma_service import ChromaVectorService
        except ImportError as import_error:
            print(f"\n⚠️ ChromaVectorService 임포트 실패 (정상 - 유닛 테스트): {import_error}")
            return
        
        # 직접 인스턴스 생성 (DB 연결 시도)
        try:
            vector_service = ChromaVectorService()
        except Exception as init_error:
            print(f"\n⚠️ ChromaVectorService 초기화 실패 (정상 - 유닛 테스트): {init_error}")
            return
        
        # test_user_로 시작하는 모든 데이터 삭제 (test_rag_도 포함)
        patterns_to_delete = [
            {"user_id": {"$like": "test_user_%"}},  # test_user_123
            {"user_id": {"$like": "test_rag_%"}}    # test_rag_123
        ]
        
        total_deleted = 0
        for pattern in patterns_to_delete:
            try:
                result = vector_service.collection.delete(where=pattern)
                # ChromaDB delete는 삭제된 ID 리스트 반환 (버전에 따라 다를 수 있음)
                if result:
                    deleted = len(result) if isinstance(result, list) else 1
                    total_deleted += deleted
            except Exception as delete_error:
                # 특정 패턴 삭제 실패는 무시하고 계속
                pass
        
        print(f"\n✅ 테스트 데이터 정리 완료: {test_user_id} (총 {total_deleted}개 삭제)")
    
    except Exception as e:
        # 최종 안전망 - 모든 예외 무시 (유닛 테스트 방해 방지)
        print(f"\n⚠️ 테스트 데이터 정리 스킵: {str(e)}")


@pytest.fixture
def api_base_url():
    """
    API 기본 URL (Integration 테스트용)
    
    환경변수 TEST_API_URL로 원격 서버 지정 가능:
    - 로컬: export TEST_API_URL=http://localhost:8000/api/v1
    - 원격: export TEST_API_URL=http://3.38.113.60/api/v1
    """
    import os
    return os.getenv("TEST_API_URL", "http://localhost:8000/api/v1")


# ====================
# Hooks: 테스트 실행 전/후 설정
# ====================

def pytest_configure(config):
    """pytest 시작 시 실행"""
    print("\n" + "="*50)
    print("🧪 온식구 AI 서버 테스트 시작")
    print("="*50)


def pytest_unconfigure(config):
    """pytest 종료 시 실행"""
    print("\n" + "="*50)
    print("✅ 테스트 완료")
    print("="*50)
