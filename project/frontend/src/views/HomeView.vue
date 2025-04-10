<template>
  <div class="home">
    <div class="hero">
      <h1>LangGraph 멀티에이전트 시스템</h1>
      <p>슈퍼바이저 패턴 기반의 병렬 처리가 가능한 AI 에이전트 시스템</p>
      <router-link to="/chat" class="btn">채팅 시작하기</router-link>
    </div>

    <div class="features card">
      <h2>주요 기능</h2>
      <ul>
        <li>
          <strong>슈퍼바이저 에이전트</strong>: 작업을 분석하고 하위 에이전트에게 적절히 할당합니다.
        </li>
        <li>
          <strong>계획 수립 에이전트</strong>: 작업을 단계별로 분해하고 실행 계획을 수립합니다.
        </li>
        <li>
          <strong>코드 생성 에이전트</strong>: 요구사항에 맞는 코드를 생성하고 파일로 저장합니다.
        </li>
        <li>
          <strong>병렬 처리</strong>: 모든 에이전트는 병렬로 실행되어 처리 속도를 극대화합니다.
        </li>
        <li>
          <strong>실시간 업데이트</strong>: WebSocket을 통해 작업 진행 상황을 실시간으로 확인할 수 있습니다.
        </li>
      </ul>
    </div>

    <div class="system-overview card">
      <h2>시스템 구성</h2>
      <p>이 시스템은 다음과 같은 컴포넌트로 구성되어 있습니다:</p>
      <ul>
        <li><strong>프론트엔드</strong>: Vue.js 기반의 사용자 인터페이스 (포트: 5174)</li>
        <li><strong>백엔드</strong>: FastAPI를 사용한 Python 서버 (포트: 6000)</li>
        <li><strong>에이전트 시스템</strong>: LangGraph 기반의 멀티에이전트 시스템</li>
        <li><strong>파일 시스템</strong>: 로컬 파일 시스템을 활용한 코드 저장 및 관리</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  padding: 2rem 1rem;
  margin-bottom: 2rem;
}

.hero h1 {
  font-size: 2.5rem;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.hero p {
  font-size: 1.2rem;
  color: var(--color-light-text);
  margin-bottom: 2rem;
}

.features, .system-overview {
  margin-bottom: 2rem;
}

h2 {
  color: var(--color-primary);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

ul {
  padding-left: 1.5rem;
}

li {
  margin-bottom: 0.5rem;
}

strong {
  color: var(--color-secondary);
}
</style> 