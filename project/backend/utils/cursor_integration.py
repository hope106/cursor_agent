"""
Cursor 통합 유틸리티
그룹 유료 구독 환경을 활용한 파일 시스템 기반 연동
"""
import os
import subprocess
from pathlib import Path
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from backend.config.settings import CURSOR_WORKSPACE_PATH

class CursorIntegration:
    """Cursor 통합 클래스"""
    
    def __init__(self, workspace_path: Optional[str] = None):
        """
        Cursor 통합 초기화
        
        Args:
            workspace_path: Cursor 워크스페이스 경로 (없으면 환경 변수에서 로드)
        """
        self.workspace_path = workspace_path or CURSOR_WORKSPACE_PATH
        if not self.workspace_path:
            raise ValueError("Cursor 워크스페이스 경로가 설정되지 않았습니다.")
        
        # 워크스페이스 경로 확인
        if not os.path.exists(self.workspace_path):
            raise ValueError(f"지정된 워크스페이스 경로가 존재하지 않습니다: {self.workspace_path}")
        
        logger.info(f"Cursor 워크스페이스 경로: {self.workspace_path}")
    
    def create_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        파일 생성
        
        Args:
            file_path: 워크스페이스 내 상대 경로
            content: 파일 내용
            
        Returns:
            생성 결과
        """
        try:
            full_path = os.path.join(self.workspace_path, file_path)
            
            # 디렉토리 경로 생성
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 파일 작성
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"파일 생성 완료: {full_path}")
            return {
                "status": "success",
                "path": full_path,
                "message": "파일이 성공적으로 생성되었습니다."
            }
        except Exception as e:
            logger.error(f"파일 생성 실패: {str(e)}")
            return {
                "status": "error",
                "path": file_path,
                "message": f"파일 생성 중 오류 발생: {str(e)}"
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일 읽기
        
        Args:
            file_path: 워크스페이스 내 상대 경로
            
        Returns:
            파일 내용
        """
        try:
            full_path = os.path.join(self.workspace_path, file_path)
            
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "path": file_path,
                    "message": "파일이 존재하지 않습니다."
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "path": full_path,
                "content": content
            }
        except Exception as e:
            logger.error(f"파일 읽기 실패: {str(e)}")
            return {
                "status": "error",
                "path": file_path,
                "message": f"파일 읽기 중 오류 발생: {str(e)}"
            }
    
    def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        파일 업데이트
        
        Args:
            file_path: 워크스페이스 내 상대 경로
            content: 새 파일 내용
            
        Returns:
            업데이트 결과
        """
        try:
            full_path = os.path.join(self.workspace_path, file_path)
            
            if not os.path.exists(full_path):
                return {
                    "status": "error",
                    "path": file_path,
                    "message": "파일이 존재하지 않습니다."
                }
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"파일 업데이트 완료: {full_path}")
            return {
                "status": "success",
                "path": full_path,
                "message": "파일이 성공적으로 업데이트되었습니다."
            }
        except Exception as e:
            logger.error(f"파일 업데이트 실패: {str(e)}")
            return {
                "status": "error",
                "path": file_path,
                "message": f"파일 업데이트 중 오류 발생: {str(e)}"
            }
    
    def execute_code(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        코드 실행
        
        Args:
            command: 실행할 명령어
            working_dir: 작업 디렉토리 (없으면 워크스페이스 루트)
            
        Returns:
            실행 결과
        """
        try:
            cwd = os.path.join(self.workspace_path, working_dir) if working_dir else self.workspace_path
            
            logger.info(f"명령어 실행: {command} (작업 디렉토리: {cwd})")
            result = subprocess.run(command, shell=True, cwd=cwd, 
                                  capture_output=True, text=True)
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except Exception as e:
            logger.error(f"명령어 실행 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"명령어 실행 중 오류 발생: {str(e)}",
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    async def execute_code_async(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        코드 비동기 실행 (병렬 처리용)
        
        Args:
            command: 실행할 명령어
            working_dir: 작업 디렉토리 (없으면 워크스페이스 루트)
            
        Returns:
            실행 결과
        """
        try:
            cwd = os.path.join(self.workspace_path, working_dir) if working_dir else self.workspace_path
            
            logger.info(f"비동기 명령어 실행: {command} (작업 디렉토리: {cwd})")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": process.returncode
            }
        except Exception as e:
            logger.error(f"비동기 명령어 실행 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"비동기 명령어 실행 중 오류 발생: {str(e)}",
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            } 