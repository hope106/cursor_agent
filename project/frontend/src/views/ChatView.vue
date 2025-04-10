<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>AI 에이전트 채팅</h1>
      <div class="chat-status">상태: {{ chatStatus }}</div>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.role === 'user' ? 'user-message' : 'agent-message']">
        <div class="message-header" v-if="message.role === 'assistant' && message.agent">
          <span class="agent-name">{{ message.agent }}</span>
          <span class="agent-step" v-if="message.step">{{ message.step }}</span>
        </div>
        <div class="message-content">{{ message.content }}</div>
        <div class="message-details" v-if="message.details">
          <div v-if="message.details.generated_code" class="code-result">
            <h4>생성된 코드</h4>
            <div class="file-info">
              <span class="file-name">{{ message.details.generated_code.filename || message.details.generated_code.generated_code?.filename || '파일명 없음' }}</span>
              <span class="file-language">{{ message.details.generated_code.language || message.details.generated_code.generated_code?.language || '' }}</span>
            </div>
            <pre class="code-block">{{ message.details.generated_code.code || message.details.generated_code.generated_code?.code || '' }}</pre>
            <p class="code-description">{{ message.details.generated_code.description || message.details.generated_code.generated_code?.description || '' }}</p>
            <div class="code-actions">
              <button class="btn btn-sm btn-download" @click="downloadGeneratedFile(message.details.generated_code, message.details.generated_code.filename || message.details.generated_code.generated_code?.filename || 'generated_file.txt')">
                파일 다운로드
              </button>
              <button class="btn btn-sm btn-copy" @click="copyCodeToClipboard(message.details.generated_code.code || message.details.generated_code.generated_code?.code || '')">
                코드 복사
              </button>
            </div>
          </div>
          <div v-if="message.details.files && message.details.files.length > 0" class="files-list">
            <h4>생성된 파일 목록</h4>
            <div v-for="(file, fileIndex) in message.details.files" :key="fileIndex" class="file-item">
              <div class="file-info">
                <span class="file-name">{{ file.filename }}</span>
                <span class="file-language">{{ file.language }}</span>
              </div>
              <pre class="code-block">{{ file.code }}</pre>
              <p class="file-description">{{ file.description }}</p>
            </div>
          </div>
          <div v-if="message.details.save_results && message.details.save_results.length > 0" class="save-results">
            <h4>저장 결과</h4>
            <div v-for="(result, resultIndex) in message.details.save_results" :key="resultIndex" class="save-result-item">
              <div class="save-result-status" :class="{ 'success': result.status === 'success', 'error': result.status === 'error' }">
                {{ result.status === 'success' ? '✅' : '❌' }} {{ result.filename }}
              </div>
              <div class="save-result-message">{{ result.message }}</div>
              <div class="save-result-path" v-if="result.path">저장 경로: {{ result.path }}</div>
              <button 
                v-if="result.status === 'success' && message.details.generated_code" 
                class="btn btn-sm btn-download"
                @click="downloadGeneratedFile(message.details.generated_code, result.filename)"
              >
                파일 다운로드
              </button>
            </div>
          </div>
        </div>
        <div v-if="message.status === 'processing'" class="processing-indicator">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
          <div class="processing-text">에이전트가 작업 중입니다...</div>
        </div>
      </div>
    </div>

    <div class="chat-controls">
      <textarea
        v-model="newMessage"
        placeholder="메시지를 입력하세요..."
        @keydown.enter.prevent="sendMessage()"
        :disabled="isLoading"
      ></textarea>
      <div class="button-group">
        <button class="btn btn-primary" @click="sendMessage()" :disabled="isLoading">전송</button>
        <button class="btn btn-secondary" @click="toggleResponseLog">로그 {{showResponseLog ? '숨기기' : '보기'}}</button>
        <button class="btn btn-info" @click="sendCodeGenerationExample">코드 생성 예제</button>
      </div>
    </div>

    <div v-if="showResponseLog" class="response-log">
      <div class="log-header">
        <h3>에이전트 실행 로그</h3>
        <div class="log-actions">
          <button class="btn btn-sm" @click="copyToClipboard">복사</button>
          <button class="btn btn-secondary btn-sm" @click="clearResponseLog">지우기</button>
        </div>
      </div>
      <div class="log-tabs">
        <button 
          class="log-tab" 
          :class="{ 'active': activeLogTab === 'all' }" 
          @click="activeLogTab = 'all'"
        >
          전체
        </button>
        <button 
          class="log-tab" 
          :class="{ 'active': activeLogTab === 'agents' }" 
          @click="activeLogTab = 'agents'"
        >
          에이전트
        </button>
        <button 
          class="log-tab" 
          :class="{ 'active': activeLogTab === 'messages' }" 
          @click="activeLogTab = 'messages'"
        >
          메시지
        </button>
        <button 
          class="log-tab" 
          :class="{ 'active': activeLogTab === 'actions' }" 
          @click="activeLogTab = 'actions'"
        >
          액션
        </button>
        <button 
          class="log-tab" 
          :class="{ 'active': activeLogTab === 'server' }" 
          @click="activeLogTab = 'server'"
        >
          서버 로그
        </button>
      </div>
      <textarea class="log-content" readonly v-model="filteredLogs"></textarea>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import axios from 'axios'

