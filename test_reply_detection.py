#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

def test_reply_detection():
    print("=" * 60)
    print("답장 감지 테스트")
    print("=" * 60)
    
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
        
        print(f"\n✓ 연결 완료: {page.url}\n")
        
        print("현재 대화창 분석 중...\n")
        
        my_messages = page.query_selector_all('.msgItemBigWrapper.sendBox')
        received_messages = page.query_selector_all('.msgItemBigWrapper.receiveBox')
        
        print(f"내가 보낸 메시지: {len(my_messages)}개")
        print(f"받은 메시지: {len(received_messages)}개")
        print(f"전체 메시지: {len(my_messages) + len(received_messages)}개\n")
        
        if my_messages:
            print("내가 보낸 메시지 (최근 3개):")
            for msg in my_messages[-3:]:
                try:
                    text = msg.query_selector('.textWrapper pre').inner_text().strip()
                    print(f"  📤 {text[:50]}...")
                except:
                    pass
        
        if received_messages:
            print("\n받은 메시지 (최근 3개):")
            for msg in received_messages[-3:]:
                try:
                    text = msg.query_selector('.textWrapper pre').inner_text().strip()
                    print(f"  📥 {text[:50]}...")
                except:
                    pass
        
        print(f"\n{'='*60}")
        print("답장 확인 로직:")
        print(f"{'='*60}")
        
        if my_messages and received_messages:
            last_my_msg_count = len(my_messages)
            last_received_count = len(received_messages)
            total_before = len(my_messages) + len(received_messages)
            
            print(f"\n현재 상태:")
            print(f"  내 메시지: {last_my_msg_count}")
            print(f"  받은 메시지: {last_received_count}")
            print(f"  전체 메시지: {total_before}")
            
            print(f"\n✓ 다음번 체크 시:")
            print(f"  받은 메시지가 {last_received_count}보다 많으면 → 답장 왔음!")
            print(f"  또는 전체 메시지가 {total_before}보다 많으면 → 답장 왔음!")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    test_reply_detection()
