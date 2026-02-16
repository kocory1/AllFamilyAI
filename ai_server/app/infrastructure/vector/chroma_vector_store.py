"""
ChromaDB 기반 벡터 스토어 (Infrastructure)

Clean Architecture:
- VectorStorePort 인터페이스 구현
- Domain Entity 입출력
- ChromaDB 구체 구현 세부사항 캡슐화

ChromaDB Python 클라이언트는 동기 API이므로, async 메서드 내에서는
asyncio.to_thread()로 스레드 풀에서 실행해 이벤트 루프 블로킹을 방지함.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime

from app.domain.entities.qa_document import QADocument
from app.domain.ports.vector_store_port import VectorStorePort

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStorePort):
    """
    ChromaDB 기반 벡터 스토어 (Port 구현)

    책임:
    - Domain Entity → ChromaDB 형식 변환
    - 임베딩 생성
    - ChromaDB 저장/검색
    - ChromaDB 형식 → Domain Entity 변환
    """

    def __init__(self, openai_client, collection):
        """
        Args:
            openai_client: OpenAI 클라이언트 (임베딩용)
            collection: ChromaDB Collection
        """
        self.openai_client = openai_client
        self.collection = collection
        logger.info("[ChromaVectorStore] 초기화 완료")

    async def store(self, doc: QADocument) -> bool:
        """
        Domain Entity 저장 (Port 구현)

        Args:
            doc: QADocument Domain Entity

        Returns:
            저장 성공 여부
        """
        try:
            logger.info(
                f"[ChromaVectorStore] 저장 시작: family_id={doc.family_id}, "
                f"member_id={doc.member_id}"
            )

            # Domain Entity → 임베딩 텍스트
            embedding_text = self._to_embedding_text(doc)

            # 임베딩 생성
            response = await self.openai_client.create_embedding(embedding_text)
            embedding = response.data[0].embedding

            # 메타데이터 생성
            metadata = {
                "family_id": doc.family_id,
                "member_id": doc.member_id,
                "role_label": doc.role_label,
                "answered_at": doc.answered_at.isoformat(),
            }

            # ChromaDB 저장 (동기 API → 스레드 풀에서 실행)
            doc_id = f"{doc.family_id}_{doc.member_id}_{int(datetime.now().timestamp() * 1000)}"
            await asyncio.to_thread(
                self.collection.add,
                ids=[doc_id],
                embeddings=[embedding],
                documents=[embedding_text],
                metadatas=[metadata],
            )

            logger.info(f"[ChromaVectorStore] 저장 완료: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 저장 실패: {e}")
            return False

    async def search_by_member(
        self, member_id: str, query_doc: QADocument, top_k: int = 5
    ) -> list[QADocument]:
        """
        개인 QA 검색 (Port 구현)

        Args:
            member_id: 멤버 ID (UUID)

        Returns:
            Domain Entity 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_text = self._to_embedding_text(query_doc)
            response = await self.openai_client.create_embedding(query_text)
            query_embedding = response.data[0].embedding

            # ChromaDB 검색 (동기 API → 스레드 풀에서 실행)
            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"member_id": member_id},
                include=["documents", "metadatas"],
            )

            # ChromaDB 결과 → Domain Entity 변환
            entities = self._to_domain_entities(results)

            logger.info(
                f"[ChromaVectorStore] 검색 완료: member_id={member_id}, " f"결과={len(entities)}개"
            )

            return entities

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 검색 실패: {e}")
            return []

    async def search_by_family(
        self, family_id: str, query_doc: QADocument, top_k: int = 5
    ) -> list[QADocument]:
        """가족 QA 검색 (Port 구현)"""
        try:
            query_text = self._to_embedding_text(query_doc)
            response = await self.openai_client.create_embedding(query_text)
            query_embedding = response.data[0].embedding

            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"family_id": family_id},
                include=["documents", "metadatas"],
            )

            entities = self._to_domain_entities(results)

            logger.info(
                f"[ChromaVectorStore] 검색 완료: family_id={family_id}, " f"결과={len(entities)}개"
            )

            return entities

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 검색 실패: {e}")
            return []

    async def search_similar_questions(
        self,
        question_text: str,
        member_id: str,
    ) -> float:
        """생성된 질문의 유사도 검색 (Port 구현)"""
        try:
            # 질문 텍스트로 임베딩 생성
            response = await self.openai_client.create_embedding(question_text)
            query_embedding = response.data[0].embedding

            # ChromaDB 검색 (유사도 포함, 동기 API → 스레드 풀에서 실행)
            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=1,
                where={"member_id": member_id},
                include=["distances"],
            )

            # 결과가 없으면 유사도 0
            if not results["ids"] or not results["ids"][0]:
                return 0.0

            # ChromaDB distance → similarity 변환 (코사인 거리)
            # distance = 1 - similarity, so similarity = 1 - distance
            distance = results["distances"][0][0]
            similarity = 1 - distance

            logger.info(
                f"[ChromaVectorStore] 유사도 검색: question={question_text[:30]}..., "
                f"similarity={similarity:.2f}"
            )

            return similarity

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 유사도 검색 실패: {e}")
            return 0.0

    async def get_recent_questions_by_member(
        self,
        member_id: str,
        limit: int = 2,
    ) -> list[QADocument]:
        """
        멤버별 최근 질문 조회 (Port 구현)

        Args:
            member_id: 멤버 ID (UUID)
            limit: 반환할 최대 결과 수

        Returns:
            최근 QADocument 리스트 (answered_at 내림차순)
        """
        try:
            # ChromaDB에서 해당 멤버의 모든 문서 조회 (동기 API → 스레드 풀에서 실행)
            # Note: ChromaDB는 메타데이터 정렬을 지원하지 않으므로 Python에서 정렬
            results = await asyncio.to_thread(
                self.collection.get,
                where={"member_id": member_id},
                include=["documents", "metadatas"],
            )

            if not results["ids"]:
                logger.info(f"[ChromaVectorStore] 최근 질문 조회: member_id={member_id}, 결과=0개")
                return []

            # Domain Entity 변환
            entities = []
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                document = results["documents"][i]

                question, answer = self._parse_embedding_text(document)

                entity = QADocument(
                    family_id=metadata["family_id"],
                    member_id=metadata["member_id"],
                    role_label=metadata["role_label"],
                    question=question,
                    answer=answer,
                    answered_at=datetime.fromisoformat(metadata["answered_at"]),
                )
                entities.append(entity)

            # answered_at 기준 내림차순 정렬 후 limit 적용
            entities.sort(key=lambda x: x.answered_at, reverse=True)
            recent_entities = entities[:limit]

            logger.info(
                f"[ChromaVectorStore] 최근 질문 조회: member_id={member_id}, "
                f"전체={len(entities)}개, 반환={len(recent_entities)}개"
            )

            return recent_entities

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 최근 질문 조회 실패: {e}")
            return []

    async def get_recent_questions_by_family(
        self,
        family_id: str,
        limit_per_member: int = 3,
    ) -> list[QADocument]:
        """
        가족 전체의 최근 질문 조회 (멤버별 N개씩)

        Args:
            family_id: 가족 ID (UUID)
            limit_per_member: 멤버당 최대 질문 수 (기본값: 3)

        Returns:
            최근 QADocument 리스트 (각 멤버별 limit_per_member개)
        """
        try:
            # ChromaDB에서 해당 가족의 모든 문서 조회 (동기 API → 스레드 풀에서 실행)
            results = await asyncio.to_thread(
                self.collection.get,
                where={"family_id": family_id},
                include=["documents", "metadatas"],
            )

            if not results["ids"]:
                logger.info(
                    f"[ChromaVectorStore] 가족 최근 질문 조회: family_id={family_id}, 결과=0개"
                )
                return []

            # Domain Entity 변환
            all_entities: list[QADocument] = []
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                document = results["documents"][i]

                question, answer = self._parse_embedding_text(document)

                entity = QADocument(
                    family_id=metadata["family_id"],
                    member_id=metadata["member_id"],
                    role_label=metadata["role_label"],
                    question=question,
                    answer=answer,
                    answered_at=datetime.fromisoformat(metadata["answered_at"]),
                )
                all_entities.append(entity)

            # 멤버별로 그룹화 후 각각 최근 N개씩 추출
            member_groups: dict[str, list[QADocument]] = defaultdict(list)
            for entity in all_entities:
                member_groups[entity.member_id].append(entity)

            # 각 멤버별 최근 N개 추출
            recent_entities: list[QADocument] = []
            for _member_id, entities in member_groups.items():
                # 시간순 내림차순 정렬
                entities.sort(key=lambda x: x.answered_at, reverse=True)
                recent_entities.extend(entities[:limit_per_member])

            logger.info(
                f"[ChromaVectorStore] 가족 최근 질문 조회: family_id={family_id}, "
                f"멤버={len(member_groups)}명, 반환={len(recent_entities)}개"
            )

            return recent_entities

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 가족 최근 질문 조회 실패: {e}")
            return []

    async def get_qa_by_family_in_range(
        self,
        family_id: str,
        start: datetime,
        end: datetime,
    ) -> list[QADocument]:
        """
        가족 QA를 기간으로 조회 (주간/월간 요약용)

        ChromaDB는 메타데이터 범위 쿼리를 지원하지 않으므로
        family_id로 전체 조회 후 Python에서 answered_at 필터링.
        """
        try:
            # ChromaDB 기간 조회 (동기 API → 스레드 풀에서 실행)
            results = await asyncio.to_thread(
                self.collection.get,
                where={"family_id": family_id},
                include=["documents", "metadatas"],
            )

            if not results["ids"]:
                logger.info(f"[ChromaVectorStore] 기간 조회: family_id={family_id}, 결과=0개")
                return []

            entities: list[QADocument] = []
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                document = results["documents"][i]
                question, answer = self._parse_embedding_text(document)
                answered_at = datetime.fromisoformat(metadata["answered_at"])
                if start <= answered_at <= end:
                    entities.append(
                        QADocument(
                            family_id=metadata["family_id"],
                            member_id=metadata["member_id"],
                            role_label=metadata["role_label"],
                            question=question,
                            answer=answer,
                            answered_at=answered_at,
                        )
                    )

            entities.sort(key=lambda x: x.answered_at)
            logger.info(
                f"[ChromaVectorStore] 기간 조회: family_id={family_id}, "
                f"[{start.date()}~{end.date()}], 반환={len(entities)}개"
            )
            return entities

        except Exception as e:
            logger.error(f"[ChromaVectorStore] 기간 조회 실패: {e}")
            return []

    async def delete_by_member(self, member_id: str) -> int:
        """
        해당 멤버의 ChromaDB 이력 전부 삭제 (방법 A: get → delete by ids).

        Args:
            member_id: 멤버 ID (UUID)

        Returns:
            삭제된 문서 수. 0이면 해당 member_id로 저장된 문서가 없음.
        """
        try:
            # 해당 멤버 문서 id만 조회 (본문 불필요)
            results = await asyncio.to_thread(
                self.collection.get,
                where={"member_id": member_id},
                include=[],
            )
            ids = results.get("ids") or []
            if not ids:
                logger.info(f"[ChromaVectorStore] 삭제 대상 없음: member_id={member_id}")
                return 0
            await asyncio.to_thread(self.collection.delete, ids=ids)
            logger.info(
                f"[ChromaVectorStore] 멤버 이력 삭제 완료: member_id={member_id}, "
                f"삭제={len(ids)}개"
            )
            return len(ids)
        except Exception as e:
            logger.error(f"[ChromaVectorStore] delete_by_member 실패: {e}", exc_info=True)
            raise

    # === Private: Infrastructure 세부사항 ===

    def _to_embedding_text(self, doc: QADocument) -> str:
        """Domain Entity → 임베딩 텍스트"""
        year, month, day = doc.get_date_parts()
        return (
            f"{year}년 {month}월 {day}일에 {doc.role_label}이(가) 받은 질문: {doc.question}\n"
            f"답변: {doc.answer}"
        )

    def _to_domain_entities(self, results: dict) -> list[QADocument]:
        """ChromaDB 결과 → Domain Entity 리스트"""
        entities = []

        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]

                # 임베딩 텍스트 파싱
                question, answer = self._parse_embedding_text(document)

                entity = QADocument(
                    family_id=metadata["family_id"],
                    member_id=metadata["member_id"],
                    role_label=metadata["role_label"],
                    question=question,
                    answer=answer,
                    answered_at=datetime.fromisoformat(metadata["answered_at"]),
                )
                entities.append(entity)

        return entities

    def _parse_embedding_text(self, text: str) -> tuple[str, str]:
        """임베딩 텍스트 파싱 → (질문, 답변)"""
        try:
            if "받은 질문:" in text and "\n답변:" in text:
                question_part = text.split("받은 질문:")[1]
                question, answer = question_part.split("\n답변:")
                return question.strip(), answer.strip()
        except Exception as e:
            logger.warning(f"[파싱 실패] {e}")

        return text, ""
