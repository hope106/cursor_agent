"""
LangGraph를 사용한 에이전트 그래프 구현
"""
import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Callable, Awaitable
from loguru import logger
from langgraph.graph import StateGraph, END

from backend.agents.base_agent import BaseAgent
from backend.agents.supervisor_agent import SupervisorAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.code_generation_agent import CodeGenerationAgent

# 상태 타입 정의
class AgentState(TypedDict, total=False):
    user_request: str
    task: Optional[str]
    analysis: Optional[Dict[str, Any]]
    plan: Optional[str]
    generated_code: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error: Optional[str]
    save_path: Optional[str]

class AgentGraph:
    """
    LangGraph를 사용한 에이전트 그래프
    """
    
    def __init__(self):
        """
        에이전트 그래프 초기화
        """
        self.supervisor = SupervisorAgent()
        self.planning_agent = PlanningAgent()
        self.code_generation_agent = CodeGenerationAgent()
        
        # 에이전트 등록
        self.supervisor.register_agent("planning", self.planning_agent)
        self.supervisor.register_agent("code_generation", self.code_generation_agent)
        
        # 그래프 생성
        self.graph = self._build_graph()
        
        logger.info("에이전트 그래프 초기화 완료")
    
    def _build_graph(self) -> StateGraph:
        """
        에이전트 그래프 구축
        
        Returns:
            상태 그래프
        """
        # 상태 그래프 생성
        builder = StateGraph(AgentState)
        
        # 노드 추가
        builder.add_node("supervisor", self._run_supervisor)
        builder.add_node("planning", self._run_planning)
        builder.add_node("code_generation", self._run_code_generation)
        
        # 에지 추가
        # 슈퍼바이저에서 planning으로 조건부 라우팅
        builder.add_conditional_edges(
            "supervisor",
            self._route_to_agents,
            {
                "planning": "planning", 
                "end": END
            }
        )
        
        # 일반 에지 추가
        builder.add_edge("planning", "code_generation")
        builder.add_edge("code_generation", END)
        
        # 시작 노드 설정 - 이전 버전에서는 entry_point
        builder.set_entry_point("supervisor")
        
        # 이전 버전 langgraph와 호환되도록 명시적으로 컴파일
        graph = builder.compile()
        
        return graph
    
    async def _run_supervisor(self, state: AgentState) -> AgentState:
        """
        슈퍼바이저 에이전트 실행
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        logger.info("슈퍼바이저 에이전트 실행")
        try:
            result = await self.supervisor.process(state)
            
            # 상태 업데이트
            new_state = state.copy()
            new_state["analysis"] = result.get("analysis", {})
            
            return new_state
        except Exception as e:
            logger.error(f"슈퍼바이저 에이전트 실행 오류: {str(e)}")
            return {**state, "error": f"슈퍼바이저 에이전트 오류: {str(e)}"}
    
    async def _run_planning(self, state: AgentState) -> AgentState:
        """
        계획 수립 에이전트 실행
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        logger.info("계획 수립 에이전트 실행")
        try:
            result = await self.planning_agent.process(state)
            
            # 상태 업데이트
            new_state = state.copy()
            if result["status"] == "success":
                new_state["plan"] = result.get("plan", "")
            else:
                new_state["error"] = result.get("message", "계획 수립 실패")
            
            return new_state
        except Exception as e:
            logger.error(f"계획 수립 에이전트 실행 오류: {str(e)}")
            return {**state, "error": f"계획 수립 에이전트 오류: {str(e)}"}
    
    async def _run_code_generation(self, state: AgentState) -> AgentState:
        """
        코드 생성 에이전트 실행
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        logger.info("코드 생성 에이전트 실행")
        try:
            result = await self.code_generation_agent.process(state)
            
            # 상태 업데이트
            new_state = state.copy()
            if result["status"] in ["success", "partial_success"]:
                new_state["generated_code"] = result.get("generated_code", {})
                new_state["results"] = result
            else:
                new_state["error"] = result.get("message", "코드 생성 실패")
            
            return new_state
        except Exception as e:
            logger.error(f"코드 생성 에이전트 실행 오류: {str(e)}")
            return {**state, "error": f"코드 생성 에이전트 오류: {str(e)}"}
    
    def _route_to_agents(self, state: AgentState) -> str:
        """
        분석 결과에 따라 적절한 에이전트로 라우팅
        
        Args:
            state: 현재 상태
            
        Returns:
            다음 노드 이름 ("planning" 또는 "end")
        """
        # 오류 발생 시 종료
        if "error" in state and state["error"]:
            logger.error(f"오류로 인한 처리 종료: {state['error']}")
            return "end"
        
        # 단순화된 라우팅 로직 (실제 구현에서는 분석 결과에 따라 결정)
        # 여기서는 항상 계획 수립 에이전트부터 시작
        return "planning"
    
    async def run(self, user_request: str, save_path: str = None) -> Dict[str, Any]:
        """
        사용자 요청으로 에이전트 그래프 실행
        
        Args:
            user_request: 사용자 요청
            save_path: 파일 저장 경로 (선택 사항)
            
        Returns:
            실행 결과
        """
        logger.info(f"에이전트 그래프 실행 시작: {user_request[:50]}...")
        
        # json 형식인지 확인
        try:
            import json
            # JSON 형식이면 파싱 시도
            if user_request.strip().startswith('{') and user_request.strip().endswith('}'):
                data = json.loads(user_request)
                
                # 실제 요청 추출
                if 'request' in data:
                    actual_request = data['request']
                    
                    # 저장 경로 추출
                    if 'save_path' in data and not save_path:
                        save_path = data['save_path']
                        logger.info(f"JSON에서 저장 경로 추출: {save_path}")
                    
                    user_request = actual_request
                    logger.info(f"JSON에서 실제 요청 추출: {user_request[:50]}...")
            
        except json.JSONDecodeError:
            # JSON이 아니라면 패스
            pass
        except Exception as e:
            logger.warning(f"JSON 파싱 오류: {str(e)}")
        
        # 초기 상태 생성
        initial_state: AgentState = {
            "user_request": user_request,
            "task": user_request,  # 태스크로도 설정
        }
        
        # 저장 경로가 있으면 상태에 추가
        if save_path:
            initial_state["save_path"] = save_path
            logger.info(f"저장 경로를 상태에 추가: {save_path}")
        
        try:
            # 그래프 실행
            logger.info("LangGraph 실행 시작")
            
            try:
                # LangGraph 0.0.x 버전에서는 다른 방식으로 호출 시도
                logger.info("LangGraph 실행 방식 1 시도")
                final_state = self.graph.invoke(initial_state)
                logger.info("LangGraph 실행 완료")
            except Exception as graph_error_1:
                logger.warning(f"첫 번째 실행 방식 오류: {str(graph_error_1)}")
                
                try:
                    # 대체 실행 방식 시도
                    logger.info("LangGraph 실행 방식 2 시도 - 직접 노드 실행")
                    
                    # 수동으로 그래프 노드 실행
                    state = initial_state.copy()
                    state = await self._run_supervisor(state)
                    
                    if "error" in state and state["error"]:
                        final_state = state
                    else:
                        next_node = self._route_to_agents(state)
                        if next_node == "planning":
                            state = await self._run_planning(state)
                            if not ("error" in state and state["error"]):
                                state = await self._run_code_generation(state)
                        final_state = state
                    
                    logger.info("수동 그래프 실행 완료")
                except Exception as manual_error:
                    logger.error(f"수동 그래프 실행 오류: {str(manual_error)}")
                    import traceback
                    logger.error(f"수동 실행 스택 트레이스: {traceback.format_exc()}")
                    raise
            
            logger.debug(f"최종 상태: {final_state}")
            
            # 결과 처리
            if "error" in final_state and final_state["error"]:
                logger.warning(f"에이전트 오류: {final_state['error']}")
                return {
                    "status": "error",
                    "message": final_state["error"],
                    "state": final_state
                }
            
            logger.info("에이전트 그래프 실행 성공")
            return {
                "status": "success",
                "message": "작업이 성공적으로 완료되었습니다.",
                "state": final_state
            }
        except Exception as e:
            logger.error(f"에이전트 그래프 실행 오류: {str(e)}")
            import traceback
            logger.error(f"오류 스택 트레이스: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"에이전트 그래프 실행 중 오류 발생: {str(e)}",
                "state": initial_state
            } 