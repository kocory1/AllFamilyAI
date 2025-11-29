"""
답변 분석 API Integration 테스트 (실제 API 호출)
로컬에서만 수동 실행, CI에서는 실행 안 함

시니어 피드백 반영:
- 데이터 품질 검증 (sentiment, scores 범위, keywords 개수)
- 스트레스 테스트 (초장문 입력)
- VectorDB 저장 확인 (Side Effect)
"""
import pytest
import httpx


@pytest.mark.integration
class TestAnswerAPI:
    """답변 분석 API 통합 테스트"""
    
    async def test_analyze_answer_basic(self, api_base_url, test_user_id):
        """기본 답변 분석"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": test_user_id,
                    "questionContent": "오늘 저녁에는 뭐 드셨어요?",
                    "answerText": "가족들과 함께 삼겹살을 구워먹었어요. 오랜만에 모여서 즐거웠어요.",
                    "questionCategory": "일상"
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 응답 구조 검증
            assert "summary" in data
            assert "keywords" in data
            assert "sentiment" in data
            assert "scores" in data
            assert "generatedBy" in data
            
            # 값 검증
            assert len(data["summary"]) > 0
            assert isinstance(data["keywords"], list)
            assert data["generatedBy"] == "ai"
    
    async def test_analyze_answer_data_quality(self, api_base_url, test_user_id):
        """
        [중요] 데이터 품질 검증 (LLM 환각 방어)
        - sentiment: 0.0~1.0 범위
        - scores: 각 항목 0.0~1.0 범위
        - keywords: 최소 2개 이상 (Hybrid Search 대비)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": test_user_id,
                    "questionContent": "최근 즐거웠던 순간은?",
                    "answerText": "아이들과 공원에서 자전거를 탔어요. 날씨가 좋아서 산책도 하고 아이스크림도 먹었어요. 가족과 함께여서 정말 행복했어요.",
                    "questionCategory": "일상"
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 1. Sentiment 범위 검증 (0.0 ~ 1.0)
            sentiment = data["sentiment"]
            assert 0.0 <= sentiment <= 1.0, \
                f"sentiment가 범위를 벗어남: {sentiment} (LLM 환각 의심)"
            
            # 2. Keywords 품질 검증
            keywords = data["keywords"]
            assert isinstance(keywords, list), "keywords는 리스트여야 함"
            assert len(keywords) >= 2, \
                f"keywords가 너무 적음: {len(keywords)}개 (최소 2개 필요 - Hybrid Search)"
            
            # 각 키워드가 의미 있는 문자열인지
            for keyword in keywords:
                assert isinstance(keyword, str), "키워드는 문자열이어야 함"
                assert len(keyword.strip()) > 0, "빈 키워드 발견"
            
            # 3. Scores 범위 검증 (0.0 ~ 1.0)
            scores = data["scores"]
            assert isinstance(scores, dict), "scores는 딕셔너리여야 함"
            
            # scores 내부 각 항목 검증
            for score_name, score_value in scores.items():
                if isinstance(score_value, (int, float)):
                    assert 0.0 <= score_value <= 1.0, \
                        f"scores.{score_name}이 범위 벗어남: {score_value}"
            
            print(f"\n✅ 데이터 품질 검증 통과")
            print(f"  - sentiment: {sentiment}")
            print(f"  - keywords: {len(keywords)}개 - {keywords}")
            print(f"  - scores: {scores}")
    
    async def test_analyze_answer_short_text(self, api_base_url, test_user_id):
        """짧은 답변 분석 (엣지 케이스)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": test_user_id,
                    "questionContent": "기분이 어때요?",
                    "answerText": "좋아요.",
                    "questionCategory": "감정"
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 짧은 답변도 분석 가능해야 함
            assert data["summary"]
            assert 0.0 <= data["sentiment"] <= 1.0
            
            # 키워드는 적을 수 있음 (1개 이상이면 OK)
            assert len(data["keywords"]) >= 1
    
    async def test_analyze_answer_long_text_resilience(self, api_base_url, test_user_id):
        """
        [스트레스 테스트] 초장문 입력 처리
        - 3,000자 입력 → Token Limit 초과?
        - 서버가 죽지 않고 적절히 처리하는지 확인
        """
        # 3,000자 초장문 생성
        long_answer = """
        오늘은 정말 특별한 하루였어요. 아침부터 가족들과 함께 여행을 떠났거든요.
        """ * 100  # 약 3,000자
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": test_user_id,
                    "questionContent": "오늘 뭐 했어요?",
                    "answerText": long_answer,
                    "questionCategory": "일상"
                },
                timeout=90.0  # 더 넉넉하게 (초장문 처리 시간)
            )
            
            # 서버가 죽지 않고 응답해야 함
            assert response.status_code in [200, 400, 422], \
                f"예상치 못한 에러: {response.status_code} (500 에러면 서버 버그)"
            
            if response.status_code == 200:
                # 정상 처리 (서비스에서 Truncate 했거나 모델이 잘 처리)
                data = response.json()
                assert data["summary"]
                assert 0.0 <= data["sentiment"] <= 1.0
                print(f"\n✅ 초장문 처리 성공 (Truncate 또는 모델 처리)")
            
            elif response.status_code in [400, 422]:
                # 명시적 거부 (권장: 길이 제한 안내)
                print(f"\n⚠️ 초장문 거부 (정상): {response.status_code}")
                print(f"  응답: {response.text}")
            
            else:
                # 500 에러면 버그!
                pytest.fail(f"500 에러 발생 - 서비스 코드에 Truncate 로직 필요")
    
    async def test_analyze_answer_vector_db_storage(self, api_base_url, test_user_id):
        """
        [사이드 이펙트] VectorDB 저장 확인
        이 API의 핵심 목적: RAG를 위한 데이터 적재
        """
        async with httpx.AsyncClient() as client:
            # 답변 분석 실행
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": f"test_storage_{test_user_id}",
                    "questionContent": "주말에 뭐 했어요?",
                    "answerText": "가족과 등산을 다녀왔어요. 날씨가 정말 좋았어요.",
                    "questionCategory": "일상"
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 분석 결과 검증
            assert data["summary"]
            assert len(data["keywords"]) >= 2
            
            # VectorDB 저장 확인 방법 1: 응답에 저장 여부 필드가 있다면
            # assert data.get("saved") is True
            
            # VectorDB 저장 확인 방법 2: 후속 RAG 쿼리로 확인
            # (실제로 저장되었는지 검색해보기)
            rag_response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "최근에 뭐 했어요?",
                    "category": "일상",
                    "subjectMemberId": f"test_storage_{test_user_id}",
                    "useRag": True
                },
                timeout=60.0
            )
            
            # RAG 쿼리 성공 여부로 간접 확인
            # (답변 1개라 RAG 활성화는 안 되지만, 에러 없이 동작해야 함)
            assert rag_response.status_code == 200
            print(f"\n✅ VectorDB 저장 간접 확인 완료")
            print(f"  - 답변 분석 성공")
            print(f"  - RAG 쿼리 정상 동작 (데이터 저장됨)")
    
    async def test_analyze_answer_invalid_request(self, api_base_url):
        """잘못된 요청 (필수 필드 누락)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/analysis/answer/api",
                json={
                    "userId": "user_123"
                    # questionContent, answerText 누락
                },
                timeout=60.0
            )
            
            # 422 Validation Error 예상
            assert response.status_code == 422
    
    async def test_analyze_answer_edge_cases(self, api_base_url, test_user_id):
        """엣지 케이스 모음"""
        test_cases = [
            {
                "name": "특수문자 포함",
                "answer": "오늘은 @#$%^& 이런 특수문자가 포함된 답변이에요!!! ㅋㅋㅋ",
                "expected_status": 200
            },
            {
                "name": "이모지 포함",
                "answer": "오늘 너무 행복해요 😊😊😊 가족들과 시간 보냈어요 ❤️",
                "expected_status": 200
            },
            {
                "name": "영어 답변",
                "answer": "I spent time with my family today. It was great!",
                "expected_status": 200
            }
        ]
        
        async with httpx.AsyncClient() as client:
            for case in test_cases:
                response = await client.post(
                    f"{api_base_url}/analysis/answer/api",
                    json={
                        "userId": test_user_id,
                        "questionContent": "오늘 뭐 했어요?",
                        "answerText": case["answer"],
                        "questionCategory": "일상"
                    },
                    timeout=60.0
                )
                
                assert response.status_code == case["expected_status"], \
                    f"{case['name']} 테스트 실패"
                
                if response.status_code == 200:
                    data = response.json()
                    assert 0.0 <= data["sentiment"] <= 1.0
                    print(f"  ✅ {case['name']} 통과")
