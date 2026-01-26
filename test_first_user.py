#!/usr/bin/env python3

import time
from playwright.sync_api import sync_playwright

def test_first_user():
    print("=" * 60)
    print("HelloTalk 테스트 - 첫 번째 유저에게만 메시지 전송")
    print("=" * 60)
    
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
            '.chat-list-item',
            '.conversation-item', 
            '[data-testid*="chat"]',
            '.message-list-item',
            'div[role="listitem"]',
            'li[class*="chat"]',
            'div[class*="conversation"]',
        ]
        
        first_user = None
        used_selector = None
        
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    first_user = elements[0]
                    used_selector = selector
                    print(f"✓ '{selector}' 선택자로 {len(elements)}개 대화 발견")
                    print(f"✓ 첫 번째 유저 선택됨\n")
                    break
            except:
                continue
        
        if not first_user:
            print("❌ 자동으로 대화 목록을 찾지 못했습니다.")
            print("\n🔍 수동 디버깅 필요:")
            print("1. 브라우저에서 F12 (개발자 도구)")
            print("2. 대화 목록의 한 항목을 우클릭 → 검사")
            print("3. 해당 요소의 클래스나 선택자를 확인")
            print("4. test_first_user.py의 selectors 리스트에 추가")
            return
        
        try:
            username = first_user.inner_text()[:30]
            print(f"📤 [{username}]에게 메시지 전송 시도...\n")
        except:
            username = "Unknown User"
            print(f"📤 첫 번째 유저에게 메시지 전송 시도...\n")
        
        first_user.click()
        print("   ✓ 대화 클릭")
        time.sleep(3)
        
        print("   🔍 메시지 입력창 찾는 중...")
        
        input_selectors = [
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="메시지"]',
            'textarea[placeholder*="Message"]',
            '.message-input textarea',
            '[contenteditable="true"]',
            'input[type="text"]',
            'textarea',
            'div[contenteditable="true"]',
        ]
        
        input_box = None
        for selector in input_selectors:
            try:
                input_box = page.wait_for_selector(selector, timeout=2000)
                if input_box:
                    print(f"   ✓ 입력창 발견: {selector}")
                    break
            except:
                continue
        
        if not input_box:
            print("   ❌ 입력창을 찾을 수 없습니다.")
            print("\n🔍 수동 확인 필요:")
            print("1. 대화창이 열렸나요?")
            print("2. 메시지 입력창이 보이나요?")
            print("3. F12 → 입력창 요소 검사 → 선택자 확인")
            return
        
        test_message = "테스트 메시지입니다 (자동 전송 테스트)"
        input_box.fill(test_message)
        print(f"   ✓ 메시지 입력: \"{test_message}\"")
        time.sleep(1)
        
        print("   🔍 전송 버튼 찾는 중...")
        
        send_selectors = [
            'button[type="submit"]',
            'button:has-text("Send")',
            'button:has-text("전송")',
            '.send-button',
            'button[aria-label*="send"]',
            'button[aria-label*="Send"]',
            'svg[class*="send"]',
        ]
        
        sent = False
        for selector in send_selectors:
            try:
                send_btn = page.query_selector(selector)
                if send_btn and send_btn.is_visible():
                    send_btn.click()
                    print(f"   ✓ 전송 버튼 클릭: {selector}")
                    sent = True
                    break
            except:
                continue
        
        if not sent:
            print("   ⚠️  전송 버튼을 찾지 못했습니다. Enter 키 시도...")
            input_box.press('Enter')
            print("   ✓ Enter 키 전송 시도")
        
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
        print("\n확인사항:")
        print("1. 메시지가 전송되었나요?")
        print("2. 전송이 성공했다면 hellotalk_bot.py를 실행하세요")
        print("3. 전송이 실패했다면 위의 오류 메시지를 확인하세요")
        
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
    test_first_user()
