#!/usr/bin/env python3
"""
특정 유저의 DOM 상태를 직접 확인하는 스크립트
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import after path is set
from playwright.sync_api import sync_playwright
import time

def check_user_dom(username):
    print(f"{'='*70}")
    print(f"DOM 체크: {username}")
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
    
    # Find user
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
    
    print(f"✓ 유저 '{username}' 찾음. 클릭 중...\n")
    target_user.click()
    time.sleep(2)
    
    # Get bot messages
    my_messages = page.query_selector_all('.msgItemBigWrapper.sendBox')
    print(f"총 bot 메시지: {len(my_messages)}개\n")
    
    if not my_messages:
        print("⚠️  Bot 메시지가 없습니다!")
        return
    
    print(f"{'='*70}")
    print("Bot 메시지들:")
    print(f"{'='*70}\n")
    
    for idx, msg in enumerate(my_messages):
        text_wrapper = msg.query_selector('.textWrapper pre')
        if text_wrapper:
            text = text_wrapper.inner_text().strip()
            print(f"[{idx}] {text}\n")
    
    print(f"{'='*70}")
    print("마지막 Bot 메시지:")
    print(f"{'='*70}\n")
    
    last_msg = my_messages[-1]
    text_wrapper = last_msg.query_selector('.textWrapper pre')
    if text_wrapper:
        text = text_wrapper.inner_text().strip()
        print(f"텍스트: \"{text}\"")
        print(f"길이: {len(text)} characters")
        print(f"소문자: \"{text.lower()}\"")
        
        # Check against templates
        print(f"\n{'='*70}")
        print("messages.txt 비교:")
        print(f"{'='*70}\n")
        
        with open('messages.txt', 'r') as f:
            messages = f.read().strip().split('\n')
        
        for i, template in enumerate(messages):
            template_lower = template.lower()
            text_lower = text.lower()
            exact_match = text_lower == template_lower
            contains = template_lower in text_lower
            
            print(f"Step {i}: {template[:60]}...")
            print(f"  Exact match: {exact_match}")
            print(f"  Contains: {contains}")
            if exact_match or contains:
                print(f"  ✓ MATCH!")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_dom.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    check_user_dom(username)
