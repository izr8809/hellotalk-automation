# HelloTalk Bot - LLM 통합 버전

## 🎯 개요

HelloTalk 웹에서 자동으로 대화하는 봇의 **LLM 통합 버전**입니다.

기존 Rule-based 시스템 대신 **로컬 LLM (Ollama)**을 사용하여 더 자연스럽고 유연한 대화를 생성합니다.

### Rule-based vs LLM

| 특징 | Rule-based | LLM (새 버전) |
|------|-----------|---------------|
| 자연스러움 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 응답 속도 | 즉시 | 2-5초 |
| 유연성 | 낮음 | 높음 |
| 설정 | 간단 | Ollama 필요 |
| 메모리 | 적음 | 5-8GB RAM |

---

## 🚀 빠른 시작

### 필수 조건

1. **macOS** (M1/M2 권장, Intel도 가능)
2. **8GB+ RAM**
3. **5GB+ 디스크 공간**
4. **Python 3.7+**

### 설치 (5분)

```bash
# 1. Ollama 설치
brew install ollama
brew services start ollama

# 2. 모델 다운로드 (4.7GB)
ollama pull llama3.1:8b

# 3. Chrome 디버그 모드 실행
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome-debug"

# 4. HelloTalk 웹 로그인
# 브라우저에서 https://web.hellotalk.com/

# 5. 봇 실행
cd ~/Downloads/hellotalk_automation
./run_llm.sh
```

---

## 📁 파일 구조

### 새로 추가된 파일

```
hellotalk_automation/
├── llm_response_handler.py    # LLM 기반 응답 핸들러
├── multi_user_bot_llm.py       # LLM 통합 봇 (메인)
├── test_llm.py                 # LLM 테스트 스크립트
├── run_llm.sh                  # 실행 스크립트
├── SETUP_LLM.md                # 상세 설치 가이드
├── QUICKSTART_LLM.md           # 빠른 시작 가이드
└── README_LLM.md               # 이 파일
```

### 기존 파일 (호환성 유지)

```
├── multi_user_bot.py           # Rule-based 봇 (여전히 작동)
├── response_handler.py         # Rule-based 핸들러
├── response_patterns.json      # Rule 정의
└── messages.txt                # Rule-based용 메시지
```

---

## 🎮 사용 방법

### 기본 실행

```bash
# LLM 버전
./run_llm.sh

# 또는 직접
python3 multi_user_bot_llm.py
```

### Rule-based로 돌아가기

```bash
python3 multi_user_bot.py
```

---

## 🧪 테스트

### 연결 테스트

```bash
python3 test_llm.py connection
```

### 대화형 테스트

```bash
python3 test_llm.py interactive
```

### 시나리오 테스트

```bash
python3 test_llm.py scenarios
```

### 전체 테스트

```bash
python3 test_llm.py
```

---

## ⚙️ 설정

### 모델 변경

`llm_response_handler.py` 파일의 `__init__()` 함수:

```python
def __init__(self, 
             model: str = "llama3.1:8b",  # 여기 수정
             ollama_url: str = "http://localhost:11434"):
```

**모델 옵션:**

| 모델 | 크기 | 속도 | 품질 | 용도 |
|------|------|------|------|------|
| `llama3.1:8b` | 4.7GB | 보통 | 높음 | **추천** |
| `mistral:7b` | 4.1GB | 빠름 | 좋음 | 빠른 응답 필요 시 |
| `phi3:mini` | 2.3GB | 매우 빠름 | 보통 | 저사양 PC |
| `llama3.1:70b` | 40GB | 느림 | 최고 | 고성능 PC |

### 대화 스타일 조정

`llm_response_handler.py`의 `system_prompt` 수정:

```python
self.system_prompt = """You are Jake, a friendly Korean language app developer...

CONVERSATION STYLE:
- Be casual and friendly (use "u" instead of "you")  # 여기 수정
- Keep messages short (1-2 sentences max)
- Show genuine interest
...
"""
```

### 응답 길이 제한

`call_llm()` 함수의 `max_tokens`:

```python
"options": {
    "temperature": 0.7,
    "max_tokens": 150  # 100-200 권장
}
```

### 창의성 조절

`temperature` 값:
- `0.1-0.3`: 보수적, 예측 가능
- `0.5-0.7`: 균형 (추천)
- `0.8-1.0`: 창의적, 다양함

---

## 🔍 동작 원리

### 대화 플로우

