# 이전 대화 복구 시스템

## 문제 상황

### 시나리오
```
실제 HelloTalk 대화창:
├─ [이전] 봇: "Hi, I'm jake, how long have you been learning Korean?"
├─ [이전] 유저: "About 3 months"
├─ [이전] 봇: "what is the hardest part?"
└─ [최신] 유저: "Grammar is really hard for me"

봇의 상태:
├─ current_step: 0 (첫 만남으로 인식)
├─ messages_processed: [] (빈 배열)
└─ 이전 대화 기록 없음
```

**문제:** 봇이 유저를 처음 만나는 것으로 착각하여:
- ❌ 다시 "Hi, I'm jake..." 전송
- ❌ 이미 진행된 대화 무시
- ❌ 유저 혼란 발생

---

## 해결 방법

### 핵심 로직

봇이 `current_step == 0` (처음 만나는 유저)인데 **첫 감지된 메시지가 어려움을 언급**하면:
- ✅ 이전에 이미 0단계, 1단계가 진행되었다고 **추정**
- ✅ 바로 **2단계 (what do you do for a living?)로 진입**
- ✅ `current_step`을 3으로 설정하여 다음부터 정상 흐름

---

## 구현 세부사항

### 1. 어려움 키워드 감지

**키워드 리스트:**
```python
difficulty_keywords = [
    "grammar", "pronunciation", "listening", "speaking", 
    "reading", "writing", "vocabulary", "particles", "verb", 
    "hard", "difficult", "batchim", "diphthong", "memorizing", 
    "time", "getting time", "where do i start", "can u help", "help me"
]
```

**감지 로직:**
```python
mentions_difficulty = any(keyword in first_msg_text.lower() for keyword in difficulty_keywords)
```

---

### 2. 처리 흐름

```
IF current_step == 0 AND 새 메시지 있음:
    첫 메시지 내용 확인
    
    IF 어려움 키워드 포함:
        print("⚠️ 이미 어려움 언급 → 이전 대화 있었음 추정")
        print("⏩ 바로 2단계(직업 질문)로 진입")
        
        # 1단계 응답으로 분석 (어려운 부분 질문에 대한 답변으로 간주)
        next_step, alt_msg = analyze_response(첫_메시지, step=1, ...)
        
        # 2단계 메시지 또는 대체 메시지 전송
        send_message(messages[2] or alternative_message)
        
        # 상태를 3으로 설정 (2단계 완료, 다음은 3단계)
        current_step = 3
        
    ELSE:
        # 정상 흐름 (유저 시작 대화 또는 봇이 먼저 시작)
```

---

## 예시

### 예시 1: 문법 어려움 언급

**상황:**
```
DOM에 이전 대화 존재:
├─ sendBox: "Hi, I'm jake, how long..."
├─ receiveBox: "3 months"
├─ sendBox: "what is the hardest part?"
└─ receiveBox: "Grammar is really hard" ← 봇이 처음 감지

bot_state.json:
{
  "current_step": 0,  // 봇은 이 유저를 처음 만남
  "messages_processed": []
}
```

**봇 동작:**
```
🔍 첫 메시지 감지됨: "Grammar is really hard"
⚠️  이미 어려움 언급 → 이전 대화 있었음 추정
⏩ 바로 2단계(직업 질문)로 진입
✓ 응답 패턴 매칭: specific_difficulty → 다음 단계: 2
📤 응답 전송: "what do you do for a living?"
✅ current_step = 3으로 설정
```

---

### 예시 2: 도움 요청

**상황:**
```
DOM:
└─ receiveBox: "Can you help me learn Korean?" ← 봇이 처음 감지

bot_state.json:
{
  "current_step": 0,
  "messages_processed": []
}
```

**봇 동작:**
```
🔍 첫 메시지 감지됨: "Can you help me learn Korean?"
⚠️  이미 어려움 언급 → 이전 대화 있었음 추정
⏩ 바로 2단계(직업 질문)로 진입
✓ 응답 패턴 매칭: ask_for_help → 다음 단계: 2
🔄 대체 메시지 사용
📤 응답 전송: "I'd love to help! That's why I built an app..."
✅ current_step = 3으로 설정
```

---

### 예시 3: 일반 인사 (어려움 없음)

**상황:**
```
DOM:
└─ receiveBox: "Hi! How are you?" ← 봇이 처음 감지

bot_state.json:
{
  "current_step": 0,
  "messages_processed": []
}
```

**봇 동작:**
```
🔍 첫 메시지 감지됨: "Hi! How are you?"
⚪ 어려움 언급 없음 → 정상 흐름
🆕 유저가 먼저 대화 시작: "Hi! How are you?"
✓ 유저 시작 패턴 매칭: ask_question
📤 적절한 첫 응답 전송: "Hi! I'm Jake. I help people learn Korean..."
✅ current_step = 1로 설정
```

**차이점:** 어려움 언급이 없으면 정상적으로 1단계부터 시작

---

## 처리 플로우 다이어그램

```
┌─────────────────────────────────────┐
│ current_step == 0 (처음 만나는 유저) │
└─────────────────┬───────────────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │ 새 메시지 있음?      │
       └──────┬───────────────┘
              │
        YES   │   NO
    ┌─────────┴─────────┐
    ▼                   ▼
┌───────────────┐  ┌──────────────────┐
│ 첫 메시지 분석 │  │ 정상 흐름        │
│ 어려움 언급?   │  │ (유저 시작 or    │
└───┬───────────┘  │  봇이 첫 메시지)  │
    │              └──────────────────┘
    │
YES │   NO
┌───┴────┬────────┐
▼        ▼        ▼
[이전    [유저    [봇이
대화     시작    먼저
추정]    대화]    시작]
│        │        │
▼        ▼        ▼
2단계    1단계    1단계
진입     진입     진입
```

