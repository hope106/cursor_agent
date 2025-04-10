import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

import './assets/main.css'

// API 기본 URL 설정
axios.defaults.baseURL = 'http://127.0.0.1:6000'

// Axios 기본 설정
axios.defaults.timeout = 30000 // 30초 타임아웃
axios.defaults.headers.common['Content-Type'] = 'application/json'

// Axios 인터셉터 설정
axios.interceptors.request.use(
  config => {
    console.log('API 요청:', config.url, config.data)
    return config
  },
  error => {
    console.error('API 요청 오류:', error)
    return Promise.reject(error)
  }
)

axios.interceptors.response.use(
  response => {
    console.log('API 응답:', response.status, response.data)
    return response
  },
  error => {
    console.error('API 응답 오류:', error.response?.status, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Axios를 전역으로 설정
app.config.globalProperties.$axios = axios

app.mount('#app') 