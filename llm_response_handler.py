#!/usr/bin/env python3
"""
LLM 기반 응답 분석 및 처리 모듈
로컬 Ollama를 사용하여 자연스러운 대화를 생성합니다.
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LLMResponseHandler:
    """LLM 기반 사용자 응답 분석 및 처리 클래스"""
    
    def __init__(self, 
                 model: str = "llama3.1:8b",
                 ollama_url: str = "http://localhost:11434"):
        """
        초기화
        
        Args:
            model: 사용할 Ollama 모델 이름
            ollama_url: Ollama 서버 URL
        """
        self.model = model
        self.ollama_url = ollama_url
        self.feedback_file = Path("user_feedback.json")
        self.feedbacks = []
        self.conversation_history = {}  # {username: [...messages]}
        
        self.load_feedback_log()
        self._verify_ollama_connection()
        
        # 대화 목표 및 가이드라인
        self.system_prompt = """You are Jake, a friendly Korean language app developer having casual conversations on HelloTalk.

CONVERSATION GOALS (in order):
1. Build rapport - ask about their Korean learning journey
2. Identify pain points - what's difficult for them
3. Understand context - their background/profession
4. Introduce your app naturally - "I'm building an app to help with Korean pronunciation"
5. Request feedback - "Would you mind trying it and giving feedback?"
6. Share app link - "Search 'kokoai' on app store"
7. Follow up - "Did you get a chance to try it?"
8. Collect feedback - "What did you think?"

CONVERSATION STYLE:
- Be casual and friendly (use "u" instead of "you", casual grammar)
- Keep messages short (1-2 sentences max)
- Show genuine interest in their responses
- Don't be pushy about the app
- Match their energy level
- Use emojis sparingly

CURRENT STAGE TRACKING:
You'll be given the current stage number (0-7) and conversation history.
Based on the user's response, decide:
- What to say next
- Whether to move to the next stage or stay at current stage
- Whether to end the conversation (if user is not interested)

