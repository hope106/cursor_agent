"""
코드 생성 에이전트 구현
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import os

from backend.agents.base_agent import BaseAgent
from backend.utils.anthropic_client import anthropic_client
from backend.utils.cursor_integration import CursorIntegration

class CodeGenerationAgent(BaseAgent):
    """
    코드 생성 에이전트: 요구사항에 맞는 코드 생성
    """
    
    def __init__(self, name: str = "코드 생성 에이전트", cursor_integration: Optional[CursorIntegration] = None):
        """
        코드 생성 에이전트 초기화
        
        Args:
            name: 에이전트 이름
            cursor_integration: Cursor 통합 인스턴스
        """
        super().__init__(name)
        self.cursor = cursor_integration or CursorIntegration()
    
    async def generate_code(self, task: str, plan: Optional[str] = None) -> Dict[str, Any]:
        """
        코드 생성
        
        Args:
            task: 수행할 작업 설명
            plan: 계획 (있는 경우)
            
        Returns:
            생성된 코드
        """
        prompt = task
        if plan:
            prompt = f"""
            작업: {task}
            
            계획: {plan}
            
            위 작업과 계획에 따라 코드를 생성해주세요.
            """
        
        system_message = """
        당신은 요구사항에 맞는 코드를 생성하는 코드 생성 에이전트입니다.
        주어진 작업과 계획을 분석하고 최적의 코드를 작성하세요.
        
        다음 규칙을 따라주세요:
        1. 코드는 실행 가능하고 버그가 없어야 합니다
        2. 최신 라이브러리와 표준을 따라야 합니다
        3. 적절한 주석과 문서화를 포함해야 합니다
        4. 효율적이고 가독성이 좋아야 합니다
        5. 보안 및 예외 처리를 고려해야 합니다
        
        코드 블록은 ```language ... ``` 형식으로 작성하세요.
        JSON 형식으로 다음 정보를 포함하여 응답해주세요:
        - filename: 파일명
        - language: 언어
        - code: 코드 내용
        - description: 코드 설명
        """
        
        response = anthropic_client.get_completion(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3,
            max_tokens=2000
        )
        
        if response["status"] == "error":
            logger.error(f"코드 생성 실패: {response.get('message')}")
            return {
                "status": "error",
                "message": "코드를 생성하는데 문제가 발생했습니다."
            }
        
        return {
            "status": "success",
            "generated_code": response["content"],
            "raw_response": response
        }
    
    async def extract_code_files(self, generated_code: str) -> Dict[str, Any]:
        """
        생성된 코드에서 파일 정보 추출
        
        Args:
            generated_code: 생성된 코드 텍스트
            
        Returns:
            파일 정보 목록
        """
        # 실제 구현에서는 생성된 코드에서 파일 정보를 파싱하는 로직 추가
        # 여기서는 예시로 간단하게 구현
        
        # JSON 형식으로 파싱 시도
        try:
            import re
            import json
            
            logger.info(f"생성된 코드 추출 시작: {generated_code[:100]}...")
            
            # 그냥 안전하게 가장 일반적인 형태로 추출
            files = []
            
            # JSON 형식 추출 시도
            json_match = re.search(r'({[\s\S]*})', generated_code)
            if json_match:
                try:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                    
                    # 저장 경로에 tests 폴더 추가
                    filename = data.get("filename", "")
                    
                    # 파일 이름에 경로가 없으면 tests/ 추가
                    if not filename.startswith("/") and "tests/" not in filename and "tests\\" not in filename:
                        if "tests" == filename.split("/")[0]:
                            # tests가 이미 포함되어 있는 경우
                            filename = filename
                        else:
                            # tests가 포함되어 있지 않은 경우
                            filename = "tests/" + filename
                    
                    files.append({
                        "filename": filename,
                        "language": data.get("language", ""),
                        "code": data.get("code", "").replace("```vue\n", "").replace("\n```", "").strip(),
                        "description": data.get("description", "")
                    })
                    
                    logger.info(f"JSON 형식으로 파일 추출 성공: {filename}")
                except Exception as e:
                    logger.warning(f"JSON 파싱 실패, 다른 방법 시도: {str(e)}")
            
            # 코드 블록 추출 시도 (JSON 파싱 실패 시)
            if not files:
                code_match = re.search(r'```([a-zA-Z]*)\n([\s\S]*?)```', generated_code)
                if code_match:
                    language = code_match.group(1) or "text"
                    code = code_match.group(2)
                    
                    # 파일명 추출 시도
                    filename_match = re.search(r'"filename"\s*:\s*"([^"]+)"', generated_code)
                    filename = filename_match.group(1) if filename_match else "example." + ("vue" if language == "vue" else "txt")
                    
                    # 파일 이름에 경로가 없으면 tests/ 추가
                    if not filename.startswith("/") and "tests/" not in filename and "tests\\" not in filename:
                        if "tests" == filename.split("/")[0]:
                            # tests가 이미 포함되어 있는 경우
                            filename = filename
                        else:
                            # tests가 포함되어 있지 않은 경우
                            filename = "tests/" + filename
                    
                    # 설명 추출 시도
                    description_match = re.search(r'"description"\s*:\s*"([^"]+)"', generated_code)
                    description = description_match.group(1) if description_match else f"{language} 파일"
                    
                    files.append({
                        "filename": filename,
                        "language": language,
                        "code": code,
                        "description": description
                    })
                    
                    logger.info(f"코드 블록에서 파일 추출 성공: {filename}")
            
            # 파일 추출 실패 시 기본값 사용
            if not files:
                logger.warning("파일 정보 추출 실패, 기본값 사용")
                filename = "tests/example.vue"
                files.append({
                    "filename": filename,
                    "language": "vue",
                    "code": "<!-- 기본 코드 -->\n" + generated_code,
                    "description": "코드 추출 실패로 생성된 기본 파일"
                })
            
            return {
                "status": "success",
                "files": files
            }
        except Exception as e:
            logger.error(f"코드 추출 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"생성된 코드에서 파일 정보를 추출하는데 실패했습니다: {str(e)}"
            }
    
    async def save_code_files(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        코드 파일 저장
        
        Args:
            files: 파일 정보 목록
            
        Returns:
            저장 결과
        """
        results = []
        success_count = 0
        error_count = 0
        
        for file in files:
            filename = file.get("filename")
            code = file.get("code")
            
            if not filename or not code:
                error_count += 1
                results.append({
                    "filename": filename or "unknown",
                    "status": "error",
                    "message": "파일명 또는 코드가 없습니다."
                })
                continue
            
            try:
                # Cursor 통합을 통해 파일 생성
                result = self.cursor.create_file(filename, code)
                
                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
                
                results.append({
                    "filename": filename,
                    "status": result["status"],
                    "message": result.get("message", ""),
                    "path": result.get("path", "")
                })
            except Exception as e:
                error_count += 1
                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": f"파일 저장 중 오류 발생: {str(e)}"
                })
        
        return {
            "status": "success" if error_count == 0 else "partial_success" if success_count > 0 else "error",
            "message": f"파일 저장 완료: 성공 {success_count}개, 실패 {error_count}개",
            "results": results
        }
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        상태 처리 및 결과 반환
        
        Args:
            state: 현재 상태
            
        Returns:
            처리 결과
        """
        self.log_start(state)
        
        try:
            task = state.get("task")
            if not task:
                return {"status": "error", "message": "수행할 작업이 지정되지 않았습니다."}
            
            # 계획이 있으면 사용
            plan = None
            if "plan" in state:
                plan = state["plan"]
            
            # 요청 텍스트에서 파일 타입 추출
            file_type = self.extract_file_type_from_request(task)
            file_summary = self.generate_file_summary(task)
            
            # 저장 경로 확인
            save_path = state.get("save_path")
            if save_path:
                logger.info(f"저장 경로 지정됨: {save_path}")
            
            # 1. 코드 생성
            generated_code = await self.generate_code(task, plan)
            if generated_code["status"] != "success":
                return generated_code
            
            # 2. 코드 파일 추출
            extracted_files = await self.extract_code_files(generated_code["generated_code"])
            if extracted_files["status"] != "success":
                return extracted_files
            
            # 저장 경로 지정이 있으면 적용
            if save_path:
                updated_files = []
                for file in extracted_files["files"]:
                    filename = file["filename"]
                    # 파일 이름이 없거나 기본값인 경우, 요청 내용에서 추출한 정보 사용
                    if not filename or filename == "tests/example.vue":
                        # 파일 이름 생성
                        new_filename = self.generate_filename(save_path, file_summary, file_type)
                        file["filename"] = new_filename
                        logger.info(f"파일명 생성: {new_filename}")
                    # 절대 경로로 시작하지 않고, 특별한 경로 지정이 없는 경우만 처리
                    elif not filename.startswith("/"):
                        # 이미 경로가 있으면 기존 경로 유지
                        if "/" in filename:
                            # 상대 경로가 있는 경우 확인
                            path_parts = filename.split("/")
                            if path_parts[0] != os.path.basename(save_path):
                                # 저장 경로와 다른 경우, 저장 경로로 변경
                                base_filename = os.path.basename(filename)
                                file["filename"] = f"{os.path.basename(save_path)}/{base_filename}"
                        else:
                            # 상대 경로가 없는 경우
                            file["filename"] = f"{os.path.basename(save_path)}/{filename}"
                        logger.info(f"파일 경로 업데이트: {filename} -> {file['filename']}")
                    updated_files.append(file)
                extracted_files["files"] = updated_files
            
            # 3. 코드 파일 저장
            save_result = await self.save_code_files(extracted_files["files"])
            
            # 결과 반환
            result = {
                "status": save_result["status"],
                "message": save_result["message"],
                "generated_code": generated_code,
                "files": extracted_files["files"],
                "save_results": save_result["results"]
            }
            
            self.log_completion(state, result)
            return result
        
        except Exception as e:
            self.log_error(state, e)
            return {
                "status": "error",
                "message": f"코드 생성 중 오류 발생: {str(e)}"
            }
    
    def extract_file_type_from_request(self, request: str) -> str:
        """
        요청 텍스트에서 파일 타입 추출
        
        Args:
            request: 요청 텍스트
            
        Returns:
            파일 타입 (.vue, .js, .html 등)
        """
        import re
        
        # 파일 확장자 패턴
        file_patterns = {
            r'\b(vue|\.vue)\b': '.vue',
            r'\b(javascript|js|\.js)\b': '.js',
            r'\b(typescript|ts|\.ts)\b': '.ts',
            r'\b(html|\.html)\b': '.html',
            r'\b(css|\.css)\b': '.css',
            r'\b(python|py|\.py)\b': '.py',
            r'\b(react|jsx|\.jsx)\b': '.jsx',
            r'\b(tsx|\.tsx)\b': '.tsx',
        }
        
        # 요청 텍스트에서 파일 타입 찾기
        for pattern, ext in file_patterns.items():
            if re.search(pattern, request.lower()):
                logger.info(f"요청에서 파일 타입 감지: {ext}")
                return ext
        
        # 기본값은 Vue 파일
        logger.info("파일 타입을 감지할 수 없어 기본값 사용: .vue")
        return '.vue'
    
    def generate_file_summary(self, request: str) -> str:
        """
        요청 텍스트에서 파일 내용 요약하여 파일명 생성
        
        Args:
            request: 요청 텍스트
            
        Returns:
            10글자 내외의 파일명
        """
        import re
        
        # 특수문자 제거 및 공백을 언더스코어로 변경
        words = re.sub(r'[^\w\s]', '', request.lower()).split()
        
        # 주요 키워드 추출 (예: 버튼, 알림, 로그인 등)
        keywords = ['button', 'alert', 'login', 'form', 'list', 'table', 'modal', 'menu', '버튼', '알림', '로그인', '폼', '리스트', '테이블', '모달', '메뉴']
        
        file_name = ""
        
        # 키워드 기반 파일명 생성
        for keyword in keywords:
            if keyword in request.lower():
                if keyword in ['button', '버튼']:
                    file_name = 'Button'
                elif keyword in ['alert', '알림']:
                    file_name = 'Alert'
                elif keyword in ['login', '로그인']:
                    file_name = 'Login'
                elif keyword in ['form', '폼']:
                    file_name = 'Form'
                elif keyword in ['list', '리스트']:
                    file_name = 'List'
                elif keyword in ['table', '테이블']:
                    file_name = 'Table'
                elif keyword in ['modal', '모달']:
                    file_name = 'Modal'
                elif keyword in ['menu', '메뉴']:
                    file_name = 'Menu'
                break
        
        # 키워드가 없는 경우 단어 조합으로 파일명 생성
        if not file_name and words:
            # 중요 단어 (명사) 우선 사용
            important_words = []
            for word in words:
                if len(word) > 2:  # 3글자 이상 단어만 고려
                    important_words.append(word)
            
            if important_words:
                # 첫 번째 중요 단어를 사용하고 첫 글자를 대문자로 변경
                file_name = important_words[0].capitalize()
                
                # 두 번째 중요 단어가 있으면 추가
                if len(important_words) > 1 and len(file_name) + len(important_words[1]) <= 10:
                    file_name += important_words[1].capitalize()
            else:
                # 중요 단어가 없으면 처음 몇 개 단어 사용
                combined = ''.join([w.capitalize() for w in words[:3] if w])
                file_name = combined[:10]  # 10글자로 제한
        
        # 파일명이 없으면 기본값 사용
        if not file_name:
            file_name = "Component"
        
        logger.info(f"요청에서 파일명 생성: {file_name}")
        return file_name
    
    def generate_filename(self, save_path: str, base_name: str, file_ext: str) -> str:
        """
        최종 파일명 생성 (중복 확인 및 처리)
        
        Args:
            save_path: 저장 경로
            base_name: 기본 파일명
            file_ext: 파일 확장자
            
        Returns:
            최종 파일명 (경로 포함)
        """
        import os
        
        # 경로가 절대 경로인지 확인
        if os.path.isabs(save_path):
            base_dir = save_path
        else:
            # 상대 경로인 경우 현재 작업 디렉토리 기준으로 처리
            base_dir = os.path.join(os.getcwd(), save_path)
        
        # 기본 파일 경로
        relative_path = os.path.basename(save_path)
        file_path = f"{relative_path}/{base_name}{file_ext}"
        full_path = os.path.join(base_dir, f"{base_name}{file_ext}")
        
        # 이미 존재하는 파일인지 확인
        counter = 1
        while os.path.exists(full_path):
            # 파일이 이미 존재하면 숫자 추가
            new_name = f"{base_name}{counter}{file_ext}"
            file_path = f"{relative_path}/{new_name}"
            full_path = os.path.join(base_dir, new_name)
            counter += 1
            
            # 안전장치 (무한루프 방지)
            if counter > 100:
                import time
                # 타임스탬프를 추가하여 유니크한 파일명 생성
                timestamp = int(time.time())
                new_name = f"{base_name}{timestamp}{file_ext}"
                file_path = f"{relative_path}/{new_name}"
                break
        
        logger.info(f"최종 파일명 생성: {file_path}")
        return file_path 