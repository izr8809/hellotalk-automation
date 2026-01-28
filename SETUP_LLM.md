# 로컬 LLM 통합 가이드

## 1. Ollama 설치 및 설정

### macOS
```bash
# Ollama 설치
brew install ollama

# Ollama 서비스 시작
brew services start ollama

# 모델 다운로드 (추천: llama3.1:8b, 약 4.7GB)
ollama pull llama3.1:8b

# 또는 더 작은 모델 (mistral:7b, 약 4.1GB)
ollama pull mistral:7b

# 모델 확인
ollama list

# 테스트
ollama run llama3.1:8b "Hello, how are you?"
```

### Windows
```powershell
# Ollama 다운로드 및 설치
# https://ollama.com/download/windows

# 설치 후 PowerShell에서
ollama pull llama3.1:8b
ollama list
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

## 2. Python 패키지 설치

```bash
pip install requests
# 또는
pip install ollama  # 공식 Python 클라이언트
```

## 3. Ollama API 사용법

### 기본 API (HTTP)
```python
import requests
import json

def call_ollama(prompt, model="llama3.1:8b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# 테스트
result = call_ollama("Hello!")
print(result)
```

### 대화 API (Chat)
```python
def chat_ollama(messages, model="llama3.1:8b"):
    """
    messages: [
        {"role": "system", "content": "You are..."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "How are you?"}
    ]
    """
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["message"]["content"]
```

## 4. 모델 선택 가이드

| 모델 | 크기 | 속도 | 품질 | 추천 용도 |
|------|------|------|------|-----------|
| `llama3.1:8b` | 4.7GB | 보통 | 높음 | **추천** - 대화 품질 우수 |
| `mistral:7b` | 4.1GB | 빠름 | 좋음 | 빠른 응답 필요 시 |
| `phi3:mini` | 2.3GB | 매우 빠름 | 보통 | 저사양 PC |
| `llama3.1:70b` | 40GB | 느림 | 최고 | 고성능 PC만 |

## 5. 통합 확인

```bash
# Ollama가 실행 중인지 확인
curl http://localhost:11434/api/tags

# 응답 예시:
# {"models":[{"name":"llama3.1:8b",...}]}
```

## 6. 문제 해결

### "connection refused" 에러
```bash
# Ollama 서비스 재시작
brew services restart ollama

# 또는 수동 실행
ollama serve
```

### 메모리 부족
- 더 작은 모델 사용: `phi3:mini`
- 또는 quantized 모델: `llama3.1:8b-q4_0`

### 느린 응답
- GPU 가속 확인 (M1/M2 Mac은 자동)
- 더 작은 모델 사용

## 7. 다음 단계

설치가 완료되면:
1. `python3 llm_response_handler.py` - 새로운 LLM 핸들러 실행
2. `python3 multi_user_bot.py` - 봇 실행 (자동으로 LLM 사용)

## 8. 참고 자료

- Ollama 공식 문서: https://github.com/ollama/ollama
- API 문서: https://github.com/ollama/ollama/blob/main/docs/api.md
- 모델 목록: https://ollama.com/library
