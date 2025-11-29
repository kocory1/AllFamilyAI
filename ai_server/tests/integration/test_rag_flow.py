"""
RAG 플로우 Integration 테스트
5회 답변 분석 → RAG 활성화 확인

로컬에서만 수동 실행, CI에서는 실행 안 함
"""
import pytest
import httpx
import asyncio


@pytest.mark.integration
class TestRAGFlow:
    """RAG 통합 테스트 (5회 답변 → RAG 활성화)"""
    
    async def test_rag_activation_after_5_answers(
        self, 
        api_base_url, 
        test_user_id,
        cleanup_test_data
    ):
        """
        시나리오:
        1. 답변 5회 저장
        2. 질문 생성 시 RAG 활성화 확인
        3. 테스트 데이터 자동 정리 (cleanup_test_data fixture)
        """
        async with httpx.AsyncClient() as client:
            # Step 1: 답변 5회 저장
            questions_and_answers = [
                ("주말에 주로 뭐 해요?", "가족과 등산을 다녀요."),
                ("최근 즐거웠던 순간은?", "아이들과 공원에서 자전거 탔어요."),
                ("요즘 관심사는 뭐예요?", "요리에 관심이 생겼어요."),
                ("좋아하는 음식은?", "삼겹살이랑 된장찌개요."),
                ("스트레스는 어떻게 푸나요?", "산책하면서 음악 들어요.")
            ]
            
            print(f"\n📝 테스트 유저 {test_user_id}로 답변 5회 저장 시작...")
            
            for i, (question, answer) in enumerate(questions_and_answers, 1):
                response = await client.post(
                    f"{api_base_url}/analysis/answer/api",
                    json={
                        "userId": test_user_id,
                        "questionContent": question,
                        "answerText": answer,
                        "questionCategory": "일상"
                    },
                    timeout=30.0
                )
                
                assert response.status_code == 200
                print(f"  ✅ {i}/5 답변 저장 완료")
                
                # API 레이트 리미트 방지
                await asyncio.sleep(1)
            
            # Step 2: RAG 활성화 확인
            print(f"\n🔍 RAG 활성화 확인 (질문 생성)...")
            
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "category": "일상",
                    "tone": "편안한",
                    "subjectMemberId": test_user_id,
                    "useRag": True  # RAG 명시적 활성화
                },
                timeout=30.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # RAG 메타데이터 검증
            assert "generationMetadata" in data
            metadata = data["generationMetadata"]
            
            assert "ragEnabled" in metadata
            assert metadata["ragEnabled"] is True
            assert "ragContextCount" in metadata
            assert metadata["ragContextCount"] >= 1
            
            print(f"  ✅ RAG 활성화 확인 완료")
            print(f"  📊 RAG Context Count: {metadata['ragContextCount']}")
            print(f"  💬 생성된 질문: {data['content']}")
            
        # cleanup_test_data fixture가 자동으로 데이터 정리
    
    async def test_rag_disabled_for_new_user(self, api_base_url):
        """신규 사용자 (답변 0개)는 RAG 비활성화"""
        new_user_id = f"test_user_new_{int(asyncio.get_event_loop().time())}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "category": "일상",
                    "subjectMemberId": new_user_id,
                    "useRag": True  # RAG 요청하지만 답변 없어서 비활성화
                },
                timeout=30.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # RAG 비활성화 확인
            metadata = data["generationMetadata"]
            assert metadata["ragEnabled"] is False
            assert metadata["ragContextCount"] == 0

