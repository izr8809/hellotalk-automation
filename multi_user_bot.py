#!/usr/bin/env python3

import time
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

class HelloTalkBot:
    def __init__(self):
        self.messages = []
        self.exclude_users = set()
        self.user_states = {}
        self.page = None
        self.daily_limit = 20
        self.today_started = 0
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
    def load_messages(self, file_path="messages.txt"):
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
            'today_started': self.today_started,
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
                saved_date = state_data.get('current_date', '')
                
                if saved_date == self.current_date:
                    self.today_started = state_data.get('today_started', 0)
                    print(f"✓ 이전 상태 로드: {len(self.user_states)}명 진행 중")
                    print(f"✓ 오늘 시작한 대화: {self.today_started}/{self.daily_limit}명")
                else:
                    self.today_started = 0
                    print(f"✓ 이전 상태 로드: {len(self.user_states)}명 진행 중")
                    print(f"✓ 새로운 날! 오늘 제한: {self.daily_limit}명")
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
                        except:
                            continue
                    
                    if users:
                        print(f"✓ {len(users)}명 유저 발견 (제외: {excluded_count}명)")
                        return users
            except:
                continue
        
        return []
    
    def get_received_message_count(self):
        try:
            received_messages = self.page.query_selector_all('.msgItemBigWrapper.receiveBox')
            return len(received_messages)
        except:
            return 0
    
    def send_message(self, message):
        try:
            input_selectors = [
                'pre.msgInputWrapper[contenteditable="true"]',
                '.msgInputWrapper[contenteditable="true"]',
                '[contenteditable="true"]',
            ]
            
            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.page.wait_for_selector(selector, timeout=2000)
                    if input_box:
                        break
                except:
                    continue
            
            if not input_box:
                return False
            
            input_box.fill(message)
            time.sleep(0.5)
            input_box.press('Enter')
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"      ❌ 전송 실패: {e}")
            return False
    
    def get_my_last_message_index(self):
        try:
            my_messages = self.page.query_selector_all('.msgItemBigWrapper.sendBox')
            
            if not my_messages:
                return -1
            
            last_msg_container = my_messages[-1]
            text_wrapper = last_msg_container.query_selector('.textWrapper pre')
            
            if not text_wrapper:
                return -1
            
            last_text = text_wrapper.inner_text().strip()
            
            for idx, template_msg in enumerate(self.messages):
                if last_text == template_msg or template_msg in last_text:
                    print(f"      내가 마지막으로 보낸 메시지: \"{last_text[:50]}...\" (메시지 {idx + 1})")
                    return idx
            
            print(f"      ⚠️  마지막 메시지를 템플릿에서 찾을 수 없음: \"{last_text[:50]}...\"")
            return -1
        except Exception as e:
            print(f"      ⚠️  메시지 확인 실패: {e}")
            return -1
    
    def check_and_send_next_message(self, user):
        username = user['name']
        
        user['element'].click()
        time.sleep(2)
        
        current_received_count = self.get_received_message_count()
        
        if username not in self.user_states:
            last_msg_idx = self.get_my_last_message_index()
            
            self.user_states[username] = {
                'current_step': max(0, last_msg_idx + 1),
                'last_received_count': current_received_count,
                'completed': False
            }
            
            if last_msg_idx >= 0:
                print(f"   ℹ️  이미 메시지 {last_msg_idx + 1}/{len(self.messages)} 전송됨 (답장: {current_received_count}개)")
        
        state = self.user_states[username]
        
        if state['completed']:
            return False
        
        if state['current_step'] == 0:
            if self.today_started >= self.daily_limit:
                print(f"   ⚠️  오늘 제한 도달 ({self.daily_limit}명), 내일 다시 시도")
                return False
            
            print(f"   📤 첫 메시지 전송: {username} (오늘 {self.today_started + 1}/{self.daily_limit})")
            success = self.send_message(self.messages[0])
            if success:
                state['current_step'] = 1
                state['last_received_count'] = current_received_count
                self.today_started += 1
                self.save_state()
                return True
        
        elif current_received_count > state['last_received_count']:
            print(f"   ✓ 답장 확인! (답장 {state['last_received_count']} → {current_received_count}개)")
            
            if state['current_step'] < len(self.messages):
                next_message = self.messages[state['current_step']]
                print(f"   📤 메시지 {state['current_step'] + 1}/{len(self.messages)} 전송")
                
                success = self.send_message(next_message)
                if success:
                    state['current_step'] += 1
                    state['last_received_count'] = current_received_count
                    
                    if state['current_step'] >= len(self.messages):
                        state['completed'] = True
                        print(f"   ✅ {username} 완료!")
                    
                    self.save_state()
                    return True
        else:
            if state['current_step'] > 0 and state['current_step'] < len(self.messages):
                print(f"   ⏳ 답장 대기 중... (메시지 {state['current_step']}/{len(self.messages)} 전송 완료)")
        
        return False
    
    def run(self):
        print("=" * 60)
        print("HelloTalk 멀티 유저 봇")
        print("=" * 60)
        
        if not self.load_messages():
            return
        
        self.load_exclude_users()
        self.load_state()
        
        print("\n🔗 Chrome 브라우저에 연결 중...")
        
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            if not browser.contexts:
                print("❌ 열린 브라우저가 없습니다.")
                return
            
            context = browser.contexts[0]
            
            self.page = None
            for p in context.pages:
                if 'hellotalk.com' in p.url:
                    self.page = p
                    break
            
            if not self.page:
                print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
                return
            
            print(f"✓ 연결 완료: {self.page.url}\n")
            
            print("=" * 60)
            print("🚀 봇 시작!")
            print("=" * 60)
            print(f"전송할 메시지: {len(self.messages)}개")
            print(f"하루 첫 메시지 제한: {self.daily_limit}명")
            print(f"오늘 시작한 대화: {self.today_started}/{self.daily_limit}명")
            print(f"체크 간격: 1분")
            print("중단: Ctrl + C\n")
            
            cycle = 0
            
            while True:
                cycle += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n{'='*60}")
                print(f"[사이클 {cycle}] {current_time}")
                print(f"{'='*60}")
                
                users = self.get_all_users()
                
                if not users:
                    print("⚠️  유저 목록을 찾을 수 없습니다.")
                    time.sleep(60)
                    continue
                
                active_users = [u for u in users if u['name'] not in self.user_states or not self.user_states[u['name']]['completed']]
                completed_users = [u for u in users if u['name'] in self.user_states and self.user_states[u['name']]['completed']]
                
                print(f"활성 유저: {len(active_users)}명 | 완료: {len(completed_users)}명 | 오늘 시작: {self.today_started}/{self.daily_limit}")
                
                if not active_users:
                    print("\n✅ 모든 유저 완료!")
                    break
                
                for idx, user in enumerate(active_users, 1):
                    username = user['name']
                    state = self.user_states.get(username, {'current_step': 0})
                    
                    print(f"\n[{idx}/{len(active_users)}] {username} (단계: {state['current_step']}/{len(self.messages)})")
                    
                    try:
                        self.check_and_send_next_message(user)
                        time.sleep(2)
                    except Exception as e:
                        print(f"   ❌ 오류: {e}")
                        continue
                
                print(f"\n⏳ 다음 체크까지 60초 대기...")
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  사용자가 중단했습니다.")
            print("진행 상태는 bot_state.json에 저장되었습니다.")
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        
        finally:
            if 'playwright' in locals():
                playwright.stop()

if __name__ == "__main__":
    bot = HelloTalkBot()
    bot.run()
