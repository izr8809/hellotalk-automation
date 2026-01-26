#!/usr/bin/env python3
"""
설치 및 설정 검증 스크립트

이 스크립트는 HelloTalk 자동화 프로그램 실행에 필요한
모든 요구사항이 충족되었는지 확인합니다.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    print("1. Python 버전 확인...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro} (3.7 이상 필요)")
        return False

def check_playwright():
    """Playwright 설치 확인"""
    print("2. Playwright 패키지 확인...")
    try:
        import playwright
        print(f"   ✓ Playwright 설치됨 (버전: {playwright.__version__})")
        return True
    except ImportError:
        print("   ✗ Playwright 미설치")
        print("      설치: pip3 install playwright")
        return False

def check_files():
    """필수 파일 확인"""
    print("3. 필수 파일 확인...")
    
    required_files = {
        'hellotalk_sender.py': '메인 프로그램',
        'messages.txt': '메시지 목록',
        'requirements.txt': '패키지 목록'
    }
    
    optional_files = {
        'exclude_users.txt': '제외 사용자 목록',
        'README.md': '문서'
    }
    
    all_ok = True
    
    for filename, description in required_files.items():
        if Path(filename).exists():
            print(f"   ✓ {filename} ({description})")
        else:
            print(f"   ✗ {filename} ({description}) - 필수 파일 없음!")
            all_ok = False
    
    for filename, description in optional_files.items():
        if Path(filename).exists():
            print(f"   ✓ {filename} ({description})")
        else:
            print(f"   ⚠ {filename} ({description}) - 선택사항")
    
    return all_ok

def check_messages_file():
    """messages.txt 내용 확인"""
    print("4. messages.txt 내용 확인...")
    
    if not Path('messages.txt').exists():
        print("   ✗ messages.txt 파일이 없습니다")
        return False
    
    try:
        with open('messages.txt', 'r', encoding='utf-8') as f:
            messages = [line.strip() for line in f if line.strip()]
        
        if not messages:
            print("   ✗ messages.txt가 비어있습니다")
            print("      최소 1개 이상의 메시지를 작성하세요")
            return False
        
        print(f"   ✓ {len(messages)}개의 메시지 발견")
        for i, msg in enumerate(messages[:3], 1):
            preview = msg[:50] + "..." if len(msg) > 50 else msg
            print(f"      {i}. {preview}")
        
        if len(messages) > 3:
            print(f"      ... 외 {len(messages) - 3}개")
        
        return True
    except Exception as e:
        print(f"   ✗ messages.txt 읽기 실패: {e}")
        return False

def check_exclude_file():
    """exclude_users.txt 확인"""
    print("5. exclude_users.txt 확인...")
    
    if not Path('exclude_users.txt').exists():
        print("   ⚠ exclude_users.txt 파일이 없습니다 (선택사항)")
        print("      모든 사용자에게 메시지를 전송합니다")
        return True
    
    try:
        with open('exclude_users.txt', 'r', encoding='utf-8') as f:
            excluded = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if excluded:
            print(f"   ✓ {len(excluded)}명의 사용자 제외")
            for user in excluded[:3]:
                print(f"      - {user}")
            if len(excluded) > 3:
                print(f"      ... 외 {len(excluded) - 3}명")
        else:
            print("   ⚠ 제외할 사용자가 없습니다")
        
        return True
    except Exception as e:
        print(f"   ✗ exclude_users.txt 읽기 실패: {e}")
        return False

def check_syntax():
    """Python 파일 구문 확인"""
    print("6. Python 구문 확인...")
    
    try:
        import py_compile
        py_compile.compile('hellotalk_sender.py', doraise=True)
        print("   ✓ hellotalk_sender.py 구문 검사 통과")
        return True
    except Exception as e:
        print(f"   ✗ 구문 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("HelloTalk 자동화 프로그램 설정 검증")
    print("=" * 60)
    print()
    
    checks = [
        check_python_version(),
        check_playwright(),
        check_files(),
        check_messages_file(),
        check_exclude_file(),
        check_syntax()
    ]
    
    print()
    print("=" * 60)
    
    if all(checks):
        print("✅ 모든 검사 통과!")
        print()
        print("프로그램을 실행할 준비가 되었습니다:")
        print("  python3 hellotalk_sender.py")
        print()
        print("추가 정보:")
        print("  - 빠른 시작: QUICKSTART.md")
        print("  - 상세 가이드: EXECUTION_GUIDE.md")
        print("  - 전체 문서: README.md")
        return 0
    else:
        print("❌ 일부 검사 실패")
        print()
        print("위의 오류를 수정한 후 다시 실행하세요:")
        print("  python3 verify_setup.py")
        print()
        print("도움말:")
        print("  - 설치 가이드: README.md")
        print("  - 문제 해결: EXECUTION_GUIDE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
