#!/bin/bash

echo "================================"
echo "HelloTalk Bot - LLM 버전"
echo "================================"
echo ""

if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama가 설치되지 않았습니다"
    echo ""
    echo "설치 방법:"
    echo "  brew install ollama"
    echo "  brew services start ollama"
    echo "  ollama pull llama3.1:8b"
    echo ""
    exit 1
fi

if ! ollama list | grep -q "llama3.1:8b\|mistral:7b\|phi3:mini"; then
    echo "⚠️  모델이 다운로드되지 않았습니다"
    echo ""
    echo "다운로드:"
    echo "  ollama pull llama3.1:8b"
    echo ""
    read -p "지금 다운로드하시겠습니까? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull llama3.1:8b
    else
        exit 1
    fi
fi

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama 서버가 실행되지 않았습니다"
    echo ""
    echo "실행:"
    echo "  brew services start ollama"
    echo ""
    exit 1
fi

if ! curl -s http://localhost:9222/json > /dev/null 2>&1; then
    echo "❌ Chrome 디버그 모드가 실행되지 않았습니다"
    echo ""
    echo "실행:"
    echo '  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \'
    echo '    --remote-debugging-port=9222 \'
    echo '    --user-data-dir="/tmp/chrome-debug"'
    echo ""
    exit 1
fi

echo "✓ 모든 사전 조건 충족"
echo ""
echo "봇 실행 중..."
echo ""

python3 multi_user_bot_llm.py
