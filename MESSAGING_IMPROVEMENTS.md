# 메시징 시스템 개선 사항

## 개요

이번 업데이트는 봇의 메시지 감지 및 응답 시스템을 대폭 개선하여 더 자연스럽고 누락 없는 대화를 가능하게 합니다.

## 🎯 해결된 문제점

### 1. ❌ 이전: 하나의 메시지만 읽음
**문제:** 유저가 3개 메시지를 보내도 첫 번째만 읽고 나머지는 무시

**해결:**
- ✅ 모든 새 메시지를 감지하고 저장
- ✅ 각 메시지에 순차적으로 응답 (3초 간격)
- ✅ 처리된 메시지는 해시로 추적하여 중복 방지

### 2. ❌ 이전: 타임스탬프 없음
**문제:** 같은 메시지를 반복해서 읽을 수 있음

**해결:**
- ✅ `bot_state.json`에 `last_check_time` 저장
- ✅ `messages_processed` 배열로 처리한 메시지 추적
- ✅ 메시지 해시 (`username:index:preview`)로 중복 방지

### 3. ❌ 이전: 유저가 먼저 말 걸면 부자연스러움
**문제:** 유저가 "Hi!"라고 먼저 인사해도 무조건 "Hi, I'm jake, how long..." 전송

**해결:**
- ✅ 유저 시작 대화 감지
- ✅ 유저 메시지 내용 분석하여 적절한 첫 응답 생성
- ✅ 대화 흐름에 맞는 단계로 자동 진입

### 4. ❌ 이전: 읽지 않은 메시지만 체크
**문제:** 현재 대화창의 메시지는 이미 "읽음" 상태로 변경됨

**해결:**
- ✅ 읽음/안 읽음 상태 무관하게 모든 새 메시지 처리
- ✅ DOM 구조 기반 감지 (봇 마지막 메시지 이후 모든 유저 메시지)
- ✅ 메시지 해시로 이미 처리한 것과 신규 구분

---

## 🔧 기술적 구현

### 1. 상태 구조 확장

#### 이전 (bot_state.json):
```json
{
  "username": {
    "current_step": 2,
    "completed": false
  }
}
```

#### 현재 (bot_state.json):
```json
{
  "username": {
    "current_step": 2,
    "completed": false,
    "last_check_time": "2026-01-26T16:30:45.123456",
    "messages_processed": [
      "username:5:Hi! How are you?",
      "username:7:That sounds great!"
    ]
  }
}
```

**필드 설명:**
- `last_check_time`: 마지막으로 체크한 시간 (ISO 8601)
- `messages_processed`: 처리된 메시지 해시 목록 (중복 방지)

---

### 2. 새 함수: `get_all_new_received_messages()`

**이전 함수:** `get_last_received_message()` - 단 하나만 반환

**새 함수:**
```python
def get_all_new_received_messages(self, username):
    # 봇 마지막 메시지 이후 모든 유저 메시지 찾기
    # 이미 처리한 메시지는 제외 (해시 비교)
    # 리스트로 반환: [{'text': ..., 'hash': ..., 'index': ...}, ...]
```

**동작:**
1. DOM에서 모든 메시지 가져오기
2. 봇의 마지막 메시지 위치 찾기
3. 그 이후의 모든 `receiveBox` 메시지 수집
4. `messages_processed`와 비교하여 신규만 필터링
5. 리스트로 반환

**예시:**
```
DOM 구조:
├─ sendBox: "Hi, I'm jake..."        (봇)
├─ receiveBox: "Hi!"                  (유저) ← 여기서부터
├─ receiveBox: "How are you?"         (유저)
└─ receiveBox: "I'm learning Korean"  (유저)

반환:
[
  {'text': 'Hi!', 'hash': 'username:1:Hi!', 'index': 1},
  {'text': 'How are you?', 'hash': 'username:2:How are you?', 'index': 2},
  {'text': "I'm learning Korean", 'hash': 'username:3:I'm learning Korean', 'index': 3}
]
```

---

### 3. 새 함수: `detect_user_initiated_conversation()`

**용도:** 유저가 먼저 대화를 시작했는지 감지

**동작:**
```python
def detect_user_initiated_conversation(self):
    # DOM에 봇 메시지가 하나도 없고
    # 유저 메시지가 있으면 → 유저 시작
    
    return (user_initiated: bool, first_message: str)
```

