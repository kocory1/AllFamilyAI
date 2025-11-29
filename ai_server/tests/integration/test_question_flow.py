"""
질문 생성 API Integration 테스트 (실제 API 호출)
로컬에서만 수동 실행, CI에서는 실행 안 함

시니어 피드백 반영:
- RAG 핵심 기능 테스트 추가
- 타임아웃 현실화 (60초)
- 질문 품질 검증 (물음표 확인)
"""
import pytest
import httpx


@pytest.mark.integration
class TestQuestionAPI:
    """질문 생성 API 통합 테스트"""
    
    async def test_generate_question_basic(self, api_base_url):
        """기본 질문 생성 (RAG 없이)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "오늘 하루는 어땠나요?",
                    "category": "일상",
                    "tone": "편안한",
                    "useRag": False
                },
                timeout=60.0  # 넉넉하게 60초
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 응답 구조 검증
            assert "content" in data
            assert "generatedBy" in data
            assert "generationModel" in data
            assert "generationConfidence" in data
            
            # 값 검증
            assert len(data["content"]) > 0
            assert data["generatedBy"] == "ai"
            assert 0 <= data["generationConfidence"] <= 1
            
            # 질문 품질 검증 (물음표 확인)
            content = data["content"]
            assert content.endswith("?") or content.endswith("요") or content.endswith("가요"), \
                f"질문이 물음표나 어미로 끝나지 않음: {content}"
    
    async def test_generate_question_with_rag_enabled_empty_db(self, api_base_url, test_user_id):
        """
        [핵심] RAG 활성화 - VectorDB 비어있을 때
        파이프라인이 터지지 않고 정상 동작하는지 확인
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "주말에 뭐 했어요?",
                    "category": "일상",
                    "tone": "편안한",
                    "subjectMemberId": f"test_rag_{test_user_id}",  # 데이터 없는 신규 유저
                    "useRag": True  # ✅ RAG 활성화 (핵심!)
                },
                timeout=60.0  # RAG는 [임베딩 -> 검색 -> 생성] 단계로 더 느림
            )
            
            # VectorDB 비어있어도 200 OK
            assert response.status_code == 200
            data = response.json()
            
            # 응답 구조 검증
            assert "content" in data
            assert "generationMetadata" in data
            
            # RAG 메타데이터 확인
            metadata = data["generationMetadata"]
            assert "ragEnabled" in metadata
            assert metadata["ragEnabled"] is False  # 데이터 없어서 비활성화
            assert metadata["ragContextCount"] == 0
            
            # 질문 생성은 정상 완료
            assert len(data["content"]) > 0
            assert data["content"].endswith("?") or "?" in data["content"] or \
                   data["content"].endswith("요") or data["content"].endswith("가요")
    
    async def test_generate_question_with_rag_pipeline(self, api_base_url, test_user_id):
        """
        [핵심] RAG 전체 파이프라인 테스트
        1. 답변 5개 저장 (RAG_MIN_ANSWERS=5 조건 충족)
        2. RAG 활성화 질문 생성
        3. RAG 컨텍스트가 반영되었는지 확인
        """
        user_id = f"test_rag_{test_user_id}"
        
        async with httpx.AsyncClient() as client:
            # Step 1: 답변 5개 저장 (RAG 활성화 조건 충족)
            answers = [
                ("주말에 뭐 했어요?", "가족과 등산을 다녀왔어요. 날씨가 좋았어요."),
                ("최근 즐거웠던 순간은?", "아이들과 공원에서 자전거를 탔어요."),
                ("요즘 관심사는 뭐예요?", "요리에 관심이 생겨서 새로운 레시피를 배우고 있어요."),
                ("좋아하는 음식은?", "삼겹살이랑 된장찌개를 좋아해요."),
                ("스트레스는 어떻게 푸나요?", "산책하면서 음악을 들어요.")
            ]
            
            print(f"\n📝 답변 5개 저장 시작 (user_id={user_id})...")
            
            for idx, (question, answer) in enumerate(answers, 1):
                response = await client.post(
                    f"{api_base_url}/analysis/answer/api",
                    json={
                        "userId": user_id,
                        "questionContent": question,
                        "answerText": answer,
                        "questionCategory": "일상"
                    },
                    timeout=60.0
                )
                assert response.status_code == 200, f"답변 저장 실패 ({idx}/5)"
                print(f"  ✅ {idx}/5 답변 저장 완료")
            
            # Step 2: RAG 활성화 질문 생성
            print(f"\n🔍 RAG 활성화 질문 생성 중...")
            
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "최근에 뭐 했어요?",
                    "category": "일상",
                    "tone": "편안한",
                    "subjectMemberId": user_id,
                    "useRag": True  # ✅ RAG 활성화
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Step 3: RAG 파이프라인 동작 확인
            # - VectorDB 연결 ✓
            # - 임베딩 생성 ✓
            # - 유사도 검색 ✓
            # - 컨텍스트 반영 ✓
            
            metadata = data["generationMetadata"]
            assert metadata["ragEnabled"] is True, \
                f"RAG가 활성화되어야 함 (답변 5개 저장함). metadata={metadata}"
            assert metadata["ragContextCount"] >= 1, \
                f"검색된 컨텍스트가 있어야 함. metadata={metadata}"
            
            # 질문 생성 정상 완료
            assert len(data["content"]) > 0
            assert data["content"].endswith("?") or "?" in data["content"] or \
                   data["content"].endswith("요") or data["content"].endswith("가요")
            
            print(f"\n✅ RAG 파이프라인 테스트 성공")
            print(f"  - 답변 저장: 5개")
            print(f"  - RAG Enabled: {metadata['ragEnabled']}")
            print(f"  - RAG Context Count: {metadata['ragContextCount']}")
            print(f"  - Generated Question: {data['content']}")
    
    async def test_generate_question_with_subject(self, api_base_url, test_user_id):
        """특정 사용자 대상 질문 생성"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "가족에 대해 말해주세요",
                    "category": "가족",
                    "tone": "따뜻한",
                    "subjectMemberId": test_user_id,
                    "useRag": False
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"]
            
            # 질문 품질 검증
            content = data["content"]
            assert content.endswith("?") or content.endswith("요") or content.endswith("가요") or "?" in content
    
    async def test_generate_question_invalid_request(self, api_base_url):
        """잘못된 요청 (필수 필드 누락)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={},  # content 누락
                timeout=60.0
            )
            
            # 422 Validation Error 예상
            assert response.status_code == 422
    
    async def test_generate_question_quality_check(self, api_base_url):
        """질문 품질 종합 체크"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/questions/api",
                json={
                    "content": "오늘 기분이 어때요?",
                    "category": "감정",
                    "tone": "친근한",
                    "useRag": False
                },
                timeout=60.0
            )
            
            assert response.status_code == 200
            data = response.json()
            content = data["content"]
            
            # 품질 체크
            assert len(content) > 0, "질문이 비어있음"
            assert len(content) <= 200, f"질문이 너무 김 ({len(content)}자)"
            
            # 질문 형식 체크 (물음표 또는 한국어 의문 어미)
            is_question = (
                content.endswith("?") or 
                content.endswith("요") or 
                content.endswith("가요") or
                content.endswith("까요") or
                content.endswith("나요") or
                "?" in content
            )
            assert is_question, f"질문 형식이 아님: {content}"
            
            # 불필요한 접두사 제거 확인
            assert not content.startswith("질문:"), "접두사가 제거되지 않음"
            assert not content.startswith("Question:"), "접두사가 제거되지 않음"
            
            # 따옴표 제거 확인
            assert not content.startswith('"'), "따옴표가 제거되지 않음"
            assert not content.startswith("'"), "따옴표가 제거되지 않음"
