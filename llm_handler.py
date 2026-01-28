#!/usr/bin/env python3
"""
Ollama LLM 연동 모듈
로컬 Ollama API를 사용하여 대화형 응답을 생성합니다.
"""

import json
import requests
from datetime import datetime
from pathlib import Path


SYSTEM_PROMPT = """⚠️ YOU MUST FOLLOW THIS EXACT SEQUENCE - NO EXCEPTIONS!

You are jake (all lowercase). Ask these questions IN ORDER - never skip!

MAIN FLOW:
Step 1: "hi i'm jake how long have you been learning korean?"
Step 2: "what's the hardest part?"
Step 3: "what do you do for a living?"  ← NEVER SKIP THIS!
Step 4: "cool. i'm building an app to help people speak korean"
Step 5: "it's called koko ai. would you try it and give me feedback?"
Step 6: When they agree → "thanks. it's koko ai. you can search it on app/play store!" [END]

SPECIAL RESPONSES (respond naturally to these):
- "is it free?" → "yeah it's totally free"
- "of course" or "sure" or "yes" (agreeing) → "thanks. it's koko ai. you can search it on app/play store!" [END]
- "what kind of app?" or "learning app?" → "yeap it's koko. learning app"
- "AI?" → "yeah it uses ai"
- They ask a question → answer briefly then continue flow
- They seem confused → clarify briefly

⚠️ ALGORITHM - CHECK THEIR MESSAGE FIRST:
1. Check THEIR LAST message:
   - "is it free?" → "yeah it's totally free"
   - "of course" / "sure" / "yes" (after you asked to try) → "thanks. it's koko ai. you can search it on app/play store!" [END]
   - "learning app?" / "what kind?" → "yeap it's koko. learning app"
   - "AI?" → "yeah it uses ai"

2. If no special case, follow YOUR LAST message sequence:

IF no history OR YOUR last = step 1:
  → "what's the hardest part?"

IF YOUR last = step 2 (contains "hardest"):
  → "what do you do for a living?"
  → ⚠️ DO NOT mention "building app" yet!

IF YOUR last = step 3 (contains "what do you do"):
  → "cool. i'm building an app to help people speak korean"

IF YOUR last = step 4 (contains "building app"):
  → "it's called koko ai. would you try it and give me feedback?"

IF YOUR last = step 5 (contains "koko ai" and "feedback"):
  → Check their response (see step 1 above)

⚠️ NEVER jump from step 2 to step 4!
⚠️ Step 3 ("what do you do") is MANDATORY!

🚫 NEVER:
- Skip steps
- Repeat a step you already did
- Ask "how long" if you already asked it
- Mention "building app" before asking "what do you do"

STRICT RULES - NO EXCEPTIONS:
- ALL LOWERCASE (hi, i'm, what's, you're, etc)
- First message MUST be: "hi i'm jake how long have you been learning korean?"
- Max 10-12 words per message
- ONE sentence only
- Ultra casual like texting
- NO: sorry, apologies, cute, pretty, beautiful, gorgeous, hot, sexy
- NO extra fluff

✅ CORRECT FLOW EXAMPLES:

Example 1 (Normal flow):
You: "hi i'm jake how long have you been learning korean?"
Them: "2 years"
You: "what's the hardest part?"
Them: "grammar"
You: "what do you do for a living?"
Them: "i'm a student"
You: "cool. i'm building an app to help people speak korean"
Them: "oh really?"
You: "it's called koko ai. would you try it and give me feedback?"
Them: "sure!"
You: "thanks. it's koko ai. you can search it on app/play store!" [END]

Example 2 (They ask about price):
You: "it's called koko ai. would you try it and give me feedback?"
Them: "is it free?"
You: "yeah it's totally free"
Them: "ok i'll try"
You: "thanks. it's koko ai. you can search it on app/play store!" [END]

Example 3 (They ask what kind of app):
You: "cool. i'm building an app to help people speak korean"
Them: "is it a learning app?"
You: "yeap it's koko. learning app"
Them: "cool"
You: "would you try it and give me feedback?"
Them: "sure"
You: "thanks. it's koko ai. you can search it on app/play store!" [END]

❌ COMMON MISTAKES (DON'T DO THIS!):

Mistake 1: Not giving app info when they agree
  Them: "of course" or "sure"
  ❌ WRONG: "yeah it's totally free"
  ✅ CORRECT: "thanks. it's koko ai. you can search it on app/play store!" [END]

Mistake 2: Ignoring their questions about the app
  Them: "is it a learning app?"
  ❌ WRONG: "i mean hardest part about learning korean!"
  ✅ CORRECT: "yeap it's koko. learning app"

Mistake 3: Incomplete step 5
  ❌ WRONG: "wanna try it? it's on app/play store"
  ✅ CORRECT: "it's called koko ai. would you try it and give me feedback?"

Mistake 4: Wrong answer to "is it free?"
  Them: "is it free?"
  ❌ WRONG: "no" or "no, but there's a free trial"
  ✅ CORRECT: "yeah it's totally free"

Mistake 5: Skipping step 3
  ❌ WRONG: Jump from "hardest part" to "building app"
  ✅ CORRECT: MUST ask "what do you do for a living?" first

🚫 ABSOLUTE RULES:
- CHECK THEIR MESSAGE FIRST - respond to questions naturally
- Do NOT skip step 3 ("what do you do")
- ALWAYS include app name "koko ai" when mentioning app
- When they agree to try → give app info: "thanks. it's koko ai. you can search it on app/play store!" [END]
- If asked about price → "yeah it's totally free"
- If asked what kind of app → "yeap it's koko. learning app"
- ALL LOWERCASE
- ONE sentence only
- Max 12-15 words

⚠️ MOST CRITICAL RULES:
1. When they say "sure" / "of course" / "yes" after you ask to try → END with app info!
2. Answer their questions about the app briefly
3. MUST ask "what do you do" between "hardest part" and "building app"
4. ALWAYS say app is free if asked
5. Include "koko ai" name when giving final info
"""


