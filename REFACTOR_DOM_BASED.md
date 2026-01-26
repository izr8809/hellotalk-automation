# DOM 기반 상태 관리로 리팩토링

## 날짜
2026-01-26

## 문제점

### 기존 시스템 (current_step 기반)
```python
state = {
    'current_step': 3,  # 다음에 보낼 메시지 인덱스
    'completed': False,
    'messages_processed': [...]
}
```

**문제:**
1. **State와 DOM 불일치** - 실제 전송한 메시지와 저장된 step이 맞지 않음
2. **Old → New 전환 시 버그** - 이전 시스템 유저의 state가 실제와 불일치
3. **복잡한 동기화 로직** - Line 328-334에서 불일치 감지 및 수정 시도
4. **디버깅 어려움** - State 보고 실제 상태 파악 불가능

### 실제 발생한 버그 (Gao Vang)
- State: `current_step = 3`
- 실제: Step 4까지 전송됨
- 결과: User 답변을 처리하지 못하고 멈춤

## 해결책: DOM이 진실의 원천 (Single Source of Truth)

### 새로운 시스템
```python
state = {
    'completed': False,  # 단순히 완료 여부만
    'messages_processed': [...]  # 중복 처리 방지용
}
```

**핵심 원칙:**
- **`current_step` 완전 제거**
- **매번 DOM에서 마지막 bot 메시지 확인**
- **State는 최소한만 저장** (완료 여부, 처리한 메시지 해시)

## 로직 흐름

### 1. 대화 열기
```python
last_msg_idx = self.get_my_last_message_index()
# DOM에서 실제 마지막 bot 메시지 찾기
```

### 2. Bot 메시지 없음 (last_msg_idx == -1)
```python
user_initiated, first_msg = self.detect_user_initiated_conversation()

if user_initiated:
    # User가 먼저 시작
    response, _ = self.response_handler.analyze_user_initiated_message(first_msg)
    # → "Hi! Nice to meet you! I'm Jake. Hi, I'm jake, how long..."
else:
    # Bot이 먼저 시작
    self.send_message(self.messages[0])
```

### 3. Bot 메시지 있음 (last_msg_idx >= 0)
```python
# 예: last_msg_idx = 2 (step 2 메시지 전송됨)
new_messages = self.get_all_new_received_messages(username)

for user_reply in new_messages:
    # User가 step 2에 대한 응답을 함
    next_step, alt_msg, _ = self.response_handler.analyze_response(
        user_reply,
        last_msg_idx,  # = 2 (응답 대상 step)
        username,
        self.messages[last_msg_idx]
    )
    
    # next_step = 3 반환
    if alt_msg:
        self.send_message(alt_msg)
    else:
        self.send_message(self.messages[next_step])
    
    # 다음 iteration에서 last_msg_idx는 다시 DOM에서 가져옴
```

## 변경된 파일

### 1. multi_user_bot.py
- **제거:** `current_step` 모든 참조
- **단순화:** `check_and_send_next_message()` 로직
- **개선:** 대소문자 무시 메시지 매칭 (`get_my_last_message_index`)

### 2. bot_state.json
- **제거:** 모든 유저의 `current_step` 필드
- **유지:** `completed`, `messages_processed`, `last_check_time`

## 장점

### 1. 버그 해결
- ✅ State 불일치 불가능 (DOM이 항상 정확)
- ✅ Old system 유저도 정상 작동
- ✅ 봇 재시작해도 문제 없음

### 2. 코드 단순화
- ✅ State 동기화 로직 완전 제거
- ✅ Conversation recovery 로직 제거
- ✅ 디버깅 쉬움 (HelloTalk 대화 = 실제 상태)

### 3. 유지보수성
- ✅ 로직이 직관적
- ✅ 새로운 개발자도 이해 쉬움
- ✅ 테스트 쉬움

## 테스트 체크리스트

- [ ] 새 유저 (bot 메시지 없음, user도 메시지 안 보냄) → Bot이 step 0 전송
- [ ] User-initiated (bot 메시지 없음, user가 "Hi" 전송) → Bot이 acknowledgment + step 0 전송
- [ ] 진행 중 유저 (bot step 2까지 전송, user 답변 있음) → Bot이 step 3 전송
- [ ] 완료 유저 (bot step 7까지 전송) → completed = True 설정
- [ ] Old system 유저 (state에 잘못된 current_step) → DOM 기반으로 정상 동작

## 마이그레이션 노트

**bot_state.json 자동 정리:**
```bash
python3 -c "
import json
with open('bot_state.json', 'r') as f:
    state = json.load(f)
for user in state['user_states']:
    state['user_states'][user].pop('current_step', None)
with open('bot_state.json', 'w') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
"
```

이미 실행 완료되었습니다.