**예시:**
```
DOM에 sendBox가 없고 receiveBox만 있음:
├─ receiveBox: "Hi there!"
└─ (봇 메시지 없음)

반환: (True, "Hi there!")
```

---

### 4. 유저 시작 대화 패턴 (response_patterns.json)

```json
{
  "user_initiated": {
    "greeting": {
      "keywords": ["hi", "hello", "hey", ...],
      "response": "Hi! Nice to meet you! I'm Jake. How long have you been learning Korean?",
      "next_message_index": 1
    },
    "ask_question": {
      "keywords": ["how are you", "what do you do", ...],
      "response": "Hi! I'm Jake. I help people learn Korean. How long have you been learning?",
      "next_message_index": 1
    },
    "korean_learning": {
      "keywords": ["korean", "learning", "study", ...],
      "response": "Oh cool! You're learning Korean? How long have you been learning?",
      "next_message_index": 1
    },
    "general": {
      "response": "Hi! Nice to meet you! I'm Jake. Are you learning Korean?",
      "next_message_index": 0
    }
  }
}
```

**작동 방식:**
1. 유저 시작 감지됨
2. 첫 메시지 내용 분석
3. 키워드 매칭으로 카테고리 결정
4. 적절한 응답 전송
5. 대화 흐름의 올바른 단계로 진입

---

### 5. response_handler.py 추가 함수

```python
def analyze_user_initiated_message(self, user_message: str) -> Tuple[str, int]:
    # user_initiated 패턴과 매칭
    # 응답 메시지와 다음 단계 반환
    
    return (response, next_message_index)
```

**테스트 결과:**
```
유저: "Hi! How are you?"
→ 패턴: greeting
→ 응답: "Hi! Nice to meet you! I'm Jake. How long have you been learning Korean?"
→ 다음 단계: 1

유저: "I am learning Korean"
→ 패턴: korean_learning
→ 응답: "Oh cool! You're learning Korean? How long have you been learning?"
→ 다음 단계: 1

유저: "Some random message"
→ 패턴: general (fallback)
→ 응답: "Hi! Nice to meet you! I'm Jake. Are you learning Korean?"
→ 다음 단계: 0
```

---

## 📊 대화 흐름 예시

### 시나리오 1: 유저가 3개 메시지 연속 전송

**유저 행동:**
```
1. "Hi!"
2. "How are you?"
3. "I'm learning Korean"
```

**봇 동작:**
```
[1/3] 메시지 처리:
   답변: "Hi!"
   ✓ 응답 패턴 매칭: just_greeting → 다음 단계: 1
   📤 응답 전송: "what is the hardest part?"
   ⏸️ 다음 메시지 처리 전 3초 대기...

[2/3] 메시지 처리:
   답변: "How are you?"
   ✓ 응답 패턴 매칭: ask_about_me → 다음 단계: 1
   🔄 대체 메시지 사용
   📤 응답 전송: "I've been helping Korean learners for a while!..."
   ⏸️ 다음 메시지 처리 전 3초 대기...

[3/3] 메시지 처리:
   답변: "I'm learning Korean"
   ✓ 응답 패턴 매칭: korean_learning → 다음 단계: 1
   📤 응답 전송: (적절한 응답)

✅ 3개 메시지 처리 완료
```

---

### 시나리오 2: 유저가 먼저 대화 시작

**유저 행동:**
```
"Hi there! How are you?"
```

**봇 감지:**
```
🆕 유저가 먼저 대화 시작: "Hi there! How are you?..."
✓ 유저 시작 패턴 매칭: ask_question
📤 적절한 첫 응답 전송
   → "Hi! I'm Jake. I help people learn Korean. How long have you been learning?"
```

**다음 메시지부터:**
```
current_step = 1로 설정되어 정상 흐름 진입
```

---

### 시나리오 3: 중복 방지

**사이클 1:**
```
유저 메시지: "Hi!"
→ 처리됨
→ messages_processed에 추가: "username:5:Hi!"
```

**사이클 2 (1분 후):**
```
유저 메시지: 여전히 "Hi!" (DOM에 그대로 있음)
→ 해시 비교: "username:5:Hi!" already in messages_processed
→ 건너뜀 (중복 처리 안 함)
```