export default {
  name: 'ChatView',
  setup() {
    const socket = ref(null)
    const responseLog = ref('') // 응답 로그를 저장할 ref 추가
    const showResponseLog = ref(false) // 로그 표시 여부 상태
    const newMessage = ref('')
    const isLoading = ref(false)
    const chatStatus = ref('연결 중...')
    const messages = ref([]) // 채팅 메시지 배열
    const messagesContainer = ref(null) // 메시지 컨테이너 참조
    const clientId = ref(`client-${Date.now()}`)
    const activeLogTab = ref('all') // 로그 탭 상태 추가

    // 로그 필터링
    const filteredLogs = computed(() => {
      if (activeLogTab.value === 'all') {
        return responseLog.value;
      }
      
      const lines = responseLog.value.split('\n');
      const filteredLines = lines.filter(line => {
        if (activeLogTab.value === 'agents' && line.includes('에이전트')) {
          return true;
        }
        if (activeLogTab.value === 'messages' && (line.includes('🔵 송신') || line.includes('🟢 수신'))) {
          return true;
        }
        if (activeLogTab.value === 'actions' && line.includes('액션')) {
          return true;
        }
        if (activeLogTab.value === 'server' && line.includes('🖥️ 서버')) {
          return true;
        }
        return false;
      });
      
      return filteredLines.join('\n');
    });

    // 로그 복사
    const copyToClipboard = () => {
      navigator.clipboard.writeText(filteredLogs.value)
        .then(() => {
          alert('로그가 클립보드에 복사되었습니다.');
        })
        .catch(err => {
          console.error('클립보드 복사 실패:', err);
          alert('클립보드 복사에 실패했습니다.');
        });
    };

    // WebSocket 연결 설정
    const setupWebSocket = () => {
      console.log('WebSocket 설정 시작 - 단계 1');
      
      if (socket.value) {
        console.log('기존 WebSocket 연결 종료 - 단계 2');
        socket.value.close();
      }
      
      // Vite 프록시를 통해 연결
      const wsUrl = `ws://${window.location.host}/ws/${clientId.value}`;
      console.log('WebSocket 연결 URL 구성 완료 - 단계 3:', wsUrl);
      
      try {
        console.log('WebSocket 인스턴스 생성 시도 - 단계 4');
        socket.value = new WebSocket(wsUrl);
        console.log('WebSocket 인스턴스 생성 완료 - 단계 5:', socket.value);
        
        // 연결 타임아웃 설정
        const connectTimeout = setTimeout(() => {
          if (socket.value && socket.value.readyState !== WebSocket.OPEN) {
            console.error('WebSocket 연결 타임아웃 발생');
            socket.value.close();
            socket.value = null;
            
            // HTTP 모드로 전환
            console.log('타임아웃으로 인해 HTTP 모드로 전환');
          }
        }, 5000); // 5초 타임아웃
        
        socket.value.onopen = () => {
          console.log('WebSocket onopen 이벤트 발생 - 단계 6: 연결 성공');
          clearTimeout(connectTimeout); // 타임아웃 제거
        };
        
        socket.value.onmessage = (event) => {
          console.log('WebSocket onmessage 이벤트 발생 - 메시지 수신:', event.data);
          try {
            const data = JSON.parse(event.data)
            // 로그에 응답 데이터 추가
            addToLog('수신', data)
            
            // 서버 로그 처리
            if (data.logs && Array.isArray(data.logs)) {
              data.logs.forEach(logEntry => {
                addToLog('서버', logEntry);
              });
            }
            
            // 오류 상태 처리
            if (data.status === 'error') {
              console.error('서버 오류 응답:', data.message);
              messages.value.push({
                role: 'assistant',
                content: `오류 발생: ${data.message}`,
                status: 'error',
                timestamp: new Date()
              });
              return;
            }
            
            handleAgentResponse(data)
          } catch (error) {
            console.error('WebSocket 메시지 파싱 오류:', error)
            addToLog('오류', error)
          }
        }
        
        socket.value.onclose = (event) => {
          console.log('WebSocket onclose 이벤트 발생 - 단계 7:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          });
          
          // WebSocket 연결이 실패하면 HTTP 요청 모드로 전환
          if (event.code !== 1000) { // 1000은 정상 종료
            console.log('WebSocket 연결 비정상 종료(code != 1000) - HTTP 모드로 전환');
          } else {
            // 정상 종료된 경우만 재연결 시도
            console.log('WebSocket 정상 종료(code = 1000) - 3초 후 재연결 시도');
            setTimeout(setupWebSocket, 3000);
          }
        };
        
        socket.value.onerror = (error) => {
          console.error('WebSocket onerror 이벤트 발생 - 단계 8:', error);
          
          // 오류 세부 정보 기록
          console.error('WebSocket 오류 세부 정보:', {
            host: window.location.hostname,
            origin: window.location.origin,
            wsUrl: wsUrl,
            readyState: socket.value?.readyState,
            readyStateText: ['CONNECTING(0)', 'OPEN(1)', 'CLOSING(2)', 'CLOSED(3)'][socket.value?.readyState || 0],
            browser: navigator.userAgent
          });
          // WebSocket 오류 발생 시 연결 객체를 null로 설정하여 HTTP 모드로 전환
          socket.value = null
        }
      } catch (error) {
        console.error('WebSocket 초기화 오류 - 단계 9:', {
          errorName: error.name,
          errorMessage: error.message,
          errorStack: error.stack
        });
        socket.value = null
      }
    }

    // 메시지 전송
    const sendMessage = async (customMessage = null) => {
      let messageToSend = customMessage;
      
      if (!messageToSend) {
        if (!newMessage.value.trim()) return;
        
        // 사용자 입력이 코드 생성 요청인지 확인
        const isCodeGeneration = checkIfCodeGenerationRequest(newMessage.value);
        
        if (isCodeGeneration) {
          // 코드 생성 요청으로 처리
          sendUserMessageAsCodeGeneration(newMessage.value);
          return;
        }
        
        messageToSend = {
          request: newMessage.value,
          save_path: "/Users/jiryang.kim/workspace/ai_agent/cursor/project/tests"
        };
        
        // 사용자 메시지 추가
        messages.value.push({
          role: 'user',
          content: newMessage.value,
          status: 'sent',
          timestamp: new Date()
        });
      } else if (typeof messageToSend === 'object' && 'target' in messageToSend) {
        // 이벤트 객체가 전달된 경우 처리
        messageToSend = {
          request: newMessage.value,
          save_path: "/Users/jiryang.kim/workspace/ai_agent/cursor/project/tests"
        };
      } else {
        // customMessage일 경우 request 필드 추가
        if (!messageToSend.request && messageToSend.message) {
          messageToSend = {
            request: messageToSend.message,
            save_path: messageToSend.save_path,
            action: messageToSend.action,
            params: messageToSend.params
          };
        }
      }
      
      isLoading.value = true;
      
      try {
        // WebSocket이 연결되어 있고 준비 상태인 경우
        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
          console.log('WebSocket으로 전송할 데이터:', messageToSend);
          const sendData = JSON.stringify(messageToSend);
          
          // 로그에 송신 데이터 추가
          addToLog('송신', messageToSend);
          
          socket.value.send(sendData);
        } else {
          // WebSocket 연결이 없는 경우 HTTP 요청 사용
          chatStatus.value = 'HTTP 모드 (WebSocket 연결 없음)';
          
          const apiUrl = 'http://localhost:8000/chat';
          const requestData = messageToSend;
          
          // 로그에 HTTP 요청 데이터 추가
          addToLog('HTTP 요청', requestData);
          
          try {
            const response = await axios.post(apiUrl, requestData, {
              headers: {
                'Content-Type': 'application/json',
              },
            });
            
            // 로그에 HTTP 응답 데이터 추가
            addToLog('HTTP 응답', response.data);
            
            handleAgentResponse(response.data);
          } catch (httpError) {
            console.error('HTTP 요청 오류:', httpError);
            
            // 로그에 HTTP 오류 추가
            addToLog('오류', httpError);
            
            throw httpError;
          }
        }
      } finally {
        isLoading.value = false;
        newMessage.value = '';
      }
    };

    // 사용자 메시지가 코드 생성 요청인지 확인
    const checkIfCodeGenerationRequest = (message) => {
      // 코드 생성 관련 키워드 패턴
      const codeGenPatterns = [
        /코드.*생성/i,
        /만들어.*주세요/i,
        /생성.*해주세요/i,
        /코드.*작성/i,
        /파일.*만들/i,
        /개발.*해/i,
        /구현.*해/i,
        /component.*만들/i,
        /컴포넌트.*만들/i,
        /버튼.*만들/i,
        /폼.*만들/i,
        /화면.*만들/i,
        /페이지.*만들/i,
        /\.vue/i,
        /\.js/i,
        /\.html/i,
        /\.py/i
      ];
      
      // 메시지가 코드 생성 패턴과 일치하는지 확인
      for (const pattern of codeGenPatterns) {
        if (pattern.test(message)) {
          console.log('코드 생성 요청으로 감지:', message);
          return true;
        }
      }
      
      return false;
    };

    // 응답에서 코드를 추출하여 파일로 저장하는 함수
    const createFileFromResponse = async (data) => {
      try {
        // 코드 정보 추출
        let code = '';
        let filename = '';
        let language = '';
        let description = '';
        
        // 응답 객체에서 코드 정보 가져오기
        if (data.generated_code) {
          const generatedCode = typeof data.generated_code === 'string' 
            ? JSON.parse(data.generated_code.replace(/```json\n|\n```/g, ''))
            : data.generated_code;
          
          code = generatedCode.code || '';
          filename = generatedCode.filename || 'generated_file.txt';
          language = generatedCode.language || '';
          description = generatedCode.description || '';
        } else if (data.results?.generated_code?.generated_code) {
          const generatedCode = typeof data.results.generated_code.generated_code === 'string'
            ? JSON.parse(data.results.generated_code.generated_code.replace(/```json\n|\n```/g, ''))
            : data.results.generated_code.generated_code;
          
          code = generatedCode.code || '';
          filename = generatedCode.filename || 'generated_file.txt';
          language = generatedCode.language || '';
          description = generatedCode.description || '';
        }
        
        if (!code) {
          console.error('코드 내용이 없습니다.');
          return;
        }
        
        // 파일 경로 구성
        let filePath = filename;
        if (!filePath.startsWith('/')) {
          filePath = `/Users/jiryang.kim/workspace/ai_agent/cursor/project/tests/${filename}`;
        }
        
        console.log('파일 생성 시도:', {
          filePath,
          code: code.substring(0, 100) + (code.length > 100 ? '...' : ''),
          language,
          description: description.substring(0, 100) + (description.length > 100 ? '...' : '')
        });
        
        // 파일 다운로드 방식으로 저장
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename.split('/').pop(); // 경로에서 파일명만 추출
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // 로그 및 메시지 업데이트
        addToLog('에이전트', {
          action: 'save_file',
          filename: filePath,
          status: 'success',
          message: '파일이 생성되어 다운로드되었습니다.'
        });
        
        return {
          filename: filePath,
          status: 'success',
          message: '파일이 생성되어 다운로드되었습니다.'
        };
      } catch (error) {
        console.error('파일 생성 오류:', error);
        addToLog('오류', {
          action: 'save_file',
          error: error.message
        });
        
        return {
          status: 'error',
          message: `파일 생성 중 오류 발생: ${error.message}`
        };
      }
    };

    // 에이전트 응답 처리
    const handleAgentResponse = (data) => {
      // 에이전트 응답 메시지 추가
      if (data) {
        console.log('handleAgentResponse - 수신된 데이터:', data);
        
        // 서버에서 파일 저장 실패 시 클라이언트에서 직접 파일 생성 시도
        if ((data.save_results && data.save_results.some(r => r.status !== 'success')) || 
            (data.results?.save_results && data.results.save_results.some(r => r.status !== 'success'))) {
          console.log('서버 파일 저장 실패, 클라이언트에서 직접 파일 생성 시도');
          createFileFromResponse(data).then(result => {
            if (result && result.status === 'success') {
              console.log('클라이언트에서 파일 생성 성공:', result);
            }
          });
        }
        
        // 파일 저장 결과 확인 및 로깅
        if (data.save_results || data.results?.save_results) {
          const saveResults = data.save_results || data.results?.save_results;
          console.log('파일 저장 결과:', saveResults);
          
          if (Array.isArray(saveResults)) {
            saveResults.forEach(result => {
              let logType = result.status === 'success' ? '에이전트' : '오류';
              let logMessage = `파일 ${result.status === 'success' ? '저장 성공' : '저장 실패'}: ${result.filename} - ${result.message}`;
              addToLog(logType, { message: logMessage, path: result.path });
              
              // 파일 경로가 잘못된 경우 콘솔에 경고
              if (result.path && !result.path.includes('/tests/')) {
                console.warn('경로 오류: 파일이 tests 폴더에 저장되지 않았습니다.', result.path);
              }
            });
          }
        }
        
        // 생성된 코드 확인 및 로깅
        if (data.generated_code || data.results?.generated_code) {
          const generatedCode = data.generated_code || data.results?.generated_code;
          if (generatedCode && typeof generatedCode === 'object') {
            console.log('생성된 코드:', generatedCode);
            
            // 코드 내용이 있으면 로그에 추가
            if (generatedCode.code || generatedCode.generated_code?.code) {
              const code = generatedCode.code || generatedCode.generated_code?.code;
              const filename = generatedCode.filename || generatedCode.generated_code?.filename || 'unknown.file';
              addToLog('에이전트', { 
                action: 'code_generation', 
                filename: filename, 
                code_snippet: code.substring(0, 100) + (code.length > 100 ? '...' : '') 
              });
            }
          }
        }
        
        // 이미 처리 중인 메시지가 있는지 확인
        const processingIndex = messages.value.findIndex(m => m.status === 'processing');
        
        if (data.status === 'processing') {
          // 진행 중인 상태인 경우
          if (processingIndex >= 0) {
            // 기존 처리 중 메시지 업데이트
            messages.value[processingIndex] = {
              ...messages.value[processingIndex],
              content: data.message || '처리 중...',
              agent: data.agent || messages.value[processingIndex].agent,
              step: data.step || messages.value[processingIndex].step,
              details: data.details || messages.value[processingIndex].details,
              status: 'processing'
            };
          } else {
            // 새 처리 중 메시지 추가
            messages.value.push({
              role: 'assistant',
              content: data.message || '작업을 처리하고 있습니다...',
              agent: data.agent || '에이전트',
              step: data.step || '준비 중',
              status: 'processing',
              timestamp: new Date(),
              details: data.details || null
            });
          }
        } else if (data.status === 'completed' || data.status === 'success') {
          // 작업 완료 상태인 경우
          if (processingIndex >= 0) {
            // 처리 중이던 메시지 완료로 업데이트
            messages.value[processingIndex] = {
              ...messages.value[processingIndex],
              content: data.message || '작업이 완료되었습니다.',
              agent: data.agent || messages.value[processingIndex].agent,
              step: '완료됨',
              details: data.details || messages.value[processingIndex].details,
              status: 'completed'
            };
          } else {
            // 새 완료 메시지 추가
            messages.value.push({
              role: 'assistant',
              content: data.message || '작업이 완료되었습니다.',
              agent: data.agent || '에이전트',
              step: '완료됨',
              status: 'completed',
              timestamp: new Date(),
              details: data.details || null
            });
          }
        } else if (data.status === 'error') {
          // 오류 상태인 경우
          if (processingIndex >= 0) {
            // 처리 중이던 메시지 오류로 업데이트
            messages.value[processingIndex] = {
              ...messages.value[processingIndex],
              content: data.message || '오류가 발생했습니다.',
              agent: data.agent || messages.value[processingIndex].agent,
              step: '오류 발생',
              details: data.details || messages.value[processingIndex].details,
              status: 'error'
            };
          } else {
            // 새 오류 메시지 추가
            messages.value.push({
              role: 'assistant',
              content: data.message || '오류가 발생했습니다.',
              agent: data.agent || '에이전트',
              step: '오류 발생',
              status: 'error',
              timestamp: new Date(),
              details: data.details || null
            });
          }
        } else {
          // 기타 상태이거나 상태가 없는 경우 일반 메시지로 처리
          messages.value.push({
            role: 'assistant',
            content: data.message || '응답을 받았습니다.',
            agent: data.agent || '에이전트',
            step: data.step || null,
            timestamp: new Date(),
            details: data.details || null
          });
        }
        
        // 메시지가 추가된 후 스크롤을 아래로 이동
        nextTick(() => {
          if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
          }
        });
      }
    }

    // 파일 업로드 처리
    const handleFileUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      const formData = new FormData()
      formData.append('file', file)
      
      messages.value.push({
        content: `파일 업로드: ${file.name}`,
        role: 'user',
        timestamp: new Date(),
      })
      
      isLoading.value = true
      
      try {
        // 브라우저의 현재 호스트 정보를 활용해 API URL 구성
        const apiUrl = '/api/v1/upload';
        console.log('파일 업로드 URL:', apiUrl);
        
        const response = await axios.post(apiUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        console.log('파일 업로드 응답:', response.data);
        
        messages.value.push({
          content: response.data.message,
          role: 'assistant',
          timestamp: new Date(),
          details: response.data.details
        })
      } catch (error) {
        console.error('파일 업로드 오류:', error)
        messages.value.push({
          content: '파일 업로드 중 오류가 발생했습니다.',
          role: 'assistant',
          timestamp: new Date(),
          error: true
        })
      }
      
      isLoading.value = false
      event.target.value = null // 파일 입력 초기화
    }

    // 스크롤을 메시지 컨테이너 아래로 이동
    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
      })
    }

    // 시간 포맷
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }

    // WebSocket 테스트
    const testWebSocket = () => {
      try {
        // 테스트용 WebSocket 생성
        console.log('테스트 WebSocket 시작 - 단계 1')
        // Vite 프록시를 통해 연결
        const wsUrl = `ws://${window.location.host}/ws-test`
        console.log('테스트 WebSocket URL - 단계 2:', wsUrl)
        
        console.log('테스트 WebSocket 인스턴스 생성 시도 - 단계 3')
        const testSocket = new WebSocket(wsUrl)
        console.log('테스트 WebSocket 인스턴스 생성 완료 - 단계 4:', testSocket)
        
        // 연결 타임아웃 설정
        const testConnectTimeout = setTimeout(() => {
          if (testSocket && testSocket.readyState !== WebSocket.OPEN) {
            console.error('테스트 WebSocket 연결 타임아웃 발생');
            testSocket.close();
            
            messages.value.push({
              content: '소켓 테스트 실패: 연결 타임아웃(5초)이 발생했습니다.',
              role: 'assistant',
              timestamp: new Date(),
              error: true
            });
          }
        }, 5000); // 5초 타임아웃
        
        testSocket.onopen = () => {
          console.log('테스트 WebSocket onopen 이벤트 발생 - 단계 5')
          clearTimeout(testConnectTimeout); // 타임아웃 제거
          messages.value.push({
            content: '소켓 테스트: 연결 성공!',
            role: 'assistant',
            timestamp: new Date()
          })
          
          // 테스트 메시지 전송
          console.log('테스트 메시지 전송 - 단계 6')
          testSocket.send('테스트 메시지')
        }
        
        testSocket.onmessage = (event) => {
          console.log('테스트 WebSocket onmessage 이벤트 발생 - 단계 7:', event.data)
          messages.value.push({
            content: `소켓 테스트 응답: ${event.data}`,
            role: 'assistant',
            timestamp: new Date()
          })
          
          // 테스트 완료 후 소켓 종료
          console.log('테스트 WebSocket 종료 - 단계 8')
          testSocket.close()
        }
        
        testSocket.onerror = (error) => {
          console.error('테스트 WebSocket onerror 이벤트 발생 - 단계 9:', error)
          
          // 오류 세부 정보 기록
          console.error('테스트 WebSocket 오류 세부 정보:', {
            host: window.location.hostname,
            origin: window.location.origin,
            wsUrl: wsUrl,
            readyState: testSocket?.readyState,
            readyStateText: ['CONNECTING(0)', 'OPEN(1)', 'CLOSING(2)', 'CLOSED(3)'][testSocket?.readyState || 0],
            browser: navigator.userAgent
          })
          
          messages.value.push({
            content: `소켓 테스트 실패: 연결 오류가 발생했습니다. (${window.location.origin} -> ${wsUrl})`,
            role: 'assistant',
            timestamp: new Date(),
            error: true
          })
        }
        
        testSocket.onclose = (event) => {
          console.log('테스트 WebSocket onclose 이벤트 발생 - 단계 10:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          })
        }
      } catch (error) {
        console.error('테스트 WebSocket 초기화 오류 - 단계 11:', {
          errorName: error.name,
          errorMessage: error.message,
          errorStack: error.stack
        })
        messages.value.push({
          content: '소켓 테스트 실패: ' + error.message,
          role: 'assistant',
          timestamp: new Date(),
          error: true
        })
      }
    }

    // 로그 표시 토글
    const toggleResponseLog = () => {
      showResponseLog.value = !showResponseLog.value
    }
    
    // 로그 지우기
    const clearResponseLog = () => {
      responseLog.value = ''
    }

    // 코드 생성 예제 메시지 보내기
    const sendCodeGenerationExample = () => {
      const codeRequest = {
        request: "vue 파일을 사용해서 'Hello 5555' alert를 표시하는 버튼을 만들어주세요. 파일은 tests 폴더에 저장해주세요.",
        action: "code_generation",
        save_path: "/Users/jiryang.kim/workspace/ai_agent/cursor/project/tests"
      };
      
      // 메시지 추가
      messages.value.push({
        role: 'user',
        content: codeRequest.request,
        status: 'sent',
        timestamp: new Date()
      });
      
      // 처리 중 메시지 추가
      messages.value.push({
        role: 'assistant',
        content: '코드를 생성하고 있습니다...',
        agent: '코드생성 에이전트',
        step: '요청 처리 중',
        status: 'processing',
        timestamp: new Date()
      });
      
      // 메시지 전송
      sendMessage(codeRequest);
      
      // 입력 필드 초기화
      newMessage.value = '';
    }

    // 사용자 메시지를 코드 생성 요청으로 처리
    const sendUserMessageAsCodeGeneration = (userMessage) => {
      const codeRequest = {
        request: userMessage,
        action: "code_generation",
        save_path: "/Users/jiryang.kim/workspace/ai_agent/cursor/project/tests"
      };
      
      // 메시지 추가
      messages.value.push({
        role: 'user',
        content: userMessage,
        status: 'sent',
        timestamp: new Date()
      });
      
      // 처리 중 메시지 추가
      messages.value.push({
        role: 'assistant',
        content: '코드를 생성하고 있습니다...',
        agent: '코드생성 에이전트',
        step: '요청 처리 중',
        status: 'processing',
        timestamp: new Date()
      });
      
      // 메시지 전송
      sendMessage(codeRequest);
      
      // 입력 필드 초기화
      newMessage.value = '';
    }

    // 로그 추가 함수
    const addToLog = (type, data) => {
      const timestamp = new Date().toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
      
      let formattedData = '';
      let messageType = '';
      
      switch(type) {
        case '송신':
          messageType = '🔵 송신';
          break;
        case '수신':
          messageType = '🟢 수신';
          break;
        case 'HTTP 요청':
          messageType = '🔷 HTTP 요청';
          break;
        case 'HTTP 응답':
          messageType = '🟦 HTTP 응답';
          break;
        case '오류':
          messageType = '🔴 오류';
          break;
        case '에이전트':
          messageType = '👤 에이전트';
          break;
        case '액션':
          messageType = '🔨 액션';
          break;
        case '서버':
          messageType = '🖥️ 서버';
          break;
        default:
          messageType = type;
      }
      
      try {
        if (typeof data === 'string') {
          try {
            const jsonData = JSON.parse(data);
            formattedData = JSON.stringify(jsonData, null, 2);
            
            // 에이전트 정보 추출
            if (jsonData.agent && type === '수신') {
              addToLog('에이전트', {
                name: jsonData.agent,
                step: jsonData.step || '작업 중',
                status: jsonData.status || 'processing'
              });
            }
            
            // 액션 정보 추출
            if (jsonData.action && type === '수신') {
              addToLog('액션', {
                type: jsonData.action,
                target: jsonData.target || '',
                status: jsonData.status || ''
              });
            }
          } catch {
            formattedData = data;
          }
        } else {
          formattedData = JSON.stringify(data, null, 2);
        }
      } catch (error) {
        formattedData = `[형식화 오류: ${error.message}] ${String(data)}`;
      }
      
      responseLog.value += `[${timestamp}] ${messageType}:\n${formattedData}\n\n`;
      
      // 로그 영역 자동 스크롤
      nextTick(() => {
        const logEl = document.querySelector('.log-content');
        if (logEl) {
          logEl.scrollTop = logEl.scrollHeight;
        }
      });
    };

    // 생성된 코드를 파일로 다운로드
    const downloadGeneratedFile = (generatedCode, suggestedFilename) => {
      try {
        let code = '';
        let filename = suggestedFilename;
        
        if (typeof generatedCode === 'string') {
          try {
            const parsedCode = JSON.parse(generatedCode.replace(/```json\n|\n```/g, ''));
            code = parsedCode.code || generatedCode;
            if (parsedCode.filename) filename = parsedCode.filename.split('/').pop();
          } catch (e) {
            code = generatedCode;
          }
        } else if (generatedCode.code) {
          code = generatedCode.code;
          if (generatedCode.filename) filename = generatedCode.filename.split('/').pop();
        } else if (generatedCode.generated_code && generatedCode.generated_code.code) {
          code = generatedCode.generated_code.code;
          if (generatedCode.generated_code.filename) filename = generatedCode.generated_code.filename.split('/').pop();
        }
        
        if (!code) {
          console.error('다운로드할 코드가 없습니다.');
          return;
        }
        
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        addToLog('에이전트', {
          action: 'download_file',
          filename: filename,
          status: 'success',
          message: '파일이 다운로드되었습니다.'
        });
      } catch (error) {
        console.error('파일 다운로드 오류:', error);
        addToLog('오류', {
          action: 'download_file',
          error: error.message
        });
      }
    };

    // 코드를 클립보드에 복사
    const copyCodeToClipboard = (code) => {
      if (!code) {
        console.error('복사할 코드가 없습니다.');
        return;
      }
      
      navigator.clipboard.writeText(code)
        .then(() => {
          addToLog('에이전트', {
            action: 'copy_code',
            status: 'success',
            message: '코드가 클립보드에 복사되었습니다.'
          });
        })
        .catch(err => {
          console.error('클립보드 복사 실패:', err);
          addToLog('오류', {
            action: 'copy_code',
            error: err.message
          });
        });
    };

    // 컴포넌트 마운트 시 WebSocket 연결
    onMounted(() => {
      setupWebSocket()
      
      // 초기 인사 메시지
      setTimeout(() => {
        messages.value.push({
          content: '안녕하세요! 슈퍼바이저 패턴 기반의 멀티에이전트 시스템입니다. 어떤 작업을 도와드릴까요?',
          role: 'assistant',
          timestamp: new Date()
        })
      }, 500)
    })

    // 컴포넌트 언마운트 시 WebSocket 연결 해제
    onUnmounted(() => {
      if (socket.value) {
        socket.value.close()
      }
    })

    // 메시지 추가 시 자동 스크롤
    watch(messages, () => {
      scrollToBottom()
    })

    return {
      messagesContainer,
      messages,
      sendMessage,
      handleFileUpload,
      formatTime,
      testWebSocket,
      responseLog,
      showResponseLog,
      toggleResponseLog,
      clearResponseLog,
      newMessage,
      isLoading,
      chatStatus,
      sendCodeGenerationExample,
      activeLogTab,
      filteredLogs,
      copyToClipboard,
      downloadGeneratedFile,
      copyCodeToClipboard
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  box-sizing: border-box;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ccc;
  margin-bottom: 1rem;
}

.chat-status {
  font-size: 0.9rem;
  color: #666;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 1rem;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 80%;
  padding: 0.8rem;
  border-radius: 1rem;
  margin-bottom: 0.5rem;
}

.user-message {
  align-self: flex-end;
  background-color: #007bff;
  color: white;
}

.agent-message {
  align-self: flex-start;
  background-color: #f1f1f1;
  color: #333;
}

.chat-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #eee;
}

