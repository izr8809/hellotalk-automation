#!/usr/bin/env python3
"""
HelloTalk 자동 메시지 전송 봇
이미 열려있는 Chrome 브라우저에 연결하여 메시지를 자동으로 전송합니다.
"""

import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

class HelloTalkBot:
    def __init__(self):
        self.messages = []
        self.exclude_users = set()
        
    def load_messages(self, file_path="messages.txt"):
        """메시지 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.messages = [line.strip() for line in f if line.strip()]
            print(f"✓ {len(self.messages)}개 메시지 로드 완료")
            return True
        except FileNotFoundError:
            print(f"❌ {file_path} 파일을 찾을 수 없습니다.")
            return False
    
    def load_exclude_users(self, file_path="exclude_users.txt"):
        """제외할 유저 목록 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.exclude_users = {line.strip() for line in f if line.strip()}
            print(f"✓ {len(self.exclude_users)}명 제외 목록 로드 완료")
        except FileNotFoundError:
            print(f"⚠️  {file_path} 파일 없음 (모든 유저에게 전송)")
            self.exclude_users = set()
    
    def wait_for_user_reply(self, page):
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
                    break
            except:
                continue
        
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
                        return True
                except:
                    continue
    
    def send_all_messages_to_user(self, page, user_element):
        user_element.click()
        time.sleep(2)
        
        for msg_idx, message in enumerate(self.messages, 1):
            try:
                input_selectors = [
                    'textarea[placeholder*="message"]',
                    'textarea[placeholder*="메시지"]',
                    '.message-input textarea',
                    '[contenteditable="true"]',
                    'input[type="text"]',
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
                    print(f"   ⚠️  메시지 {msg_idx}: 입력창을 찾을 수 없습니다.")
                    return False
                
                input_box.fill(message)
                time.sleep(0.5)
                
                send_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Send")',
                    'button:has-text("전송")',
                    '.send-button',
                ]
                
                sent = False
                for selector in send_selectors:
                    try:
                        send_btn = page.query_selector(selector)
                        if send_btn:
                            send_btn.click()
                            sent = True
                            break
                    except:
                        continue
                
                if not sent:
                    input_box.press('Enter')
                
                print(f"   ✓ 메시지 {msg_idx}/{len(self.messages)} 전송: \"{message[:40]}...\"")
                
                if msg_idx < len(self.messages):
                    self.wait_for_user_reply(page)
                
            except Exception as e:
                print(f"   ❌ 메시지 {msg_idx} 전송 실패: {e}")
                return False
        
        return True
    
    def connect_to_browser(self):
        """이미 열린 Chrome에 연결"""
        print("\n🔗 Chrome 브라우저에 연결 중...")
        print("   (Chrome을 디버그 모드로 실행했는지 확인하세요)")
        
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            if not browser.contexts:
                print("❌ 열린 브라우저 컨텍스트가 없습니다.")
                return None, None, None
            
            context = browser.contexts[0]
            
            # HelloTalk 페이지 찾기
            page = None
            for p in context.pages:
                if 'hellotalk.com' in p.url:
                    page = p
                    break
            
            if not page:
                print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
                print("   브라우저에서 https://web.hellotalk.com/ 을 열어주세요.")
                return None, None, None
            
            print(f"✓ 연결 성공: {page.url}")
            return playwright, browser, page
            
        except Exception as e:
            print(f"❌ 브라우저 연결 실패: {e}")
            print("\n💡 해결 방법:")
            print("   1. Chrome을 디버그 모드로 실행:")
            print('      /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\')
            print('        --remote-debugging-port=9222 \\')
            print('        --user-data-dir="/tmp/chrome-debug"')
            print("   2. HelloTalk 웹에 로그인")
            print("   3. 이 스크립트 다시 실행")
            return None, None, None
    
    def get_chat_list(self, page):
        """대화 목록에서 유저 가져오기"""
        print("\n📋 대화 목록 스캔 중...")
        
        try:
            # HelloTalk 웹 구조 분석 필요
            # 일반적인 패턴으로 시도
            selectors = [
                '.chat-list-item',
                '.conversation-item',
                '[data-testid*="chat"]',
                '.message-list-item',
            ]
            
            users = []
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"✓ '{selector}' 선택자로 {len(elements)}개 대화 발견")
                        users = elements
                        break
                except:
                    continue
            
            if not users:
                print("⚠️  자동으로 대화 목록을 찾지 못했습니다.")
                print("   수동 모드를 사용하거나 코드를 수정해주세요.")
                return []
            
            return users
            
        except Exception as e:
            print(f"❌ 대화 목록 가져오기 실패: {e}")
            return []
    

    
    def run(self):
        """메인 실행 함수"""
        print("=" * 60)
        print("HelloTalk 자동 메시지 전송 봇")
        print("=" * 60)
        
        # 설정 파일 로드
        if not self.load_messages():
            return
        self.load_exclude_users()
        
        # 브라우저 연결
        playwright, browser, page = self.connect_to_browser()
        if not page:
            return
        
        try:
            # 대화 목록 가져오기
            users = self.get_chat_list(page)
            if not users:
                print("\n⚠️  대화 목록을 찾을 수 없습니다.")
                print("   HelloTalk 웹 구조가 변경되었을 수 있습니다.")
                return
            
            print(f"\n🚀 {len(users)}명에게 순차 메시지 전송 시작...")
            print(f"   각 유저에게 {len(self.messages)}개 메시지 전송 (답변 대기)")
            print(f"   제외: {len(self.exclude_users)}명\n")
            
            sent_count = 0
            for idx, user in enumerate(users, 1):
                try:
                    username = user.inner_text()[:20] if user else f"User {idx}"
                    
                    if username in self.exclude_users:
                        print(f"[{idx}/{len(users)}] ⏭️  건너뜀: {username}")
                        continue
                    
                    print(f"\n{'='*50}")
                    print(f"[{idx}/{len(users)}] 📤 {username}에게 대화 시작...")
                    print(f"{'='*50}")
                    
                    success = self.send_all_messages_to_user(page, user)
                    
                    if success:
                        sent_count += 1
                        print(f"   ✅ {username}와의 대화 완료!\n")
                    else:
                        print(f"   ⚠️  전송 실패, 다음 유저로 이동\n")
                    
                    time.sleep(3)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  사용자가 중단했습니다.")
                    break
                except Exception as e:
                    print(f"   ❌ 오류 발생: {e}")
                    continue
            
            print(f"\n{'=' * 60}")
            print(f"✅ 완료: {sent_count}명에게 메시지 전송 완료")
            print(f"{'=' * 60}\n")
            
        except Exception as e:
            print(f"\n❌ 실행 중 오류: {e}")
        finally:
            # 정리
            if browser:
                print("브라우저 연결 종료 (브라우저 창은 열린 상태로 유지)")
                # browser.close()는 호출하지 않음 - 기존 브라우저 유지
            if playwright:
                playwright.stop()


if __name__ == "__main__":
    bot = HelloTalkBot()
    bot.run()
