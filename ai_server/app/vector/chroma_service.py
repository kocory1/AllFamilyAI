"""ChromaDB 벡터 서비스 구현체"""

import logging
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.adapters.openai_client import OpenAIClient
from app.core.config import settings
from app.vector.base import VectorService
from app.vector.models import QADocument

logger = logging.getLogger(__name__)


class ChromaVectorService(VectorService):
    """ChromaDB 기반 벡터 서비스 (단일 컬렉션 qa_history 사용)"""

    def __init__(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            # 파일 기반 Persistent Storage
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
            )

            # 단일 컬렉션 생성 또는 로드 (config에서 이름 가져오기)
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={
                    "description": "가족 QA 히스토리 (단일 컬렉션)",
                    "embedding_model": settings.embedding_model,
                },
            )

            # OpenAI 클라이언트 (임베딩 생성용)
            self.openai_client = OpenAIClient()

            logger.info(
                f"[ChromaDB 초기화 완료] "
                f"경로={settings.chroma_persist_directory}, "
                f"컬렉션={settings.chroma_collection_name}, "
                f"기존 데이터={self.collection.count()}개"
            )

        except Exception as e:
            logger.error(f"[ChromaDB 초기화 실패] error={str(e)}", exc_info=True)
            raise

    async def store_qa(self, doc: QADocument) -> bool:
        """
        QA 문서를 ChromaDB에 저장

        프로세스:
        1. QADocument에서 임베딩 텍스트 생성 (연/월/일 포함)
        2. OpenAI API로 임베딩 생성
        3. 메타데이터와 함께 ChromaDB에 저장
        """
        try:
            logger.info(
                f"[QA 저장 시작] family_id={doc.family_id}, "
                f"member_id={doc.member_id}, role={doc.role_label}"
            )

            # 1. 임베딩 텍스트 생성 (연/월/일 포함)
            embedding_text = doc.to_embedding_text()

            # 2. 임베딩 생성
            response = await self.openai_client.create_embedding(
                text=embedding_text, model=settings.embedding_model
            )
            embedding = response.data[0].embedding

            # 3. 메타데이터 생성
            metadata = doc.to_metadata()

            # 4. 고유 ID 생성: {family_id}_{member_id}_{timestamp_ms}
            timestamp_ms = int(datetime.now().timestamp() * 1000)
            doc_id = f"{doc.family_id}_{doc.member_id}_{timestamp_ms}"

            # 5. ChromaDB에 저장
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[embedding_text],  # 임베딩 텍스트 저장 (연/월/일 포함)
                metadatas=[metadata],
            )

            logger.info(f"[QA 저장 완료] id={doc_id}, 총 데이터={self.collection.count()}개")
            return True

        except Exception as e:
            logger.error(
                f"[QA 저장 실패] family_id={doc.family_id}, "
                f"member_id={doc.member_id}, error={str(e)}",
                exc_info=True,
            )
            return False

    async def search_for_personal(self, member_id: int, query: str, top_k: int = 5) -> list[dict]:
        """
        개인 QA 검색 (member_id 필터)

        프로세스:
        1. 쿼리를 임베딩으로 변환
        2. ChromaDB에서 member_id 필터링하여 검색
        3. 결과 포맷팅 및 반환
        """
        try:
            logger.info(
                f"[개인 검색 시작] member_id={member_id}, "
                f"query='{query[:30]}...', top_k={top_k}"
            )

            # 1. 쿼리 임베딩 생성
            response = await self.openai_client.create_embedding(
                text=query, model=settings.embedding_model
            )
            query_embedding = response.data[0].embedding

            # 2. member_id 필터링 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"member_id": member_id},
                include=["documents", "metadatas", "distances"],
            )

            # 3. 결과 포맷팅
            formatted_results = self._format_search_results(results)

            logger.info(f"[개인 검색 완료] 결과={len(formatted_results)}개")
            return formatted_results

        except Exception as e:
            logger.error(f"[개인 검색 실패] member_id={member_id}, error={str(e)}", exc_info=True)
            return []

    async def search_for_family(self, family_id: int, query: str, top_k: int = 5) -> list[dict]:
        """
        가족 QA 검색 (family_id 필터)

        프로세스:
        1. 쿼리를 임베딩으로 변환
        2. ChromaDB에서 family_id 필터링하여 검색
        3. 결과 포맷팅 및 반환 (member_id 포함)
        """
        try:
            logger.info(
                f"[가족 검색 시작] family_id={family_id}, "
                f"query='{query[:30]}...', top_k={top_k}"
            )

            # 1. 쿼리 임베딩 생성
            response = await self.openai_client.create_embedding(
                text=query, model=settings.embedding_model
            )
            query_embedding = response.data[0].embedding

            # 2. family_id 필터링 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"family_id": family_id},
                include=["documents", "metadatas", "distances"],
            )

            # 3. 결과 포맷팅 (member_id 포함)
            formatted_results = self._format_search_results(results, include_member_id=True)

            logger.info(f"[가족 검색 완료] 결과={len(formatted_results)}개")
            return formatted_results

        except Exception as e:
            logger.error(f"[가족 검색 실패] family_id={family_id}, error={str(e)}", exc_info=True)
            return []

    def _format_search_results(self, results: dict, include_member_id: bool = False) -> list[dict]:
        """
        ChromaDB 검색 결과를 포맷팅

        Args:
            results: ChromaDB query 결과
            include_member_id: member_id를 결과에 포함할지 여부 (가족 검색 시 True)

        Returns:
            List[dict]: 포맷팅된 결과 리스트
        """
        formatted_results = []

        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                document = results["documents"][0][i]

                # 임베딩 텍스트에서 질문/답변 추출
                # 포맷: "YYYY년 M월 D일에 {role_label}이(가) 받은 질문: {question}\n답변: {answer}"
                question, answer = self._parse_embedding_text(document)

                # 거리를 유사도로 변환 (0 = 완전 동일, 2 = 완전 다름)
                # similarity = 1 - (distance / 2)
                similarity = max(0, 1 - distance / 2)

                result = {
                    "question": question,
                    "answer": answer,
                    "role_label": metadata.get("role_label", ""),
                    "answered_at": metadata.get("answered_at", ""),
                    "similarity": round(similarity, 3),
                }

                # 가족 검색 시 member_id 포함
                if include_member_id:
                    result["member_id"] = metadata.get("member_id")

                formatted_results.append(result)

        return formatted_results

    def _parse_embedding_text(self, embedding_text: str) -> tuple[str, str]:
        """
        임베딩 텍스트에서 질문과 답변 추출

        포맷: "YYYY년 M월 D일에 {role_label}이(가) 받은 질문: {question}\n답변: {answer}"

        Args:
            embedding_text: 임베딩 텍스트

        Returns:
            (question, answer) 튜플
        """
        try:
            # "받은 질문:" 이후 부분 추출
            if "받은 질문:" in embedding_text:
                question_part = embedding_text.split("받은 질문:")[1]
                # "\n답변:" 기준으로 질문/답변 분리
                if "\n답변:" in question_part:
                    question, answer = question_part.split("\n답변:")
                    return question.strip(), answer.strip()

            # 파싱 실패 시 전체 텍스트 반환
            return embedding_text, ""

        except Exception as e:
            logger.warning(f"[임베딩 텍스트 파싱 실패] error={str(e)}")
            return embedding_text, ""
