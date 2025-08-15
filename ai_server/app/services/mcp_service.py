import json
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from app.database.models import (
    QuestionDB, AnswerDB, FamilyMemberDB, 
    ConversationHistoryDB, MCPContextDB
)
from app.models.question import QuestionCategory
from app.core.config import settings

logger = logging.getLogger(__name__)

class MCPService:
    """
    Model Context Protocol 서비스
    과거 질문과 답변 데이터를 분석하여 컨텍스트를 제공하는 서비스
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.context_window = settings.mcp_context_window
        self.similarity_threshold = settings.mcp_similarity_threshold
        
    async def analyze_family_patterns(self, family_id: str, target_member: str) -> Dict[str, Any]:
        """
        가족의 질문-답변 패턴을 분석합니다.
        """
        try:
            # 최근 대화 기록 가져오기
            recent_conversations = await self._get_recent_conversations(family_id, target_member)
            
            # 답변 패턴 분석
            answer_patterns = await self._analyze_answer_patterns(target_member)
            
            # 선호 카테고리 분석
            preferred_categories = await self._analyze_preferred_categories(target_member)
            
            # 감정 톤 분석
            emotional_patterns = await self._analyze_emotional_patterns(target_member)
            
            # 시간대별 활동 패턴
            time_patterns = await self._analyze_time_patterns(target_member)
            
            analysis_result = {
                "target_member": target_member,
                "analysis_timestamp": datetime.now().isoformat(),
                "recent_conversations": recent_conversations,
                "answer_patterns": answer_patterns,
                "preferred_categories": preferred_categories,
                "emotional_patterns": emotional_patterns,
                "time_patterns": time_patterns,
                "recommendations": await self._generate_recommendations(
                    target_member, answer_patterns, preferred_categories, emotional_patterns
                )
            }
            
            # MCP 컨텍스트 저장
            await self._save_mcp_context(family_id, "family_analysis", analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"가족 패턴 분석 실패: {str(e)}")
            raise Exception(f"패턴 분석에 실패했습니다: {str(e)}")
    
    async def get_contextual_question_data(self, target_member: str, category: Optional[QuestionCategory] = None) -> Dict[str, Any]:
        """
        새로운 질문 생성을 위한 컨텍스트 데이터를 제공합니다.
        """
        try:
            # 최근 질문들 중 중복 방지를 위한 데이터
            recent_questions = await self._get_recent_questions(target_member, limit=20)
            
            # 답변 빈도가 높은 주제들
            popular_topics = await self._get_popular_topics(target_member)
            
            # 답변이 부족한 카테고리
            underexplored_categories = await self._get_underexplored_categories(target_member)
            
            # 최근 답변의 감정 톤
            recent_emotional_state = await self._get_recent_emotional_state(target_member)
            
            # 가족 구성원과의 연관성 분석
            family_connections = await self._analyze_family_connections(target_member)
            
            context_data = {
                "target_member": target_member,
                "requested_category": category.value if category else None,
                "recent_questions": recent_questions,
                "popular_topics": popular_topics,
                "underexplored_categories": underexplored_categories,
                "recent_emotional_state": recent_emotional_state,
                "family_connections": family_connections,
                "avoidance_keywords": await self._get_avoidance_keywords(target_member),
                "preferred_question_styles": await self._get_preferred_question_styles(target_member)
            }
            
            return context_data
            
        except Exception as e:
            logger.error(f"컨텍스트 데이터 생성 실패: {str(e)}")
            raise Exception(f"컨텍스트 데이터 생성에 실패했습니다: {str(e)}")
    
    async def _get_recent_conversations(self, family_id: str, target_member: str, limit: int = 10) -> List[Dict]:
        """최근 대화 기록을 가져옵니다."""
        query = select(ConversationHistoryDB).join(QuestionDB).where(
            and_(
                QuestionDB.target_member == target_member,
                ConversationHistoryDB.created_at >= datetime.now() - timedelta(days=30)
            )
        ).order_by(desc(ConversationHistoryDB.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        return [
            {
                "id": conv.id,
                "question_content": conv.question.content if conv.question else None,
                "conversation_summary": conv.conversation_summary,
                "emotional_tone": conv.emotional_tone,
                "topics_discussed": conv.topics_discussed,
                "created_at": conv.created_at.isoformat()
            }
            for conv in conversations
        ]
    
    async def _analyze_answer_patterns(self, target_member: str) -> Dict[str, Any]:
        """답변 패턴을 분석합니다."""
        query = select(AnswerDB).join(QuestionDB).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(AnswerDB.created_at)).limit(50)
        
        result = await self.db.execute(query)
        answers = result.scalars().all()
        
        if not answers:
            return {"pattern_type": "insufficient_data", "message": "분석할 답변이 부족합니다."}
        
        # 답변 길이 분석
        answer_lengths = [len(answer.answer_text) for answer in answers]
        avg_length = sum(answer_lengths) / len(answer_lengths)
        
        # 감정 분석
        sentiments = [answer.sentiment_score for answer in answers if answer.sentiment_score]
        sentiment_distribution = {}
        for sentiment in sentiments:
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # 키워드 빈도 분석
        all_keywords = []
        for answer in answers:
            if answer.keywords:
                all_keywords.extend(answer.keywords)
        
        keyword_frequency = {}
        for keyword in all_keywords:
            keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
        
        # 상위 키워드 추출
        top_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_answers": len(answers),
            "average_answer_length": avg_length,
            "answer_length_category": "short" if avg_length < 50 else "medium" if avg_length < 150 else "long",
            "sentiment_distribution": sentiment_distribution,
            "dominant_sentiment": max(sentiment_distribution.items(), key=lambda x: x[1])[0] if sentiment_distribution else None,
            "top_keywords": top_keywords,
            "answer_frequency": len(answers)  # 전체 답변 수
        }
    
    async def _analyze_preferred_categories(self, target_member: str) -> List[Dict]:
        """선호 카테고리를 분석합니다."""
        query = select(
            QuestionDB.category,
            func.count(AnswerDB.id).label('answer_count'),
            func.avg(func.length(AnswerDB.answer_text)).label('avg_response_length')
        ).join(AnswerDB).where(
            QuestionDB.target_member == target_member
        ).group_by(QuestionDB.category).order_by(desc('answer_count'))
        
        result = await self.db.execute(query)
        category_stats = result.all()
        
        return [
            {
                "category": stat.category.value,
                "answer_count": stat.answer_count,
                "avg_response_length": float(stat.avg_response_length) if stat.avg_response_length else 0,
                "engagement_level": "high" if stat.answer_count > 5 else "medium" if stat.answer_count > 2 else "low"
            }
            for stat in category_stats
        ]
    
    async def _analyze_emotional_patterns(self, target_member: str) -> Dict[str, Any]:
        """감정 패턴을 분석합니다."""
        query = select(ConversationHistoryDB).join(QuestionDB).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(ConversationHistoryDB.created_at)).limit(20)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        emotional_tones = [conv.emotional_tone for conv in conversations if conv.emotional_tone]
        
        if not emotional_tones:
            return {"pattern": "neutral", "consistency": "unknown"}
        
        tone_frequency = {}
        for tone in emotional_tones:
            tone_frequency[tone] = tone_frequency.get(tone, 0) + 1
        
        dominant_tone = max(tone_frequency.items(), key=lambda x: x[1])[0]
        consistency = "high" if tone_frequency[dominant_tone] > len(emotional_tones) * 0.7 else "medium" if tone_frequency[dominant_tone] > len(emotional_tones) * 0.4 else "low"
        
        return {
            "dominant_tone": dominant_tone,
            "tone_distribution": tone_frequency,
            "consistency": consistency,
            "recent_trend": emotional_tones[:5] if len(emotional_tones) >= 5 else emotional_tones
        }
    
    async def _analyze_time_patterns(self, target_member: str) -> Dict[str, Any]:
        """시간대별 활동 패턴을 분석합니다."""
        query = select(AnswerDB).join(QuestionDB).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(AnswerDB.created_at)).limit(100)
        
        result = await self.db.execute(query)
        answers = result.scalars().all()
        
        if not answers:
            return {"pattern": "insufficient_data"}
        
        # 시간대별 답변 분포
        hour_distribution = {}
        weekday_distribution = {}
        
        for answer in answers:
            hour = answer.created_at.hour
            weekday = answer.created_at.weekday()
            
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            weekday_distribution[weekday] = weekday_distribution.get(weekday, 0) + 1
        
        # 가장 활발한 시간대와 요일
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None
        peak_weekday = max(weekday_distribution.items(), key=lambda x: x[1])[0] if weekday_distribution else None
        
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        
        return {
            "peak_hour": peak_hour,
            "peak_weekday": weekday_names[peak_weekday] if peak_weekday is not None else None,
            "hour_distribution": hour_distribution,
            "weekday_distribution": weekday_distribution,
            "activity_level": "high" if len(answers) > 50 else "medium" if len(answers) > 20 else "low"
        }
    
    async def _generate_recommendations(self, target_member: str, answer_patterns: Dict, preferred_categories: List[Dict], emotional_patterns: Dict) -> List[str]:
        """분석 결과를 바탕으로 추천사항을 생성합니다."""
        recommendations = []
        
        # 답변 길이 기반 추천
        if answer_patterns.get("answer_length_category") == "short":
            recommendations.append("짧고 간단한 답변을 선호하시므로, 구체적이고 명확한 질문을 추천합니다.")
        elif answer_patterns.get("answer_length_category") == "long":
            recommendations.append("상세한 답변을 선호하시므로, 깊이 있는 사고를 유도하는 질문을 추천합니다.")
        
        # 카테고리 기반 추천
        if preferred_categories:
            top_category = preferred_categories[0]["category"]
            recommendations.append(f"'{top_category}' 카테고리에 높은 관심을 보이시므로, 관련 질문을 더 자주 제공하겠습니다.")
        
        # 감정 패턴 기반 추천
        if emotional_patterns.get("dominant_tone"):
            tone = emotional_patterns["dominant_tone"]
            if tone == "positive":
                recommendations.append("긍정적인 분위기의 대화를 선호하시므로, 밝고 희망적인 질문을 추천합니다.")
            elif tone == "reflective":
                recommendations.append("성찰적인 대화를 즐기시므로, 깊이 있는 생각을 유도하는 질문을 추천합니다.")
        
        # 기본 추천사항
        if not recommendations:
            recommendations.append("더 다양한 주제의 질문으로 대화의 폭을 넓혀보시는 것을 추천합니다.")
        
        return recommendations
    
    async def _get_recent_questions(self, target_member: str, limit: int = 20) -> List[str]:
        """최근 질문들을 가져옵니다."""
        query = select(QuestionDB.content).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(QuestionDB.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        return [q for q in questions]
    
    async def _get_popular_topics(self, target_member: str) -> List[Dict]:
        """답변 빈도가 높은 주제들을 가져옵니다."""
        query = select(
            QuestionDB.category,
            func.count(AnswerDB.id).label('count')
        ).join(AnswerDB).where(
            QuestionDB.target_member == target_member
        ).group_by(QuestionDB.category).order_by(desc('count')).limit(5)
        
        result = await self.db.execute(query)
        topics = result.all()
        
        return [
            {"category": topic.category.value, "answer_count": topic.count}
            for topic in topics
        ]
    
    async def _get_underexplored_categories(self, target_member: str) -> List[str]:
        """답변이 부족한 카테고리를 가져옵니다."""
        # 모든 카테고리에 대한 질문 수 조회
        query = select(
            QuestionDB.category,
            func.count(QuestionDB.id).label('question_count'),
            func.count(AnswerDB.id).label('answer_count')
        ).outerjoin(AnswerDB).where(
            QuestionDB.target_member == target_member
        ).group_by(QuestionDB.category)
        
        result = await self.db.execute(query)
        category_stats = result.all()
        
        # 질문 대비 답변 비율이 낮은 카테고리 찾기
        underexplored = []
        for stat in category_stats:
            answer_ratio = stat.answer_count / stat.question_count if stat.question_count > 0 else 0
            if answer_ratio < 0.5 or stat.answer_count < 2:  # 답변률 50% 미만 또는 답변 2개 미만
                underexplored.append(stat.category.value)
        
        return underexplored
    
    async def _get_recent_emotional_state(self, target_member: str) -> str:
        """최근 감정 상태를 가져옵니다."""
        query = select(ConversationHistoryDB.emotional_tone).join(QuestionDB).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(ConversationHistoryDB.created_at)).limit(3)
        
        result = await self.db.execute(query)
        recent_tones = result.scalars().all()
        
        if not recent_tones:
            return "neutral"
        
        # 최근 3개 대화의 감정 톤 중 가장 빈번한 것
        tone_count = {}
        for tone in recent_tones:
            if tone:
                tone_count[tone] = tone_count.get(tone, 0) + 1
        
        return max(tone_count.items(), key=lambda x: x[1])[0] if tone_count else "neutral"
    
    async def _analyze_family_connections(self, target_member: str) -> Dict[str, Any]:
        """가족 구성원과의 연관성을 분석합니다."""
        # 다른 가족 구성원이 언급된 답변들 찾기
        query = select(AnswerDB).join(QuestionDB).where(
            QuestionDB.target_member == target_member
        ).limit(50)
        
        result = await self.db.execute(query)
        answers = result.scalars().all()
        
        # 간단한 가족 관련 키워드 분석 (실제로는 더 정교한 NLP 분석 필요)
        family_keywords = ["엄마", "아빠", "형", "누나", "동생", "언니", "오빠", "할머니", "할아버지", "가족"]
        
        family_mentions = {}
        for answer in answers:
            if answer.keywords:
                for keyword in answer.keywords:
                    if keyword in family_keywords:
                        family_mentions[keyword] = family_mentions.get(keyword, 0) + 1
        
        return {
            "family_mentions": family_mentions,
            "connection_strength": "high" if sum(family_mentions.values()) > 10 else "medium" if sum(family_mentions.values()) > 5 else "low"
        }
    
    async def _get_avoidance_keywords(self, target_member: str) -> List[str]:
        """회피하는 키워드들을 가져옵니다."""
        # 질문은 있지만 답변이 없거나 매우 짧은 답변의 키워드들
        query = select(QuestionDB).outerjoin(AnswerDB).where(
            and_(
                QuestionDB.target_member == target_member,
                or_(
                    AnswerDB.id.is_(None),  # 답변이 없음
                    func.length(AnswerDB.answer_text) < 10  # 매우 짧은 답변
                )
            )
        ).limit(20)
        
        result = await self.db.execute(query)
        unanswered_questions = result.scalars().all()
        
        # 간단한 키워드 추출 (실제로는 더 정교한 NLP 분석 필요)
        avoidance_keywords = []
        sensitive_topics = ["돈", "성적", "실패", "화", "싸움", "이별", "병", "죽음"]
        
        for question in unanswered_questions:
            for topic in sensitive_topics:
                if topic in question.content:
                    avoidance_keywords.append(topic)
        
        return list(set(avoidance_keywords))
    
    async def _get_preferred_question_styles(self, target_member: str) -> Dict[str, Any]:
        """선호하는 질문 스타일을 분석합니다."""
        query = select(QuestionDB, AnswerDB).join(AnswerDB).where(
            QuestionDB.target_member == target_member
        ).order_by(desc(func.length(AnswerDB.answer_text))).limit(10)
        
        result = await self.db.execute(query)
        answered_questions = result.all()
        
        if not answered_questions:
            return {"style": "general", "preference": "unknown"}
        
        # 질문 길이와 답변 길이의 상관관계 분석
        question_lengths = [len(q.QuestionDB.content) for q in answered_questions]
        answer_lengths = [len(q.AnswerDB.answer_text) for q in answered_questions]
        
        avg_q_length = sum(question_lengths) / len(question_lengths)
        avg_a_length = sum(answer_lengths) / len(answer_lengths)
        
        # 스타일 분류
        if avg_q_length < 30 and avg_a_length > 50:
            style = "prefers_simple_questions"
        elif avg_q_length > 50 and avg_a_length > 100:
            style = "prefers_detailed_questions"
        else:
            style = "balanced"
        
        return {
            "style": style,
            "avg_question_length": avg_q_length,
            "avg_answer_length": avg_a_length,
            "engagement_ratio": avg_a_length / avg_q_length if avg_q_length > 0 else 0
        }
    
    async def _save_mcp_context(self, family_id: str, context_type: str, context_data: Dict[str, Any]):
        """MCP 컨텍스트를 저장합니다."""
        try:
            mcp_context = MCPContextDB(
                family_id=family_id,
                context_type=context_type,
                context_data=context_data,
                confidence_score="high",  # 실제로는 분석 품질에 따라 동적으로 설정
                expiry_date=datetime.now() + timedelta(days=30)  # 30일 후 만료
            )
            
            self.db.add(mcp_context)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"MCP 컨텍스트 저장 실패: {str(e)}")
            await self.db.rollback()