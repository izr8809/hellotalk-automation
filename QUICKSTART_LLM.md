# LLM 통합 버전 빠른 시작 가이드

## 🚀 5분 설정

### 1단계: Ollama 설치 (1분)

```bash
# macOS
brew install ollama
brew services start ollama

# 모델 다운로드 (추천: llama3.1:8b, 약 4.7GB)
ollama pull llama3.1:8b

# 확인
ollama list
```

### 2단계: Chrome 디버그 모드 실행 (1분)

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome-debug"
```

### 3단계: HelloTalk 웹 로그인 (1분)

브라우저에서 https://web.hellotalk.com/ 열고 로그인

### 4단계: 봇 실행 (1분)

```bash
cd ~/Downloads/hellotalk_automation
python3 multi_user_bot_llm.py
```

끝! LLM이 자동으로 자연스러운 대화를 생성합니다.

---

## 🔄 Rule-based vs LLM 비교

### Rule-based (기존)
```bash
python3 multi_user_bot.py
```
- ✅ 빠른 응답
- ✅ 예측 가능한 대화
- ❌ 덜 자연스러움
- ❌ 유연성 부족

### LLM (새 버전)
```bash
python3 multi_user_bot_llm.py
```
- ✅ 자연스러운 대화
- ✅ 유연한 응답
- ✅ 상황 이해
- ❌ 느린 응답 (2-5초)
- ❌ Ollama 설치 필요

---

## ⚙️ 설정 옵션

### 모델 변경

`llm_response_handler.py` 파일에서:

```python
def __init__(self, 
             model: str = "llama3.1:8b",  # 여기 수정
             ollama_url: str = "http://localhost:11434"):
```

**모델 옵션:**
- `llama3.1:8b` - 추천 (4.7GB, 높은 품질)
- `mistral:7b` - 빠름 (4.1GB)
- `phi3:mini` - 저사양 (2.3GB)

### 온도 조절 (창의성)

`llm_response_handler.py`의 `call_llm()` 함수에서:

```python
"options": {
    "temperature": 0.7,  # 0.1-1.0 (낮을수록 보수적)
    "max_tokens": 150
}
```

---

## 🧪 테스트

```bash
# LLM handler 단독 테스트
python3 llm_response_handler.py

# 실제 봇 테스트
python3 multi_user_bot_llm.py
```

---

## 📊 피드백 확인

```bash
# 수집된 피드백 보기
cat user_feedback.json | python3 -m json.tool

# 피드백 개수
cat user_feedback.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
```

---

## 🔧 문제 해결

### "Ollama 서버에 연결할 수 없습니다"

```bash
# Ollama 재시작
brew services restart ollama

# 또는 수동 실행
ollama serve
```

### "모델을 찾을 수 없습니다"

```bash
# 모델 다운로드
ollama pull llama3.1:8b

# 확인
ollama list
```

### 응답이 너무 느림

- 더 작은 모델 사용: `phi3:mini`
- GPU 가속 확인 (M1/M2 Mac은 자동)

### 응답이 너무 길음

`llm_response_handler.py`에서 `max_tokens` 줄이기:

```python
"max_tokens": 100  # 150 → 100
```

---

## 💡 팁

1. **첫 실행은 느림**: 모델 로드에 시간이 걸립니다 (30초)
2. **메모리 사용**: 약 5-8GB RAM 필요
3. **배터리**: 노트북 사용 시 전원 연결 권장
4. **대화 품질**: 2-3명과 테스트 후 조정

---

## 🎯 다음 단계

1. **프롬프트 개선**: `llm_response_handler.py`의 `system_prompt` 수정
2. **대화 스타일 조정**: temperature 값 실험
3. **피드백 분석**: 수집된 피드백으로 프롬프트 개선
4. **모델 비교**: 다른 모델 테스트

---

## 📚 추가 문서

- 상세 설명: `SETUP_LLM.md`
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- 모델 목록: https://ollama.com/library
