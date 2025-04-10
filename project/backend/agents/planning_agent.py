"""
계획 수립 에이전트 구현
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.utils.anthropic_client import anthropic_client

class PlanningAgent(BaseAgent):
    """
    계획 수립 에이전트: 작업을 단계별로 분해하고 실행 계획 수립
    """
    
    def __init__(self, name: str = "계획 수립 에이전트"):
        """
        계획 수립 에이전트 초기화
        
        Args:
            name: 에이전트 이름
        """
        super().__init__(name)
    
    async def create_plan(self, task: str) -> Dict[str, Any]:
        """
        작업에 대한 계획 수립
        
        Args:
            task: 수행할 작업 설명
            
        Returns:
            계획 결과
        """
        system_message = """
        당신은 작업을 단계별로 분해하고 실행 계획을 수립하는 계획 수립 에이전트입니다.
        주어진 작업을 분석하고 다음 작업을 수행하세요:
        1. 작업을 완료하기 위한 단계별 계획 작성
        2. 각 단계에 필요한 자원과 정보 식별
        3. 잠재적인 문제와 해결 방법 예측
        4. 우선순위와 일정 제안
        
        계획은 구체적이고 실행 가능해야 합니다.
        JSON 형식으로 응답해주세요.
        """
        
        response = anthropic_client.get_completion(
            prompt=task,
            system_message=system_message,
            temperature=0.2
        )
        
        if response["status"] == "error":
            logger.error(f"계획 수립 실패: {response.get('message')}")
            return {
                "status": "error",
                "message": "계획을 수립하는데 문제가 발생했습니다."
            }
        
        return {
            "status": "success",
            "plan": response["content"],
            "raw_response": response
        }
    
    async def prioritize_steps(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        계획 단계 우선순위 지정
        
        Args:
            plan: 계획 결과
            
        Returns:
            우선순위가 지정된 계획
        """
        if plan["status"] != "success":
            return plan
        
        # 여기서는 단순화를 위해 원본 계획을 반환하지만,
        # 실제 구현에서는 우선순위 알고리즘 추가 가능
        return {
            "status": "success",
            "prioritized_plan": plan["plan"],
            "original_plan": plan
        }
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        상태 처리 및 결과 반환
        
        Args:
            state: 현재 상태
            
        Returns:
            처리 결과
        """
        self.log_start(state)
        
        try:
            task = state.get("task")
            if not task:
                return {"status": "error", "message": "수행할 작업이 지정되지 않았습니다."}
            
            # 1. 계획 수립
            plan = await self.create_plan(task)
            if plan["status"] != "success":
                return plan
            
            # 2. 우선순위 지정
            prioritized_plan = await self.prioritize_steps(plan)
            
            # 결과 반환
            result = {
                "status": "success",
                "message": "계획 수립 완료",
                "plan": prioritized_plan["prioritized_plan"],
                "details": {
                    "original_plan": plan,
                    "prioritized_plan": prioritized_plan
                }
            }
            
            self.log_completion(state, result)
            return result
        
        except Exception as e:
            self.log_error(state, e)
            return {
                "status": "error",
                "message": f"계획 수립 중 오류 발생: {str(e)}"
            } 