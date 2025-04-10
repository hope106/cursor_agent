# LangGraph 멀티에이전트 시스템 프론트엔드

Vue.js로 개발된 LangGraph 멀티에이전트 시스템의 웹 인터페이스입니다.

## 기능

- 홈 페이지: 시스템 정보와 기능 설명
- 채팅 인터페이스: 에이전트와 실시간 대화
- 파일 업로드: 코드 파일 분석 및 처리 기능
- 실시간 업데이트: WebSocket을 통한 에이전트 작업 상태 수신

## 설치 및 설정

1. 필요한 패키지 설치:

```bash
npm install
```

2. 개발 서버 실행:

```bash
npm run dev
```

3. 프로덕션 빌드:

```bash
npm run build
```

## 환경 설정

프로젝트에서 사용하는 기본 API URL은 `http://localhost:6000`으로 설정되어 있습니다. 다른 URL을 사용하려면 `main.js` 파일에서 `axios.defaults.baseURL` 값을 변경하세요.

## 백엔드 연결

이 프론트엔드는 FastAPI로 개발된 백엔드 서버와 통신합니다. 백엔드는 다음 기능을 제공합니다:

- REST API 엔드포인트 (`/api/v1/process`): 요청 처리
- WebSocket 엔드포인트 (`/api/v1/ws/{client_id}`): 실시간 업데이트
- 파일 업로드 엔드포인트 (`/api/v1/upload`): 파일 처리

백엔드 서버가 실행 중이어야 프론트엔드가 정상적으로 동작합니다.

## 프로젝트 구조

- `src/views/`: 페이지 컴포넌트 (HomeView, ChatView)
- `src/router/`: 라우터 설정
- `src/assets/`: CSS 및 정적 파일
- `src/App.vue`: 메인 애플리케이션 컴포넌트 