# 실행 가이드

HelloTalk 자동 메시지 전송 프로그램 완벽 실행 가이드

## 📋 사전 준비 체크리스트

실행하기 전에 다음 항목을 확인하세요:

- [ ] Python 3.7 이상 설치됨
- [ ] Playwright 패키지 설치됨
- [ ] Playwright 브라우저(Chromium) 설치됨
- [ ] messages.txt 파일 작성 완료
- [ ] exclude_users.txt 파일 확인 (선택사항)
- [ ] HelloTalk 모바일 앱 준비됨

## 🚀 단계별 실행 방법

### 1단계: 환경 확인

```bash
# Python 버전 확인 (3.7 이상이어야 함)
python3 --version

# 프로젝트 디렉토리로 이동
cd ~/Downloads/hellotalk_automation

# 파일 목록 확인
ls -la
```

**예상 출력:**
```
hellotalk_sender.py
messages.txt
exclude_users.txt
requirements.txt
README.md
```

### 2단계: 패키지 설치 확인

```bash
# 필요한 패키지 설치
pip3 install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

**성공 메시지:**
```
Successfully installed playwright-1.41.0
Chromium 123.0.6312.4 downloaded
```

### 3단계: 설정 파일 확인

#### messages.txt 확인

```bash
cat messages.txt
```

**최소 1개 이상의 메시지가 있어야 합니다:**
```
안녕하세요! 언어 교환 파트너를 찾고 있어요. 함께 공부할래요?
Hello! I'm looking for a language exchange partner.
```

#### exclude_users.txt 확인 (선택사항)

```bash
cat exclude_users.txt
```

**제외할 사용자가 있다면:**
```
BadUser123
SpamAccount
```

### 4단계: 프로그램 실행

```bash
python3 hellotalk_sender.py
```

### 5단계: QR 코드 스캔

프로그램이 실행되면:

1. **브라우저 자동 실행**
   - Chromium 브라우저가 자동으로 열립니다
   - HelloTalk 웹 페이지가 로드됩니다
   - QR 코드가 표시됩니다

2. **모바일 앱으로 스캔**
   - HelloTalk 모바일 앱을 엽니다
   - 설정 또는 메뉴에서 "QR 코드 스캔" 찾기
   - 브라우저의 QR 코드를 스캔합니다

3. **로그인 대기**
   - 터미널에 다음 메시지가 표시됩니다:
   ```
   ============================================================
   HelloTalk 웹 페이지가 열렸습니다.
   모바일 앱으로 QR 코드를 스캔하여 로그인해주세요.
   로그인이 완료되면 자동으로 진행됩니다...
   ============================================================
   ```

4. **로그인 완료**
   - 5분 이내에 로그인해야 합니다
   - 로그인되면 자동으로 다음 단계로 진행됩니다

### 6단계: 자동 전송 진행

로그인 후 프로그램이 자동으로:

1. **사용자 목록 스캔**
   ```
   사용자 목록을 가져오는 중...
   총 15명의 사용자를 찾았습니다 (제외된 사용자 제외).
   ```

2. **메시지 전송 시작**
   ```
   ============================================================
   총 15명에게 메시지 전송을 시작합니다.
   전송 간격: 60초
   ============================================================
   ```

3. **각 사용자에게 전송**
   ```
   [1/15] 진행 중...
   'Alice'에게 메시지 전송 시도...
   ✓ 'Alice'에게 메시지 전송 완료: 안녕하세요! 언어 교환 파트너를...
   60초 대기 중...
   
   [2/15] 진행 중...
   'Bob'에게 메시지 전송 시도...
   ✓ 'Bob'에게 메시지 전송 완료: Hello! I'm looking for a language...
   60초 대기 중...
   ```

### 7단계: 완료 확인

모든 전송이 완료되면:

```
============================================================
메시지 전송 완료!
성공: 13명
실패: 2명
총: 15명
============================================================
5초 후 브라우저를 닫습니다...
```

## 🛑 프로그램 중단 방법

### 정상 중단
언제든지 `Ctrl + C`를 누르면 안전하게 중단됩니다:

```
^C
사용자에 의해 프로그램이 중단되었습니다.
```

### 강제 종료 (권장하지 않음)
```bash
# 프로세스 찾기
ps aux | grep hellotalk_sender.py

