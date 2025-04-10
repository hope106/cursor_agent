"""
환경 변수 설정 모듈
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent

# .env 파일 로드
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path)

# 환경 변수 접근
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CURSOR_WORKSPACE_PATH = os.getenv("CURSOR_WORKSPACE_PATH")
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 6000))

# 환경 변수 검증 (개발 또는 테스트 환경에서는 무시)
if not ANTHROPIC_API_KEY and APP_ENV not in ["development", "test"]:
    raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
# 개발 환경에서는 API 키가 없을 경우 로그만 출력
if APP_ENV == "development" and not ANTHROPIC_API_KEY:
    from loguru import logger
    logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. API 호출은 동작하지 않을 수 있습니다.")

# 업로드 디렉토리 설정
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# API 관련 설정
API_PREFIX = "/api/v1"

# 환경별 설정
if APP_ENV == "development":
    DEBUG = True
    HOST = "0.0.0.0"
elif APP_ENV == "production":
    DEBUG = False
    HOST = "0.0.0.0"
else:  # test
    DEBUG = True
    HOST = "localhost"
    # 테스트 환경 특수 설정
    TEST_UPLOAD_DIR = os.path.join(PROJECT_ROOT, "tests", "temp")
    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True) 