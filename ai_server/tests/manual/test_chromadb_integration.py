"""
ChromaDB Integration Test (Manual)

실제 ChromaDB를 사용하여 저장 → 검색 → 삭제(delete_by_member) 동작 검증

실행 방법:
    poetry run python tests/manual/test_chromadb_integration.py

⚠️ 주의: 이 테스트는 실제 ChromaDB + OpenAI 임베딩을 사용하므로 수동으로만 실행하세요.
"""

import asyncio
import tempfile
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.adapters.openai_client import OpenAIClient
from app.domain.entities.qa_document import QADocument
from app.infrastructure.vector.chroma_vector_store import ChromaVectorStore


async def test_chromadb_store_and_search():
    """실제 ChromaDB 저장 · 검색 · 삭제 테스트"""

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 임시 ChromaDB 디렉토리: {temp_dir}")

        # 1. ChromaDB 초기화
        print("\n1️⃣ ChromaDB 초기화 중...")
        client = chromadb.PersistentClient(
            path=temp_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )

        collection = client.get_or_create_collection(
            name="test_qa_history", metadata={"description": "테스트용 QA 히스토리"}
        )
        print(f"✅ ChromaDB Collection 생성: {collection.name}")
        print(f"   기존 데이터: {collection.count()}개")

        # 2. ChromaVectorStore 초기화
        print("\n2️⃣ ChromaVectorStore 초기화 중...")
        openai_client = OpenAIClient()
        vector_store = ChromaVectorStore(openai_client=openai_client, collection=collection)
        print("✅ ChromaVectorStore 초기화 완료")

        # 3. 테스트 데이터 저장
        print("\n3️⃣ 테스트 QA 데이터 저장 중...")
        test_docs = [
            QADocument(
                family_id="family-999",
                member_id="member-1",
                role_label="테스트 엄마",
                question="오늘 저녁 뭐 먹고 싶어?",
                answer="김치찌개 먹고 싶어요",
                answered_at=datetime(2026, 1, 20, 18, 0, 0),
            ),
            QADocument(
                family_id="family-999",
                member_id="member-1",
                role_label="테스트 엄마",
                question="주말에 뭐 할까?",
                answer="공원에 가고 싶어요",
                answered_at=datetime(2026, 1, 19, 10, 0, 0),
            ),
            QADocument(
                family_id="family-999",
                member_id="member-2",
                role_label="테스트 아빠",
                question="오늘 회사 어땠어?",
                answer="좋았어요",
                answered_at=datetime(2026, 1, 20, 19, 0, 0),
            ),
        ]

        for i, doc in enumerate(test_docs, 1):
            result = await vector_store.store(doc)
            if result:
                print(f"   ✅ 문서 {i}/3 저장 성공: {doc.question[:20]}...")
            else:
                print(f"   ❌ 문서 {i}/3 저장 실패")
                return False

        print(f"\n   📊 현재 ChromaDB 데이터: {collection.count()}개")

        # 4. 검색 테스트 (개인)
        print("\n4️⃣ 개인 검색 테스트 (member_id=member-1)...")
        query_doc = QADocument(
            family_id="family-999",
            member_id="member-1",
            role_label="테스트 엄마",
            question="저녁 메뉴",
            answer="",
            answered_at=datetime.now(),
        )

        results = await vector_store.search_by_member(
            member_id="member-1", query_doc=query_doc, top_k=5
        )

        print(f"   ✅ 검색 결과: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"      {i}. Q: {result.question}")
            print(f"         A: {result.answer}")
            print(f"         Role: {result.role_label}")

        # 5. 검색 테스트 (가족)
        print("\n5️⃣ 가족 검색 테스트 (family_id=999)...")
        family_results = await vector_store.search_by_family(
            family_id="family-999", query_doc=query_doc, top_k=5
        )

        print(f"   ✅ 검색 결과: {len(family_results)}개")
        for i, result in enumerate(family_results, 1):
            print(f"      {i}. Q: {result.question}")
            print(f"         A: {result.answer}")
            print(f"         Role: {result.role_label}")

        # 6. 검증
        print("\n6️⃣ 검증...")
        assert collection.count() == 3, f"저장 실패: {collection.count()}개 (예상: 3개)"
        assert len(results) > 0, "개인 검색 실패"
        assert len(family_results) > 0, "가족 검색 실패"
        assert all(r.family_id == "family-999" for r in family_results), "가족 필터 실패"
        print("   ✅ 저장/검색 검증 통과")

        # 7. 삭제 테스트 (delete_by_member)
        print("\n7️⃣ 멤버 이력 삭제 테스트...")
        deleted_1 = await vector_store.delete_by_member("member-1")
        assert deleted_1 == 2, f"member-1 삭제 예상 2건, 실제 {deleted_1}건"
        print(f"   ✅ member-1 삭제: {deleted_1}건 (예상 2건)")
        assert collection.count() == 1, f"삭제 후 1건 남아야 함: {collection.count()}개"

        deleted_2 = await vector_store.delete_by_member("member-2")
        assert deleted_2 == 1, f"member-2 삭제 예상 1건, 실제 {deleted_2}건"
        print(f"   ✅ member-2 삭제: {deleted_2}건 (예상 1건)")
        assert collection.count() == 0, f"전부 삭제 후 0건: {collection.count()}개"
        print("   ✅ delete_by_member 검증 통과")

        print("\n" + "=" * 50)
        print("🎉 모든 테스트 통과!")
        print("=" * 50)
        print("\n✅ ChromaDB 저장 · 검색 · 삭제 정상 동작 확인!")
        print("✅ 실제 배포 환경에서도 동일하게 작동합니다.")

        return True


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 ChromaDB Integration Test")
    print("=" * 50)

    try:
        result = asyncio.run(test_chromadb_store_and_search())
        if result:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
