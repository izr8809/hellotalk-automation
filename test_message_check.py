#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import time

def load_messages(file_path="messages.txt"):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def test_message_check():
    print("=" * 60)
    print("현재 대화창 메시지 확인 테스트")
    print("=" * 60)
    
    messages = load_messages()
    print(f"\n템플릿 메시지:")
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
        
        print(f"\n✓ 연결 완료: {page.url}")
        print("\n현재 대화창의 내 메시지 확인 중...\n")
        
        my_messages = page.query_selector_all('.msgItemBigWrapper.sendBox')
        
        if not my_messages:
            print("⚠️  내가 보낸 메시지가 없습니다.")
        else:
            print(f"✓ 내가 보낸 메시지 {len(my_messages)}개 발견\n")
            
            for idx, msg_container in enumerate(my_messages, 1):
                try:
                    text_wrapper = msg_container.query_selector('.textWrapper pre')
                    if text_wrapper:
                        text = text_wrapper.inner_text().strip()
                        print(f"[{idx}] {text[:60]}...")
                        
                        for template_idx, template_msg in enumerate(messages):
                            if text == template_msg or template_msg in text:
                                print(f"    ✓ 템플릿 메시지 {template_idx + 1}과 일치")
                                break
                except Exception as e:
                    print(f"[{idx}] ❌ 오류: {e}")
            
            last_msg_container = my_messages[-1]
            text_wrapper = last_msg_container.query_selector('.textWrapper pre')
            if text_wrapper:
                last_text = text_wrapper.inner_text().strip()
                
                print(f"\n{'='*60}")
                print(f"마지막으로 보낸 메시지:")
                print(f"  \"{last_text}\"")
                
                for idx, template_msg in enumerate(messages):
                    if last_text == template_msg or template_msg in last_text:
                        print(f"\n✓ 템플릿 메시지 {idx + 1}/{len(messages)}과 일치")
                        print(f"  다음 보낼 메시지: {idx + 2}/{len(messages)}")
                        if idx + 1 < len(messages):
                            print(f"  내용: \"{messages[idx + 1][:50]}...\"")
                        else:
                            print(f"  ✅ 모든 메시지 전송 완료!")
                        break
                else:
                    print(f"\n⚠️  템플릿에서 찾을 수 없음")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    test_message_check()
