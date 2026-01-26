#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

def load_messages(file_path="messages.txt"):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def debug_message_matching():
    print("=" * 60)
    print("메시지 매칭 디버그")
    print("=" * 60)
    
    messages = load_messages()
    print(f"\n템플릿 메시지:")
    for idx, msg in enumerate(messages, 1):
        print(f"  {idx}. {msg}")
    
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
        print("내가 보낸 모든 메시지:")
        print("=" * 60)
        
        my_messages = page.query_selector_all('.msgItemBigWrapper.sendBox')
        
        if not my_messages:
            print("❌ 내가 보낸 메시지가 없습니다.")
            return
        
        print(f"\n✓ 총 {len(my_messages)}개 발견\n")
        
        for idx, msg_container in enumerate(my_messages, 1):
            try:
                text_wrapper = msg_container.query_selector('.textWrapper pre')
                if text_wrapper:
                    text = text_wrapper.inner_text().strip()
                    print(f"[{idx}] {text}")
                    
                    matched = False
                    for template_idx, template_msg in enumerate(messages):
                        if text == template_msg:
                            print(f"    ✓ 정확히 일치: 템플릿 {template_idx + 1}")
                            matched = True
                            break
                        elif template_msg in text:
                            print(f"    ⚠️  부분 일치 (template in text): 템플릿 {template_idx + 1}")
                            matched = True
                        elif text in template_msg:
                            print(f"    ⚠️  부분 일치 (text in template): 템플릿 {template_idx + 1}")
                            matched = True
                    
                    if not matched:
                        print(f"    ❌ 템플릿에서 찾을 수 없음")
                    
                    print()
            except Exception as e:
                print(f"[{idx}] ❌ 오류: {e}\n")
        
        print("=" * 60)
        print("마지막 메시지 매칭 테스트:")
        print("=" * 60)
        
        last_msg_container = my_messages[-1]
        text_wrapper = last_msg_container.query_selector('.textWrapper pre')
        
        if text_wrapper:
            last_text = text_wrapper.inner_text().strip()
            print(f"\n마지막 메시지: \"{last_text}\"\n")
            
            print("현재 로직 (첫 매칭):")
            for idx, template_msg in enumerate(messages):
                if last_text == template_msg or template_msg in last_text:
                    print(f"  → 템플릿 {idx + 1}: \"{template_msg}\"")
                    print(f"  ✓ 다음 메시지는: {idx + 2}/{len(messages)}")
                    if idx + 1 < len(messages):
                        print(f"     \"{messages[idx + 1]}\"")
                    break
            
            print("\n개선된 로직 (정확한 매칭):")
            for idx, template_msg in enumerate(messages):
                if last_text == template_msg:
                    print(f"  → 템플릿 {idx + 1}: \"{template_msg}\"")
                    print(f"  ✓ 다음 메시지는: {idx + 2}/{len(messages)}")
                    if idx + 1 < len(messages):
                        print(f"     \"{messages[idx + 1]}\"")
                    break
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    debug_message_matching()
