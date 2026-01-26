# HelloTalk 웹사이트 분석 결과

## 분석 일시
2026-01-26

## 웹사이트 정보
- URL: https://web.hellotalk.com/
- 제목: HelloTalk Web

## 1. 로그인 방식

### QR 코드 스캔 전용
HelloTalk 웹 버전은 **QR 코드 스캔 방식만** 지원합니다.

**발견된 요소:**
- `#login_box` - 로그인 박스 컨테이너
- `#qrcode` - QR 코드 표시 영역
- `.scanRemind` - "Scan to log in to HelloTalk" 안내 문구

**특징:**
- 전통적인 ID/PW 입력 방식 없음
- 모바일 앱으로 QR 코드를 스캔해야 함
- 로그인 세션은 브라우저에 유지됨

**자동화 접근 방식:**
1. Playwright로 브라우저 열기
2. HelloTalk 웹 페이지 로드
3. 사용자가 수동으로 QR 코드 스캔
4. 로그인 완료 감지 (login_box 요소 사라짐)
5. 자동화 시작

## 2. 페이지 구조

### HTML 구조
```
<div class="mainWrapper">
  <div class="loginWrapper">
    <div id="login_box" class="scanRemind">
      <div class="qr-title"></div>
      <div class="ht-group-box">
        <div id="qrcode"></div>
      </div>
      <div class="scanRemindImg"></div>
    </div>
  </div>
</div>
```

### 사용된 태그
- DIV (주요 레이아웃)
- CANVAS (QR 코드 렌더링)
- P (텍스트)
- SCRIPT (JavaScript)
- STYLE (CSS)

## 3. 대화 목록 (추정)

로그인 후 나타날 것으로 예상되는 요소들:

### 가능한 선택자 (Selectors)
프로그램에서 시도하는 선택자 목록:

1. `.chatList .chat-item` - 대화 목록 아이템
2. `.chat-list .chat-item` - 대체 선택자
3. `[class*="chatList"] [class*="item"]` - 부분 일치
4. `[class*="chat-list"] [class*="item"]` - 부분 일치
5. `.conversation-item` - 대화 아이템
6. `[class*="conversation"]` - 대화 관련 요소

**참고:** 실제 구조는 로그인 후에만 확인 가능

## 4. 메시지 전송 (추정)

### 메시지 입력창 선택자
프로그램에서 시도하는 선택자:

1. `textarea[placeholder*="메시지"]` - 한국어 플레이스홀더
2. `textarea[placeholder*="message"]` - 영어 플레이스홀더
3. `input[type="text"][placeholder*="메시지"]` - 텍스트 입력
4. `.message-input textarea` - 클래스 기반
5. `[class*="input"] textarea` - 부분 일치
6. `textarea` - 일반 텍스트 영역
7. `input[type="text"]` - 일반 텍스트 입력

### 전송 버튼 선택자
프로그램에서 시도하는 선택자:

1. `button[type="submit"]` - 제출 버튼
2. `button:has-text("전송")` - 한국어 버튼
3. `button:has-text("Send")` - 영어 버튼
4. `.send-button` - 클래스 기반
5. `.btn-send` - 대체 클래스
6. `[class*="send"]` - 부분 일치

**폴백:** 전송 버튼을 찾지 못하면 Enter 키 입력

## 5. 네트워크 요청

### 관찰된 요청
- 정적 리소스 (JavaScript, CSS, 이미지)
- QR 코드 생성 API (추정)
- WebSocket 연결 가능성 (실시간 메시지용)

## 6. 자동화 전략

### 구현된 접근 방식

1. **로그인 처리**
   - Playwright로 브라우저 실행 (headless=False)
   - HelloTalk 웹 페이지 로드
   - 사용자가 QR 코드 스캔할 때까지 대기 (최대 5분)
   - `#login_box` 요소 사라짐 감지로 로그인 확인

2. **사용자 목록 추출**
   - 여러 선택자 시도 (폴백 메커니즘)
   - 각 사용자 요소에서 이름 추출
   - exclude_users.txt와 비교하여 필터링

3. **메시지 전송**
   - 사용자 요소 클릭 → 대화창 열기
   - 메시지 입력창 찾기 (여러 선택자 시도)
   - 메시지 입력
   - 전송 버튼 클릭 또는 Enter 키 입력
   - 1분 대기 (rate limiting)

4. **에러 처리**
   - 각 단계에서 예외 처리
   - 로그 파일에 상세 기록
   - 실패 시 다음 사용자로 계속 진행

## 7. 제한사항 및 주의사항

### 기술적 제한
1. **페이지 구조 의존성**: HelloTalk이 웹 구조를 변경하면 선택자 업데이트 필요
2. **QR 코드 로그인**: 완전 자동화 불가능 (사용자 개입 필요)
3. **동적 콘텐츠**: JavaScript로 렌더링되는 요소 대기 필요

### 보안 고려사항
1. **계정 보호**: 1분 간격 전송으로 rate limiting 준수
2. **스팸 방지**: 제외 목록 기능 제공
3. **로그인 보안**: QR 코드만 사용, 크레덴셜 저장 안 함

### 서비스 약관
- HelloTalk의 자동화 도구 사용 정책 확인 필요
- 과도한 사용 시 계정 제한 가능성
- 교육/개인 용도로만 사용 권장

## 8. 개선 가능 영역

### 향후 개선 사항
1. **세션 저장**: 로그인 세션을 저장하여 재로그인 불필요
2. **응답 감지**: 메시지 전송 성공 여부 확인
3. **통계 기록**: 전송 성공률, 응답률 등 추적
4. **GUI 추가**: 명령줄 대신 그래픽 인터페이스
5. **스케줄링**: 특정 시간에 자동 실행

### 코드 개선
1. **선택자 자동 학습**: 페이지 구조 변경 시 자동 적응
2. **병렬 처리**: 여러 대화를 동시에 처리 (주의 필요)
3. **재시도 로직**: 실패 시 자동 재시도

## 9. 결론

HelloTalk 웹 버전은 QR 코드 스캔 방식만 지원하므로 완전 자동화는 불가능합니다. 
그러나 로그인 후 메시지 전송 과정은 Playwright를 통해 효과적으로 자동화할 수 있습니다.

**구현된 프로그램의 장점:**
- ✅ 안전한 로그인 방식 (QR 코드)
- ✅ 유연한 선택자 시스템 (페이지 구조 변경 대응)
- ✅ 상세한 로그 기록
- ✅ 에러 처리 및 복구
- ✅ Rate limiting 준수

**사용자 책임:**
- 서비스 약관 준수
- 적절한 메시지 작성
- 스팸 방지
- 계정 보안 유지
