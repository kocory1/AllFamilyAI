import openai
import uuid
from datetime import datetime
from typing import Optional
import logging

from app.core.config import settings
from app.models.question import QuestionCategory, QuestionResponse

# 로거 설정
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def generate_question(
        self,
        target_member: str,
        category: Optional[QuestionCategory] = None,
        family_context: Optional[str] = None,
        mood: Optional[str] = None
    ) -> QuestionResponse:
        """
        OpenAI API를 사용하여 가족을 위한 질문을 생성합니다.
        """
        try:
            # 프롬프트 구성
            prompt = self._build_prompt(target_member, category, family_context, mood)
            
            # OpenAI API 호출
            response = await self._call_openai(prompt)
            
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
            
            logger.info(f"질문 생성 완료: {question_content[:50]}...")
            return question
            
        except Exception as e:
            logger.error(f"질문 생성 중 오류 발생: {str(e)}")
            raise Exception(f"질문 생성에 실패했습니다: {str(e)}")
    
    def _build_prompt(
        self,
        target_member: str,
        category: Optional[QuestionCategory] = None,
        family_context: Optional[str] = None,
        mood: Optional[str] = None
    ) -> str:
        """
        OpenAI API 호출을 위한 프롬프트를 구성합니다.
        """
        base_prompt = f"""
당신은 가족 유대감을 증진시키는 따뜻한 질문을 만드는 전문가입니다.
다음 조건에 맞는 {target_member}에게 직접 던지는 질문을 하나만 생성해주세요.

조건:
- 질문은 한국어로 작성
- {target_member}에게 직접 "{target_member}님" 또는 "{target_member}"로 호칭하여 질문
- 존댓말로 질문 (예: "~이신가요?", "~하시나요?", "~이었나요?")
- {target_member}의 역할과 특성을 고려한 맞춤형 질문
- 가족 구성원들이 함께 대화할 수 있도록 유도
- 너무 개인적이거나 민감한 주제는 피하기
- 답변하기 쉽고 재미있게
- 질문 길이는 50자 이내
- 질문만 생성하고 설명은 하지 마세요

"""
        
        if category:
            base_prompt += f"카테고리: {category.value}\n"
        
        if family_context:
            base_prompt += f"가족 구성: {family_context}\n"
        
        if mood:
            base_prompt += f"원하는 분위기: {mood}\n"
        
        base_prompt += "\n질문:"
        
        return base_prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """
        OpenAI API를 호출합니다.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",  # 최신 저렴한 모델 사용
                messages=[
                    {"role": "system", "content": "당신은 가족 유대감 증진을 위한 질문 생성 전문가입니다. 따뜻하고 진정성 있는 질문을 만드는 것이 목표입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8  # 약간 더 창의적으로
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {str(e)}")
            raise Exception(f"AI 서비스 호출에 실패했습니다: {str(e)}")
    
    def _parse_response(self, response: str) -> str:
        """
        OpenAI 응답을 파싱하여 질문만 추출합니다.
        """
        # 응답에서 질문만 추출 (불필요한 텍스트 제거)
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('질문:') and not line.startswith('답변:'):
                # 질문으로 보이는 내용 반환
                return line
        
        # 파싱 실패 시 전체 응답 반환
        return response.strip() 