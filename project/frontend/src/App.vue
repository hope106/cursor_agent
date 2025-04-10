<template>
  <div id="app">
    <nav class="app-nav">
      <router-link to="/" class="nav-link">홈</router-link>
      <router-link to="/chat" class="nav-link">채팅</router-link>
    </nav>
    <main class="app-main">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>© 2023 LangGraph 멀티에이전트 시스템</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
@import '@/assets/main.css';

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-nav {
  background-color: var(--color-primary);
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: center;
  box-shadow: var(--box-shadow);
}

.nav-link {
  margin: 0 1rem;
  color: white;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
}

.app-main {
  flex: 1;
  padding: 2rem;
  background-color: var(--color-background);
}

.app-footer {
  padding: 1rem;
  text-align: center;
  background-color: var(--color-light-bg);
  border-top: 1px solid var(--color-border);
  color: var(--color-light-text);
}
</style> 