.button-group {
  display: flex;
  gap: 0.5rem;
}

textarea {
  width: 100%;
  resize: none;
  min-height: 80px;
  padding: 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid #ccc;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: bold;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.response-log {
  margin-top: 1rem;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  overflow: hidden;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f1f1f1;
  border-bottom: 1px solid #ddd;
}

.log-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.log-tabs {
  display: flex;
  border-bottom: 1px solid #ddd;
  background-color: #f8f9fa;
}

.log-tab {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: bold;
  color: #6c757d;
  border-bottom: 2px solid transparent;
}

.log-tab.active {
  color: #007bff;
  border-bottom: 2px solid #007bff;
}

.log-tab:hover {
  color: #007bff;
  background-color: #f1f1f1;
}

.log-content {
  width: 100%;
  height: 200px;
  padding: 0.5rem;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  white-space: pre-wrap;
  overflow-y: auto;
  background-color: #f8f9fa;
  color: #333;
  border: none;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: #666;
}

.agent-name {
  font-weight: bold;
  color: #17a2b8;
}

.agent-step {
  color: #6c757d;
  font-style: italic;
}

.message-details {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
}

.code-result, .files-list, .save-results {
  margin-bottom: 1rem;
}

.code-result h4, .files-list h4, .save-results h4 {
  margin: 0.5rem 0;
  color: #17a2b8;
  font-size: 0.9rem;
}

.file-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.file-name {
  font-weight: bold;
  color: #007bff;
}

.file-language {
  color: #6c757d;
}

.code-block {
  background-color: #f8f9fa;
  padding: 0.75rem;
  border-radius: 0.25rem;
  border: 1px solid #eee;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0.5rem 0;
}

.code-description, .file-description {
  font-size: 0.9rem;
  color: #666;
  margin: 0.5rem 0;
}

.save-result-item {
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  border-radius: 0.25rem;
  background-color: #f8f9fa;
}

.save-result-status {
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.save-result-status.success {
  color: #28a745;
}

.save-result-status.error {
  color: #dc3545;
}

.save-result-message {
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.save-result-path {
  font-size: 0.8rem;
  color: #6c757d;
  font-family: 'Courier New', monospace;
}

.processing-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #eee;
}

.loading-dots {
  display: flex;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  margin: 0 4px;
  border-radius: 50%;
  background-color: #17a2b8;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.processing-text {
  font-size: 0.9rem;
  color: #6c757d;
}

.btn-download {
  background-color: #28a745;
  color: white;
  margin-top: 0.5rem;
}

.code-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-copy {
  background-color: #6c757d;
  color: white;
}
</style> 