"""
FastAPI 애플리케이션 메인 모듈
"""
import os
import sys
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 내부 모듈 임포트
from backend.config.settings import BACKEND_PORT, HOST, DEBUG, API_PREFIX, LOG_LEVEL
from backend.api.routes import router as api_router

# 로깅 설정
logger.remove()
logger.add(
    sink=lambda msg: print(msg),
    level=LOG_LEVEL.upper(),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="LangGraph 멀티에이전트 시스템",
    description="슈퍼바이저 패턴 기반의 멀티에이전트 시스템 API",
    version="0.1.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(api_router)

# 루트 엔드포인트
@app.get("/")
async def root():
    """
    API 루트 엔드포인트
    
    Returns:
        기본 정보
    """
    return {
        "message": "LangGraph 멀티에이전트 시스템 API에 오신 것을 환영합니다.",
        "docs_url": "/docs",
        "api_prefix": API_PREFIX
    }

# WebSocket 테스트 엔드포인트
@app.websocket("/ws-test")
async def websocket_test(websocket: WebSocket):
    """
    WebSocket 테스트 엔드포인트
    """
    logger.info("WS-TEST: 연결 요청 수신")
    try:
        await websocket.accept()
        logger.info("WS-TEST: 연결 수락 완료")
        logger.info(f"WS-TEST: 클라이언트 정보 - headers: {websocket.headers.get('user-agent', '알 수 없음')}")
        
        try:
            # 간단한 에코 서버
            while True:
                logger.info("WS-TEST: 메시지 대기 중")
                data = await websocket.receive_text()
                logger.info(f"WS-TEST: 메시지 수신 - {data}")
                
                # 응답 전송
                logger.info("WS-TEST: 응답 전송")
                await websocket.send_text(f"에코: {data}")
                logger.info("WS-TEST: 응답 전송 완료")
        except Exception as e:
            logger.error(f"WS-TEST: 내부 루프 오류 - {str(e)}")
            import traceback
            logger.error(f"WS-TEST: 스택 트레이스 - {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"WS-TEST: 연결 수락 오류 - {str(e)}")
        import traceback
        logger.error(f"WS-TEST: 스택 트레이스 - {traceback.format_exc()}")
    finally:
        logger.info("WS-TEST: 연결 종료")

# 애플리케이션 시작
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작")
    
# 애플리케이션 종료
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료")

if __name__ == "__main__":
    # 서버 실행
    logger.info(f"서버 시작 - 호스트: {HOST}, 포트: {BACKEND_PORT}, 디버그 모드: {DEBUG}")
    uvicorn.run(
        "main:app",
        host=HOST,
        port=BACKEND_PORT,
        reload=DEBUG,
        log_level="info" if DEBUG else "warning"
    ) 