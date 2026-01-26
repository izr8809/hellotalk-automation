#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

def find_unread_indicator():
    print("=" * 60)
    print("읽지 않은 메시지 표시 찾기")
    print("=" * 60)
    print("\n⚠️  먼저 HelloTalk 웹에서 읽지 않은 메시지가 있는 대화가 있는지 확인하세요!\n")
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
        
        context = browser.contexts[0]
        page = None
        for p in context.pages:
            if 'hellotalk.com' in p.url:
                page = p
                break
        
        if not page:
            print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
            return
        
        print(f"✓ 연결 완료: {page.url}\n")
        
        print("=" * 60)
        print("1. userItem 요소들 분석")
        print("=" * 60)
        
        user_items = page.query_selector_all('.userItem')
        
        if not user_items:
            print("❌ userItem을 찾을 수 없습니다.")
            return
        
        print(f"✓ {len(user_items)}개 대화 발견\n")
        
        for idx, item in enumerate(user_items[:10], 1):
            try:
                username_elem = item.query_selector('.userName')
                username = username_elem.inner_text().strip() if username_elem else "Unknown"
                
                html = item.inner_html()
                
                has_red_class = 'red' in html.lower() or 'unread' in html.lower() or 'badge' in html.lower()
                
                classes = item.get_attribute('class')
                
                print(f"[{idx}] {username}")
                print(f"    클래스: {classes}")
                
                if has_red_class:
                    print(f"    ⚠️  'red', 'unread', 또는 'badge' 발견!")
                
                has_dot = item.query_selector('.unreadDot, [class*="dot"], [class*="badge"], [class*="unread"]')
                if has_dot:
                    dot_classes = has_dot.get_attribute('class')
                    print(f"    🔴 읽지 않은 표시: {dot_classes}")
                
                last_msg = item.query_selector('.lastMsgContent')
                if last_msg:
                    msg_text = last_msg.inner_text().strip()[:30]
                    print(f"    마지막 메시지: {msg_text}...")
                
                print()
                
            except Exception as e:
                print(f"[{idx}] ❌ 오류: {e}\n")
        
        print("=" * 60)
        print("2. 모든 가능한 읽지 않은 표시 선택자 검색")
        print("=" * 60)
        
        possible_selectors = [
            '.unreadDot',
            '[class*="unread"]',
            '[class*="badge"]',
            '[class*="dot"]',
            '[class*="red"]',
            '.unread',
            '.badge',
            '.notification',
            '[class*="count"]',
            '[class*="number"]',
        ]
        
        for selector in possible_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"\n✓ '{selector}' → {len(elements)}개 발견")
                    
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            classes = elem.get_attribute('class')
                            text = elem.inner_text().strip() if elem.inner_text() else "(빈 요소)"
                            print(f"  [{i}] class=\"{classes}\" text=\"{text}\"")
                        except:
                            pass
            except:
                pass
        
        print("\n" + "=" * 60)
        print("3. 스크린샷 저장")
        print("=" * 60)
        
        page.screenshot(path="unread_check.png")
        print("✓ 스크린샷을 'unread_check.png'에 저장했습니다.")
        
        print("\n" + "=" * 60)
        print("완료!")
        print("=" * 60)
        print("\n💡 다음 단계:")
        print("1. unread_check.png를 열어서 빨간 표시 확인")
        print("2. 위의 출력에서 읽지 않은 메시지가 있는 대화의 특징 확인")
        print("3. 해당 선택자를 코드에 적용")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    find_unread_indicator()
