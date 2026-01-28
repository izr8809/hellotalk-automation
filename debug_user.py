#!/usr/bin/env python3
"""
특정 유저의 메시지 히스토리와 봇 상태를 디버그하는 스크립트
"""

import sys
import time
from playwright.sync_api import sync_playwright

def debug_user_conversation(username):
    print(f"{'='*70}")
    print(f"디버그: {username}")
    print(f"{'='*70}\n")
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    
    if not browser.contexts:
        print("❌ 열린 브라우저가 없습니다.")
        return
    
    context = browser.contexts[0]
    page = None
    
    for p in context.pages:
        if 'hellotalk.com' in p.url:
            page = p
            break
    
    if not page:
        print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
        return
    
    # Find and click the user
    try:
        users = page.query_selector_all('.memberItem')
        target_user = None
        
        for user in users:
            name_elem = user.query_selector('.name')
            if name_elem and name_elem.inner_text().strip() == username:
                target_user = user
                break
        
        if not target_user:
            print(f"❌ 유저 '{username}'을 찾을 수 없습니다.")
            return
        
        print(f"✓ 유저 '{username}' 찾음. 클릭 중...")
        target_user.click()
        time.sleep(2)
        
        # Get all messages
        all_messages = page.query_selector_all('.msgItemBigWrapper')
        print(f"\n총 메시지 수: {len(all_messages)}\n")
        print(f"{'='*70}")
        print("메시지 히스토리")
        print(f"{'='*70}\n")
        
        for idx, msg in enumerate(all_messages):
            is_sent = 'sendBox' in msg.get_attribute('class')
            is_received = 'receiveBox' in msg.get_attribute('class')
            
            text_wrapper = msg.query_selector('.textWrapper pre')
            if text_wrapper:
                text = text_wrapper.inner_text().strip()
                
                if is_sent:
                    print(f"[{idx}] 🤖 BOT: {text}")
                elif is_received:
                    print(f"[{idx}] 👤 USER: {text}")
        
        # Check bot state
        print(f"\n{'='*70}")
        print("봇 상태 파일 (bot_state.json)")
        print(f"{'='*70}\n")
        
        import json
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
        
        user_state = state['user_states'].get(username, {})
        print(f"current_step: {user_state.get('current_step')}")
        print(f"completed: {user_state.get('completed')}")
        print(f"last_check_time: {user_state.get('last_check_time', 'N/A')}")
        print(f"messages_processed: {user_state.get('messages_processed', [])}")
        
        # Check expected messages
        print(f"\n{'='*70}")
        print("기대되는 메시지 플로우")
        print(f"{'='*70}\n")
        
        with open('messages.txt', 'r') as f:
            messages = f.read().strip().split('\n')
        
        for i, msg in enumerate(messages):
            print(f"Step {i}: {msg}")
        
        current = user_state.get('current_step', 0)
        print(f"\n현재 step {current}:")
        print(f"  - 이미 보낸 메시지: Step {current - 1} (if > 0)")
        print(f"  - 다음에 보낼 메시지: Step {current}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 debug_user.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    debug_user_conversation(username)
