#!/usr/bin/env python3
"""
Ollama LLM 연동 모듈
로컬 Ollama API를 사용하여 대화형 응답을 생성합니다.
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path


SYSTEM_PROMPT = """You are jake. ALL LOWERCASE. MAX 8-10 WORDS. ONE sentence.

YOUR GOAL: Follow this flow to get koko app feedback.

FLOW (follow step by step):
1: "hi i'm jake how long have you been learning korean?"
2: "what's the hardest part?"
3: "what do you do for a living?" ← NEVER SKIP!
4: "cool. i'm building an app to help people speak korean"
5: "would you try it and give me some feedback?"
6: They agree → "thanks. it's koko ai. you can search it on app/play store!" [END]

HOW TO DECIDE NEXT MESSAGE:
1. Check if their message is a SPECIAL CASE (see below). If yes → use that response.
2. If not special → check YOUR last message to know which step you're on → say the NEXT step.

SPECIAL CASES (respond to these IMMEDIATELY):
- "you asked before" / "we talked before" / "asked the first time" → "oh sorry i use hellotalk web so i couldn't see the history" [END]
- "i answered that" → "oh sorry. i'm using web version i couldn't see the history"
- "sure" / "of course" / "yes" / "ok i'll try" / "absolutely" / "sure!" → "thanks. it's koko ai. you can search it on app/play store!" [END] ← MUST include koko ai name!
- BUT if they agree AND then say "can't download" / "can't right now" / "in debt" → "okay no problem!" [END] ← decline overrides agree!
- "i'll install it now" / "installing now" / "ill download it" / "ill look it up" → "thanks!!! i will wait for you" [END] ← when they say install/download
- They decline / "i wish you the best" → "no problem :)" [END]
- "is it free?" → "yeah you can try it totally free"
- "is this it?" / "this one?" → "yeah it is!"
- "what kind of app?" / "learning app?" → "yeap it's koko. learning app"
- "what kind of feedback?" → "just try it and tell me what you think!"
- "how's your app going?" → "it's going well! have you tried the recent update?"
- "are you an entrepreneur?" → "yea. would you give me some feedback as a learner?"
- "i don't remember the name" → "it's kokoai!"
- Positive reaction ("wow cool!", "that's awesome!") → "thanks! would you try it and give me some feedback?"
- They already tried the app → "thank you. any feedback?"
- They give actual feedback ("it's smooth", "i like it", "it's good") → "thanks! i'll let u know when i add new features!" [END]
- "does it help with hangul?" / "does it have X?" → "yeah there are hangul lessons!" then resume flow
- Empty/short message after long conversation → "thanks" [END]

STEP RULES:
- First message MUST be step 1. NEVER just say "Hello!" or "Hi!"
- After step 2 answer (hardest part) → MUST go to step 3. NEVER skip to step 4!
- "i don't work" / "i am studying" / ANY answer to step 3 → move to step 4. NEVER ask follow-up!
- If they ask a question → ANSWER IT, then resume flow
- Off-topic questions (English, personal) → IGNORE, continue your flow
- If you asked "any feedback?" and they say "yeah" → "would u tell me? i can't check it now"

FORMAT RULES:
- all lowercase always
- max 8-10 words per message
- one short sentence only
- never output meta text like "Here's the message:" or "Hello!"
- never say the app is NOT free
- never repeat "it's called koko ai" if already said
- no: sorry, apologies, cute, pretty, beautiful

EXAMPLES:
Them: "grammar" (after you asked hardest part)
You: "what do you do for a living?" ← CORRECT (step 3)
WRONG: "i'm building an app" ← SKIPPED step 3!

Them: "i am studying" (answer to "what do you do")
You: "cool. i'm building an app to help people speak korean" ← CORRECT (step 4)
WRONG: "what are you studying?" ← DON'T ask follow-up! Move on!

Them: "i don't work"
You: "i see. i'm building an app to help people speak korean" ← CORRECT

Them: "Sure!" (after you asked for feedback)
You: "thanks. it's koko ai. you can search it on app/play store!" ← CORRECT (step 6)
WRONG: "thanks!!! i will wait for you" ← WRONG! They haven't installed yet! Tell them the app name!

