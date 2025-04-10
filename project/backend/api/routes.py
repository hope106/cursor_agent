"""
FastAPI 라우트 모듈
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
from loguru import logger
import os
import uuid
import logging
from io import StringIO

from backend.agents.agent_graph import AgentGraph
from backend.config.settings import UPLOAD_DIR, APP_ENV

# 로그 캡처를 위한 StringIO 객체와 핸들러
class LogCapture:
    def __init__(self):
        self.log_records = []
        self.max_records = 100  # 최대 로그 항목 수
    
    def add_record(self, record):
        # 필요한 로그 정보만 저장
        log_entry = {
            "time": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            "level": record["level"].name,
            "message": record["message"],
            "name": record["name"],
            "function": record["function"],
            "line": record["line"]
        }
        self.log_records.append(log_entry)
        
        # 최대 항목 수를 초과하면 가장 오래된 항목 제거
        if len(self.log_records) > self.max_records:
            self.log_records.pop(0)
    
    def get_records(self):
        return self.log_records
    
    def clear(self):
        self.log_records = []

# 로그 캡처 인스턴스 생성
log_capture = LogCapture()

# loguru 커스텀 로그 핸들러 추가
logger.configure(
    handlers=[
        # 기존 콘솔 로그 핸들러 유지
        {"sink": lambda msg: print(msg), "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"},
        # 로그 캡처 핸들러 추가
        {"sink": log_capture.add_record, "format": "{time} | {level} | {name}:{function}:{line} - {message}"}
    ]
)

# 모델 정의
class UserRequest(BaseModel):
    request: str
    
class AgentResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

# 라우터 생성
router = APIRouter(prefix="/api/v1")

# 에이전트 그래프 인스턴스
agent_graph = AgentGraph()

# 활성 WebSocket 연결 저장
active_connections: Dict[str, WebSocket] = {}

# 웹소켓 클라이언트 목록
websocket_clients: Dict[str, WebSocket] = {}

# API 엔드포인트
@router.post("/process", response_model=AgentResponse)
async def process_request(request: UserRequest) -> AgentResponse:
    """
    사용자 요청 처리
    
    Args:
        request: 사용자 요청
        
    Returns:
        처리 결과
    """
    try:
        logger.info(f"사용자 요청 수신: {request.request[:50]}...")
        logger.debug(f"전체 요청 데이터: {request}")
        
        # 에이전트 그래프 실행
        result = await agent_graph.run(request.request)
        logger.debug(f"에이전트 그래프 실행 결과: {result}")
        
        # 응답 반환
        response = AgentResponse(
            status=result["status"],
            message=result["message"],
            details={"state": result.get("state", {})}
        )
        logger.info(f"응답 반환: {response.status}")
        return response
    except Exception as e:
        logger.error(f"요청 처리 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"요청 처리 중 오류 발생: {str(e)}"
        )

@router.post("/upload", response_model=AgentResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> AgentResponse:
    """
    파일 업로드 및 분석
    
    Args:
        background_tasks: 백그라운드 작업
        file: 업로드된 파일
        
    Returns:
        처리 결과
    """
    try:
        logger.info(f"파일 업로드: {file.filename}")
        
        # 파일 내용 읽기
        content = await file.read()
        file_text = content.decode("utf-8")
        
        # 백그라운드에서 처리 (비동기 실행)
        background_tasks.add_task(agent_graph.run, f"다음 파일을 분석해주세요: {file.filename}\n\n{file_text[:1000]}...")
        
        return AgentResponse(
            status="accepted",
            message=f"파일 '{file.filename}'이 업로드되었으며 처리 중입니다.",
            details={"filename": file.filename}
        )
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류 발생: {str(e)}"
        )

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket 엔드포인트
    
    Args:
        websocket: WebSocket 연결
        client_id: 클라이언트 ID
    """
    logger.info(f"API-WS: 연결 요청 수신 - client_id={client_id}")
    logger.info(f"API-WS: 요청 헤더 - {websocket.headers}")
    
    try:
        logger.info(f"API-WS: 연결 수락 시도 - client_id={client_id}")
        await websocket.accept()
        logger.info(f"API-WS: 연결 수락 완료 - client_id={client_id}")
        
        # 클라이언트 등록
        websocket_clients[client_id] = websocket
        
        # 연결 성공 메시지 전송
        logger.info(f"API-WS: 연결 성공 메시지 전송 - client_id={client_id}")
        await websocket.send_json({
            "status": "connected",
            "message": "WebSocket 연결이 설정되었습니다.",
            "client_id": client_id
        })
        logger.info(f"API-WS: 연결 성공 메시지 전송 완료 - client_id={client_id}")
        
        # 메시지 대기 루프
        try:
            logger.info(f"API-WS: 메시지 대기 시작 - client_id={client_id}")
            while True:
                # 메시지 수신
                data = await websocket.receive_text()
                logger.info(f"API-WS: 메시지 수신 완료 - client_id={client_id}, 데이터 길이: {len(data)}")
                
                # JSON 파싱
                logger.info(f"API-WS: JSON 파싱 시도 - client_id={client_id}")
                json_data = json.loads(data)
                logger.info(f"API-WS: JSON 파싱 성공 - client_id={client_id}")
                
                # 에이전트 그래프 실행
                request = json_data.get("request", "")
                logger.info(f"API-WS: 에이전트 그래프 실행 시작 - client_id={client_id}, 요청: {request[:50]}...")
                
                # 저장 경로 확인
                save_path = json_data.get("save_path")
                if save_path:
                    logger.info(f"API-WS: 저장 경로 지정됨 - client_id={client_id}, 경로: {save_path}")
                
                # 로그 캡처 초기화
                log_capture.clear()
                
                # 에이전트 그래프 실행
                result = await agent_graph.run(request, save_path)
                
                logger.info(f"API-WS: 에이전트 그래프 실행 완료 - client_id={client_id}")
                
                # 응답 전송
                logger.info(f"API-WS: 응답 전송 시작 - client_id={client_id}")
                
                # 응답에 로그 추가
                result["logs"] = log_capture.get_records()
                
                await websocket.send_json(result)
                logger.info(f"API-WS: 응답 전송 완료 - client_id={client_id}")
                
                # 로그 캡처 초기화
                log_capture.clear()
        except WebSocketDisconnect:
            logger.info(f"API-WS: 클라이언트 연결 종료 - client_id={client_id}")
        except Exception as e:
            logger.error(f"API-WS: 메시지 처리 오류 - client_id={client_id}, 오류: {str(e)}")
            # 클라이언트에게 오류 전송
            try:
                await websocket.send_json({
                    "status": "error",
                    "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
                })
            except:
                pass
    except WebSocketDisconnect:
        logger.info(f"API-WS: 클라이언트 연결 종료 - client_id={client_id}, 코드: 1006")
    except Exception as e:
        logger.error(f"API-WS: 연결 설정 오류 - client_id={client_id}, 오류: {str(e)}")
    finally:
        # 클라이언트 제거
        if client_id in websocket_clients:
            del websocket_clients[client_id]
        
        logger.info(f"API-WS: 클라이언트 연결 종료 처리 완료 - client_id={client_id}")

# 상태 확인 엔드포인트
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    서버 상태 확인
    
    Returns:
        상태 정보
    """
    return {"status": "ok", "message": "서버가 정상 동작 중입니다."} 