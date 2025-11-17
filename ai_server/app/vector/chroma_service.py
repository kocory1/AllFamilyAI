"""ChromaDB 벡터 서비스 구현체"""
import logging
from typing import List, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.vector.base import VectorService
from app.core.config import settings
from app.adapters.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class ChromaVectorService(VectorService):
    """ChromaDB 기반 벡터 서비스 (파일 기반 Persistent Storage)"""
    
    def __init__(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            # 파일 기반 Persistent Storage
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            # 컬렉션 생성 또는 로드 (이미 있으면 로드)
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={
                    "description": "가족 질문&답변 벡터 DB",
                    "embedding_model": settings.embedding_model
                }
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
    
    async def store_answer(
        self,
        answer_id: str,
        user_id: str,
        question_text: str,
        answer_text: str,
        category: Optional[str] = None,
        sentiment: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        답변을 ChromaDB에 저장
        
        프로세스:
        1. OpenAI API로 답변 텍스트 임베딩 생성
        2. 메타데이터와 함께 ChromaDB에 저장
        3. 자동으로 디스크에 Persist됨
        """
        try:
            logger.info(f"[벡터 저장 시작] answer_id={answer_id}, user_id={user_id}")
            
            # 1. 임베딩 생성
            response = await self.openai_client.create_embedding(
                text=answer_text,
                model=settings.embedding_model
            )
            embedding = response.data[0].embedding
            
            # 2. 메타데이터 구성
            metadata = {
                "user_id": user_id,
                "question": question_text,
                "timestamp": (timestamp or datetime.now()).isoformat()
            }
            
            # 선택적 메타데이터
            if category:
                metadata["category"] = category
            if sentiment is not None:
                metadata["sentiment"] = sentiment
            
            # 3. ChromaDB에 저장
            self.collection.add(
                ids=[answer_id],
                embeddings=[embedding],
                documents=[answer_text],  # 원본 답변!
                metadatas=[metadata]
            )
            
            logger.info(
                f"[벡터 저장 완료] answer_id={answer_id}, "
                f"총 데이터={self.collection.count()}개"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"[벡터 저장 실패] answer_id={answer_id}, error={str(e)}",
                exc_info=True
            )
            return False
    
    async def search_similar_answers(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None
    ) -> List[dict]:
        """
        유사한 과거 답변 검색 (RAG용)
        
        프로세스:
        1. 쿼리를 임베딩으로 변환
        2. ChromaDB에서 벡터 유사도 검색
        3. user_id 필터링 (다른 사용자 데이터 제외)
        4. 결과 포맷팅
        """
        try:
            logger.info(
                f"[벡터 검색 시작] user_id={user_id}, query='{query[:50]}...', top_k={top_k}"
            )
            
            # 1. 쿼리 임베딩 생성
            response = await self.openai_client.create_embedding(
                text=query,
                model=settings.embedding_model
            )
            query_embedding = response.data[0].embedding
            
            # 2. 필터 구성
            where_filter = {"user_id": user_id}
            if category:
                where_filter["category"] = category
            
            # 3. 유사도 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # 4. 결과 포맷팅
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # 거리를 유사도로 변환 (0 = 완전 동일, 2 = 완전 다름)
                    # similarity = 1 - (distance / 2)
                    similarity = max(0, 1 - distance / 2)
                    
                    formatted_results.append({
                        "question": metadata.get("question", ""),
                        "answer": results["documents"][0][i],
                        "category": metadata.get("category"),
                        "timestamp": metadata.get("timestamp"),
                        "similarity": round(similarity, 3)
                    })
            
            logger.info(f"[벡터 검색 완료] 결과={len(formatted_results)}개")
            return formatted_results
            
        except Exception as e:
            logger.error(
                f"[벡터 검색 실패] user_id={user_id}, error={str(e)}",
                exc_info=True
            )
            # 검색 실패 시 빈 리스트 반환 (Graceful degradation)
            return []