---

## 코드 위치

**파일:** `multi_user_bot.py`

**함수:** `check_and_send_next_message()`

**라인:** 약 361-377

```python
new_messages = self.get_all_new_received_messages(username)

if state['current_step'] == 0 and new_messages:
    first_msg_text = new_messages[0]['text']
    print(f"   🔍 첫 메시지 감지됨: \"{first_msg_text[:50]}...\"")
    
    difficulty_keywords = [...]
    
    mentions_difficulty = any(keyword in first_msg_text.lower() 
                             for keyword in difficulty_keywords)
    
    if mentions_difficulty:
        print(f"   ⚠️  이미 어려움 언급 → 이전 대화 있었음 추정")
        print(f"   ⏩ 바로 2단계(직업 질문)로 진입")
        
        # 1단계 응답으로 분석
        next_step, alt_msg, _ = self.response_handler.analyze_response(
            first_msg_text, 1, username, self.messages[1]
        )
        
        # 2단계 메시지 전송
        if alt_msg:
            response = alt_msg
        elif next_step is not None and next_step < len(self.messages):
            response = self.messages[next_step]
        else:
            response = self.messages[2]
        
        success = self.send_message(response)
        if success:
            state['current_step'] = 3  # 2단계 완료
            state['messages_processed'].append(new_messages[0]['hash'])
            self.save_state()
            return True
```

---

## 테스트 케이스

| 첫 메시지 | 어려움 감지 | 진입 단계 | 전송 메시지 |
|----------|------------|----------|------------|
| "Grammar is really hard" | ✅ Yes | 2단계 | "what do you do for a living?" |
| "Pronunciation is difficult" | ✅ Yes | 2단계 | "what do you do for a living?" |
| "Can you help me learn?" | ✅ Yes | 2단계 | "I'd love to help! That's why..." |
| "Getting time is the problem" | ✅ Yes | 2단계 | "what do you do for a living?" |
| "Hi! How are you?" | ❌ No | 1단계 | "Hi! I'm Jake..." |
| "3 months" | ❌ No | 1단계 | "what is the hardest part?" |

---

## 왜 이 방법이 효과적인가?

### 1. 실용적 추정
- HelloTalk에서 유저가 갑자기 "문법이 어려워"라고 말하면, 99% 이전에 "뭐가 어려워?" 질문이 있었음
- 완벽한 추정은 아니지만 **실용적으로 충분**

### 2. 대화 흐름 유지
- 유저가 이미 진행 중인 대화를 계속할 수 있음
- 처음부터 다시 시작하지 않아 자연스러움

### 3. 유연한 복구
- DOM이 완벽하게 로드되지 않아도 작동
- 이전 메시지가 보이지 않아도 문맥으로 추정

### 4. 최소 침해
- 어려움 언급이 없으면 정상 흐름 유지
- False positive 가능성 낮음

---

## 한계 및 주의사항

### 1. False Positive 가능성
**케이스:** 유저가 처음부터 "Grammar is hard" 같은 일반적 얘기를 할 때

**예시:**
```
유저: "Hi! I heard Korean grammar is hard, is that true?"
봇: (어려움 감지) → 2단계로 진입
```

**해결:** 현재로서는 허용 (실제로 드문 케이스)

---

### 2. 키워드 의존성
**문제:** 키워드 리스트에 없는 표현은 감지 못함

**예시:**
```
유저: "The alphabet is tricky for me"
→ "tricky"는 키워드에 없음
→ 정상 흐름으로 진행
```

**해결:** 자주 나오는 표현을 키워드에 추가

---

### 3. 다중 건너뛰기 불가
**현재:** 0단계 → 2단계만 건너뛰기

**만약 필요하다면:**
- 직업 언급이 있으면 → 3단계로
- 앱 언급이 있으면 → 4단계로

**예시:**
```python
if mentions_job:
    print("⏩ 3단계로 진입")
    state['current_step'] = 4
```

---

## 향후 개선 가능 사항

### 1. 더 스마트한 단계 추정
```python
def estimate_conversation_step(first_message):
    if mentions_app_or_koko:
        return 4  # 앱 소개 이후
    elif mentions_job:
        return 3  # 직업 질문 이후
    elif mentions_difficulty:
        return 2  # 어려움 질문 이후
    elif mentions_duration:
        return 1  # 기간 질문 이후
    else:
        return 0  # 처음부터
```

### 2. DOM 메시지 카운트 활용
```python
my_message_count = len(page.query_selector_all('.sendBox'))
received_message_count = len(page.query_selector_all('.receiveBox'))

if my_message_count > 0:
    # 이미 대화 진행됨
    estimated_step = min(my_message_count, len(messages))
```

### 3. 타임스탬프 기반 감지
```python
# 마지막 메시지가 오래됐으면 이전 대화로 간주
if last_message_age > timedelta(hours=1):
    # 이전 대화 추정
```

---

## 요약

**문제:** 봇이 이전 대화를 못 읽어서 처음부터 다시 시작

**해결:** 첫 메시지에 어려움이 언급되면 이전 대화가 있었다고 추정하고 2단계로 진입

**효과:**
- ✅ 자연스러운 대화 흐름 유지
- ✅ 유저 혼란 방지
- ✅ 대화 효율성 증가

**제한:**
- ⚠️ 완벽한 추정은 아님 (실용적으로 충분)
- ⚠️ 키워드 리스트에 의존
- ⚠️ 0→2 단계만 지원 (확장 가능)
