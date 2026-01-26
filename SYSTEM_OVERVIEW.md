# HelloTalk 봇 시스템 개요

## 주요 개선 사항 (2026-01-26)

### 1. 전체 유저 스윕 후 대기
**이전 문제점:**
- 매 사이클마다 `in_progress` 유저만 체크
- 신규 유저는 첫 사이클에만 체크
- 일부 유저가 누락될 가능성

**개선 사항:**
- 모든 신규 유저 + 진행 중인 유저를 한번에 스윕
- 모든 유저를 체크한 후에만 60초 대기
- 누락 없이 모든 유저에게 응답 가능

### 2. 확장된 메시지 플로우
**이전:** 6개 메시지 (앱 링크 전송 후 종료)

**현재:** 8개 메시지 (앱 사용 확인 + 피드백 수집까지)

#### 새로운 메시지 단계

**단계 6:** "Did you get a chance to try it?"
- 앱 사용 여부 확인
- 긍정적 → 단계 7로
- 부정적 → 단계 7로 (피드백 저장)
- 아직 안 해봄 → 단계 6 반복
- 못 찾음 → 종료 (피드백 저장)

**단계 7:** "What did you think of it?"
- 상세한 피드백 수집
- 모든 응답을 `user_feedback.json`에 저장
- 긍정적/부정적/혼합 피드백 모두 분류

### 3. 자동 피드백 저장
**저장 위치:** `user_feedback.json`

**저장 조건:**
- 사용자가 앱을 사용한 후 의견을 공유할 때
- 앱을 못 찾았을 때
- 부정적 피드백을 줄 때
- 상세한 피드백을 줄 때

**저장 내용:**
```json
{
  "timestamp": "2026-01-26T16:30:45.123456",
  "username": "TestUser",
  "message_step": 7,
  "my_message": "What did you think of it?",
  "user_feedback": "I love the pronunciation feature!",
  "feedback_type": "detailed_feedback",
  "analyzed": false
}
```

## 시스템 구조

```
┌─────────────────────────────────────────────────────┐
│              multi_user_bot.py (메인)                │
│  - 브라우저 연결                                      │
│  - 유저 목록 가져오기                                 │
│  - 사이클 관리 (모든 유저 스윕)                       │
│  - 상태 저장/로드                                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         response_handler.py (응답 분석)              │
│  - 사용자 응답 키워드 분석                            │
│  - 다음 메시지 결정                                   │
│  - 피드백 저장                                        │
│  - 예상 밖 응답 로깅                                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│        response_patterns.json (패턴 설정)            │
│  - 8개 메시지 단계별 예상 응답 패턴                   │
│  - 키워드, 다음 단계, 대체 메시지 정의                │
│  - Fallback 응답 패턴                                │
└─────────────────────────────────────────────────────┘
```

## 메시지 플로우 (전체)

```
0. "Hi, I'm jake, how long have you been learning Korean?"
   └─> 사용자 답변 분석
       
1. "what is the hardest part?"
   └─> 어려움 파악
       
2. "what do you do for a living?"
   └─> 직업 파악
       
3. "I'm building an app to help people learn Korean..."
   └─> 앱 소개
       
4. "Do u mind giving me some feedback as learner?"
   └─> 피드백 요청
       
5. "u can search 'kokoai' on app store.!"
   └─> 앱 링크 제공
       
6. "Did you get a chance to try it?"
   └─> 앱 사용 확인
       ├─ 사용함 → 7단계
       ├─ 아직 안 함 → 대기 후 재확인
       └─ 못 찾음 → 종료 + 피드백 저장
       
7. "What did you think of it?"
   └─> 피드백 수집
       ├─ 상세 피드백 → 저장 + 종료
       ├─ 일반 긍정 → 저장 + 종료
       ├─ 혼합 피드백 → 저장 + 종료
       └─ 모호한 답변 → 저장 + 종료
```

## 봇 사이클 동작 방식

### 이전 방식 (문제)
```
사이클 N:
1. 유저 목록 가져오기
2. IF 첫 사이클:
   - 신규 유저에게 첫 메시지 전송
3. 진행 중인 유저만 체크
4. 60초 대기
```

**문제:** 신규 유저는 첫 사이클에만 처리되고, 그 이후에는 무시됨

### 현재 방식 (개선)
```
사이클 N:
1. 유저 목록 가져오기
2. 신규 유저 + 진행 중인 유저 = 체크 대상
3. 모든 체크 대상 유저를 하나씩 스윕:
   - 신규 유저: 첫 메시지 전송
   - 진행 중: 답장 확인 → 응답 분석 → 다음 메시지
4. 전체 스윕 완료 후 60초 대기
```