**유저가 새 메시지 보냄:**
```
유저 메시지: "That sounds cool!"
→ 새 해시: "username:7:That sounds cool!"
→ messages_processed에 없음
→ 처리 진행
```

---

## 🎨 출력 예시

### 여러 메시지 처리
```
[12/50] 🔴 진행 | Sarah (단계: 2/8)
   ✓ 새 메시지 3개 발견

   [1/3] 메시지 처리:
      답변: "I've been learning for 6 months..."
      ✓ 응답 패턴 매칭: duration_answer → 다음 단계: 1
      📤 응답 전송 (단계: 0 → 1)
      ⏸️  다음 메시지 처리 전 3초 대기...

   [2/3] 메시지 처리:
      답변: "Pronunciation is really hard!"
      ✓ 응답 패턴 매칭: specific_difficulty → 다음 단계: 2
      📤 응답 전송 (단계: 1 → 2)
      ⏸️  다음 메시지 처리 전 3초 대기...

   [3/3] 메시지 처리:
      답변: "I'm a teacher"
      ✓ 응답 패턴 매칭: job_answer → 다음 단계: 3
      📤 응답 전송 (단계: 2 → 3)

   ✅ 3개 메시지 처리 완료
```

### 유저 시작 대화
```
[5/50] 🆕 신규 | John (단계: 0/8)
   🆕 유저가 먼저 대화 시작: "Hey! What's up?..."
   ✓ 유저 시작 패턴 매칭: greeting
   📤 적절한 첫 응답 전송
```

---

## ⚙️ 설정

### 메시지 간 대기 시간
`multi_user_bot.py` 약 415번째 줄:
```python
if msg_idx < len(new_messages):
    print(f"      ⏸️  다음 메시지 처리 전 3초 대기...")
    time.sleep(3)  # ← 여기 수정
```

**권장 값:**
- 2-3초: 자연스러운 대화 속도
- 5초+: 느리지만 안정적
- 1초 미만: 빠르지만 부자연스러움

---

## 🔍 디버깅

### 메시지 처리 확인
```python
# bot_state.json 확인
{
  "username": {
    "messages_processed": [
      "username:5:Hi!",
      "username:7:That's cool"
    ]
  }
}
```

- 메시지가 여기 있으면 이미 처리됨
- 없으면 신규로 감지됨

### 유저 시작 대화 테스트
```bash
cd /Users/jaeseunglee/Downloads/hellotalk_automation
python3 << 'EOF'
from response_handler import ResponseHandler
handler = ResponseHandler()

msg = "Hi! How are you?"
response, next_idx = handler.analyze_user_initiated_message(msg)
print(f"응답: {response}")
print(f"다음 단계: {next_idx}")
EOF
```

---

## 📈 성능 영향

### 메시지 처리 속도
- **이전:** 메시지 1개당 약 2초
- **현재:** 메시지 N개당 약 2 + (N-1) * 3초
  - 예: 3개 메시지 = 2 + 2*3 = 8초

### 메모리 사용
- `messages_processed` 배열 크기: 약 50-100 bytes/user
- 1000명 유저 기준: ~50-100 KB (무시 가능)

### bot_state.json 크기
- **이전:** ~5KB (100명 기준)
- **현재:** ~8KB (100명 기준, 메시지 해시 포함)

---

## 🚨 주의사항

1. **메시지 해시 충돌 가능성**
   - 매우 낮음 (username + index + preview)
   - 같은 내용 반복 시 의도적으로 무시됨

2. **DOM 구조 변경**
   - HelloTalk 웹 업데이트 시 선택자 변경 가능
   - `.msgItemBigWrapper`, `.sendBox`, `.receiveBox` 의존

3. **메시지 순서**
   - DOM 순서대로 처리
   - 타임스탬프는 저장하지 않음 (해시만 사용)

---

## 🎯 향후 개선 가능 사항

- [ ] 실제 메시지 타임스탬프 파싱 (DOM에서 추출)
- [ ] 메시지 ID 추출 (해시 대신 공식 ID 사용)
- [ ] 이미지/스티커 메시지 처리
- [ ] 긴 메시지 자동 분할 응답
- [ ] 메시지 편집 감지
