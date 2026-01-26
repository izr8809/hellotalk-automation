#!/usr/bin/env python3

import time
import json
import random
from playwright.sync_api import sync_playwright
from datetime import datetime
from response_handler import ResponseHandler

class HelloTalkBot:
    def __init__(self):
        self.messages = []
        self.exclude_users = set()
        self.user_states = {}
        self.page = None
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.response_handler = ResponseHandler()
        
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
                        except:
                            continue
                    
                    if users:
                        print(f"✓ {len(users)}명 유저 발견 (제외: {excluded_count}명)")
                        return users
            except:
                continue
        
        return []
    
    def get_current_chat_user(self):
        """현재 열려있는 채팅창의 유저 이름 가져오기"""
        try:
            chat_header_selectors = [
                '.chatHeader .userName',
                '.chatHeader .name',
                'div[class*="chatHeader"] span[class*="name"]',
            ]
            
            for selector in chat_header_selectors:
                try:
                    name_elem = self.page.query_selector(selector)
                    if name_elem:
                        username = name_elem.inner_text().strip()
                        if username:
                            return username
                except:
                    continue
            
            return None
        except Exception as e:
            return None
    
    def get_users_with_unread(self):
        selectors = [
            '.userItem',
            'div.userItem',
        ]
        
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                if elements:
                    users_with_unread = []
                    excluded_count = 0
                    for elem in elements:
                        try:
                            unread_badge = elem.query_selector('.newMsgCount')
                            if not unread_badge:
                                continue
                            
                            username = elem.query_selector('.userName')
                            if username:
                                name = username.inner_text().strip()
                                if name:
                                    if self.should_exclude_user(name):
                                        excluded_count += 1
                                    else:
                                        unread_count_elem = unread_badge.query_selector('span')
                                        unread_count = unread_count_elem.inner_text().strip() if unread_count_elem else '?'
                                        
                                        users_with_unread.append({
                                            'element': elem,
                                            'name': name,
                                            'unread_count': unread_count
                                        })
                        except:
                            continue
                    
                    if users_with_unread:
                        print(f"✓ 읽지 않은 메시지: {len(users_with_unread)}명 (제외: {excluded_count}명)")
                        return users_with_unread
                    else:
                        print(f"✓ 읽지 않은 메시지가 있는 유저 없음")
                        return []
            except:
                continue
        
        return []
    
    def get_all_new_received_messages(self, username):
        try:
            all_messages = self.page.query_selector_all('.msgItemBigWrapper')
            
            if not all_messages:
                return []
            
            my_last_idx = -1
            for idx, msg in enumerate(all_messages):
                if 'sendBox' in msg.get_attribute('class'):
                    my_last_idx = idx
            
            new_messages = []
            state = self.user_states.get(username, {})
            processed_msgs = set(state.get('messages_processed', []))
            
            start_idx = my_last_idx + 1 if my_last_idx >= 0 else 0
            
            for idx in range(start_idx, len(all_messages)):
                msg = all_messages[idx]
                if 'receiveBox' in msg.get_attribute('class'):
                    text_wrapper = msg.query_selector('.textWrapper pre')
                    if text_wrapper:
                        text = text_wrapper.inner_text().strip()
                        msg_hash = f"{username}:{idx}:{text[:30]}"
                        
                        if msg_hash not in processed_msgs:
                            new_messages.append({
                                'text': text,
                                'hash': msg_hash,
                                'index': idx
                            })
            
            return new_messages
        except Exception as e:
            print(f"      ⚠️  메시지 확인 실패: {e}")
            return []
    
    def get_last_received_message(self):
        try:
            all_messages = self.page.query_selector_all('.msgItemBigWrapper')
            
            if not all_messages:
                return None
            
            my_last_idx = -1
            for idx, msg in enumerate(all_messages):
                if 'sendBox' in msg.get_attribute('class'):
                    my_last_idx = idx
            
            if my_last_idx == -1:
                return None
            
            for idx in range(my_last_idx + 1, len(all_messages)):
                msg = all_messages[idx]
                if 'receiveBox' in msg.get_attribute('class'):
                    text_wrapper = msg.query_selector('.textWrapper pre')
                    if text_wrapper:
                        return text_wrapper.inner_text().strip()
            
            return None
        except Exception as e:
            print(f"      ⚠️  답장 확인 실패: {e}")
            return None
    
    def has_reply_after_my_last_message(self):
        return self.get_last_received_message() is not None
    
    def detect_user_initiated_conversation(self):
        try:
            all_messages = self.page.query_selector_all('.msgItemBigWrapper')
            
            if not all_messages:
                return False, None, 0
            
            has_bot_message = False
            first_user_message = None
            user_message_count = 0
            
            for msg in all_messages:
                if 'sendBox' in msg.get_attribute('class'):
                    has_bot_message = True
                    break
                elif 'receiveBox' in msg.get_attribute('class'):
                    user_message_count += 1
                    if first_user_message is None:
                        text_wrapper = msg.query_selector('.textWrapper pre')
                        if text_wrapper:
                            first_user_message = text_wrapper.inner_text().strip()
            
            return not has_bot_message and first_user_message is not None, first_user_message, user_message_count
        except Exception as e:
            print(f"      ⚠️  대화 감지 실패: {e}")
            return False, None, 0
    
    def infer_conversation_step(self, user_message):
        """
        유저의 첫 메시지를 분석하여 모바일에서 이미 진행된 대화 단계를 추론
        HelloTalk 웹은 모바일 히스토리를 보여주지 않으므로, 유저 메시지로 추론 필요
        """
        msg_lower = user_message.lower()
        
        step_indicators = {
            0: [],
            1: ["month", "year", "week", "day", "started", "beginner", "recently", "long time"],
            2: ["hard", "difficult", "grammar", "pronunciation", "listening", "speaking", "vocabulary"],
            3: ["student", "work", "teacher", "engineer", "doctor", "designer", "job", "studying"],
            4: ["sounds good", "tell me more", "how does it work", "explain"],
            5: ["give feedback", "try it", "check it out", "test it"],
            6: ["downloaded", "tried it", "installed", "searched", "found it"],
            7: ["i like", "i love", "really good", "really helpful", "feature", "useful", "what i think"]
        }
        
        matched_step = 0
        for step, keywords in step_indicators.items():
            if any(keyword in msg_lower for keyword in keywords):
                matched_step = max(matched_step, step)
        
        return matched_step
    
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
            
            typing_delay = len(message) * 0.05 + random.uniform(1, 3)
            time.sleep(typing_delay)
            
            input_box.fill(message)
            time.sleep(random.uniform(0.3, 0.8))
            input_box.press('Enter')
            time.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            print(f"      ❌ 전송 실패: {e}")
            return False
    
    def get_my_last_message_index(self):
        try:
            my_messages = self.page.query_selector_all('.msgItemBigWrapper.sendBox')
            
            if not my_messages:
                print(f"      ⚠️  Bot 메시지를 찾을 수 없음 (selector: '.msgItemBigWrapper.sendBox')")
                return -1
            
            print(f"      ℹ️  Bot 메시지 {len(my_messages)}개 발견")
            
            last_msg_container = my_messages[-1]
            text_wrapper = last_msg_container.query_selector('.textWrapper pre')
            
            if not text_wrapper:
                print(f"      ⚠️  마지막 bot 메시지에서 텍스트를 찾을 수 없음 (selector: '.textWrapper pre')")
                return -1
            
            last_text = text_wrapper.inner_text().strip()
            last_text_lower = last_text.lower()
            
            for idx, template_msg in enumerate(self.messages):
                template_lower = template_msg.lower()
                
                if last_text_lower == template_lower:
                    print(f"      ✓ 정확한 매칭: step {idx}")
                    return idx
            
            print(f"      ⚠️  마지막 메시지를 템플릿에서 찾을 수 없음:")
            print(f"      실제 DOM: \"{last_text}\"")
            print(f"      비교 시도한 템플릿:")
            for idx, template_msg in enumerate(self.messages):
                similarity = template_msg.lower() in last_text_lower
                print(f"        Step {idx}: {'✓' if similarity else '✗'} \"{template_msg[:60]}...\"")
            return -1
        except Exception as e:
            print(f"      ⚠️  메시지 확인 실패: {e}")
            return -1
    
    def check_and_send_next_message(self, user):
        username = user['name']
        
        if user['element']:
            user['element'].click()
            time.sleep(2)
        else:
            print(f"   ℹ️  이미 열려있는 채팅창")
        
        if username not in self.user_states:
            self.user_states[username] = {
                'current_step': 0,
                'completed': False,
                'last_check_time': datetime.now().isoformat(),
                'messages_processed': []
            }
        
        state = self.user_states[username]
        
        if state.get('completed'):
            return False
        
        current_step = state.get('current_step', 0)
        
        if current_step < 0:
            current_step = 0
        
        if current_step == 0:
            dom_step = self.get_my_last_message_index()
            if dom_step >= 0:
                print(f"   🔄 DOM에서 step 복구: state는 0이지만 실제로는 step {dom_step}까지 전송됨")
                current_step = dom_step + 1
                state['current_step'] = current_step
                self.save_state()
            elif dom_step == -1:
                all_messages = self.page.query_selector_all('.msgItemBigWrapper')
                bot_messages = self.page.query_selector_all('.msgItemBigWrapper.sendBox')
                
                if len(bot_messages) > 0:
                    print(f"   ⚠️  Bot 메시지 {len(bot_messages)}개 있지만 템플릿과 매칭 안됨")
                    print(f"   ⏭️  이전 버전 메시지이거나 수정된 메시지 - 스킵")
                    state['completed'] = True
                    self.save_state()
                    return False
        
        if current_step >= len(self.messages):
            print(f"   ✅ 모든 메시지 전송 완료")
            state['completed'] = True
            self.save_state()
            return False
        
        print(f"   ℹ️  현재 step: {current_step}/{len(self.messages)}")
        
        if current_step == 0:
            user_initiated, first_msg, user_msg_count = self.detect_user_initiated_conversation()
            
            if user_initiated:
                print(f"   🔍 유저가 먼저 대화 시작: \"{first_msg[:50] if first_msg else ''}...\"")
                print(f"   📊 유저 메시지 수: {user_msg_count}개")
                
                if user_msg_count > 1:
                    print(f"   ⏭️  모바일에서 이미 여러 대화 진행됨 (웹에서는 안 보임) - 메시지 보내지 않음")
                    state['completed'] = True
                    self.save_state()
                    return False
                
                state['messages_processed'].append(f"{username}:0:{first_msg[:30] if first_msg else ''}")
            
            print(f"   📤 Step {current_step} 메시지 전송")
            success = self.send_message(self.messages[current_step])
            if success:
                state['current_step'] = current_step + 1
                state['last_check_time'] = datetime.now().isoformat()
                self.save_state()
                return True
            return False
        
        new_messages = self.get_all_new_received_messages(username)
        
        if not new_messages:
            print(f"   ⏳ 답장 대기 중...")
            return False
        
        print(f"   ✓ 새 메시지 {len(new_messages)}개 발견")
        
        for msg_data in new_messages:
            msg_hash = msg_data['hash']
            state['messages_processed'].append(msg_hash)
        
        last_user_message = new_messages[-1]['text']
        print(f"   📝 마지막 메시지만 처리: \"{last_user_message[:50]}...\"")
        
        current_step = state.get('current_step', 0)
        
        if current_step >= len(self.messages):
            print(f"   ✅ 이미 모든 메시지 전송 완료")
            state['completed'] = True
            state['last_check_time'] = datetime.now().isoformat()
            self.save_state()
            return False
        
        my_last_message = self.messages[current_step - 1] if current_step > 0 else ""
        
        next_step, alternative_message, _ = self.response_handler.analyze_response(
            last_user_message, 
            current_step - 1,
            username,
            my_last_message
        )
        
        if next_step == -1:
            print(f"   🏁 대화 종료 신호")
            if alternative_message:
                print(f"   📤 종료 메시지 전송")
                self.send_message(alternative_message)
            state['completed'] = True
            state['last_check_time'] = datetime.now().isoformat()
            self.save_state()
            return True
        
        if next_step is not None and next_step < len(self.messages):
            next_message = self.messages[next_step]
            print(f"   📤 Step {next_step} 메시지 전송")
        else:
            next_step = current_step
            if next_step < len(self.messages):
                next_message = self.messages[next_step]
                print(f"   ⚠️  패턴 매칭 실패 → step {next_step} 메시지로 진행")
            else:
                print(f"   ✅ 모든 메시지 전송 완료")
                state['completed'] = True
                state['last_check_time'] = datetime.now().isoformat()
                self.save_state()
                return False
        
        success = self.send_message(next_message)
        if success:
            state['current_step'] = next_step + 1
            
            if state['current_step'] >= len(self.messages):
                state['completed'] = True
                print(f"   ✅ 대화 완료!")
        
        state['last_check_time'] = datetime.now().isoformat()
        self.save_state()
        return True
    
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
            print(f"체크 간격: 10분")
            print("중단: Ctrl + C\n")
            
            cycle = 0
            
            while True:
                cycle += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n{'='*60}")
                print(f"[사이클 {cycle}] {current_time}")
                print(f"{'='*60}")
                
                current_chat_user = self.get_current_chat_user()
                if current_chat_user:
                    print(f"\n💬 현재 채팅창: {current_chat_user}")
                    print(f"   → 먼저 체크 (새 메시지가 자동으로 읽음 처리될 수 있음)")
                    
                    user_obj = {'name': current_chat_user, 'element': None}
                    try:
                        self.check_and_send_next_message(user_obj)
                        time.sleep(2)
                    except Exception as e:
                        print(f"   ❌ 오류: {e}")
                
                users_with_unread = self.get_users_with_unread()
                all_users = self.get_all_users()
                
                if not all_users:
                    print("⚠️  유저 목록을 찾을 수 없습니다.")
                    time.sleep(60)
                    continue
                
                completed_users = [u for u in all_users if u['name'] in self.user_states and self.user_states[u['name']]['completed']]
                not_started_yet = [u for u in all_users if u['name'] not in self.user_states]
                in_progress = [u for u in all_users if u['name'] in self.user_states and not self.user_states[u['name']]['completed']]
                unread_names = {u['name'] for u in users_with_unread}
                
                print(f"읽지 않은 메시지: {len(users_with_unread)}명 | 진행 중: {len(in_progress)}명 | 완료: {len(completed_users)}명 | 신규: {len(not_started_yet)}명")
                
                users_to_check = []
                
                new_with_unread = [u for u in not_started_yet if u['name'] in unread_names and u['name'] != current_chat_user]
                in_progress_with_unread = [u for u in in_progress if u['name'] in unread_names and u['name'] != current_chat_user]
                
                users_to_check.extend(new_with_unread)
                users_to_check.extend(in_progress_with_unread)
                
                if new_with_unread:
                    print(f"\n🆕 읽지 않은 메시지 있는 신규 유저: {len(new_with_unread)}명")
                if in_progress_with_unread:
                    print(f"🔄 읽지 않은 메시지 있는 진행 중 유저: {len(in_progress_with_unread)}명")
                
                if not users_to_check:
                    print("\n✅ 체크할 유저가 없습니다.")
                    print(f"\n⏳ 다음 체크까지 600초 (10분) 대기...")
                    time.sleep(600)
                    continue
                
                print(f"\n🔄 전체 {len(users_to_check)}명 스윕 시작:")
                
                BATCH_SIZE = 30
                total_actions = 0
                
                for batch_num in range(0, len(users_to_check), BATCH_SIZE):
                    batch = users_to_check[batch_num:batch_num + BATCH_SIZE]
                    batch_actions = 0
                    
                    batch_label = f"배치 {batch_num//BATCH_SIZE + 1}/{(len(users_to_check) + BATCH_SIZE - 1)//BATCH_SIZE}"
                    print(f"\n{'='*60}")
                    print(f"📦 {batch_label}: {len(batch)}명 처리 중")
                    print(f"{'='*60}")
                    
                    for idx, user in enumerate(batch, 1):
                        username = user['name']
                        
                        is_new = username not in self.user_states
                        if is_new:
                            status_label = "🆕 신규"
                        else:
                            state = self.user_states.get(username, {'current_step': 0})
                            has_unread = username in unread_names
                            unread_indicator = "🔴" if has_unread else "⚪"
                            status_label = f"{unread_indicator} 진행"
                        
                        current_step = self.user_states.get(username, {}).get('current_step', 0)
                        global_idx = batch_num + idx
                        print(f"\n[{global_idx}/{len(users_to_check)}] {status_label} | {username} (단계: {current_step}/{len(self.messages)})")
                        
                        try:
                            action = self.check_and_send_next_message(user)
                            if action:
                                batch_actions += 1
                            time.sleep(2)
                        except Exception as e:
                            print(f"   ❌ 오류: {e}")
                            continue
                    
                    total_actions += batch_actions
                    
                    print(f"\n{'='*60}")
                    print(f"✅ {batch_label} 완료: {len(batch)}명 체크, {batch_actions}개 액션")
                    print(f"{'='*60}")
                    
                    if batch_num + BATCH_SIZE < len(users_to_check):
                        remaining = len(users_to_check) - (batch_num + BATCH_SIZE)
                        print(f"\n⏸️  잠시 휴식... (남은 유저: {remaining}명)")
                        print(f"⏳ 30초 후 다음 배치 시작...")
                        time.sleep(30)
                
                print(f"\n{'='*60}")
                print(f"🎉 전체 스윕 완료!")
                print(f"총 {len(users_to_check)}명 체크, {total_actions}개 액션")
                print(f"{'='*60}")
                
                print(f"\n⏳ 다음 사이클까지 600초 (10분) 대기...")
                time.sleep(600)
        
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
