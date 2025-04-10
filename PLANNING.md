# LangGraph 멀티에이전트 시스템 - 프로젝트 계획

## 프로젝트 개요
LangGraph를 활용하여 슈퍼바이저 패턴 기반의 멀티에이전트 시스템을 구현합니다. 이 시스템은 Cursor 에이전트를 통해 파일을 생성하고 실행하며, Vue.js로 구현된 채팅 인터페이스와 Python 백엔드로 구성됩니다. 특히, 각 노드(에이전트)는 병렬로 실행되어 작업 처리 속도와 응답성이 크게 향상됩니다.

## 아키텍처
- **프론트엔드**: Vue.js를 사용한 채팅 UI
- **백엔드**: Python (FastAPI 또는 Flask)
- **에이전트 프레임워크**: LangGraph
- **에이전트 패턴**: 슈퍼바이저 패턴
- **도구**: Cursor 에이전트를 통한 파일 생성 및 실행

## 주요 컴포넌트
1. **슈퍼바이저 에이전트**
   - 사용자 요청을 분석하고 적절한 하위 에이전트에게 작업 할당
   - 하위 에이전트들의 작업 결과를 모니터링하고 조율
   - 최종 결과를 검증하고 사용자에게 응답 제공
   - 단계별 진행 상황을 추적하고 필요시 중재
   - **병렬 실행**: 하위 에이전트에 작업 분배 시, 각 에이전트는 병렬로 실행되어 전체 처리 시간을 단축

2. **하위 에이전트**
   - 계획 수립 에이전트: 작업을 단계별로 분해하고 실행 계획 수립
   - 코드 생성 에이전트: 요구사항에 맞는 코드 생성
   - Cursor 인터페이스 에이전트: Cursor와 통신하여 파일 생성 및 코드 실행
   - 디버깅 에이전트: 오류 발견 및 해결
   - 문서화 에이전트: 코드 문서화 및 사용 설명서 작성
   - **병렬 실행**: 각 하위 에이전트는 독립적으로 병렬 실행되어 동시에 다양한 작업을 수행

3. **Vue.js 채팅 인터페이스**
   - 실시간 메시지 교환 기능
   - 에이전트 활동 및 진행 상황 시각화
   - 코드 블록 및 실행 결과 표시
   - 파일 업로드/다운로드 기능 (로컬 파일 시스템 기반)
   - **실시간 반영**: 백엔드에서 병렬로 처리된 여러 에이전트의 결과를 즉시 통합하여 실시간으로 표시

4. **Python 백엔드**
   - FastAPI 또는 Flask를 사용한 RESTful API
   - LangGraph 기반 에이전트 시스템 구현
   - Cursor API와의 연동
   - 세션 관리 및 상태 유지
   - **병렬 처리**: 각 에이전트 노드의 병렬 실행을 지원하기 위한 스레드 또는 비동기 처리

5. **테스트 및 디버깅**
   - 단위 테스트 및 통합 테스트 실행
   - 에이전트 로직 검증
   - 사용자 시나리오 테스트
   - **병렬 처리 테스트**: 병렬 실행 환경에서 발생할 수 있는 동기화 문제 및 오류 중점 테스트

## 환경 설정
- `.env` 파일에 필요한 환경 변수 정의
  ```
  # LLM API 키
  OPENAI_API_KEY=your_openai_api_key
  ANTHROPIC_API_KEY=your_anthropic_api_key

  # Cursor 설정 (이미 그룹 단위 유료 구독 중)
  CURSOR_WORKSPACE_PATH=/path/to/your/workspace
  CURSOR_EDITOR_CONFIG=default

  # 애플리케이션 설정
  APP_ENV=development
  LOG_LEVEL=info
  PORT=3000
  ```
- 개발 및 프로덕션 환경 설정
- API 키 및 인증 설정 (LLM API 키)
- 외부 스토리지 서비스(AWS S3 등)는 사용하지 않고 로컬 파일 시스템 활용
- 모든 API 키는 직접 하드코딩하지 않고 반드시 `.env` 파일에서 로드
- Cursor는 이미 그룹 단위 유료 구독 중이므로 Cursor 통합에 추가 API 키가 필요하지 않음

## 파일 구조
```
project/
├── frontend/           # Vue.js 채팅 인터페이스
├── backend/            # Python 백엔드
│   ├── agents/         # 에이전트 구현
│   ├── api/            # API 엔드포인트
│   ├── uploads/        # 업로드된 파일 임시 저장소
│   ├── config/         # 설정 파일 (.env 로드)
│   └── utils/          # 유틸리티 함수
├── tests/              # 테스트 스위트
├── docs/               # 문서
├── requirements.txt    # Python 의존성
├── .env.example        # 환경 변수 예시
├── .gitignore          # .env 파일 포함
├── README.md           # 프로젝트 문서
├── PLANNING.md         # 프로젝트 계획 (이 파일)
└── TASK.md             # 작업 추적
```

