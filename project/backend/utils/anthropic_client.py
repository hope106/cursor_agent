"""
Anthropic API 클라이언트 유틸리티
"""
import os
from typing import List, Dict, Any, Optional, Union
from loguru import logger
from anthropic import Anthropic

from backend.config.settings import ANTHROPIC_API_KEY

class AnthropicClient:
    """Anthropic API 클라이언트 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Anthropic 클라이언트 초기화
        
        Args:
            api_key: Anthropic API 키 (없으면 환경 변수에서 로드)
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API 키가 설정되지 않았습니다.")
        
        self.client = Anthropic(api_key=self.api_key)
        logger.info("Anthropic 클라이언트 초기화 완료")
    
    def get_completion(
        self, 
        prompt: str, 
        model: str = "claude-3-opus-20240229",
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            model: 사용할 모델
            system_message: 시스템 메시지
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            생성 결과
        """
        try:
            response = self.client.messages.create(
                model=model,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "status": "success",
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Anthropic API 호출 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"Anthropic API 호출 중 오류 발생: {str(e)}",
                "content": None
            }
    
    def get_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        채팅 완성 생성
        
        Args:
            messages: 메시지 목록 (역할과 내용 포함)
            model: 사용할 모델
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            생성 결과
        """
        try:
            # 시스템 메시지를 별도로 추출
            system_message = None
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    chat_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = self.client.messages.create(
                model=model,
                system=system_message,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "status": "success",
                "content": response.content[0].text,
                "role": "assistant",
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except Exception as e:
            logger.error(f"Anthropic Chat API 호출 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"Anthropic Chat API 호출 중 오류 발생: {str(e)}",
                "content": None
            }

# 싱글턴 인스턴스
anthropic_client = AnthropicClient() 