```
1. 유저 메시지 수신
   ↓
2. LLM에게 전달:
   - System prompt (목표, 스타일)
   - 대화 히스토리 (최근 10개)
   - 현재 단계 (0-7)
   ↓
3. LLM 분석:
   - 유저 의도 파악
   - 적절한 응답 생성
   - 다음 단계 결정
   ↓
4. 응답 전송 및 상태 업데이트
```

### 대화 단계 (0-7)

```
0. 학습 기간 확인
1. 어려운 점 파악
2. 직업/배경 확인
3. 앱 소개
4. 피드백 요청
5. 앱 링크 공유
6. 사용 여부 확인
7. 피드백 수집
```

LLM은 각 단계에서:
- 유저 응답에 따라 유연하게 대응
- 관심 없으면 조기 종료
- 긍정적이면 다음 단계로 자연스럽게 이동

---

## 📊 피드백 분석

### 피드백 확인

```bash
# JSON 예쁘게 보기
cat user_feedback.json | python3 -m json.tool

# 피드백 개수
cat user_feedback.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"

# 최근 5개만 보기
cat user_feedback.json | python3 -c "import sys,json; data=json.load(sys.stdin); print('\n'.join([f'{x[\"username\"]}: {x[\"feedback\"]}' for x in data[-5:]]))"
```

### 피드백 구조

```json
{
  "timestamp": "2026-01-28T16:30:45.123456",
  "username": "Sarah",
  "stage": 7,
  "feedback": "I love the pronunciation feature!",
  "analyzed": false
}
```

---

## 🔧 문제 해결

### Ollama 관련

**"Ollama 서버에 연결할 수 없습니다"**

```bash
# 확인
curl http://localhost:11434/api/tags

# 재시작
brew services restart ollama

# 수동 실행
ollama serve
```

**"모델을 찾을 수 없습니다"**

```bash
# 모델 목록 확인
ollama list

# 다운로드
ollama pull llama3.1:8b
```

**메모리 부족**

더 작은 모델 사용:
```bash
ollama pull phi3:mini
```

### 응답 품질

**응답이 너무 길 때**

`max_tokens` 줄이기:
```python
"max_tokens": 100  # 150 → 100
```

**응답이 부적절할 때**

`system_prompt` 수정:
```python
self.system_prompt = """...

CONVERSATION STYLE:
- Be professional  # 추가
- Avoid casual language  # 수정
...
"""
```

**응답이 일관성 없을 때**

`temperature` 낮추기:
```python
"temperature": 0.3  # 0.7 → 0.3
```

### 성능

**응답이 느릴 때**

1. 더 작은 모델: `phi3:mini`
2. GPU 가속 확인 (M1/M2는 자동)
3. 대화 히스토리 줄이기:
```python
llm_messages.extend(history[-5:])  # -10 → -5
```

---

## 🚨 주의사항

### 정책 위반 가능성

이 봇은 **Anthropic 사용 정책** 및 **HelloTalk 약관**을 위반할 수 있습니다:

- ❌ 자동화된 소셜 상호작용
- ❌ 사용자 속이기
- ❌ 스팸 행위

**권장 사항:**
1. 교육/연구 목적으로만 사용
2. 소수의 유저로 테스트
3. 투명하게 AI 사용 명시
4. 과도한 사용 자제

### 윤리적 고려사항

- 상대방이 봇과 대화한다는 것을 알리는 것이 바람직
- 개인 정보 수집 금지
- 부적절한 대화 자동 종료
- 피드백 수집 시 동의 구하기

---

## 📈 향후 개선 방향

### 단기
- [ ] 감정 분석 추가
- [ ] 다국어 지원
- [ ] 응답 시간 최적화
- [ ] 로깅 개선

### 중기
- [ ] GUI 인터페이스
- [ ] 실시간 피드백 분석
- [ ] A/B 테스트 기능
- [ ] 통계 대시보드

### 장기
- [ ] 파인튜닝된 모델
- [ ] 멀티모달 지원 (이미지)
- [ ] 클라우드 배포
- [ ] API 서버화

---

## 📚 추가 문서

- **SETUP_LLM.md**: 상세 설치 가이드
- **QUICKSTART_LLM.md**: 5분 빠른 시작
- **llm_response_handler.py**: 소스 코드 (주석 포함)
- **test_llm.py**: 테스트 예제

---

## 🤝 기여

개선 사항이나 버그 발견 시:

1. 이슈 생성
2. Pull Request
3. 피드백 공유

---

## 📝 라이선스

MIT License - 교육 목적

---

## ⚖️ 면책 조항

- HelloTalk 공식 도구 아님
- 사용자 책임 하에 사용
- 계정 정지 위험 있음
- 개발자는 책임 없음

---

**행운을 빕니다! 🚀**
