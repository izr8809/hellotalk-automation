# 빠른 시작 가이드

HelloTalk 자동 메시지 전송 프로그램을 5분 안에 시작하세요!

## 1단계: 설치 (2분)

```bash
# 프로젝트 디렉토리로 이동
cd ~/Downloads/hellotalk_automation

# 패키지 설치
pip3 install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

## 2단계: 설정 (2분)

### messages.txt 편집

```bash
nano messages.txt
```

또는 텍스트 에디터로 열어서 전송할 메시지를 작성:

```
안녕하세요! 언어 교환 파트너를 찾고 있어요.
Hello! Looking for a language exchange partner.
```

### exclude_users.txt 편집 (선택사항)

제외할 사용자가 있다면:

```bash
nano exclude_users.txt
```

## 3단계: 실행 (1분)

```bash
python3 hellotalk_sender.py
```

1. 브라우저가 자동으로 열립니다
2. HelloTalk 모바일 앱으로 QR 코드를 스캔합니다
3. 로그인되면 자동으로 메시지 전송이 시작됩니다!

## 중단하기

언제든지 `Ctrl + C`를 누르면 안전하게 중단됩니다.

## 문제가 있나요?

1. 로그 파일 확인: `cat hellotalk_automation.log`
2. README.md의 "문제 해결" 섹션 참고
3. Python 버전 확인: `python3 --version` (3.7 이상 필요)

## 다음 단계

- 더 많은 메시지를 messages.txt에 추가하세요
- 전송 간격을 조정하세요 (기본: 60초)
- 로그를 확인하여 전송 결과를 모니터링하세요

자세한 내용은 [README.md](README.md)를 참고하세요.
