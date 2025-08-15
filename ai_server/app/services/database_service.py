from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
import logging

from app.database.models import (
    QuestionDB, AnswerDB, FamilyMemberDB, 
    ConversationHistoryDB, MCPContextDB
)
from app.models.question import QuestionCategory, QuestionResponse

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    데이터베이스 CRUD 작업을 담당하는 서비스
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    # === 질문 관련 CRUD ===
    async def save_question(
        self,
        question_response: QuestionResponse,
        family_id: str = "default"
    ) -> QuestionDB:
        """
        생성된 질문을 데이터베이스에 저장합니다.
        """
        try:
            question_db = QuestionDB(
                question_uuid=question_response.id,
                content=question_response.content,
                category=question_response.category,
                target_member=question_response.target_member,
                family_context=question_response.family_context,
                mood=question_response.mood,
                created_at=question_response.created_at
            )
            
            self.db.add(question_db)
            await self.db.commit()
            await self.db.refresh(question_db)
            
            logger.info(f"질문 저장 완료 - ID: {question_db.id}, UUID: {question_response.id}")
            return question_db
            
        except Exception as e:
            logger.error(f"질문 저장 실패: {str(e)}")
            await self.db.rollback()
            raise Exception(f"질문 저장에 실패했습니다: {str(e)}")
    
    async def get_question_by_uuid(self, question_uuid: str) -> Optional[QuestionDB]:
        """
        UUID로 질문을 조회합니다.
        """
        try:
            query = select(QuestionDB).where(QuestionDB.question_uuid == question_uuid)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"질문 조회 실패 (UUID: {question_uuid}): {str(e)}")
            return None
    
    async def get_questions_by_member(
        self,
        target_member: str,
        limit: int = 50,
        category: Optional[QuestionCategory] = None
    ) -> List[QuestionDB]:
        """
        특정 가족 구성원의 질문들을 조회합니다.
        """
        try:
            query = select(QuestionDB).where(QuestionDB.target_member == target_member)
            
            if category:
                query = query.where(QuestionDB.category == category)
            
            query = query.order_by(desc(QuestionDB.created_at)).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"가족 구성원 질문 조회 실패 ({target_member}): {str(e)}")
            return []
    
    async def get_recent_questions(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[QuestionDB]:
        """
        최근 질문들을 조회합니다.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = select(QuestionDB).where(
                QuestionDB.created_at >= cutoff_date
            ).order_by(desc(QuestionDB.created_at)).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"최근 질문 조회 실패: {str(e)}")
            return []
    
    # === 답변 관련 CRUD ===
    async def save_answer(
        self,
        question_uuid: str,
        answer_text: str,
        answerer_name: str,
        sentiment_score: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> AnswerDB:
        """
        질문에 대한 답변을 저장합니다.
        """
        try:
            # 질문 조회
            question = await self.get_question_by_uuid(question_uuid)
            if not question:
                raise Exception(f"질문을 찾을 수 없습니다: {question_uuid}")
            
            answer_db = AnswerDB(
                question_id=question.id,
                answer_text=answer_text,
                answerer_name=answerer_name,
                sentiment_score=sentiment_score,
                keywords=keywords or []
            )
            
            self.db.add(answer_db)
            await self.db.commit()
            await self.db.refresh(answer_db)
            
            logger.info(f"답변 저장 완료 - 질문 ID: {question.id}, 답변자: {answerer_name}")
            return answer_db
            
        except Exception as e:
            logger.error(f"답변 저장 실패: {str(e)}")
            await self.db.rollback()
            raise Exception(f"답변 저장에 실패했습니다: {str(e)}")
    
    async def get_answers_by_question(self, question_uuid: str) -> List[AnswerDB]:
        """
        특정 질문의 모든 답변을 조회합니다.
        """
        try:
            query = select(AnswerDB).join(QuestionDB).where(
                QuestionDB.question_uuid == question_uuid
            ).order_by(AnswerDB.created_at)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"질문 답변 조회 실패 ({question_uuid}): {str(e)}")
            return []
    
    async def get_answers_by_member(
        self,
        answerer_name: str,
        limit: int = 50
    ) -> List[AnswerDB]:
        """
        특정 가족 구성원의 모든 답변을 조회합니다.
        """
        try:
            query = select(AnswerDB).where(
                AnswerDB.answerer_name == answerer_name
            ).order_by(desc(AnswerDB.created_at)).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"답변자 답변 조회 실패 ({answerer_name}): {str(e)}")
            return []
    
    # === 가족 구성원 관련 CRUD ===
    async def save_family_member(
        self,
        name: str,
        role: Optional[str] = None,
        age_group: Optional[str] = None,
        interests: Optional[List[str]] = None,
        personality_traits: Optional[List[str]] = None
    ) -> FamilyMemberDB:
        """
        가족 구성원 정보를 저장합니다.
        """
        try:
            # 중복 확인
            existing = await self.get_family_member_by_name(name)
            if existing:
                raise Exception(f"이미 등록된 가족 구성원입니다: {name}")
            
            member_db = FamilyMemberDB(
                name=name,
                role=role,
                age_group=age_group,
                interests=interests or [],
                personality_traits=personality_traits or []
            )
            
            self.db.add(member_db)
            await self.db.commit()
            await self.db.refresh(member_db)
            
            logger.info(f"가족 구성원 저장 완료: {name}")
            return member_db
            
        except Exception as e:
            logger.error(f"가족 구성원 저장 실패: {str(e)}")
            await self.db.rollback()
            raise Exception(f"가족 구성원 저장에 실패했습니다: {str(e)}")
    
    async def get_family_member_by_name(self, name: str) -> Optional[FamilyMemberDB]:
        """
        이름으로 가족 구성원을 조회합니다.
        """
        try:
            query = select(FamilyMemberDB).where(FamilyMemberDB.name == name)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"가족 구성원 조회 실패 ({name}): {str(e)}")
            return None
    
    async def get_all_family_members(self) -> List[FamilyMemberDB]:
        """
        모든 가족 구성원을 조회합니다.
        """
        try:
            query = select(FamilyMemberDB).order_by(FamilyMemberDB.name)
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"전체 가족 구성원 조회 실패: {str(e)}")
            return []
    
    async def update_family_member_preferences(
        self,
        name: str,
        preferred_question_types: List[str]
    ) -> bool:
        """
        가족 구성원의 선호 질문 유형을 업데이트합니다.
        """
        try:
            query = update(FamilyMemberDB).where(
                FamilyMemberDB.name == name
            ).values(
                preferred_question_types=preferred_question_types,
                updated_at=datetime.now()
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"가족 구성원 선호도 업데이트 실패 ({name}): {str(e)}")
            await self.db.rollback()
            return False
    
    # === 대화 기록 관련 CRUD ===
    async def save_conversation_history(
        self,
        question_uuid: str,
        conversation_data: Dict[str, Any],
        participants: List[str],
        conversation_summary: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        topics_discussed: Optional[List[str]] = None
    ) -> ConversationHistoryDB:
        """
        대화 기록을 저장합니다.
        """
        try:
            question = await self.get_question_by_uuid(question_uuid)
            if not question:
                raise Exception(f"질문을 찾을 수 없습니다: {question_uuid}")
            
            conversation = ConversationHistoryDB(
                question_id=question.id,
                conversation_data=conversation_data,
                participants=participants,
                conversation_summary=conversation_summary,
                emotional_tone=emotional_tone,
                topics_discussed=topics_discussed or []
            )
            
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            
            logger.info(f"대화 기록 저장 완료 - 질문 ID: {question.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"대화 기록 저장 실패: {str(e)}")
            await self.db.rollback()
            raise Exception(f"대화 기록 저장에 실패했습니다: {str(e)}")
    
    async def get_conversation_history(
        self,
        family_id: str = "default",
        limit: int = 50
    ) -> List[ConversationHistoryDB]:
        """
        대화 기록을 조회합니다.
        """
        try:
            query = select(ConversationHistoryDB).options(
                selectinload(ConversationHistoryDB.question)
            ).order_by(desc(ConversationHistoryDB.created_at)).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"대화 기록 조회 실패: {str(e)}")
            return []
    
    # === 통계 및 분석 ===
    async def get_question_statistics(self) -> Dict[str, Any]:
        """
        질문 통계를 조회합니다.
        """
        try:
            # 전체 질문 수
            total_questions = await self.db.execute(select(func.count(QuestionDB.id)))
            total_count = total_questions.scalar()
            
            # 카테고리별 질문 수
            category_stats = await self.db.execute(
                select(QuestionDB.category, func.count(QuestionDB.id))
                .group_by(QuestionDB.category)
            )
            category_counts = {row[0].value: row[1] for row in category_stats.all()}
            
            # 가족 구성원별 질문 수
            member_stats = await self.db.execute(
                select(QuestionDB.target_member, func.count(QuestionDB.id))
                .group_by(QuestionDB.target_member)
            )
            member_counts = {row[0]: row[1] for row in member_stats.all()}
            
            # 최근 7일간 질문 수
            week_ago = datetime.now() - timedelta(days=7)
            recent_questions = await self.db.execute(
                select(func.count(QuestionDB.id))
                .where(QuestionDB.created_at >= week_ago)
            )
            recent_count = recent_questions.scalar()
            
            return {
                "total_questions": total_count,
                "category_distribution": category_counts,
                "member_distribution": member_counts,
                "recent_week_count": recent_count,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"질문 통계 조회 실패: {str(e)}")
            return {}
    
    async def get_answer_statistics(self) -> Dict[str, Any]:
        """
        답변 통계를 조회합니다.
        """
        try:
            # 전체 답변 수
            total_answers = await self.db.execute(select(func.count(AnswerDB.id)))
            total_count = total_answers.scalar()
            
            # 답변자별 답변 수
            answerer_stats = await self.db.execute(
                select(AnswerDB.answerer_name, func.count(AnswerDB.id))
                .group_by(AnswerDB.answerer_name)
            )
            answerer_counts = {row[0]: row[1] for row in answerer_stats.all()}
            
            # 감정별 답변 수
            sentiment_stats = await self.db.execute(
                select(AnswerDB.sentiment_score, func.count(AnswerDB.id))
                .where(AnswerDB.sentiment_score.is_not(None))
                .group_by(AnswerDB.sentiment_score)
            )
            sentiment_counts = {row[0]: row[1] for row in sentiment_stats.all()}
            
            # 평균 답변 길이
            avg_length = await self.db.execute(
                select(func.avg(func.length(AnswerDB.answer_text)))
            )
            average_length = avg_length.scalar()
            
            return {
                "total_answers": total_count,
                "answerer_distribution": answerer_counts,
                "sentiment_distribution": sentiment_counts,
                "average_answer_length": float(average_length) if average_length else 0,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"답변 통계 조회 실패: {str(e)}")
            return {}
    
    # === 데이터 정리 ===
    async def cleanup_old_data(self, days_to_keep: int = 365) -> Dict[str, int]:
        """
        오래된 데이터를 정리합니다.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 오래된 대화 기록 삭제
            old_conversations = await self.db.execute(
                delete(ConversationHistoryDB)
                .where(ConversationHistoryDB.created_at < cutoff_date)
            )
            
            # 오래된 MCP 컨텍스트 삭제
            old_contexts = await self.db.execute(
                delete(MCPContextDB)
                .where(MCPContextDB.last_updated < cutoff_date)
            )
            
            await self.db.commit()
            
            return {
                "deleted_conversations": old_conversations.rowcount,
                "deleted_contexts": old_contexts.rowcount,
                "cleanup_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"데이터 정리 실패: {str(e)}")
            await self.db.rollback()
            return {"error": str(e)}