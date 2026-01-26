# HelloTalk Automation Bot

HelloTalk 웹버전에서 여러 유저에게 자동으로 메시지를 순차 전송하는 Python 봇입니다.

## ⚠️ 주의사항

- 이 프로그램은 교육/개인 연구 목적입니다
- HelloTalk 이용약관을 확인하세요
- 과도한 사용 시 계정 제한될 수 있습니다
- 스팸 또는 악용 시 발생하는 문제는 사용자 책임입니다

## ✨ 특징

- ✅ 이미 열린 Chrome 브라우저 제어 (로그인 상태 유지)
- ✅ 유저별 순차 메시지 전송 (답장 기반)
- ✅ 하루 최대 20명 제한 (안전)
- ✅ 답장이 올 때까지 대기 후 다음 메시지 전송
- ✅ 상태 저장 (중단 후 재시작 가능)
- ✅ 제외 리스트 지원
- ✅ 자동 필터링 (HT, HelloTalk 등 시스템 계정)

## 📋 동작 방식

1. **모든 유저에게 첫 메시지 전송** (하루 최대 20명)
2. **1분마다 모든 대화 체크**
3. 답장이 온 유저 발견 → 다음 메시지 전송
4. 6개 메시지 완료 시 → 해당 유저 완료 처리
5. 반복

## 🚀 설치 및 사용

자세한 설치 및 사용 방법은 [SETUP.md](SETUP.md)를 참조하세요.

### 빠른 시작

```bash
# 1. 가상환경 생성 및 패키지 설치
python3 -m venv venv
source venv/bin/activate
pip install playwright
playwright install chromium

# 2. 설정 파일 준비
cp messages.example.txt messages.txt
cp exclude_users.example.txt exclude_users.txt
# messages.txt와 exclude_users.txt 편집

# 3. Chrome 디버그 모드 실행
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome-debug"

# 4. HelloTalk 웹 로그인 (https://web.hellotalk.com/)

# 5. 봇 실행
./run_multi.sh
```

## 📝 라이선스

MIT License
