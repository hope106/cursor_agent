"""
기본 추상 에이전트 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger

class BaseAgent(ABC):
    """
    모든 에이전트의 기본 추상 클래스
    """
    
    def __init__(self, name: str):
        """
        에이전트 초기화
        
        Args:
            name: 에이전트 이름
        """
        self.name = name
        logger.info(f"에이전트 초기화: {name}")
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        상태를 처리하고 결과 반환
        
        Args:
            state: 현재 상태 정보
            
        Returns:
            업데이트된 상태
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        에이전트 메타데이터 반환
        
        Returns:
            메타데이터
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__
        }
    
    def log_start(self, state: Dict[str, Any]) -> None:
        """
        처리 시작 로깅
        
        Args:
            state: 현재 상태
        """
        logger.info(f"에이전트 시작: {self.name}")
    
    def log_completion(self, state: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        처리 완료 로깅
        
        Args:
            state: 이전 상태
            result: 처리 결과
        """
        logger.info(f"에이전트 완료: {self.name}")
    
    def log_error(self, state: Dict[str, Any], error: Exception) -> None:
        """
        오류 로깅
        
        Args:
            state: 현재 상태
            error: 발생한 오류
        """
        logger.error(f"에이전트 오류 ({self.name}): {str(error)}") 