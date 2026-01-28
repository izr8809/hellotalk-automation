#!/usr/bin/env python3
"""
LLM Response Handler 테스트 스크립트
"""

import sys
from llm_response_handler import LLMResponseHandler

def test_scenarios():
    """다양한 대화 시나리오 테스트"""
    
    print("="*60)
    print("LLM Response Handler 테스트")
    print("="*60 + "\n")
    
    handler = LLMResponseHandler()
    
    scenarios = [
        {
            "name": "정상 대화 플로우",
            "username": "Sarah",
            "conversations": [
                (0, "Hi, I'm jake, how long have you been learning Korean?", 
                 "I've been learning for about 3 months!"),
                (1, None, "The pronunciation is really hard!"),
                (2, None, "I'm a software engineer"),
                (3, None, "That sounds really cool!"),
                (4, None, "Sure, I'd love to help!"),
                (5, None, "Thanks! I'll check it out"),
                (6, None, "Yes! I tried it yesterday"),
                (7, None, "I really like the pronunciation feature, it's super helpful!")
            ]
        },
        {
            "name": "관심 없는 유저",
            "username": "Mike",
            "conversations": [
                (0, "Hi, I'm jake, how long have you been learning Korean?", 
                 "About 2 months"),
                (1, None, "Grammar is tough"),
                (2, None, "I'm a teacher"),
                (3, None, "Cool"),
                (4, None, "Sorry, I'm not interested")
            ]
        },
        {
            "name": "앱을 못 찾은 유저",
            "username": "Emma",
            "conversations": [
                (0, "Hi, I'm jake, how long have you been learning Korean?",
                 "Just started last week"),
                (1, None, "Everything is hard haha"),
                (2, None, "Student"),
                (3, None, "Interesting!"),
                (4, None, "Yeah sure!"),
                (5, None, "Cool!"),
                (6, None, "I can't find it on the app store")
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"시나리오: {scenario['name']}")
        print(f"{'='*60}\n")
        
        username = scenario['username']
        handler.clear_history(username)
        
        for stage, my_message, user_message in scenario['conversations']:
            print(f"\n[단계 {stage}]")
            if my_message:
                print(f"봇: {my_message}")
            print(f"유저: {user_message}")
            
            next_msg, next_stage, end = handler.analyze_response(
                username, user_message, stage, my_message or ""
            )
            
            print(f"→ 봇 응답: {next_msg}")
            print(f"→ 다음 단계: {stage} → {next_stage}")
            print(f"→ 종료 여부: {end}")
            
            if end:
                print(f"\n✅ 대화 종료")
                break
        
        handler.clear_history(username)

def test_user_initiated():
    """유저가 먼저 대화를 시작하는 경우"""
    
    print(f"\n{'='*60}")
    print("유저 먼저 대화 시작 테스트")
    print(f"{'='*60}\n")
    
    handler = LLMResponseHandler()
    
    test_cases = [
        "Hi! How are you?",
        "Hey, what's your name?",
        "Do you speak Korean?",
        "안녕하세요!",
    ]
    
    for i, user_msg in enumerate(test_cases, 1):
        print(f"\n[케이스 {i}]")
        print(f"유저: {user_msg}")
        
        response, stage = handler.handle_user_initiated(f"User{i}", user_msg)
        
        print(f"→ 봇 응답: {response}")
        print(f"→ 시작 단계: {stage}")
        
        handler.clear_history(f"User{i}")

def test_ollama_connection():
    """Ollama 연결 테스트"""
    
    print(f"\n{'='*60}")
    print("Ollama 연결 테스트")
    print(f"{'='*60}\n")
    
    handler = LLMResponseHandler()
    
    test_messages = [
        {"role": "user", "content": "Say hi in one short sentence"}
    ]
    
    print("테스트 프롬프트: 'Say hi in one short sentence'")
    response = handler.call_llm(test_messages)
    
    if response:
        print(f"✅ 연결 성공!")
        print(f"응답: {response}")
    else:
        print(f"❌ 연결 실패")
        print(f"\n해결 방법:")
        print(f"1. ollama serve 실행")
        print(f"2. ollama pull llama3.1:8b")

def interactive_test():
    """대화형 테스트"""
    
    print(f"\n{'='*60}")
    print("대화형 테스트 모드")
    print("(종료: 'quit' 입력)")
    print(f"{'='*60}\n")
    
    handler = LLMResponseHandler()
    username = "Interactive"
    stage = 0
    my_last_message = "Hi, I'm jake, how long have you been learning Korean?"
    
    print(f"봇: {my_last_message}\n")
    
    while True:
        user_input = input("유저: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n테스트 종료")
            break
        
        if not user_input:
            continue
        
        next_msg, next_stage, end = handler.analyze_response(
            username, user_input, stage, my_last_message
        )
        
        print(f"\n봇: {next_msg}")
        print(f"[단계: {stage} → {next_stage}, 종료: {end}]\n")
        
        if end:
            print("✅ 대화 종료\n")
            break
        
        stage = next_stage
        my_last_message = next_msg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "connection":
            test_ollama_connection()
        elif mode == "interactive":
            interactive_test()
        elif mode == "user-initiated":
            test_user_initiated()
        elif mode == "scenarios":
            test_scenarios()
        else:
            print(f"사용법: python3 {sys.argv[0]} [connection|interactive|user-initiated|scenarios]")
    else:
        print("전체 테스트 실행\n")
        test_ollama_connection()
        test_user_initiated()
        test_scenarios()
        
        print(f"\n{'='*60}")
        print("대화형 테스트를 실행하려면:")
        print(f"  python3 {sys.argv[0]} interactive")
        print(f"{'='*60}")