## 스타일 가이드라인
- PEP8 표준 준수
- 모든 함수에 타입 힌트 사용
- Google 스타일 docstring으로 함수 문서화
- Black으로 코드 포맷팅
- Pydantic을 사용한 데이터 검증

## 의존성
- langchain
- langgraph
- fastapi/flask
- vue.js
- python-dotenv (환경 변수 로드)
- openai
- cursor-api

## 예상 결과물
- LangGraph 기반 슈퍼바이저 패턴 멀티에이전트 시스템 (병렬 실행 지원)
- Vue.js 기반 채팅 인터페이스 (실시간 업데이트 및 병렬 처리 결과 반영)
- Python 백엔드 API (비동기 및 병렬 처리 지원)
- Cursor 통합을 통한 파일 생성 및 코드 실행 기능 (병렬 처리 가능)
- 시스템 사용 설명서 및 API 문서 (병렬 처리에 관한 상세 설명 포함)

## 구현 단계
1. **에이전트 설계**
   - 슈퍼바이저와 하위 에이전트의 역할과 책임 정의
   - 에이전트 간 통신 프로토콜 설계
   - 의사결정 로직 및 오류 처리 메커니즘 구현
   - **병렬 실행 고려**: 에이전트 간의 병렬 실행에 따른 동기화 및 데이터 일관성 유지 전략 수립

2. **LangGraph 그래프 구성**
   - 노드 및 에지 정의
   - 상태 관리 및 트랜지션 로직 구현
   - 분기 및 반복 처리 로직 설계
   - **병렬 실행**: 각 노드가 독립적으로 동작하며 동시에 실행될 수 있도록 설계

3. **Cursor 에이전트 연동**
   - Cursor API 연결 설정
   - 파일 생성 및 수정 명령 구현
   - 코드 실행 및 결과 수집 기능 구현
   - **병렬 처리**: 여러 파일 생성 및 코드 실행 명령을 동시에 처리하는 병렬 통신 구현

4. **프론트엔드 개발**
   - Vue.js 기반 채팅 UI 구현
   - 웹소켓 연결 설정
   - 메시지 포맷 및 표시 로직 구현
   - 반응형 디자인 적용
   - 로컬 파일 시스템 기반 파일 업로드/다운로드 기능 구현
   - **실시간 업데이트**: 병렬 처리된 결과를 웹소켓을 통해 실시간으로 UI에 반영

5. **백엔드 API 개발**
   - 에이전트 시스템과 프론트엔드 연결
   - 인증 및 권한 관리
   - 데이터 흐름 최적화
   - 로컬 파일 처리 시스템 구현
   - **비동기 처리**: 병렬로 실행되는 에이전트 결과를 효율적으로 처리하기 위한 비동기 API 구성

6. **테스트 및 디버깅**
   - 단위 테스트 및 통합 테스트 실행
   - 에이전트 로직 검증
   - 사용자 시나리오 테스트
   - 파일 업로드/다운로드 기능 테스트
   - **병렬 처리 테스트**: 병렬 실행 환경에서 발생할 수 있는 동기화 문제 및 오류 중점 테스트

## 구현 예시
### 환경 변수 로드
```python
# backend/config/settings.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 접근
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CURSOR_WORKSPACE_PATH = os.getenv("CURSOR_WORKSPACE_PATH")
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", 3000))

# 환경 변수 검증
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
```

### Cursor 통합 (그룹 유료 구독 사용)
```python
# backend/utils/cursor_integration.py
import subprocess
import os
from backend.config.settings import CURSOR_WORKSPACE_PATH

def create_file(file_path, content):
    """
    Cursor 워크스페이스에 파일을 생성합니다.
    그룹 유료 구독이 있으므로 직접 파일 시스템 접근을 사용합니다.
    """
    full_path = os.path.join(CURSOR_WORKSPACE_PATH, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'w') as f:
        f.write(content)
    
    return {"status": "success", "path": full_path}

def execute_code(command, working_dir=None):
    """
    Cursor 환경에서 코드를 실행합니다.
    """
    cwd = working_dir if working_dir else CURSOR_WORKSPACE_PATH
    result = subprocess.run(command, shell=True, cwd=cwd, 
                          capture_output=True, text=True)
    
    return {
        "status": "success" if result.returncode == 0 else "error",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode
    }
```