**장점:**
- 모든 유저가 빠짐없이 체크됨
- 신규 유저가 언제든 추가될 수 있음
- 진행 상황이 명확하게 표시됨

## 사이클 출력 예시

```
============================================================
[사이클 3] 16:30:45
============================================================
읽지 않은 메시지: 5명 | 진행 중: 12명 | 완료: 8명 | 오늘 시작: 19/20

🆕 신규 유저: 1명

🔄 전체 13명 스윕 시작:

[1/13] 🆕 신규 | John (단계: 0/8)
   📤 첫 메시지 전송: John (오늘 20/20)

[2/13] 🔴 진행 | Sarah (단계: 3/8)
   ✓ 답장 확인: "That sounds cool!..."
   ✓ 응답 패턴 매칭: interested → 다음 단계: 4
   📤 메시지 전송 (단계: 3 → 4)

[3/13] ⚪ 진행 | Mike (단계: 2/8)
   ⏳ 답장 대기 중... (메시지 2/8 전송 완료)

...

[13/13] 🔴 진행 | Emma (단계: 7/8)
   ✓ 답장 확인: "I love the pronunciation feature!..."
   ✓ 응답 패턴 매칭: detailed_feedback → 다음 단계: -1
   💾 피드백 저장됨: "I love the pronunciation feature!..." (타입: detailed_feedback)
   🏁 대화 종료 신호
   📤 종료 메시지 전송
   ✅ Emma 완료!

============================================================
✅ 스윕 완료: 13명 체크, 8개 액션
============================================================

⏳ 다음 체크까지 60초 대기...
```

## 파일 구조

```
hellotalk_automation/
├── multi_user_bot.py              # 메인 봇 (실행 파일)
├── response_handler.py            # 응답 분석 모듈
├── response_patterns.json         # 응답 패턴 설정 (수정 가능)
├── messages.txt                   # 메시지 목록 (8줄)
├── exclude_users.txt              # 제외할 유저 목록
├── bot_state.json                 # 봇 상태 (자동 생성)
├── user_feedback.json             # 피드백 로그 (자동 생성)
├── unhandled_responses.json       # 예상 밖 응답 로그 (자동 생성)
├── RESPONSE_SYSTEM_README.md      # 응답 시스템 상세 문서
└── SYSTEM_OVERVIEW.md             # 이 파일
```

## 실행 방법

### 1. Chrome 디버그 모드 실행
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome-debug"
```

### 2. HelloTalk 웹 로그인
브라우저에서 https://web.hellotalk.com/ 열고 로그인

### 3. 봇 실행
```bash
python3 multi_user_bot.py
```

## 주요 기능

### 자동 상태 복구
- 봇을 중단했다가 재시작해도 이전 상태에서 계속 진행
- `bot_state.json`에 모든 유저 상태 저장

### 하루 제한
- 하루에 시작할 수 있는 대화 수 제한 (기본: 20명)
- 자정이 되면 자동으로 리셋

### 예상 밖 응답 처리
- 패턴에 없는 응답은 `unhandled_responses.json`에 로깅
- 나중에 패턴 추가할 때 참고

### 피드백 자동 저장
- 사용자가 앱에 대한 의견을 줄 때 자동 저장
- `user_feedback.json`에서 확인 가능

## 통계 확인

```python
from response_handler import ResponseHandler

handler = ResponseHandler()

# 예상 밖 응답 통계
stats = handler.get_unhandled_stats()
print(f"예상 밖 응답: {stats['total']}개")

# 피드백 확인
print(f"수집된 피드백: {len(handler.feedbacks)}개")
```

## 패턴 수정

`response_patterns.json` 파일을 수정하여 새로운 응답 패턴을 추가하거나 기존 패턴을 변경할 수 있습니다.

상세한 방법은 `RESPONSE_SYSTEM_README.md` 참조.

## 문제 해결

### 유저가 누락되는 것 같을 때
- 봇은 이제 모든 유저를 스윕하므로 누락 불가능
- `bot_state.json`에서 유저 상태 확인

### 메시지가 8개보다 적게 보내질 때
- 사용자 응답에 따라 대화가 조기 종료될 수 있음
- 예: "not interested" 응답 시 즉시 종료

### 피드백이 저장되지 않을 때
- `response_patterns.json`에서 `save_feedback: true` 설정 확인
- 단계 6, 7에서 특정 패턴 매칭 시에만 저장됨

## 향후 개선 가능 사항

1. **스마트 대기 시간**: 모든 유저가 답장 대기 중일 때만 60초 대기
2. **우선순위 시스템**: 읽지 않은 메시지가 있는 유저 먼저 체크
3. **LLM 통합**: 예상 밖 응답에 대한 자동 답변 생성
4. **피드백 분석**: 수집된 피드백 자동 분석 및 요약
