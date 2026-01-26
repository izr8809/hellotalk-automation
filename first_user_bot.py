#!/usr/bin/env python3

import time
from playwright.sync_api import sync_playwright

def load_messages(file_path="messages.txt"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            messages = [line.strip() for line in f if line.strip()]
        print(f"✓ {len(messages)}개 메시지 로드 완료")
        return messages
    except FileNotFoundError:
        print(f"❌ {file_path} 파일을 찾을 수 없습니다.")
        return []

def wait_for_user_reply(page):
    print(f"   ⏳ 유저 답변 대기 중... (답변이 올 때까지 대기)")
    
    message_selectors = [
        '.message-item',
        '.chat-message',
        '[class*="message"]',
        '[data-testid*="message"]',
        'div[class*="Message"]',
        '[role="article"]',
    ]
    
    start_time = time.time()
    initial_count = 0
    
    for selector in message_selectors:
        try:
            messages = page.query_selector_all(selector)
            if messages:
                initial_count = len(messages)
                print(f"   📊 현재 메시지 개수: {initial_count} (선택자: {selector})")
                break
        except:
            continue
    
    if initial_count == 0:
        print(f"   ⚠️  메시지 개수를 확인할 수 없습니다. 10초마다 체크합니다.")
    
    check_count = 0
    while True:
        time.sleep(2)
        check_count += 1
        
        if check_count % 30 == 0:
            elapsed_min = int((time.time() - start_time) / 60)
            print(f"   ⏳ 계속 대기 중... ({elapsed_min}분 경과)")
        
        for selector in message_selectors:
            try:
                messages = page.query_selector_all(selector)
                if messages and len(messages) > initial_count:
                    elapsed = int(time.time() - start_time)
                    elapsed_min = elapsed // 60
                    elapsed_sec = elapsed % 60
                    print(f"   ✓ 답변 도착! ({elapsed_min}분 {elapsed_sec}초 경과)")
                    print(f"   📊 메시지 개수: {initial_count} → {len(messages)}")
                    return True
            except:
                continue

def send_message(page, message):
    input_selectors = [
        'pre.msgInputWrapper[contenteditable="true"]',
        '.msgInputWrapper[contenteditable="true"]',
        '[contenteditable="true"]',
        'textarea[placeholder*="message"]',
        'textarea[placeholder*="Message"]',
    ]
    
    input_box = None
    for selector in input_selectors:
        try:
            input_box = page.wait_for_selector(selector, timeout=3000)
            if input_box:
                break
        except:
            continue
    
    if not input_box:
        print(f"   ❌ 입력창을 찾을 수 없습니다.")
        return False
    
    input_box.fill(message)
    time.sleep(0.5)
    
    send_selectors = [
        'button[type="submit"]',
        'button:has-text("Send")',
        'button:has-text("전송")',
        '.send-button',
        'button[aria-label*="send"]',
        'button[aria-label*="Send"]',
    ]
    
    sent = False
    for selector in send_selectors:
        try:
            send_btn = page.query_selector(selector)
            if send_btn and send_btn.is_visible():
                send_btn.click()
                sent = True
                break
        except:
            continue
    
    if not sent:
        input_box.press('Enter')
    
    return True

def main():
    print("=" * 60)
    print("HelloTalk 첫 번째 유저 테스트 봇")
    print("=" * 60)
    
    messages = load_messages()
    if not messages:
        return
    
    print(f"\n📋 전송할 메시지:")
    for idx, msg in enumerate(messages, 1):
        print(f"  {idx}. {msg[:50]}{'...' if len(msg) > 50 else ''}")
    
    print("\n🔗 Chrome 브라우저에 연결 중...")
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
        
        if not browser.contexts:
            print("❌ 열린 브라우저가 없습니다.")
            print("\n다음 명령으로 Chrome을 실행하세요:")
            print('/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\')
            print('  --remote-debugging-port=9222 \\')
            print('  --user-data-dir="/tmp/chrome-debug"')
            return
        
        context = browser.contexts[0]
        
        page = None
        for p in context.pages:
            if 'hellotalk.com' in p.url:
                page = p
                break
        
        if not page:
            print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
            print("브라우저에서 https://web.hellotalk.com/ 을 열어주세요.")
            return
        
        print(f"✓ 연결 완료: {page.url}\n")
        
        print("📋 대화 목록에서 첫 번째 유저 찾는 중...")
        
        selectors = [
            '.userItem',
            'div.userItem',
            '[class*="userItem"]',
        ]
        
        first_user = None
        all_users = []
        
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    all_users = elements
                    print(f"✓ '{selector}' 선택자로 {len(elements)}개 대화 발견")
                    
                    for elem in elements:
                        try:
                            classes = elem.get_attribute('class')
                            if 'userItem' in classes and 'select' not in classes:
                                first_user = elem
                                break
                        except:
                            continue
                    
                    if not first_user and elements:
                        first_user = elements[0]
                    
                    if first_user:
                        print(f"✓ 첫 번째 유저 선택됨\n")
                        break
            except:
                continue
        
        if not first_user:
            print("❌ 자동으로 대화 목록을 찾지 못했습니다.")
            print("\n💡 HelloTalk 대화 목록 페이지에 있는지 확인하세요.")
            print("   또는 debug_page.py를 실행해서 페이지 구조를 확인하세요.")
            return
        
        try:
            username = first_user.inner_text()[:30]
        except:
            username = "Unknown User"
        
        print(f"{'='*60}")
        print(f"📤 [{username}]에게 대화 시작...")
        print(f"{'='*60}\n")
        
        first_user.click()
        time.sleep(3)
        
        for msg_idx, message in enumerate(messages, 1):
            try:
                print(f"\n--- 메시지 {msg_idx}/{len(messages)} ---")
                print(f"📤 전송: \"{message}\"")
                
                success = send_message(page, message)
                
                if not success:
                    print(f"❌ 메시지 {msg_idx} 전송 실패")
                    break
                
                print(f"✓ 전송 완료!")
                
                if msg_idx < len(messages):
                    wait_for_user_reply(page)
                    time.sleep(2)
            
            except KeyboardInterrupt:
                print("\n\n⚠️  사용자가 중단했습니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                break
        
        print(f"\n{'='*60}")
        print(f"✅ [{username}]와의 대화 완료!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n문제 해결:")
        print("1. Chrome이 디버그 모드로 실행되었나요?")
        print("2. HelloTalk에 로그인되어 있나요?")
        print("3. 대화 목록 페이지에 있나요?")
    
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    main()
