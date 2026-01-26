# 유연한 응답 처리 시스템

## 개요

HelloTalk 봇이 사용자의 답변 내용을 분석하여 적절한 다음 메시지를 선택할 수 있도록 하는 시스템입니다.

## 주요 기능

### 1. 키워드 기반 응답 분석
- 사용자 답변을 키워드로 분석하여 의도 파악
- 각 메시지 단계별로 예상되는 응답 패턴 정의
- 패턴에 따라 다른 메시지 전송 가능

### 2. 예상 밖 응답 로깅
- 처리하지 못한 응답을 자동으로 기록
- `unhandled_responses.json`에 저장되어 나중에 패턴 개선 가능
- 중복 응답은 자동으로 필터링

### 3. Fallback 응답
- 혼란스러워하는 경우: 질문을 명확히 설명
- 주제를 벗어난 경우: 대화를 원래 주제로 유도
- 부적절한 경우: 사용자 플래그 및 대화 종료

## 파일 구조

```
hellotalk_automation/
├── response_patterns.json       # 응답 패턴 설정 (수정 가능)
├── response_handler.py          # 응답 분석 로직 (코드)
├── unhandled_responses.json     # 처리하지 못한 응답 로그 (자동 생성)
└── multi_user_bot.py            # 메인 봇 (통합됨)
```

## 사용 방법

### 1. 봇 실행
기존과 동일하게 실행하면 자동으로 응답 분석 기능이 작동합니다:

```bash
python3 multi_user_bot.py
```

### 2. 응답 패턴 수정

`response_patterns.json` 파일을 수정하여 새로운 응답 패턴을 추가할 수 있습니다.

#### 예시: 메시지 단계 0 (첫 인사)

```json
"0": {
  "message": "Hi, I'm jake, how long have you been learning Korean?",
  "expected_responses": {
    "duration_answer": {
      "keywords": ["month", "year", "week", "day", "since", "for", "just started"],
      "next_message_index": 1,
      "description": "User provides duration of learning"
    },
    "no_learning": {
      "keywords": ["not learning", "don't learn", "not yet"],
      "next_message_index": 2,
      "alternative_message": "Oh! Are you interested in learning Korean?",
      "description": "User is not learning Korean"
    }
  }
}
```

#### 패턴 필드 설명

- `keywords`: 매칭할 키워드 리스트 (소문자로 작성)
- `next_message_index`: 다음에 보낼 메시지 인덱스 (0-5, -1은 대화 종료)
- `alternative_message`: (선택) 기본 메시지 대신 보낼 메시지
- `skip_to_end`: (선택) true면 대화 즉시 종료
- `description`: 패턴 설명 (주석용)

### 3. 예상 밖 응답 확인

봇 실행 중 처리하지 못한 응답은 `unhandled_responses.json`에 기록됩니다:

```json
[
  {
    "timestamp": "2026-01-26T16:30:45.123456",
    "username": "TestUser",
    "message_step": 0,
    "my_message": "Hi, I'm jake, how long have you been learning Korean?",
    "user_response": "I'm busy right now",
    "analyzed": false
  }
]
```

이 로그를 확인하여 `response_patterns.json`에 새로운 패턴을 추가할 수 있습니다.

### 4. 패턴 업데이트 워크플로우

1. 봇 실행
2. `unhandled_responses.json` 확인
3. 자주 나오는 응답 패턴 파악
4. `response_patterns.json`에 새 패턴 추가
5. 봇 재시작 (변경사항 자동 적용)

## 예시: 새 패턴 추가하기

### 상황
사용자들이 "I'm too busy"라고 자주 답변하는 것을 발견했습니다.

### 해결

`response_patterns.json`의 해당 단계에 패턴 추가:

```json
"4": {
  "message": "Do u mind giving me some feedback as learner? It will be big help!",
  "expected_responses": {
    "too_busy": {
      "keywords": ["too busy", "very busy", "no time right now"],
      "next_message_index": 5,
      "alternative_message": "No worries! You can check it out when you have time. Search 'kokoai' on app store!",
      "skip_to_end": true,
      "description": "User is too busy"
    }
  }
}
```

## 고급 기능

### Fallback 응답

예상 패턴에 맞지 않지만 특정 상황에 대응해야 할 때 사용:

```json
"fallback_responses": {
  "confused": {
    "keywords": ["what", "huh", "don't understand"],
    "response": "Sorry if I wasn't clear! I'm just asking about your Korean learning experience."
  }
}
```

### 대화 흐름 예시

```
사용자: "Hi! I've been learning for 3 months"
→ 패턴 매칭: duration_answer
→ 다음 메시지: messages[1] = "what is the hardest part?"

사용자: "pronunciation is so hard!"
→ 패턴 매칭: specific_difficulty
→ 다음 메시지: messages[2] = "what do you do for a living?"

사용자: "I don't want to say"
→ 패턴 매칭: private
→ 대체 메시지: "No problem! I'm building an app..."
→ 다음 메시지 건너뛰고 messages[3] 전송
```

## 테스트

`response_handler.py`를 직접 실행하면 테스트 케이스를 통해 패턴이 제대로 작동하는지 확인할 수 있습니다:

```bash
python3 response_handler.py
```

## 주의사항

1. **키워드는 소문자로 작성**: 시스템이 자동으로 소문자 변환
2. **단어 경계 매칭**: "learn"은 "learning"과도 매칭됨
3. **순서 중요**: 먼저 정의된 패턴이 우선 매칭됨
4. **백업 저장**: `response_patterns.json` 수정 전 백업 권장

## 통계 확인

Python으로 통계 확인:

```python
from response_handler import ResponseHandler

handler = ResponseHandler()
stats = handler.get_unhandled_stats()

print(f"총 예상 밖 응답: {stats['total']}개")
print(f"단계별 분포: {stats['by_step']}")
print(f"최근 10개: {stats['recent_10']}")
```

## 문제 해결

### 패턴이 매칭되지 않음
- 키워드 철자 확인
- 소문자로 작성했는지 확인
- 더 일반적인 키워드 추가 시도

### 너무 많은 예상 밖 응답
- 키워드 범위를 넓히기 (예: "not interested" 외에 "no thanks", "pass" 추가)
- Fallback 응답 활용

### 잘못된 메시지 전송
- `next_message_index`가 올바른지 확인
- messages.txt의 인덱스는 0부터 시작

## 향후 개선 가능 사항

현재 시스템에서 패턴 개선이 필요하면:

1. `unhandled_responses.json` 검토
2. 공통 패턴 식별
3. `response_patterns.json`에 추가
4. 필요시 새로운 `alternative_message` 작성

이 시스템은 사용자 피드백을 기반으로 계속 발전할 수 있도록 설계되었습니다!