Them: "is it free?"
You: "yeah you can try it totally free" ← CORRECT
WRONG: "no" ← NEVER!
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

    def _detect_step_from_history(self, history):
        """
        대화 히스토리의 마지막 메시지들을 보고 현재 스텝을 추론.
        LLM에게 현재 위치를 알려주는 힌트 문자열을 반환.
        """
        if not history:
            return None

        # 마지막 봇 메시지 찾기
        last_bot = None
        last_user = None
        for msg in reversed(history):
            if msg["role"] == "assistant" and last_bot is None:
                last_bot = msg["content"].lower()
            if msg["role"] == "user" and last_user is None:
                last_user = msg["content"].lower()
            if last_bot and last_user:
                break

        if not last_bot and not last_user:
            return None

        # 봇 메시지 기준으로 완료된 스텝 판별
        bot = last_bot or ""
        user = last_user or ""

        # END 상태 감지
        end_phrases = ["no problem", "thanks!!!", "i will wait for you",
                       "app/play store", "thanks!"]
        if any(p in bot for p in end_phrases) and not user:
            return None  # 이미 종료된 대화

        # 스텝 감지
        if "how long" in bot and "korean" in bot:
            return f"(User replied: \"{user}\". Your last message was step 1. Now say step 2: ask the hardest part.)"
        if "hardest" in bot:
            return f"(User replied: \"{user}\". Your last message was step 2. Now say step 3: ask what they do for a living.)"
        if ("what do you do" in bot or "for a living" in bot):
            return f"(User replied: \"{user}\". Your last message was step 3. Now say step 4: mention you're building an app.)"
        if "building" in bot and "app" in bot:
            return f"(User replied: \"{user}\". Your last message was step 4. Now say step 5: ask for feedback.)"
        if "feedback" in bot and ("try" in bot or "give" in bot):
            return f"(User replied: \"{user}\". Your last message was step 5. If they agree, say step 6: thanks + koko ai + app/play store.)"
        if "koko" in bot and ("app" in bot or "store" in bot):
            return None  # Step 6 이미 완료

        # 봇 메시지로 판별 불가 → 유저 메시지 기반 힌트
        if last_user and not last_bot:
            return f"(This is an ongoing conversation. The user's last message was: \"{user}\". Check the conversation above and respond with the correct next step.)"

        return None

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

        # 대화 히스토리에서 현재 스텝 자동 감지
        step_hint = self._detect_step_from_history(history)
        if step_hint:
            print(f"   🎯 Step hint: {step_hint[:80]}...")

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
        elif step_hint:
            # 진행 중인 대화 → LLM에게 현재 위치 힌트
            messages.append({
                "role": "user",
                "content": step_hint
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
                            "temperature": 0.2,  # Very low - follow instructions precisely
                            "num_predict": 30,    # STRICT short - max ~15 words
                            "top_p": 0.8,         # More focused
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

                # 메타/시스템 응답 감지 → 폐기하고 재시도
                meta_phrases = ["here's the", "initial message", "you're ready",
                               "the conversation", "send your", "it seems like",
                               "i can help", "let me know"]
                if any(phrase in clean_message.lower() for phrase in meta_phrases):
                    print(f"   ⚠️  Meta response detected, retrying...")
                    continue

                # 너무 긴 응답 → 첫 문장만 사용
                if len(clean_message.split()) > 15:
                    sentences = [s.strip() for s in clean_message.replace('!', '!|').replace('?', '?|').replace('.', '.|').split('|') if s.strip()]
                    if sentences:
                        clean_message = sentences[0]
                        print(f"   ✂️  Response trimmed to: \"{clean_message}\"")

                # DON'T add to history here - send_message will add actual sent message
                # self.add_message(username, "assistant", clean_message)

                # 응답 품질 평가
                score, reasons = self.score_response(clean_message, history)
                score_emoji = "🟢" if score >= 8 else "🟡" if score >= 5 else "🔴"
                print(f"   {score_emoji} Response Score: {score}/10")
                if reasons:
                    for r in reasons:
                        print(f"      {r}")

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

    def score_response(self, response, conversation_history, user_message=None):
        """
        LLM 응답 품질을 0~10점으로 평가

        Args:
            response: LLM이 생성한 응답
            conversation_history: 대화 히스토리 [{'role': ..., 'content': ...}]
            user_message: 유저의 마지막 메시지 (없으면 히스토리에서 추출)

        Returns:
            (score, reasons) 튜플 - 점수와 감점/가점 사유 리스트
        """
        score = 10.0
        reasons = []
        resp = response.replace("[END]", "").strip()
        resp_lower = resp.lower()

        # 유저 마지막 메시지 추출
        if user_message is None:
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break
        user_lower = (user_message or "").lower().strip()

        # 봇 마지막 메시지 추출
        last_bot = None
        for msg in reversed(conversation_history):
            if msg["role"] == "assistant":
                last_bot = msg["content"].lower()
                break

        # 현재 스텝 판별
        def detect_current_step():
            if not last_bot:
                return 0  # 첫 메시지 전
            if "how long" in last_bot:
                return 1
            if "hardest" in last_bot:
                return 2
            if "what do you do" in last_bot or "for a living" in last_bot:
                return 3
            if "building" in last_bot and "app" in last_bot:
                return 4
            if "feedback" in last_bot and ("koko" in last_bot or "try" in last_bot):
                return 5
            return -1

        current_step = detect_current_step()

        # === 1. 형식 검사 (최대 -3점) ===

        # 소문자 체크
        has_upper = any(c.isupper() for c in resp if c.isalpha())
        if has_upper:
            score -= 1.0
            reasons.append("-1.0 | 대문자 사용 (소문자만 허용)")

        # 문장 수 체크 (최대 1문장)
        sentences = [s.strip() for s in re.split(r'[.!?]+', resp) if s.strip()]
        if len(sentences) > 2:
            score -= 2.0
            reasons.append(f"-2.0 | 문장 {len(sentences)}개 (최대 2개)")
        elif len(sentences) > 1:
            # 2문장은 경미한 감점
            score -= 0.5
            reasons.append(f"-0.5 | 문장 2개 (1개가 이상적)")

        # 단어 수 체크 (최대 10단어)
        word_count = len(resp.split())
        if word_count > 15:
            score -= 3.0
            reasons.append(f"-3.0 | 단어 {word_count}개 (너무 김!)")
        elif word_count > 12:
            score -= 2.0
            reasons.append(f"-2.0 | 단어 {word_count}개 (12단어 초과)")
        elif word_count > 10:
            score -= 1.0
            reasons.append(f"-1.0 | 단어 {word_count}개 (10단어 초과)")

        # === 2. 특수 케이스 처리 검사 (최대 -5점) ===

        # "talked before" / "asked before" 감지
        talked_before = any(kw in user_lower for kw in [
            "asked me before", "you asked", "we talked", "you've asked",
            "asked before", "asked the first time"
        ])
        if talked_before:
            if "couldn't see" not in resp_lower and "history" not in resp_lower:
                score -= 5.0
                reasons.append("-5.0 | '이전에 물어봤다'에 대한 올바른 응답 아님")
            else:
                reasons.append("+0 | '이전 대화' 특수 케이스 올바르게 처리")

        # "is it free?" 감지
        asking_free = any(kw in user_lower for kw in [
            "is it free", "it's free right", "free right", "is it free?"
        ])
        if asking_free:
            if "no" in resp_lower.split() or "not free" in resp_lower or "trial" in resp_lower:
                score -= 5.0
                reasons.append("-5.0 | 무료 질문에 'no' 응답 (반드시 free라고 해야 함)")
            elif "free" in resp_lower:
                reasons.append("+0 | 무료 질문에 올바르게 응답")
            else:
                score -= 2.0
                reasons.append("-2.0 | 무료 질문에 명확한 답변 없음")

        # 동의/수락 감지 → koko 이름 + 스토어 알려줘야 함
        agreement_words = ["sure", "of course", "ok i'll try", "i'll try it",
                          "i'll check it out", "okay sure", "ok sure", "absolutely"]
        user_agrees = any(kw in user_lower for kw in agreement_words)
        # "install" 키워드가 없으면 아직 앱 이름을 모르는 상태
        user_installing = any(kw in user_lower for kw in ["install", "installing", "download"])
        if user_agrees and current_step >= 4 and not user_installing:
            if "koko" in resp_lower and ("app" in resp_lower or "store" in resp_lower):
                reasons.append("+0 | 동의 시 koko 이름 + 스토어 안내 올바름")
            elif "wait for you" in resp_lower:
                score -= 4.0
                reasons.append("-4.0 | 동의했는데 앱 이름 안 알려주고 'wait' 응답")
            elif "thanks" in resp_lower and "koko" not in resp_lower:
                score -= 3.0
                reasons.append("-3.0 | 동의했는데 koko 앱 이름 미포함")

        # 질문에 대한 응답 검사
        user_asking = "?" in user_lower
        if user_asking:
            # "how's your app" 질문
            if any(kw in user_lower for kw in ["how's your app", "how is your app", "app going"]):
                if "going well" in resp_lower or "update" in resp_lower:
                    reasons.append("+0 | 앱 근황 질문에 올바르게 응답")
                else:
                    score -= 3.0
                    reasons.append("-3.0 | 앱 근황 질문 무시")

            # "what kind" / "learning app?" 질문
            if any(kw in user_lower for kw in ["learning app", "what kind", "translation"]):
                if "koko" in resp_lower or "learning" in resp_lower:
                    reasons.append("+0 | 앱 종류 질문에 올바르게 응답")
                else:
                    score -= 2.0
                    reasons.append("-2.0 | 앱 종류 질문에 불명확한 응답")

            # "entrepreneur" 질문
            if "entrepreneur" in user_lower:
                if "feedback" in resp_lower or "yea" in resp_lower:
                    reasons.append("+0 | 기업가 질문에 올바르게 응답")
                else:
                    score -= 2.0
                    reasons.append("-2.0 | 기업가 질문 무시")

        # === 3. 대화 흐름 검사 (최대 -5점) ===

        # Step 스킵 체크
        if current_step == 2:
            # hardest part 물어본 직후 → 다음은 "what do you do"
            if "building" in resp_lower and "app" in resp_lower:
                score -= 5.0
                reasons.append("-5.0 | Step 3 스킵 (hardest part → 바로 앱 언급)")
            elif "what do you do" in resp_lower or "for a living" in resp_lower:
                reasons.append("+0 | Step 3 올바르게 진행")

        if current_step == 1:
            # how long 물어본 직후 → 다음은 "hardest part"
            if "hardest" in resp_lower or "challenging" in resp_lower:
                reasons.append("+0 | Step 2 올바르게 진행")
            elif "what do you do" in resp_lower:
                score -= 3.0
                reasons.append("-3.0 | Step 2 스킵 (how long → 바로 what do you do)")
            elif "building" in resp_lower and "app" in resp_lower:
                score -= 5.0
                reasons.append("-5.0 | Step 2,3 모두 스킵")

        # "I don't work" 답변 후 재질문 체크
        if current_step == 3:
            no_work = any(kw in user_lower for kw in [
                "don't work", "unemployed", "no job", "nothing",
                "i don't work"
            ])
            if no_work and ("what do you do" in resp_lower or "for a living" in resp_lower):
                score -= 4.0
                reasons.append("-4.0 | 이미 '안 일한다'고 답했는데 재질문")

        # 긍정 반응 후 처음부터 재시작 체크
        positive_reaction = any(kw in user_lower for kw in [
            "that's cool", "that's awesome", "super cool", "wow",
            "that's great", "amazing", "nice"
        ])
        if positive_reaction and current_step >= 3:
            if "how long" in resp_lower:
                score -= 5.0
                reasons.append("-5.0 | 긍정 반응 후 처음부터 재시작")

        # === 4. 거절 시 수용 검사 ===
        decline_keywords = ["hesitant", "don't want to", "i wish you the best",
                           "sorry i can't", "not interested", "no thanks",
                           "can't download", "can't right now", "in debt"]
        user_declines = any(kw in user_lower for kw in decline_keywords)
        if user_declines:
            if "no problem" in resp_lower or resp_lower in ["no problem :)", "no worries"]:
                reasons.append("+0 | 거절에 올바르게 수용")
            else:
                score -= 4.0
                reasons.append("-4.0 | 유저가 거절했는데 설득 시도")

        # === 5. 앱 이름 질문 검사 ===
        forgot_name = any(kw in user_lower for kw in [
            "don't remember the name", "what's it called", "what's the app",
            "name of the app"
        ])
        if forgot_name:
            if "kokoai" in resp_lower or "koko ai" in resp_lower:
                reasons.append("+0 | 앱 이름 질문에 올바르게 응답")
            elif "building" in resp_lower:
                score -= 3.0
                reasons.append("-3.0 | 앱 이름 물어봤는데 처음부터 다시 소개")

        # === 6. "10번째 사람" 류 응답 과잉 검사 ===
        many_people = any(kw in user_lower for kw in [
            "10th person", "everyone tells me", "heard that before"
        ])
        if many_people:
            if len(resp.split()) > 5:
                score -= 1.5
                reasons.append("-1.5 | '여러 번 들었다'에 너무 긴 응답")

        # === 7. 이미 앱 사용 중인 유저에게 스토어 안내 검사 ===
        already_tried = any(kw in user_lower for kw in [
            "the app is so cool", "i really like it", "gonna use it",
            "i tried it", "i downloaded it", "i love the app"
        ])
        if already_tried:
            if "app/play store" in resp_lower or "search it" in resp_lower:
                score -= 4.0
                reasons.append("-4.0 | 이미 앱 사용 중인데 스토어 안내")

        # === 7-1. 실제 피드백 줬을 때 감사로 마무리 검사 ===
        gave_feedback = any(kw in user_lower for kw in [
            "it's smooth", "it's good", "i like it", "really good",
            "smooth and good", "it's great", "love it"
        ])
        if gave_feedback:
            if "thanks" in resp_lower or "appreciate" in resp_lower:
                reasons.append("+0 | 피드백에 감사 응답 올바름")
            elif "koko" in resp_lower or "learning app" in resp_lower:
                score -= 4.0
                reasons.append("-4.0 | 피드백 줬는데 앱 소개 반복")

        # === 7-2. 다운로드하겠다 → wait 응답 검사 ===
        will_download = any(kw in user_lower for kw in [
            "ill download", "i'll download", "ill look it up",
            "i'll look it up", "download it"
        ])
        if will_download and "no problem" in resp_lower:
            score -= 3.0
            reasons.append("-3.0 | 다운로드하겠다는데 'no problem' 응답")

        # === 8. 반복 언급 검사 ===
        already_mentioned_koko = False
        for msg in conversation_history:
            if msg["role"] == "assistant" and "koko" in msg["content"].lower():
                already_mentioned_koko = True
                break
        if already_mentioned_koko and "it's called koko" in resp_lower:
            score -= 2.0
            reasons.append("-2.0 | 이미 언급한 'koko ai' 이름 반복")

        # === 9. "is this it?" 확인 질문 검사 ===
        confirming_app = any(kw in user_lower for kw in [
            "is this it", "this one?", "is this the app"
        ])
        if confirming_app:
            if "yeah it is" in resp_lower or "yes" in resp_lower:
                reasons.append("+0 | 앱 확인 질문에 올바르게 응답")
            elif "no problem" in resp_lower or "app/play store" in resp_lower:
                score -= 4.0
                reasons.append("-4.0 | 앱 확인 질문에 엉뚱한 응답")

        # === 10. 캐릭터 이탈 검사 ===
        meta_phrases = ["here's the", "initial message", "you're ready",
                       "the conversation", "send your"]
        if any(phrase in resp_lower for phrase in meta_phrases):
            score -= 5.0
            reasons.append("-5.0 | 캐릭터 이탈 (시스템/메타 응답)")

        # === 11. "ooo okay" 오인식 검사 ===
        soft_ack = any(kw in user_lower for kw in [
            "ooo okay", "ooh okay", "ah okay", "oh okay"
        ])
        if soft_ack and not any(kw in user_lower for kw in ["sure", "i'll try"]):
            if "app/play store" in resp_lower:
                score -= 3.0
                reasons.append("-3.0 | 단순 인정을 동의로 오인 (END 처리)")

        # === 12. "i answered that" 처리 검사 ===
        already_answered = any(kw in user_lower for kw in [
            "i answered that", "i already told you", "already asked"
        ])
        if already_answered:
            if "web version" in resp_lower or "couldn't see" in resp_lower:
                reasons.append("+0 | 재질문 사과 올바르게 처리")
            elif "how long" in resp_lower or meta_phrases:
                score -= 4.0
                reasons.append("-4.0 | '이미 답했다'는데 무시하고 재시작")

        # === 13. 금지어 검사 (-1점) ===
        banned_words = ["sorry", "apologies", "cute", "pretty",
                       "beautiful", "gorgeous", "hot", "sexy"]
        for word in banned_words:
            if word in resp_lower:
                score -= 1.0
                reasons.append(f"-1.0 | 금지어 사용: '{word}'")

        # 최종 점수 범위 제한
        score = max(0.0, min(10.0, score))

        return round(score, 1), reasons

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
