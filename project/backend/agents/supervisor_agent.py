"""
슈퍼바이저 에이전트 구현
"""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.utils.anthropic_client import anthropic_client

class SupervisorAgent(BaseAgent):
    """
    슈퍼바이저 에이전트: 하위 에이전트의 작업을 조율하고 관리
    """
    
    def __init__(self, name: str = "슈퍼바이저"):
        """
        슈퍼바이저 에이전트 초기화
        
        Args:
            name: 에이전트 이름
        """
        super().__init__(name)
        self.sub_agents = {}
    
    def register_agent(self, agent_id: str, agent: BaseAgent) -> None:
        """
        하위 에이전트 등록
        
        Args:
            agent_id: 에이전트 ID
            agent: 에이전트 인스턴스
        """
        self.sub_agents[agent_id] = agent
        logger.info(f"에이전트 등록: {agent_id} ({agent.name})")
    
    def get_registered_agents(self) -> Dict[str, BaseAgent]:
        """
        등록된 모든 하위 에이전트 가져오기
        
        Returns:
            하위 에이전트 사전
        """
        return self.sub_agents
    
    async def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        사용자 요청 분석
        
        Args:
            user_request: 사용자 요청 텍스트
            
        Returns:
            분석 결과
        """
        system_message = """
        당신은 작업을 분석하고 적절한 하위 에이전트에게 할당하는 슈퍼바이저입니다.
        사용자 요청을 분석하고 다음 작업을 수행하세요:
        1. 요청의 주요 목적과 필요한 작업 식별
        2. 필요한 하위 에이전트 목록 작성 (계획 수립, 코드 생성, 디버깅 등)
        3. 각 하위 에이전트에게 할당할 구체적인 작업 정의
        4. 작업 간의 의존성 파악
        
        JSON 형식으로 응답해주세요.
        """
        
        response = anthropic_client.get_completion(
            prompt=user_request,
            system_message=system_message,
            temperature=0.3
        )
        
        if response["status"] == "error":
            logger.error(f"요청 분석 실패: {response.get('message')}")
            return {
                "status": "error",
                "message": "사용자 요청을 분석하는데 문제가 발생했습니다."
            }
        
        # TODO: 응답을 구조화된 형태로 파싱
        return {
            "status": "success",
            "analysis": response["content"],
            "raw_response": response
        }
    
    async def allocate_tasks(self, analysis: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 할당
        
        Args:
            analysis: 요청 분석 결과
            state: 현재 상태
            
        Returns:
            작업 할당 결과
        """
        # TODO: 분석 결과에서 필요한 에이전트와 작업 추출
        # 예시용 임시 구현
        task_allocation = {}
        
        for agent_id, agent in self.sub_agents.items():
            task_allocation[agent_id] = {
                "agent": agent.name,
                "assigned": True,
                "task": f"작업 수행: {analysis.get('analysis', '일반 작업')[:50]}..."
            }
        
        return {
            "status": "success",
            "task_allocation": task_allocation
        }
    
    async def execute_parallel(self, tasks: Dict[str, Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 병렬 실행
        
        Args:
            tasks: 할당된 작업 목록
            state: 현재 상태
            
        Returns:
            실행 결과
        """
        if not tasks:
            return {"status": "error", "message": "실행할 작업이 없습니다."}
        
        # 병렬로 실행할 작업 생성
        coroutines = []
        for agent_id, task in tasks.items():
            if agent_id in self.sub_agents and task.get("assigned", False):
                agent = self.sub_agents[agent_id]
                # 각 에이전트에 필요한 상태 복사본 생성
                agent_state = state.copy()
                agent_state["task"] = task["task"]
                coroutines.append(agent.process(agent_state))
        
        # 병렬 실행
        results = {}
        if coroutines:
            try:
                executed_results = await asyncio.gather(*coroutines, return_exceptions=True)
                
                # 결과 처리
                for i, agent_id in enumerate(tasks.keys()):
                    if i < len(executed_results):
                        result = executed_results[i]
                        if isinstance(result, Exception):
                            logger.error(f"에이전트 실행 오류 ({agent_id}): {str(result)}")
                            results[agent_id] = {
                                "status": "error",
                                "message": f"실행 중 오류 발생: {str(result)}"
                            }
                        else:
                            results[agent_id] = result
            except Exception as e:
                logger.error(f"병렬 실행 오류: {str(e)}")
                return {"status": "error", "message": f"병렬 실행 중 오류 발생: {str(e)}"}
        
        return {
            "status": "success",
            "results": results
        }
    
    async def integrate_results(self, results: Dict[str, Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 결과 통합
        
        Args:
            results: 각 에이전트의 실행 결과
            state: 현재 상태
            
        Returns:
            통합된 결과
        """
        # 결과 요약 생성
        summary = []
        success_count = 0
        error_count = 0
        
        for agent_id, result in results.items():
            if result.get("status") == "success":
                success_count += 1
                summary.append(f"✅ {self.sub_agents[agent_id].name}: 성공")
            else:
                error_count += 1
                summary.append(f"❌ {self.sub_agents[agent_id].name}: 실패 - {result.get('message', '알 수 없는 오류')}")
        
        # 결과 통합
        integrated_result = {
            "status": "success" if error_count == 0 else "partial_success" if success_count > 0 else "error",
            "summary": "\n".join(summary),
            "success_count": success_count,
            "error_count": error_count,
            "details": results
        }
        
        return integrated_result
    
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
            user_request = state.get("user_request")
            if not user_request:
                return {"status": "error", "message": "사용자 요청이 없습니다."}
            
            # 1. 요청 분석
            analysis = await self.analyze_request(user_request)
            if analysis["status"] != "success":
                return analysis
            
            # 2. 작업 할당
            task_allocation = await self.allocate_tasks(analysis, state)
            if task_allocation["status"] != "success":
                return task_allocation
            
            # 3. 병렬 실행
            execution_results = await self.execute_parallel(task_allocation["task_allocation"], state)
            if execution_results["status"] != "success":
                return execution_results
            
            # 4. 결과 통합
            integrated_result = await self.integrate_results(execution_results["results"], state)
            
            # 최종 상태 업데이트
            result = {
                "status": integrated_result["status"],
                "message": integrated_result["summary"],
                "analysis": analysis,
                "task_allocation": task_allocation,
                "execution_results": execution_results,
                "integrated_result": integrated_result
            }
            
            self.log_completion(state, result)
            return result
        
        except Exception as e:
            self.log_error(state, e)
            return {
                "status": "error",
                "message": f"처리 중 오류 발생: {str(e)}"
            } 