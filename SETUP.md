# 설치 및 사용 가이드

## 📋 목차

- [설치 방법](#설치-방법)
- [설정 파일](#설정-파일)
- [사용 방법](#사용-방법)
- [스크립트 설명](#스크립트-설명)
- [문제 해결](#문제-해결)

## 설치 방법

### 1. Python 가상환경 생성

```bash
cd hellotalk_automation
python3 -m venv venv
source venv/bin/activate
```

### 2. Playwright 설치

```bash
pip install playwright
playwright install chromium
```

## 설정 파일

### messages.txt

전송할 메시지를 한 줄에 하나씩 입력:

```bash
cp messages.example.txt messages.txt
# messages.txt 편집
```

**예시:**
```
Hi, I'm jake, how long have you been learning Korean?
what is the hardest part?
what do you do for a living?
I'm building an app to help people learn Korean more easily.
Do u mind giving me some feedback as learner?
u can search 'kokoai' on app store.!
```

### exclude_users.txt (선택사항)

제외할 유저 이름 입력:

```bash
cp exclude_users.example.txt exclude_users.txt
# exclude_users.txt 편집
```

**예시:**
```
John Doe
Live & Voiceroom
HT Community
```

**자동 제외 규칙:**
- "HT"로 시작하거나 포함된 이름
- "HelloTalk" 포함된 이름

## 사용 방법

### 1단계: Chrome 디버그 모드 실행

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome-debug"
```

**중요:** 이 Chrome 창은 닫지 마세요!

### 2단계: HelloTalk 웹 로그인

1. 새로 열린 Chrome에서 https://web.hellotalk.com/ 접속
2. 계정으로 로그인
3. 대화 목록이 보이는지 확인

### 3단계: 봇 실행

```bash
./run_multi.sh
```

또는

```bash
source venv/bin/activate
python3 multi_user_bot.py
```

### 중단 방법

언제든지 `Ctrl + C`로 중단 가능합니다. 진행 상태는 자동 저장됩니다.

## 스크립트 설명

### 주요 스크립트

| 파일 | 설명 |
|------|------|
| `multi_user_bot.py` | 멀티 유저 자동 메시지 봇 (메인) |
| `first_user_bot.py` | 첫 번째 유저만 테스트 |
| `test_message_check.py` | 마지막 메시지 확인 테스트 |
| `test_reply_detection.py` | 답장 감지 테스트 |
| `debug_page.py` | HelloTalk 페이지 구조 분석 |

### 유틸리티 스크립트

| 파일 | 설명 |
|------|------|
| `run.sh` | first_user_bot.py 실행 |
| `run_multi.sh` | multi_user_bot.py 실행 |

## 설정 변경

### 하루 전송 제한 변경

`multi_user_bot.py`의 16번째 줄:

```python
self.daily_limit = 20  # 원하는 숫자로 변경
```

### 체크 간격 변경

`multi_user_bot.py`의 마지막 부분:

```python
time.sleep(60)  # 60초 → 원하는 초로 변경
```

## 상태 관리

### bot_state.json

프로그램이 자동으로 생성하는 상태 파일입니다.

**기능:**
- 각 유저의 진행 상태 저장
- 중단 후 재시작 시 이어서 진행
- 날짜별 전송 카운트 관리

**초기화 방법:**
```bash
rm bot_state.json
```

## 문제 해결

### "브라우저 연결 실패" 오류

**원인:** Chrome이 디버그 모드로 실행되지 않음

**해결:**
1. 모든 Chrome 창 닫기
2. 디버그 모드 명령 다시 실행
3. HelloTalk 재로그인

### "대화 목록을 찾을 수 없습니다" 오류

**해결:**
1. HelloTalk 웹에 제대로 로그인되어 있는지 확인
2. 대화 목록 페이지에 있는지 확인
3. 페이지 구조 분석:

```bash
python3 debug_page.py
```

이 스크립트가 생성하는 파일들을 확인:
- `page_structure.html` - 전체 HTML 구조
- `hellotalk_screenshot.png` - 현재 화면

### 답장 감지가 안 됨

**해결:**

```bash
python3 test_reply_detection.py
```

메시지 구조를 확인하고, HelloTalk 웹 구조가 변경되었는지 확인하세요.

### 마지막 메시지 확인

대화창을 열어놓고:

```bash
python3 test_message_check.py
```

마지막으로 보낸 메시지를 제대로 인식하는지 확인할 수 있습니다.

## 안전 장치

1. **하루 20명 제한** - 첫 메시지 전송 제한
2. **답장 기반 전송** - 상대가 답장할 때만 다음 메시지
3. **느린 속도** - 1분 간격 체크
4. **자동 필터링** - 시스템 계정 제외
5. **상태 저장** - 중단해도 진행 상황 유지

## 실행 화면 예시

```
============================================================
HelloTalk 멀티 유저 봇
============================================================
✓ 6개 메시지 로드 완료
✓ 18명 제외 목록 로드 완료
   제외할 유저: Courtney, Raine, Mina, ...
✓ 이전 상태 로드: 5명 진행 중
✓ 오늘 시작한 대화: 5/20명

🔗 Chrome 브라우저에 연결 중...
✓ 연결 완료: https://web.hellotalk.com/

============================================================
🚀 봇 시작!
============================================================
전송할 메시지: 6개
하루 첫 메시지 제한: 20명
오늘 시작한 대화: 5/20명
체크 간격: 1분
중단: Ctrl + C

============================================================
[사이클 1] 14:30:15
============================================================
✓ 25명 유저 발견 (제외: 18명)
활성 유저: 20명 | 완료: 5명 | 오늘 시작: 5/20

[1/20] Atenea Hyde (단계: 1/6)
   ⏳ 답장 대기 중... (메시지 1/6 전송 완료)

[2/20] Elizabeth (단계: 2/6)
   ✓ 답장 확인! (답장 1 → 2개)
   📤 메시지 3/6 전송

[3/20] Rosy (단계: 0/6)
   📤 첫 메시지 전송: Rosy (오늘 6/20)

...

⏳ 다음 체크까지 60초 대기...
```