IMPORTANT:
- If user says they're not interested or busy → politely end conversation
- If user can't find the app → offer to help or end gracefully
- If user gives negative feedback → thank them and ask for details
- Always be respectful and authentic"""

    def _verify_ollama_connection(self):
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if self.model in model_names:
                    print(f"✓ Ollama 연결 성공: {self.model} 사용 가능")
                else:
                    print(f"⚠️  모델 '{self.model}' 없음. 사용 가능: {', '.join(model_names)}")
                    print(f"   다운로드: ollama pull {self.model}")
            else:
                print(f"⚠️  Ollama 서버 응답 오류: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Ollama 서버에 연결할 수 없습니다: {self.ollama_url}")
            print(f"   실행: brew services start ollama")
        except Exception as e:
            print(f"❌ Ollama 연결 확인 실패: {e}")

    def load_feedback_log(self):
        """피드백 로그 파일 로드"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedbacks = json.load(f)
                print(f"✓ 피드백 로그 로드: {len(self.feedbacks)}개")
        except Exception as e:
            print(f"⚠️  피드백 로그 로드 실패: {e}")
            self.feedbacks = []

    def save_feedback(self, username: str, feedback: str, stage: int):
        """사용자 피드백 저장"""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "stage": stage,
            "feedback": feedback,
            "analyzed": False
        }
        self.feedbacks.append(feedback_entry)
        
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedbacks, f, indent=2, ensure_ascii=False)
        
        print(f"💾 피드백 저장: {username} - {feedback[:50]}...")

    def call_llm(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Ollama LLM 호출
        
        Args:
            messages: 대화 히스토리 [{"role": "system/user/assistant", "content": "..."}]
            
        Returns:
            LLM 응답 텍스트 또는 None (에러 시)
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # 적절한 창의성
                        "top_p": 0.9,
                        "max_tokens": 150    # 짧은 응답 유도
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"].strip()
            else:
                print(f"❌ LLM API 오류: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ LLM 응답 시간 초과 (30초)")
            return None
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            return None

    def analyze_response(self, 
                        username: str,
                        user_message: str, 
                        current_stage: int,
                        my_last_message: str) -> Tuple[Optional[str], int, bool]:
        """
        사용자 응답 분석 및 다음 메시지 생성
        
        Args:
            username: 사용자 이름
            user_message: 사용자의 메시지
            current_stage: 현재 대화 단계 (0-7)
            my_last_message: 내가 보낸 마지막 메시지
            
        Returns:
            (다음 메시지, 다음 단계, 대화 종료 여부)
        """
        # 대화 히스토리 가져오기
        if username not in self.conversation_history:
            self.conversation_history[username] = []
        
        history = self.conversation_history[username]
        
        # 현재 메시지를 히스토리에 추가
        if my_last_message:
            history.append({"role": "assistant", "content": my_last_message})
        history.append({"role": "user", "content": user_message})
        
        # LLM에게 전달할 메시지 구성
        llm_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"CURRENT STAGE: {current_stage}/7"},
            {"role": "system", "content": "CONVERSATION HISTORY:"}
        ]
        
        # 대화 히스토리 추가 (최근 10개만)
        llm_messages.extend(history[-10:])
        
        # LLM에게 지시
        llm_messages.append({
            "role": "system", 
            "content": """Based on the conversation, respond with a JSON object:
{
  "next_message": "your response here",
  "next_stage": 0-7 (or -1 to end conversation),
  "save_feedback": true/false (true if stage >= 6 and user gave feedback),
  "reasoning": "brief explanation of your decision"
}

Remember:
- Keep responses SHORT (1-2 sentences)
- Be casual and friendly
- Move to next stage naturally when appropriate
- End conversation (-1) if user is clearly not interested"""
        })
        
        # LLM 호출
        llm_response = self.call_llm(llm_messages)
        
        if not llm_response:
            # LLM 실패 시 폴백
            return self._fallback_response(current_stage), current_stage + 1, False
        
        # LLM 응답 파싱
        try:
            # JSON 추출 (LLM이 추가 텍스트를 붙일 수 있음)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(llm_response)
            
            next_message = result.get("next_message", "")
            next_stage = result.get("next_stage", current_stage + 1)
            save_feedback = result.get("save_feedback", False)
            reasoning = result.get("reasoning", "")
            
            print(f"🤖 LLM 결정: stage {current_stage} → {next_stage}")
            print(f"   이유: {reasoning}")
            
            # 피드백 저장
            if save_feedback and current_stage >= 6:
                self.save_feedback(username, user_message, current_stage)
            
            # 대화 종료 체크
            end_conversation = (next_stage == -1)
            if end_conversation:
                next_stage = current_stage  # 단계 유지
            
            # 히스토리에 응답 추가
            history.append({"role": "assistant", "content": next_message})
            
            return next_message, next_stage, end_conversation
            
        except json.JSONDecodeError as e:
            print(f"❌ LLM 응답 파싱 실패: {e}")
            print(f"   응답: {llm_response[:200]}")
            return self._fallback_response(current_stage), current_stage + 1, False

    def _fallback_response(self, stage: int) -> str:
        """LLM 실패 시 폴백 응답"""
        fallbacks = {
            0: "That's cool! What's been the hardest part for you?",
            1: "I see! What do you do for a living?",
            2: "Nice! I'm actually building an app to help with Korean pronunciation.",
            3: "Would you mind trying it and giving me some feedback?",
            4: "You can search 'kokoai' on the app store!",
            5: "Did you get a chance to try it?",
            6: "What did you think of it?",
            7: "Thanks so much for the feedback! Really appreciate it!"
        }
        return fallbacks.get(stage, "Thanks for chatting!")

    def handle_user_initiated(self, username: str, user_message: str) -> Tuple[str, int]:
        """
        유저가 먼저 대화를 시작한 경우 처리
        
        Returns:
            (응답 메시지, 시작 단계)
        """
        llm_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": "The user initiated this conversation. Respond friendly and naturally, then guide towards stage 0 (asking about Korean learning)."},
            {"role": "user", "content": user_message}
        ]
        
        llm_response = self.call_llm(llm_messages)
        
        if llm_response:
            # 히스토리 초기화
            self.conversation_history[username] = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": llm_response}
            ]
            return llm_response, 0
        else:
            return "Hi! Nice to meet you! I'm Jake.", 0

    def clear_history(self, username: str):
        """특정 유저의 대화 히스토리 삭제"""
        if username in self.conversation_history:
            del self.conversation_history[username]


# 테스트 코드
if __name__ == "__main__":
    print("=== LLM Response Handler 테스트 ===\n")
    
    handler = LLMResponseHandler()
    
    # 시나리오 1: 정상적인 대화 플로우
    print("\n[시나리오 1] 정상 대화 플로우")
    username = "TestUser"
    
    stage = 0
    my_msg = "Hi, I'm jake, how long have you been learning Korean?"
    user_msg = "I've been learning for about 3 months!"
    
    next_msg, next_stage, end = handler.analyze_response(
        username, user_msg, stage, my_msg
    )
    
    print(f"\n유저: {user_msg}")
    print(f"봇: {next_msg}")
    print(f"단계: {stage} → {next_stage}, 종료: {end}")
    
    # 시나리오 2: 관심 없음
    print("\n\n[시나리오 2] 관심 없는 유저")
    username2 = "NotInterested"
    stage = 4
    my_msg = "Do u mind giving me some feedback as learner?"
    user_msg = "Sorry, I'm not interested"
    
    next_msg, next_stage, end = handler.analyze_response(
        username2, user_msg, stage, my_msg
    )
    
    print(f"\n유저: {user_msg}")
    print(f"봇: {next_msg}")
    print(f"단계: {stage} → {next_stage}, 종료: {end}")
