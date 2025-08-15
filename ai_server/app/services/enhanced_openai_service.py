import openai
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.question import QuestionCategory, QuestionResponse
from app.services.mcp_service import MCPService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class EnhancedOpenAIService(OpenAIService):
    """
    MCP(Model Context Protocol)를 활용한 강화된 OpenAI 서비스
    과거 질문-답변 데이터를 분석하여 더 개인화된 질문을 생성합니다.
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__()
        self.db = db_session
        self.mcp_service = MCPService(db_session)
    
    async def generate_contextual_question(
        self,
        target_member: str,
        family_id: str = "default",
        category: Optional[QuestionCategory] = None,
        family_context: Optional[str] = None,
        mood: Optional[str] = None,
        use_mcp: bool = True
    ) -> QuestionResponse:
        """
        MCP 컨텍스트를 활용하여 개인화된 질문을 생성합니다.
        """
        try:
            if use_mcp:
                # MCP를 통한 컨텍스트 데이터 수집
                context_data = await self.mcp_service.get_contextual_question_data(
                    target_member=target_member,
                    category=category
                )
                
                # 가족 패턴 분석
                family_analysis = await self.mcp_service.analyze_family_patterns(
                    family_id=family_id,
                    target_member=target_member
                )
                
                # MCP 기반 프롬프트 구성
                prompt = await self._build_mcp_enhanced_prompt(
                    target_member=target_member,
                    category=category,
                    family_context=family_context,
                    mood=mood,
                    context_data=context_data,
                    family_analysis=family_analysis
                )
            else:
                # 기존 방식 사용
                prompt = self._build_prompt(target_member, category, family_context, mood)
            
            # OpenAI API 호출
            response = await self._call_enhanced_openai(prompt, use_mcp)
            
            # 응답 파싱
            question_content = self._parse_response(response)
            
            # QuestionResponse 객체 생성
            question = QuestionResponse(
                id=str(uuid.uuid4()),
                content=question_content,
                category=category or QuestionCategory.FAMILY,
                target_member=target_member,
                created_at=datetime.now(),
                family_context=family_context,
                mood=mood
            )
            
            logger.info(f"MCP 기반 질문 생성 완료: {question_content[:50]}...")
            return question
            
        except Exception as e:
            logger.error(f"컨텍스트 기반 질문 생성 중 오류 발생: {str(e)}")
            # MCP 실패 시 기존 방식으로 폴백
            logger.info("기존 방식으로 폴백하여 질문 생성 시도")
            return await super().generate_question(target_member, category, family_context, mood)
    
    async def _build_mcp_enhanced_prompt(
        self,
        target_member: str,
        category: Optional[QuestionCategory] = None,
        family_context: Optional[str] = None,
        mood: Optional[str] = None,
        context_data: Dict[str, Any] = None,
        family_analysis: Dict[str, Any] = None
    ) -> str:
        """
        MCP 데이터를 활용한 강화된 프롬프트를 구성합니다.
        """
        base_prompt = f"""
당신은 가족 유대감을 증진시키는 AI 질문 생성 전문가입니다.
{target_member}님을 위한 맞춤형 질문을 생성해주세요.

=== 대상자 정보 ===
이름: {target_member}

=== 과거 대화 분석 결과 ===
"""
        
        # 컨텍스트 데이터 추가
        if context_data:
            if context_data.get("recent_questions"):
                recent_q = context_data["recent_questions"][:5]  # 최근 5개만
                base_prompt += f"""
최근 질문들 (중복 방지용):
{chr(10).join(f"- {q}" for q in recent_q)}
"""
            
            if context_data.get("popular_topics"):
                base_prompt += f"""
관심 있는 주제들:
{chr(10).join(f"- {topic['category']}: {topic['answer_count']}번 답변" for topic in context_data["popular_topics"])}
"""
            
            if context_data.get("underexplored_categories"):
                base_prompt += f"""
아직 많이 다루지 않은 카테고리: {', '.join(context_data["underexplored_categories"])}
"""
            
            if context_data.get("recent_emotional_state"):
                base_prompt += f"최근 감정 상태: {context_data['recent_emotional_state']}\n"
            
            if context_data.get("avoidance_keywords"):
                base_prompt += f"""
피해야 할 주제: {', '.join(context_data["avoidance_keywords"])}
"""
        
        # 가족 분석 결과 추가
        if family_analysis:
            answer_patterns = family_analysis.get("answer_patterns", {})
            if answer_patterns:
                base_prompt += f"""
=== 답변 패턴 분석 ===
- 선호 답변 길이: {answer_patterns.get("answer_length_category", "보통")}
- 주요 감정: {answer_patterns.get("dominant_sentiment", "중립")}
- 답변 활동도: {answer_patterns.get("answer_frequency", 0)}번의 답변 기록
"""
            
            if family_analysis.get("preferred_categories"):
                top_cats = family_analysis["preferred_categories"][:3]
                base_prompt += f"""
선호 카테고리:
{chr(10).join(f"- {cat['category']}: {cat['engagement_level']} 관심도" for cat in top_cats)}
"""
            
            if family_analysis.get("recommendations"):
                base_prompt += f"""
