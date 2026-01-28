#!/usr/bin/env python3

import time
import json
import random
from playwright.sync_api import sync_playwright
from datetime import datetime

try:
    from llm_response_handler import LLMResponseHandler
    USE_LLM = True
except ImportError:
    print("⚠️  LLM handler를 찾을 수 없습니다. Rule-based fallback 사용")
    from response_handler import ResponseHandler
    USE_LLM = False

class HelloTalkBot:
    def __init__(self, use_llm=True):
        self.messages = []
        self.exclude_users = set()
        self.user_states = {}
        self.page = None
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        if use_llm and USE_LLM:
            print("🤖 LLM 모드 활성화")
            self.response_handler = LLMResponseHandler()
            self.use_llm = True
        else:
            print("📋 Rule-based 모드")
            self.response_handler = ResponseHandler()
            self.use_llm = False
        
    def load_messages(self, file_path="messages.txt"):
        if self.use_llm:
            print("✓ LLM 모드: messages.txt 불필요 (자동 생성)")
            return True
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.messages = [line.strip() for line in f if line.strip()]
            print(f"✓ {len(self.messages)}개 메시지 로드 완료")
            return True
        except FileNotFoundError:
            print(f"❌ {file_path} 파일을 찾을 수 없습니다.")
            return False
    
    def load_exclude_users(self, file_path="exclude_users.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.exclude_users = {line.strip() for line in f if line.strip() and not line.startswith('#')}
            print(f"✓ {len(self.exclude_users)}명 제외 목록 로드 완료")
            if self.exclude_users:
                print(f"   제외할 유저: {', '.join(list(self.exclude_users)[:5])}{'...' if len(self.exclude_users) > 5 else ''}")
        except FileNotFoundError:
            print(f"⚠️  {file_path} 파일 없음 (모든 유저에게 전송)")
            self.exclude_users = set()
    
    def save_state(self):
        state_file = "bot_state.json"
        state_data = {
            'user_states': self.user_states,
            'current_date': self.current_date
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
    
    def load_state(self):
        state_file = "bot_state.json"
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            if isinstance(state_data, dict) and 'user_states' in state_data:
                self.user_states = state_data['user_states']
                print(f"✓ 이전 상태 로드: {len(self.user_states)}명 진행 중")
            else:
                self.user_states = state_data
                print(f"✓ 이전 상태 로드: {len(self.user_states)}명 진행 중")
        except FileNotFoundError:
            print("⚠️  이전 상태 없음, 새로 시작합니다.")
            self.user_states = {}
    
    def should_exclude_user(self, name):
        if name in self.exclude_users:
            return True
        
        name_lower = name.lower()
        if 'ht ' in name_lower or name_lower.startswith('ht'):
            return True
        if 'hellotalk' in name_lower:
            return True
        
        return False
    
    def get_all_users(self):
        selectors = [
            '.userItem',
            'div.userItem',
        ]
        
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                if elements:
                    users = []
                    excluded_count = 0
                    for elem in elements:
                        try:
                            username = elem.query_selector('.userName')
                            if username:
                                name = username.inner_text().strip()
                                if name:
                                    if self.should_exclude_user(name):
                                        excluded_count += 1
                                    else:
                                        users.append({
                                            'element': elem,
                                            'name': name
                                        })
                        except Exception:
                            continue
                    
                    if users or excluded_count:
                        if excluded_count:
                            print(f"   제외: {excluded_count}명")
                        return users
            except Exception:
                continue
        
        return []
    
    def check_new_reply(self, username):
        user_elem = None
        for user in self.get_all_users():
            if user['name'] == username:
                user_elem = user['element']
                break
        
        if not user_elem:
            return False
        
        try:
            unread = user_elem.query_selector('.unread-num')
            return unread is not None
        except:
            return False
    
    def click_user(self, username):
        for user in self.get_all_users():
            if user['name'] == username:
                user['element'].click()
                time.sleep(2)
                return True
        return False
    
    def get_last_received_message(self):
        message_selectors = [
            '.msg-receiver .msg-content',
            'div.msg-receiver .msg-content',
        ]
        
        for selector in message_selectors:
            try:
                messages = self.page.query_selector_all(selector)
                if messages:
                    last_message = messages[-1]
                    return last_message.inner_text().strip()
            except:
                continue
        
        return None
    
    def send_message(self, message_text):
        input_selectors = [
            'textarea.msgInput',
            'textarea[placeholder*="message"]',
            'div.msgInput',
        ]
        
        input_elem = None
        for selector in input_selectors:
            try:
                input_elem = self.page.query_selector(selector)
                if input_elem:
                    break
            except:
                continue
        
        if not input_elem:
            return False
        
        try:
            input_elem.click()
            time.sleep(0.5)
            input_elem.fill(message_text)
            time.sleep(0.5)
            
            send_button_selectors = [
                'button.sendBtn',
                'button[type="submit"]',
            ]
            
            button_found = False
            for selector in send_button_selectors:
                try:
                    button = self.page.query_selector(selector)
                    if button:
                        button.click()
                        button_found = True
                        break
                except:
                    continue
            
            if not button_found:
                input_elem.press("Enter")
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"   ❌ 전송 실패: {e}")
            return False
    
    def check_and_reply(self, username):
        if not self.click_user(username):
            print(f"   ⚠️  {username} 클릭 실패")
            return False
        
        user_reply = self.get_last_received_message()
        if not user_reply:
            print(f"   ⏳ 답장 대기 중... (메시지 {self.user_states[username]['message_index']}/8 전송 완료)")
            return False
        
        user_state = self.user_states[username]
        if user_state.get('last_reply') == user_reply:
            print(f"   ⏳ 답장 대기 중... (메시지 {user_state['message_index']}/8 전송 완료)")
            return False
        
        print(f"   ✓ 답장 확인: \"{user_reply[:50]}...\"")
        
        current_stage = user_state['message_index']
        my_last_message = user_state.get('last_sent_message', '')
        
        if self.use_llm:
            next_message, next_stage, should_end = self.response_handler.analyze_response(
                username, user_reply, current_stage, my_last_message
            )
            
            if should_end:
                print(f"   🏁 대화 종료 신호")
                if self.send_message(next_message):
                    print(f"   📤 종료 메시지 전송")
                    user_state['status'] = 'completed'
                    user_state['last_reply'] = user_reply
                    self.save_state()
                    print(f"   ✅ {username} 완료!")
                return True
            
            if self.send_message(next_message):
                print(f"   📤 메시지 전송 (단계: {current_stage} → {next_stage})")
                user_state['message_index'] = next_stage
                user_state['last_reply'] = user_reply
                user_state['last_sent_message'] = next_message
                user_state['last_message_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if next_stage >= 8:
                    user_state['status'] = 'completed'
                    print(f"   ✅ {username} 완료! (8단계 도달)")
                
                self.save_state()
                return True
        else:
            next_step, ack = self.response_handler.analyze_response(user_reply, current_stage)
            
            if ack:
                print(f"   ✓ 응답 패턴 매칭: {ack[:30]}... → 다음 단계: {next_step}")
            
            if next_step == -1:
                print(f"   🏁 대화 종료 신호")
                ending_msg = "Thanks for chatting! Good luck with your Korean learning!"
                if self.send_message(ending_msg):
                    user_state['status'] = 'completed'
                    user_state['last_reply'] = user_reply
                    self.save_state()
                    print(f"   ✅ {username} 완료!")
                return True
            
            if 0 <= next_step < len(self.messages):
                next_message = self.messages[next_step]
                if self.send_message(next_message):
                    print(f"   📤 메시지 전송 (단계: {current_stage} → {next_step})")
                    user_state['message_index'] = next_step
                    user_state['last_reply'] = user_reply
                    user_state['last_sent_message'] = next_message
                    user_state['last_message_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if next_step >= len(self.messages) - 1:
                        user_state['status'] = 'completed'
                        print(f"   ✅ {username} 완료! (마지막 메시지 전송)")
                    
                    self.save_state()
                    return True
        
        return False
    
    def send_first_message(self, username):
        if not self.click_user(username):
            print(f"   ⚠️  {username} 클릭 실패")
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_starts = sum(1 for u in self.user_states.values() 
                          if u.get('started_today') and u.get('start_date') == today)
        
        if today_starts >= 20:
            print(f"   ⏸️  오늘 최대 시작 횟수 도달 (20/20)")
            return False
        
        if self.use_llm:
            first_message = "Hi, I'm jake, how long have you been learning Korean?"
        else:
            first_message = self.messages[0]
        
        if self.send_message(first_message):
            print(f"   📤 첫 메시지 전송: {username} (오늘 {today_starts + 1}/20)")
            
            self.user_states[username] = {
                'message_index': 0,
                'status': 'in_progress',
                'last_message_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'started_today': True,
                'start_date': today,
                'last_sent_message': first_message
            }
            
            self.save_state()
            return True
        
        return False
    
    def run(self):
        print("\n" + "="*60)
        print("HelloTalk Bot - LLM 통합 버전")
        print("="*60 + "\n")
        
        if not self.use_llm:
            if not self.load_messages():
                return
        
        self.load_exclude_users()
        self.load_state()
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                contexts = browser.contexts
                if not contexts:
                    print("❌ Chrome 브라우저가 디버그 모드로 실행되지 않았습니다.")
                    print("   실행: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=\"/tmp/chrome-debug\"")
                    return
                
                context = contexts[0]
                pages = context.pages
                
                if not pages:
                    print("❌ 열린 페이지가 없습니다. HelloTalk 웹을 먼저 열어주세요.")
                    return
                
                self.page = pages[0]
                print(f"✓ 페이지 연결: {self.page.url[:50]}...")
                
                cycle = 0
                while True:
                    cycle += 1
                    print(f"\n{'='*60}")
                    print(f"[사이클 {cycle}] {datetime.now().strftime('%H:%M:%S')}")
                    print(f"{'='*60}")
                    
                    users = self.get_all_users()
                    
                    if not users:
                        print("⚠️  유저를 찾을 수 없습니다.")
                        print("⏳ 60초 대기 후 재시도...")
                        time.sleep(60)
                        continue
                    
                    in_progress = [name for name, state in self.user_states.items() 
                                  if state.get('status') == 'in_progress']
                    completed = [name for name, state in self.user_states.items() 
                                if state.get('status') == 'completed']
                    
                    new_users = [u['name'] for u in users if u['name'] not in self.user_states]
                    
                    unread_count = sum(1 for u in users 
                                      if self.check_new_reply(u['name']))
                    
                    print(f"읽지 않은 메시지: {unread_count}명 | 진행 중: {len(in_progress)}명 | 완료: {len(completed)}명")
                    
                    if new_users:
                        print(f"\n🆕 신규 유저: {len(new_users)}명")
                    
                    to_check = new_users + in_progress
                    
                    if not to_check:
                        print("\n✅ 체크할 유저 없음")
                        print("⏳ 다음 체크까지 60초 대기...")
                        time.sleep(60)
                        continue
                    
                    print(f"\n🔄 전체 {len(to_check)}명 스윕 시작:\n")
                    
                    actions_taken = 0
                    for i, username in enumerate(to_check, 1):
                        is_new = username in new_users
                        prefix = "🆕 신규" if is_new else "🔴 진행"
                        
                        if username in self.user_states:
                            stage = self.user_states[username].get('message_index', 0)
                            max_stage = 8 if self.use_llm else len(self.messages)
                            print(f"[{i}/{len(to_check)}] {prefix} | {username} (단계: {stage}/{max_stage})")
                        else:
                            print(f"[{i}/{len(to_check)}] {prefix} | {username} (단계: 0/8)")
                        
                        if is_new:
                            if self.send_first_message(username):
                                actions_taken += 1
                        else:
                            if self.check_and_reply(username):
                                actions_taken += 1
                        
                        time.sleep(random.uniform(2, 4))
                    
                    print(f"\n{'='*60}")
                    print(f"✅ 스윕 완료: {len(to_check)}명 체크, {actions_taken}개 액션")
                    print(f"{'='*60}\n")
                    
                    print("⏳ 다음 체크까지 60초 대기...")
                    time.sleep(60)
                    
            except KeyboardInterrupt:
                print("\n\n⏸️  봇 중단됨")
                self.save_state()
                print("✓ 상태 저장 완료")
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                self.save_state()

if __name__ == "__main__":
    bot = HelloTalkBot(use_llm=True)
    bot.run()
