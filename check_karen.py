#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

def check_karen():
    print("=" * 60)
    print("Karen 상태 체크")
    print("=" * 60)
    
    messages = []
    with open("messages.txt", 'r', encoding='utf-8') as f:
        messages = [line.strip() for line in f if line.strip()]
    
    print("\n템플릿 메시지:")
    for idx, msg in enumerate(messages, 1):
        print(f"  {idx}. {msg[:50]}...")
    
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
        
        print(f"\n✓ 연결 완료\n")
        print("=" * 60)
        print("Karen 대화창 분석")
        print("=" * 60)
        
        my_messages = page.query_selector_all('.msgItemBigWrapper.sendBox')
        received_messages = page.query_selector_all('.msgItemBigWrapper.receiveBox')
        
        print(f"\n내가 보낸 메시지: {len(my_messages)}개")
        if my_messages:
            print("\n최근 메시지:")
            for idx, msg in enumerate(my_messages[-3:], len(my_messages) - 2):
                try:
                    text = msg.query_selector('.textWrapper pre').inner_text().strip()
                    print(f"  [{idx}] 📤 {text[:60]}...")
                    
                    for t_idx, template in enumerate(messages):
                        if text == template:
                            print(f"       → 템플릿 {t_idx + 1}")
                            break
                except:
                    pass
        
        print(f"\n받은 메시지: {len(received_messages)}개")
        if received_messages:
            print("\n최근 답장:")
            for idx, msg in enumerate(received_messages[-3:], len(received_messages) - 2):
                try:
                    text = msg.query_selector('.textWrapper pre').inner_text().strip()
                    print(f"  [{idx}] 📥 {text[:60]}...")
                except:
                    pass
        
        print(f"\n{'='*60}")
        print("bot_state.json과 비교:")
        print(f"{'='*60}")
        
        print(f"\nbot_state.json:")
        print(f"  current_step: 2")
        print(f"  last_received_count: 1")
        
        print(f"\n실제 상태:")
        print(f"  내가 보낸 메시지: {len(my_messages)}개")
        print(f"  받은 메시지: {len(received_messages)}개")
        
        if my_messages:
            last_msg = my_messages[-1]
            last_text = last_msg.query_selector('.textWrapper pre').inner_text().strip()
            print(f"\n마지막 메시지: \"{last_text}\"")
            
            for idx, template in enumerate(messages):
                if last_text == template:
                    print(f"  → 이것은 템플릿 메시지 {idx + 1}/{len(messages)}")
                    print(f"  → current_step은 {idx + 1}이어야 함")
                    break
        
        print(f"\n{'='*60}")
        print("문제 진단:")
        print(f"{'='*60}")
        
        if len(received_messages) > 1:
            print(f"\n✓ 답장이 {len(received_messages)}개 있습니다.")
            print(f"  하지만 bot_state.json에는 last_received_count: 1")
            print(f"  → 봇이 답장을 감지하지 못했습니다!")
        
        if len(my_messages) >= 2:
            msg2 = my_messages[-2] if len(my_messages) >= 2 else None
            if msg2:
                text2 = msg2.query_selector('.textWrapper pre').inner_text().strip()
                if "hardest part" in text2:
                    print(f"\n✓ 'what is the hardest part?' 전송됨")
                    print(f"  현재 current_step: 2")
                    if len(received_messages) > 1:
                        print(f"  답장: {len(received_messages)}개")
                        print(f"  → 다음 메시지 (3번)를 보내야 합니다!")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    check_karen()
