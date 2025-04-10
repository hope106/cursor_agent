"""
코드 생성 테스트 스크립트
"""
import os
import json
import asyncio
from pathlib import Path

# 프로젝트 루트 디렉토리를 파이썬 패스에 추가
import sys
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.utils.anthropic_client import anthropic_client

async def test_code_generation():
    """Anthropic API를 사용하여 코드 생성을 테스트합니다."""
    prompt = "vue 파일을 사용해서 'Hello World11111' alert를 표시하는 버튼을 만들어주세요. 파일은 tests 폴더에 저장해주세요."
    
    system_message = """
    당신은 요구사항에 맞는 코드를 생성하는 코드 생성 에이전트입니다.
    주어진 작업을 분석하고 최적의 코드를 작성하세요.
    
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
    
    print("Anthropic API 호출 중...")
    response = anthropic_client.get_completion(
        prompt=prompt,
        system_message=system_message,
        temperature=0.3,
        max_tokens=2000
    )
    
    print("\n응답 상태:", response["status"])
    
    if response["status"] == "error":
        print("오류:", response.get("message"))
        return
    
    # 응답 내용 출력
    print("\n=== 응답 내용 ===")
    print(response["content"])
    
    # JSON 데이터 추출 시도
    try:
        # 코드 블록 추출 시도
        import re
        content = response["content"]
        
        # 코드 블록 패턴 찾기
        code_pattern = r'```(vue|javascript|js|html)(.*?)```'
        code_match = re.search(code_pattern, content, re.DOTALL)
        
        if code_match:
            code_content = code_match.group(2).strip()
            
            # 파일명 찾기
            filename_match = re.search(r'"filename"\s*:\s*"([^"]+)"', content)
            if filename_match:
                filename = filename_match.group(1)
            else:
                filename = "HelloWorld.vue"
                
            # tests 폴더 경로 추가
            if not filename.startswith("/") and "tests/" not in filename and "tests\\" not in filename:
                filename = f"tests/{filename}"
                
            # 설명 찾기
            description_match = re.search(r'"description"\s*:\s*"([^"]+)"', content)
            description = description_match.group(1) if description_match else "Vue 컴포넌트"
            
            # 파일 저장 경로 생성
            save_dir = project_root / os.path.dirname(filename)
            os.makedirs(save_dir, exist_ok=True)
            
            file_path = project_root / filename
            
            # 파일 저장
            with open(file_path, "w") as f:
                f.write(code_content)
            
            print(f"\n파일이 성공적으로 저장되었습니다: {file_path}")
            print("\n=== 파일 정보 ===")
            print(f"파일명: {filename}")
            print(f"설명: {description}")
        else:
            print("\n코드 블록을 찾을 수 없습니다.")
    except Exception as e:
        print(f"\n파일 저장 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_code_generation()) 