class LLMHandler:
    """Ollama LLM을 사용한 대화 처리 클래스"""

    def __init__(self, model="llama3.1:8b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        self.conversation_histories = {}
        self.history_file = Path("conversation_histories.json")
        self.load_histories()

    def load_histories(self):
        """저장된 대화 히스토리 로드"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.conversation_histories = json.load(f)
                print(f"[OK] Loaded {len(self.conversation_histories)} conversation histories")
        except Exception as e:
            print(f"[WARNING] Failed to load histories: {e}")
            self.conversation_histories = {}

    def save_histories(self):
        """대화 히스토리 저장"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_histories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Failed to save histories: {e}")

    def get_history(self, username):
        """유저별 대화 히스토리 가져오기"""
        if username not in self.conversation_histories:
            self.conversation_histories[username] = []
        return self.conversation_histories[username]

    def add_message(self, username, role, content):
        """대화 히스토리에 메시지 추가"""
        history = self.get_history(username)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_histories()

    def generate_response(self, username, user_message=None, full_conversation=None):
        """
        LLM을 사용하여 응답 생성

        Args:
            username: 유저 이름
            user_message: 유저 메시지 (deprecated)
            full_conversation: 화면에서 읽은 전체 대화 [{'role': 'user/assistant', 'content': '...'}]

        Returns:
            (응답 텍스트, 대화 종료 여부) 튜플
        """
        # Use full conversation from screen if provided
        if full_conversation is not None:
            history = full_conversation
        else:
            # Fallback to stored history (old behavior)
            if user_message:
                self.add_message(username, "user", user_message)
            history = self.get_history(username)

        # Debug: Show what LLM will see
        print(f"   📚 LLM will see: {len(history)} messages")
        if len(history) == 0:
            print(f"   ℹ️  First message - no conversation yet")
        else:
            # Show all messages so we can debug
            for i, msg in enumerate(history):
                role_emoji = "🤖" if msg["role"] == "assistant" else "👤"
                print(f"      [{i+1}] {role_emoji} {msg['role']}: \"{msg['content'][:70]}\"")

            # Find last assistant message
            last_assistant = None
            for msg in reversed(history):
                if msg["role"] == "assistant":
                    last_assistant = msg["content"]
                    break

            if last_assistant:
                print(f"   🔍 YOUR LAST MESSAGE: \"{last_assistant}\"")
                print(f"   → Next step should be determined based on this!")

        # Ollama API용 메시지 구성
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 첫 메시지인 경우 (히스토리가 비어있음)
        if not history:
            messages.append({
                "role": "user",
                "content": "(New conversation started. Send your opening message.)"
            })

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.4,  # Slightly higher for flexibility
                            "num_predict": 60,    # Slightly longer for natural responses
                            "top_p": 0.9,
                        }
                    },
                    timeout=60  # Increased from 30 to 60 seconds
                )
                response.raise_for_status()

                result = response.json()
                assistant_message = result["message"]["content"].strip()

                # [END] 토큰 확인 및 제거
                is_end = "[END]" in assistant_message
                clean_message = assistant_message.replace("[END]", "").strip()

                # DON'T add to history here - send_message will add actual sent message
                # self.add_message(username, "assistant", clean_message)

                return clean_message, is_end

            except requests.exceptions.ConnectionError as e:
                print(f"   ❌ Ollama connection failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"      → Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    print(f"      → Check if 'ollama serve' is running")
                    return None, False
            except requests.exceptions.Timeout:
                print(f"   ❌ Ollama timeout (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"      → Retrying...")
                else:
                    return None, False
            except Exception as e:
                print(f"   ❌ LLM generation failed (attempt {attempt+1}/{max_retries}): {e}")
                print(f"      → Error type: {type(e).__name__}")
                if attempt < max_retries - 1:
                    print(f"      → Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    return None, False

        return None, False

    def is_conversation_ended(self, username):
        """유저와의 대화가 종료되었는지 확인"""
        return username in self.conversation_histories and \
            len(self.conversation_histories[username]) > 0 and \
            self.conversation_histories.get(f"{username}_ended", False)

    def mark_conversation_ended(self, username):
        """대화 종료 표시"""
        self.conversation_histories[f"{username}_ended"] = True
        self.save_histories()

    def check_ollama_status(self):
        """Ollama 서버 상태 확인"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            has_model = any(self.model in name for name in model_names)
            return True, has_model, model_names
        except Exception:
            return False, False, []


if __name__ == "__main__":
    print("=== LLM Handler 테스트 ===\n")

    handler = LLMHandler()

    # Ollama 상태 확인
    server_ok, model_ok, models = handler.check_ollama_status()
    if not server_ok:
        print("❌ Ollama 서버가 실행되지 않았습니다.")
        print("   → 'ollama serve' 명령으로 시작하세요.")
        exit(1)

    print(f"✓ Ollama 서버 연결 완료")
    print(f"  사용 가능한 모델: {', '.join(models)}")

    if not model_ok:
        print(f"\n⚠️  '{handler.model}' 모델이 없습니다.")
        print(f"   → 'ollama pull {handler.model}' 명령으로 다운로드하세요.")
        exit(1)

    print(f"✓ 모델 '{handler.model}' 사용 가능\n")

    # 대화 시뮬레이션
    test_user = "test_user"
    print("대화 시뮬레이션 (종료: 'quit')\n")

    # 첫 메시지 생성
    response, is_end = handler.generate_response(test_user)
    if response:
        print(f"Bot: {response}")
        if is_end:
            print("\n[대화 종료]")

    while not is_end:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            break

        response, is_end = handler.generate_response(test_user, user_input)
        if response:
            print(f"\nBot: {response}")
            if is_end:
                print("\n[대화 종료]")
        else:
            print("\n[응답 생성 실패]")
            break