=== AI 추천사항 ===
{chr(10).join(f"- {rec}" for rec in family_analysis["recommendations"][:3])}
"""
        
        # 질문 생성 지침
        base_prompt += f"""

=== 질문 생성 지침 ===
1. 위 분석을 바탕으로 {target_member}님께 가장 적합한 질문 생성
2. 최근 질문들과 중복되지 않도록 주의
3. {target_member}님의 답변 패턴과 선호도를 고려
4. 가족 간의 소통과 유대감 증진에 도움이 되는 내용
5. 존댓말로 정중하게 질문 (예: "~하시나요?", "~이신가요?")
6. 질문 길이는 50자 이내로 간결하게
7. {target_member}님이 편안하게 답변할 수 있는 수준의 질문
"""
        
        if category:
            base_prompt += f"8. 카테고리: {category.value}\n"
        
        if family_context:
            base_prompt += f"9. 가족 구성: {family_context}\n"
        
        if mood:
            base_prompt += f"10. 원하는 분위기: {mood}\n"
        
        base_prompt += """
=== 출력 형식 ===
분석이나 설명 없이 질문만 출력해주세요.
질문:"""
        
        return base_prompt
    
    async def _call_enhanced_openai(self, prompt: str, use_mcp: bool = True) -> str:
        """
        강화된 OpenAI API 호출
        """
        try:
            # MCP 사용 시 더 많은 토큰과 다른 설정 사용
            max_tokens = 150 if use_mcp else settings.max_tokens
            temperature = 0.9 if use_mcp else settings.temperature
            
            response = self.client.chat.completions.create(
                model=settings.default_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 가족 유대감 증진을 위한 개인화된 질문 생성 전문가입니다. 과거 대화 분석을 통해 각 가족 구성원에게 최적화된 질문을 만드는 것이 목표입니다."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                presence_penalty=0.3,  # 새로운 주제 장려
                frequency_penalty=0.5   # 반복 방지
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Enhanced OpenAI API 호출 실패: {str(e)}")
            raise Exception(f"AI 서비스 호출에 실패했습니다: {str(e)}")
    
    async def generate_follow_up_question(
        self,
        target_member: str,
        previous_answer: str,
        original_question: str,
        family_id: str = "default"
    ) -> QuestionResponse:
        """
        이전 답변을 바탕으로 후속 질문을 생성합니다.
        """
        try:
            # 이전 답변 분석
            answer_analysis = await self._analyze_answer_content(previous_answer)
            
            # 후속 질문 프롬프트 구성
            prompt = f"""
당신은 가족 대화의 흐름을 이어가는 전문가입니다.

=== 이전 대화 ===
질문: {original_question}
{target_member}님의 답변: {previous_answer}

=== 답변 분석 ===
감정 톤: {answer_analysis.get('emotional_tone', '알 수 없음')}
주요 키워드: {', '.join(answer_analysis.get('keywords', []))}
답변 길이: {answer_analysis.get('length_category', '보통')}

=== 후속 질문 생성 지침 ===
1. 이전 답변의 내용을 자연스럽게 이어가는 질문 생성
2. {target_member}님이 더 깊이 있게 이야기할 수 있도록 유도
3. 답변에서 언급된 구체적인 내용에 대해 궁금해하는 방식
4. 존댓말로 정중하게 질문
5. 50자 이내로 간결하게

후속 질문:"""
            
            response = await self._call_enhanced_openai(prompt, use_mcp=True)
            question_content = self._parse_response(response)
            
            # QuestionResponse 객체 생성
            question = QuestionResponse(
                id=str(uuid.uuid4()),
                content=question_content,
                category=QuestionCategory.FAMILY,  # 후속 질문은 일반적으로 FAMILY 카테고리
                target_member=target_member,
                created_at=datetime.now(),
                family_context="후속 질문",
                mood="자연스러운 대화 흐름"
            )
            
            logger.info(f"후속 질문 생성 완료: {question_content[:50]}...")
            return question
            
        except Exception as e:
            logger.error(f"후속 질문 생성 실패: {str(e)}")
            raise Exception(f"후속 질문 생성에 실패했습니다: {str(e)}")
    
    async def _analyze_answer_content(self, answer_text: str) -> Dict[str, Any]:
        """
        답변 내용을 분석합니다.
        """
        try:
            # 간단한 분석 (실제로는 더 정교한 NLP 분석 필요)
            analysis = {
                "length_category": "short" if len(answer_text) < 50 else "medium" if len(answer_text) < 150 else "long",
                "keywords": [],
                "emotional_tone": "neutral"
            }
            
            # 간단한 키워드 추출
            positive_words = ["좋", "행복", "기쁨", "사랑", "즐거", "웃음"]
            negative_words = ["슬프", "힘들", "어려", "걱정", "스트레스", "화"]
            
            answer_lower = answer_text.lower()
            
            # 감정 톤 분석
            positive_count = sum(1 for word in positive_words if word in answer_lower)
            negative_count = sum(1 for word in negative_words if word in answer_lower)
            
            if positive_count > negative_count:
                analysis["emotional_tone"] = "positive"
            elif negative_count > positive_count:
                analysis["emotional_tone"] = "negative"
            else:
                analysis["emotional_tone"] = "neutral"
            
            # 키워드 추출 (실제로는 더 정교한 방법 필요)
            words = answer_text.split()
            analysis["keywords"] = [word for word in words if len(word) > 2][:10]  # 상위 10개
            
            return analysis
            
        except Exception as e:
            logger.error(f"답변 분석 실패: {str(e)}")
            return {"length_category": "unknown", "keywords": [], "emotional_tone": "neutral"}
    
    async def generate_themed_questions(
        self,
        target_member: str,
        theme: str,
        count: int = 5,
        family_id: str = "default"
    ) -> List[QuestionResponse]:
        """
        특정 테마에 맞는 여러 질문을 생성합니다.
        """
        try:
            # 컨텍스트 데이터 수집
            context_data = await self.mcp_service.get_contextual_question_data(
                target_member=target_member
            )
            
            # 테마별 질문 생성 프롬프트
            prompt = f"""