# 프로세스 종료
kill -9 [PID]
```

## 📊 진행 상황 모니터링

### 터미널 출력
실시간으로 진행 상황이 표시됩니다:
- 현재 전송 중인 사용자
- 전송 성공/실패 여부
- 대기 시간

### 로그 파일
별도 터미널에서 로그를 실시간으로 확인:

```bash
# 실시간 로그 모니터링
tail -f hellotalk_automation.log

# 전체 로그 확인
cat hellotalk_automation.log

# 에러만 확인
grep ERROR hellotalk_automation.log
```

## ⚠️ 일반적인 문제 해결

### 문제 1: "메시지 파일을 찾을 수 없습니다"

**증상:**
```
ERROR - 메시지 파일을 찾을 수 없습니다: messages.txt
```

**해결:**
```bash
# 현재 위치 확인
pwd

# messages.txt 생성
echo "안녕하세요!" > messages.txt
```

### 문제 2: "로그인 대기 중 오류 발생"

**증상:**
```
ERROR - 5분 내에 로그인하지 않았거나 페이지 구조가 변경되었습니다.
```

**해결:**
1. 프로그램 재실행
2. QR 코드가 표시되는지 확인
3. 5분 이내에 스캔
4. 네트워크 연결 확인

### 문제 3: "사용자 목록을 찾을 수 없습니다"

**증상:**
```
WARNING - 사용자 목록을 찾을 수 없습니다. 페이지 구조를 확인해주세요.
```

**해결:**
1. 로그인이 제대로 되었는지 확인
2. 대화 목록 페이지가 표시되는지 확인
3. 로그 파일에서 디버그 정보 확인
4. HelloTalk 웹 구조가 변경되었을 수 있음 (코드 업데이트 필요)

### 문제 4: "메시지 입력창을 찾을 수 없습니다"

**증상:**
```
ERROR - 'Alice': 메시지 입력창을 찾을 수 없습니다.
```

**해결:**
1. 대화창이 제대로 열렸는지 확인
2. 수동으로 메시지를 보낼 수 있는지 테스트
3. 페이지 구조가 변경되었을 수 있음

### 문제 5: Playwright 설치 오류

**증상:**
```
Error: Executable doesn't exist at /path/to/chromium
```

**해결:**
```bash
# Playwright 재설치
pip3 install --upgrade playwright

# 브라우저 재설치
playwright install chromium

# 권한 문제가 있다면
sudo playwright install chromium
```

## 🔍 디버깅 팁

### 로그 레벨 변경
더 자세한 정보를 보려면 `hellotalk_sender.py` 파일 수정:

```python
# 17번째 줄 근처
logging.basicConfig(
    level=logging.DEBUG,  # INFO에서 DEBUG로 변경
    ...
)
```

### 브라우저 창 유지
프로그램 종료 후에도 브라우저를 열어두려면:

```python
# 345번째 줄 근처 주석 처리
# await browser.close()
```

### 전송 간격 단축 (테스트용)
**주의: 실제 사용 시 1분 이상 권장**

```python
# 373번째 줄 근처
automation = HelloTalkAutomation(
    messages_file="messages.txt",
    exclude_file="exclude_users.txt",
    interval_seconds=10  # 테스트용 10초
)
```

## 📈 성공적인 실행을 위한 팁

1. **첫 실행은 소수의 사용자로 테스트**
   - exclude_users.txt에 대부분의 사용자를 추가
   - 2-3명에게만 먼저 전송해보기

2. **다양한 메시지 준비**
   - messages.txt에 여러 메시지 작성
   - 자연스러운 대화 시작

3. **적절한 시간대 선택**
   - 대상 사용자가 활동하는 시간
   - 너무 늦은 밤이나 이른 아침 피하기

4. **정기적인 로그 확인**
   - 전송 성공률 모니터링
   - 에러 패턴 파악

5. **제외 목록 관리**
   - 응답이 없는 사용자 추가
   - 이미 대화 중인 사용자 제외

## 🎯 다음 단계

프로그램이 성공적으로 실행되면:

1. **결과 분석**
   - 로그 파일 검토
   - 성공률 확인
   - 개선점 파악

2. **설정 최적화**
   - 메시지 내용 개선
   - 전송 간격 조정
   - 제외 목록 업데이트

3. **정기 실행**
   - 일정 간격으로 실행
   - 새로운 사용자에게 메시지 전송
   - 응답률 추적

## 📞 추가 도움말

- **README.md**: 전체 문서
- **QUICKSTART.md**: 빠른 시작 가이드
- **ANALYSIS.md**: 기술적 분석 결과
- **로그 파일**: hellotalk_automation.log

---

**행운을 빕니다! 🍀**