당신은 가족 유대감 증진을 위한 테마별 질문 생성 전문가입니다.

=== 대상자 정보 ===
이름: {target_member}
테마: {theme}
요청 질문 수: {count}개

=== 과거 질문 분석 ===
"""
            
            if context_data and context_data.get("recent_questions"):
                recent_q = context_data["recent_questions"][:10]
                prompt += f"""
최근 질문들 (중복 방지용):
{chr(10).join(f"- {q}" for q in recent_q)}
"""
            
            prompt += f"""
=== 생성 지침 ===
1. '{theme}' 테마에 맞는 {count}개의 서로 다른 질문 생성
2. 각 질문은 서로 다른 관점이나 접근 방식 사용
3. {target_member}님께 적합한 난이도와 내용
4. 존댓말로 정중하게 질문
5. 각 질문은 50자 이내로 간결하게
6. 번호를 매겨서 나열

테마별 질문 목록:"""
            
            response = await self._call_enhanced_openai(prompt, use_mcp=True)
            
            # 응답에서 개별 질문들 추출
            questions_text = response.strip().split('\n')
            questions = []
            
            for i, line in enumerate(questions_text):
                if line.strip() and any(char.isdigit() for char in line[:3]):
                    # 번호 제거하고 질문만 추출
                    clean_question = line.split('.', 1)[-1].strip() if '.' in line else line.strip()
                    
                    if clean_question and len(clean_question) > 5:  # 유효한 질문인지 확인
                        question = QuestionResponse(
                            id=str(uuid.uuid4()),
                            content=clean_question,
                            category=QuestionCategory.FAMILY,
                            target_member=target_member,
                            created_at=datetime.now(),
                            family_context=f"테마: {theme}",
                            mood="테마별 질문"
                        )
                        questions.append(question)
                        
                        if len(questions) >= count:  # 요청된 수만큼 생성되면 중단
                            break
            
            logger.info(f"{theme} 테마 질문 {len(questions)}개 생성 완료")
            return questions
            
        except Exception as e:
            logger.error(f"테마별 질문 생성 실패: {str(e)}")
            raise Exception(f"테마별 질문 생성에 실패했습니다: {str(e)}")
    
    async def analyze_conversation_effectiveness(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        대화의 효과성을 분석합니다.
        """
        try:
            analysis_prompt = f"""
당신은 가족 대화 분석 전문가입니다. 다음 대화의 효과성을 분석해주세요.

=== 대화 데이터 ===
{json.dumps(conversation_data, ensure_ascii=False, indent=2)}

=== 분석 항목 ===
1. 참여도: 얼마나 적극적으로 참여했는가?
2. 감정 교류: 감정적 연결이 얼마나 이루어졌는가?
3. 정보 공유: 새로운 정보나 이야기가 얼마나 공유되었는가?
4. 대화 지속성: 대화가 자연스럽게 이어졌는가?
5. 만족도: 참여자들이 만족할만한 대화였는가?

각 항목을 1-5점으로 평가하고 간단한 설명을 포함해주세요.
JSON 형식으로 결과를 제공해주세요.

분석 결과:"""
            
            response = await self._call_enhanced_openai(analysis_prompt, use_mcp=True)
            
            # JSON 파싱 시도
            try:
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 구조 생성
                analysis_result = {
                    "participation": {"score": 3, "comment": "분석 데이터 부족"},
                    "emotional_connection": {"score": 3, "comment": "분석 데이터 부족"},
                    "information_sharing": {"score": 3, "comment": "분석 데이터 부족"},
                    "conversation_flow": {"score": 3, "comment": "분석 데이터 부족"},
                    "satisfaction": {"score": 3, "comment": "분석 데이터 부족"},
                    "overall_score": 3.0,
                    "recommendations": ["더 많은 대화 데이터가 필요합니다."]
                }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"대화 효과성 분석 실패: {str(e)}")
            return {
                "error": "분석 실패",
                "message": str(e),
                "overall_score": 0.0
            }