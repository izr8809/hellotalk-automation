#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

import time
import json
import random
from playwright.sync_api import sync_playwright
from datetime import datetime
from llm_handler import LLMHandler

class HelloTalkBot:
    def __init__(self):
        self.exclude_users = set()
        self.user_states = {}
        self.page = None
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.llm_handler = LLMHandler()
        self.feedback_file = "feedback_data.json"
        self.hardest_part_file = "hardest_part_answers.json"
        self.negative_users_file = "negative_users.json"
        self.contacted_users_file = "contacted_users.json"
        self.contacted_users = {}  # {username: {date, device, status}}
        
    def load_exclude_users(self, file_path="exclude_users.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.exclude_users = {line.strip() for line in f if line.strip() and not line.startswith('#')}
            print(f"✓ Excluded users list loaded ({len(self.exclude_users)} users)")
            if self.exclude_users:
                print(f"   Users to exclude: {', '.join(list(self.exclude_users)[:5])}{'...' if len(self.exclude_users) > 5 else ''}")
        except FileNotFoundError:
            print(f"⚠️  {file_path} file not found (sending to all users)")
            self.exclude_users = set()
    
    def load_contacted_users(self):
        """이전에 대화한 유저 목록 로드"""
        try:
            with open(self.contacted_users_file, 'r', encoding='utf-8') as f:
                self.contacted_users = json.load(f)
            print(f"✓ Contacted users loaded ({len(self.contacted_users)} users)")
        except FileNotFoundError:
            print("⚠️  No contacted users file, starting fresh.")
            self.contacted_users = {}

    def save_contacted_user(self, username):
        """대화한 유저를 contacted 목록에 저장"""
        if username not in self.contacted_users:
            self.contacted_users[username] = {
                "first_contact": datetime.now().isoformat(),
                "device": "web"
            }
            try:
                with open(self.contacted_users_file, 'w', encoding='utf-8') as f:
                    json.dump(self.contacted_users, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"   ⚠️  Failed to save contacted user: {e}")

    def is_already_contacted(self, username):
        """이미 대화한 유저인지 확인"""
        return username in self.contacted_users

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
                print(f"✓ Previous state loaded: {len(self.user_states)} users in progress")
            else:
                self.user_states = state_data
                print(f"✓ Previous state loaded: {len(self.user_states)} users in progress")
        except FileNotFoundError:
            print("⚠️  No previous state, starting fresh.")
            self.user_states = {}

    # === 부정적 유저 감지 및 관리 ===

    # 확실히 거부/거절 의사를 표현한 경우만 감지 (너무 넓게 잡지 않음)
    NEGATIVE_KEYWORDS = [
        "stop messaging me", "leave me alone", "don't message me",
        "go away", "block", "report", "i wish you the best",
        "not interested in downloading", "i don't want to download",
    ]

    def detect_negative_response(self, user_message):
        """유저 메시지가 확실히 거부인지 감지 (너무 민감하게 잡지 않음)"""
        if not user_message:
            return False
        msg_lower = user_message.lower().strip()
        # 짧은 메시지는 무시 (오탐 방지)
        if len(msg_lower) < 15:
            return False
        return any(kw in msg_lower for kw in self.NEGATIVE_KEYWORDS)

    def save_negative_user(self, username, user_message, context=""):
        """부정적 유저를 파일에 저장하고 exclude 목록에 추가"""
        try:
            # 1. negative_users.json에 저장
            negative_data = []
            try:
                with open(self.negative_users_file, 'r', encoding='utf-8') as f:
                    negative_data = json.load(f)
            except FileNotFoundError:
                pass

            # 이미 등록된 유저인지 확인
            existing = [u for u in negative_data if u['username'] == username]
            if not existing:
                negative_data.append({
                    'timestamp': datetime.now().isoformat(),
                    'username': username,
                    'last_message': user_message,
                    'context': context,
                    'reviewed': False,
                    'action': None  # 나중에 리뷰할 때 결정
                })

                with open(self.negative_users_file, 'w', encoding='utf-8') as f:
                    json.dump(negative_data, f, indent=2, ensure_ascii=False)

                print(f"   🚫 Negative user saved: {username}")

            # 2. exclude_users.txt에 자동 추가
            self.add_to_exclude_list(username)

        except Exception as e:
            print(f"   ⚠️  Failed to save negative user: {e}")

    def add_to_exclude_list(self, username):
        """exclude_users.txt에 유저 추가"""
        exclude_file = "exclude_users.txt"
        try:
            existing = set()
            try:
                with open(exclude_file, 'r', encoding='utf-8') as f:
                    existing = {line.strip() for line in f if line.strip() and not line.startswith('#')}
            except FileNotFoundError:
                pass

            if username not in existing:
                with open(exclude_file, 'a', encoding='utf-8') as f:
                    f.write(f"{username}\n")
                self.exclude_users.add(username)
                print(f"   ➕ Added '{username}' to exclude list")

        except Exception as e:
            print(f"   ⚠️  Failed to add to exclude list: {e}")

    def review_negative_users(self):
        """부정적 유저 리뷰 - 하나씩 보여주고 처리 방법 결정"""
        try:
            with open(self.negative_users_file, 'r', encoding='utf-8') as f:
                negative_data = json.load(f)
        except FileNotFoundError:
            print("No negative users to review.")
            return

        unreviewed = [u for u in negative_data if not u.get('reviewed')]
        if not unreviewed:
            print("All negative users have been reviewed.")
            return

        print(f"\n{'='*60}")
        print(f"🔍 NEGATIVE USER REVIEW ({len(unreviewed)} pending)")
        print(f"{'='*60}\n")

        for i, user in enumerate(unreviewed):
            print(f"[{i+1}/{len(unreviewed)}] 👤 {user['username']}")
            print(f"   📅 Date: {user['timestamp'][:10]}")
            print(f"   💬 Message: \"{user['last_message']}\"")
            if user.get('context'):
                print(f"   📝 Context: {user['context']}")
            print()
            print(f"   Options:")
            print(f"     1) Keep excluded (don't message again)")
            print(f"     2) Remove from exclude (try again later)")
            print(f"     3) Skip for now")
            print()

            choice = input(f"   Choice (1/2/3): ").strip()

            if choice == '1':
                user['reviewed'] = True
                user['action'] = 'keep_excluded'
                print(f"   ✓ '{user['username']}' will stay excluded")
            elif choice == '2':
                user['reviewed'] = True
                user['action'] = 'removed_from_exclude'
                # exclude_users.txt에서 제거
                self.remove_from_exclude_list(user['username'])
                print(f"   ✓ '{user['username']}' removed from exclude list")
            elif choice == '3':
                print(f"   ⏭️  Skipped")
            else:
                print(f"   ⏭️  Invalid choice, skipped")
            print()

        # 결과 저장
        with open(self.negative_users_file, 'w', encoding='utf-8') as f:
            json.dump(negative_data, f, indent=2, ensure_ascii=False)

        print(f"{'='*60}")
        print(f"✓ Review complete!")
        print(f"{'='*60}\n")

    def remove_from_exclude_list(self, username):
        """exclude_users.txt에서 유저 제거"""
        exclude_file = "exclude_users.txt"
        try:
            lines = []
            with open(exclude_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            with open(exclude_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != username:
                        f.write(line)

            self.exclude_users.discard(username)
            print(f"   ➖ Removed '{username}' from exclude list")
        except Exception as e:
            print(f"   ⚠️  Failed to remove from exclude list: {e}")

    def save_feedback(self, username, user_message, llm_response, correct_response):
        """Save feedback data for prompt improvement"""
        try:
            # Load existing feedback
            feedback_data = []
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
            except FileNotFoundError:
                pass

            # Add new feedback
            feedback_data.append({
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'user_message': user_message,
                'llm_response': llm_response,
                'correct_response': correct_response
            })

            # Save
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️  Failed to save feedback: {e}")

    def save_hardest_part_answer(self, username, answer):
        """Save user's answer to 'hardest part' question for product feedback"""
        try:
            # Load existing answers
            answers = []
            try:
                with open(self.hardest_part_file, 'r', encoding='utf-8') as f:
                    answers = json.load(f)
            except FileNotFoundError:
                pass

            # Check if already saved for this user
            if any(item['username'] == username for item in answers):
                return

            # Add new answer
            answers.append({
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'answer': answer
            })

            # Save
            with open(self.hardest_part_file, 'w', encoding='utf-8') as f:
                json.dump(answers, f, indent=2, ensure_ascii=False)

            print(f"   💾 Saved hardest part answer: \"{answer[:50]}...\"")
        except Exception as e:
            print(f"   ⚠️  Failed to save hardest part answer: {e}")

    def extract_hardest_part_answer(self, full_conversation):
        """Extract user's answer to 'hardest part' question from conversation"""
        try:
            # Find "hardest part" question from bot
            for i, msg in enumerate(full_conversation):
                if msg['role'] == 'assistant' and 'hardest part' in msg['content'].lower():
                    # Look for next user message
                    if i + 1 < len(full_conversation):
                        next_msg = full_conversation[i + 1]
                        if next_msg['role'] == 'user':
                            return next_msg['content']
            return None
        except Exception as e:
            return None

    def should_exclude_user(self, name):
        if name in self.exclude_users:
            return True
        if self.is_already_contacted(name):
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
                        print(f"✓ Found {len(users)} users (excluded: {excluded_count})")
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
                        print(f"✓ Unread messages: {len(users_with_unread)} users (excluded: {excluded_count})")
                        for u in users_with_unread:
                            print(f"   📩 {u['name']} ({u['unread_count']} unread)")
                        return users_with_unread
                    else:
                        print(f"✓ No users with unread messages (checked {len(elements)} users, excluded: {excluded_count})")
                        return []
            except:
                continue
        
        return []
    
    def get_full_conversation_from_screen(self):
        """화면에서 전체 대화 내역 읽기 (순서대로)"""
        try:
            all_messages = self.page.query_selector_all('.msgItemBigWrapper')

            if not all_messages:
                return []

            conversation = []
            for idx, msg in enumerate(all_messages):
                text_wrapper = msg.query_selector('.textWrapper pre')
                if not text_wrapper:
                    continue

                text = text_wrapper.inner_text().strip()

                if 'sendBox' in msg.get_attribute('class'):
                    # My message (bot)
                    conversation.append({
                        'role': 'assistant',
                        'content': text,
                        'index': idx
                    })
                elif 'receiveBox' in msg.get_attribute('class'):
                    # Their message (user)
                    conversation.append({
                        'role': 'user',
                        'content': text,
                        'index': idx
                    })

            return conversation
        except Exception as e:
            print(f"      ⚠️  Failed to read conversation: {e}")
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
            print(f"      ⚠️  Failed to check messages: {e}")
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
            print(f"      ⚠️  Failed to check reply: {e}")
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
            text_message_count = 0  # 텍스트 메시지만 카운트 (스티커 제외)

            for msg in all_messages:
                if 'sendBox' in msg.get_attribute('class'):
                    has_bot_message = True
                    break
                elif 'receiveBox' in msg.get_attribute('class'):
                    text_wrapper = msg.query_selector('.textWrapper pre')
                    if text_wrapper:
                        text = text_wrapper.inner_text().strip()
                        if text:
                            text_message_count += 1
                            if first_user_message is None:
                                first_user_message = text
                    # 스티커/이미지 등 텍스트 없는 메시지는 카운트하지 않음

            # 스티커만 있는 경우 (텍스트 0개) → 새 대화로 취급
            if not has_bot_message and text_message_count == 0:
                return False, None, 0

            return not has_bot_message and first_user_message is not None, first_user_message, text_message_count
        except Exception as e:
            print(f"      ⚠️  Failed to detect conversation: {e}")
            return False, None, 0
    
    def send_message(self, message, username=None, user_last_message=None):
        try:
            # Ask user for confirmation with context
            print(f"\n{'='*60}")
            print(f"💬 CONVERSATION CONTEXT")
            print(f"{'='*60}")
            if username:
                print(f"👤 User: {username}")
            if user_last_message:
                print(f"📥 Their last message: \"{user_last_message}\"")
            else:
                print(f"📥 (Starting new conversation)")
            print(f"\n📤 Bot will send: \"{message}\"")
            print(f"{'='*60}")
            print(f"Press ENTER to send as-is, 'skip' to cancel, 'negative' to block user, or type corrected message: ", end='', flush=True)

            user_input = input().strip()

            if user_input.lower() == 'skip':
                print(f"   ⏭️  Message cancelled by user")
                return False

            if user_input.lower() == 'negative':
                print(f"   🚫 Marking '{username}' as negative user")
                self.save_negative_user(username, user_last_message or "", context="manually marked during review")
                return False

            # If user provided feedback, use it as the message and save for learning
            if user_input and user_input != '':
                original_message = message
                message = user_input
                print(f"   ✏️  Using your message instead: \"{message}\"")

                # Save feedback for learning
                self.save_feedback(username, user_last_message, original_message, message)
                print(f"   💾 Feedback saved for learning")

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

            # No need to save to history - we read from screen each time
            print(f"   ✓ Message sent successfully")

            return True

        except Exception as e:
            print(f"      ❌ Send failed: {e}")
            return False
    
    def check_and_send_next_message(self, user):
        username = user['name']

        if user['element']:
            user['element'].click()
            time.sleep(2)

            # 채팅 전환 확인
            actual_user = self.get_current_chat_user()
            if actual_user and actual_user != username:
                print(f"   ⚠️  Chat didn't switch (expected: {username}, got: {actual_user})")
                # 한번 더 시도
                user['element'].click()
                time.sleep(2)
                actual_user = self.get_current_chat_user()
                if actual_user and actual_user != username:
                    print(f"   ❌ Chat switch failed, skipping")
                    return False

            # 최신 메시지 보이도록 스크롤
            try:
                chat_area = self.page.query_selector('.msgListWrapper') or \
                            self.page.query_selector('.chatMsgList') or \
                            self.page.query_selector('[class*="msgList"]')
                if chat_area:
                    chat_area.evaluate('el => el.scrollTop = el.scrollHeight')
                    time.sleep(0.5)
            except:
                pass
        else:
            print(f"   ℹ️  Already open chat window")

        if username not in self.user_states:
            self.user_states[username] = {
                'started': False,
                'completed': False,
                'last_check_time': datetime.now().isoformat(),
                'messages_processed': []
            }

        state = self.user_states[username]

        if state.get('completed'):
            return False

        # Read full conversation from screen
        full_conversation = self.get_full_conversation_from_screen()
        print(f"   📖 Read {len(full_conversation)} messages from screen")
        for msg in full_conversation:
            role_emoji = "🤖" if msg['role'] == 'assistant' else "👤"
            print(f"      {role_emoji} {msg['role']}: \"{msg['content'][:50]}...\"")

        # Extract and save "hardest part" answer if present
        hardest_part_answer = self.extract_hardest_part_answer(full_conversation)
        if hardest_part_answer:
            self.save_hardest_part_answer(username, hardest_part_answer)

        # Check if bot already sent messages (sync state with screen)
        bot_messages_on_screen = [m for m in full_conversation if m['role'] == 'assistant']
        if bot_messages_on_screen and not state.get('started'):
            print(f"   ⚠️  Found {len(bot_messages_on_screen)} bot messages on screen, marking as started")
            state['started'] = True
            self.save_state()

        # 첫 메시지 전송 (대화 시작)
        if not state.get('started'):
            user_initiated, first_msg, user_msg_count = self.detect_user_initiated_conversation()

            if user_initiated:
                print(f"   🔍 User initiated conversation: \"{first_msg[:50] if first_msg else ''}...\"")
                print(f"   📊 User message count: {user_msg_count}")

                if user_msg_count > 1:
                    print(f"   ⏭️  Multiple conversations already in progress on mobile - skipping")
                    state['completed'] = True
                    self.save_state()
                    return False

            # Generate response based on full conversation from screen
            print(f"   🤖 Generating LLM response based on screen conversation...")
            response, is_end = self.llm_handler.generate_response(username, full_conversation=full_conversation)
            user_last_msg = first_msg if user_initiated else None

            if not response:
                print(f"   ❌ LLM response generation failed")
                return False

            print(f"   📤 Sending message: \"{response[:60]}...\"")
            success = self.send_message(response, username, user_last_msg)
            if success:
                state['started'] = True
                self.save_contacted_user(username)
                if is_end:
                    state['completed'] = True
                    self.llm_handler.mark_conversation_ended(username)
                    print(f"   🏁 Conversation ended")
                state['last_check_time'] = datetime.now().isoformat()
                self.save_state()
                return True
            return False

        # 진행 중인 대화: 마지막 메시지가 유저인지 확인
        if not full_conversation:
            print(f"   ⏳ No conversation on screen")
            return False

        last_msg = full_conversation[-1]
        if last_msg['role'] == 'assistant':
            print(f"   ⏳ Waiting for reply... (last msg is bot)")
            return False

        # 이미 처리한 메시지인지 확인
        last_user_text = last_msg['content'][:50]
        last_msg_key = f"{username}:last:{last_user_text}"
        if last_msg_key == state.get('last_processed_msg'):
            print(f"   ⏳ Already processed this message")
            return False

        print(f"   ✓ New user message detected: \"{last_user_text}...\"")

        # Collect user messages after last bot message
        all_messages_text = last_msg['content']
        new_messages = self.get_all_new_received_messages(username)
        if new_messages:
            for msg_data in new_messages:
                state['messages_processed'].append(msg_data['hash'])
            all_messages_text = " | ".join([msg['text'] for msg in new_messages])
        print(f"   📝 User message: \"{all_messages_text[:100]}...\"")

        # Check for negative response - save silently, continue conversation
        if self.detect_negative_response(all_messages_text):
            self.save_negative_user(username, all_messages_text, context="auto-detected during conversation")

        # Re-read full conversation from screen
        full_conversation = self.get_full_conversation_from_screen()
        print(f"   📖 Full conversation: {len(full_conversation)} messages")

        # Extract and save "hardest part" answer if present
        hardest_part_answer = self.extract_hardest_part_answer(full_conversation)
        if hardest_part_answer:
            self.save_hardest_part_answer(username, hardest_part_answer)

        # Generate response based on full conversation from screen
        print(f"   🤖 Generating LLM response based on screen conversation...")
        response, is_end = self.llm_handler.generate_response(username, full_conversation=full_conversation)

        if not response:
            print(f"   ❌ LLM response generation failed")
            return False

        print(f"   📤 Sending message: \"{response[:60]}...\"")
        # Pass all messages as context for manual approval display
        success = self.send_message(response, username, all_messages_text)

        if success and is_end:
            state['completed'] = True
            self.llm_handler.mark_conversation_ended(username)
            print(f"   🏁 Conversation completed!")

        if success:
            state['last_processed_msg'] = last_msg_key
        state['last_check_time'] = datetime.now().isoformat()
        self.save_state()
        return success

    def print_daily_stats(self):
        """오늘 통계 출력"""
        today = datetime.now().strftime("%Y-%m-%d")
        total_completed = 0
        today_completed = 0
        today_contacted = 0
        today_completed_names = []

        for name, state in self.user_states.items():
            if name.endswith('_ended'):
                continue
            if state.get('completed'):
                total_completed += 1
                check_time = state.get('last_check_time', '')
                if check_time.startswith(today):
                    today_completed += 1
                    today_completed_names.append(name)

        for name, info in self.contacted_users.items():
            contact_time = info.get('first_contact', '')
            if contact_time.startswith(today):
                today_contacted += 1

        ongoing = sum(1 for name, s in self.user_states.items()
                      if not name.endswith('_ended')
                      and s.get('started') and not s.get('completed'))

        print(f"\n{'='*60}")
        print(f"📊 TODAY ({today}) STATS")
        print(f"{'='*60}")
        print(f"   🆕 Contacted today: {today_contacted}")
        print(f"   💬 Ongoing: {ongoing}")
        print(f"   ✅ Completed today: {today_completed}")
        print(f"   🏆 Total completed (all time): {total_completed}")
        if today_completed_names:
            print(f"   📋 Completed: {', '.join(today_completed_names)}")
        print(f"{'='*60}")

    def run(self):
        print("=" * 60)
        print("HelloTalk Multi-User Bot (LLM)")
        print("=" * 60)

        self.load_exclude_users()
        self.load_contacted_users()
        self.load_state()

        # Check Ollama status
        server_ok, model_ok, models = self.llm_handler.check_ollama_status()
        if not server_ok:
            print("❌ Cannot connect to Ollama server.")
            print("   → Start with 'ollama serve' command.")
            return
        print(f"✓ Ollama server connected (models: {', '.join(models)})")
        if not model_ok:
            print(f"❌ Model '{self.llm_handler.model}' not found.")
            print(f"   → Download with 'ollama pull {self.llm_handler.model}' command.")
            return
        print(f"✓ Model '{self.llm_handler.model}' ready to use")
        
        print("\n🔗 Connecting to Chrome browser...")

        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp("http://localhost:9222")

            if not browser.contexts:
                print("❌ No open browser found.")
                return

            context = browser.contexts[0]

            self.page = None
            for p in context.pages:
                if 'hellotalk.com' in p.url:
                    self.page = p
                    break

            if not self.page:
                print("❌ HelloTalk page not found.")
                return

            print(f"✓ Connected: {self.page.url}\n")
            
            print("=" * 60)
            print("🚀 Bot started!")
            print("=" * 60)
            print(f"LLM model: {self.llm_handler.model}")
            print("Stop: Ctrl + C\n")

            cycle = 0

            while True:
                cycle += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n{'='*60}")
                print(f"[Cycle {cycle}] {current_time}")
                print(f"{'='*60}")

                # 현재 열려있는 채팅 먼저 처리
                current_chat_user = self.get_current_chat_user()
                if current_chat_user:
                    print(f"\n💬 Current chat: {current_chat_user}")
                    user_obj = {'name': current_chat_user, 'element': None}
                    try:
                        self.check_and_send_next_message(user_obj)
                        time.sleep(2)
                    except Exception as e:
                        print(f"   ❌ Error: {e}")

                # unread 뱃지 있는 유저만 체크
                users_with_unread = self.get_users_with_unread()
                users_to_check = [u for u in users_with_unread if u['name'] != current_chat_user]

                if not users_to_check:
                    print("✅ No new messages.")
                else:
                    print(f"\n📩 {len(users_to_check)} users with new messages:")
                    total_actions = 0
                    for idx, user in enumerate(users_to_check, 1):
                        username = user['name']
                        print(f"\n[{idx}/{len(users_to_check)}] 📩 {username} ({user.get('unread_count', '?')} unread)")

                        try:
                            action = self.check_and_send_next_message(user)
                            if action:
                                total_actions += 1
                            time.sleep(2)
                        except Exception as e:
                            print(f"   ❌ Error: {e}")
                            import traceback
                            traceback.print_exc()
                            continue

                    print(f"\n{'='*60}")
                    print(f"✅ Cycle {cycle} done: {len(users_to_check)} checked, {total_actions} actions")
                    print(f"{'='*60}")

                self.print_daily_stats()
                print(f"\n⏳ Waiting 100 seconds until next cycle...")
                time.sleep(100)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  User interrupted.")
            print("Progress saved to bot_state.json.")

        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
        
        finally:
            if 'playwright' in locals():
                playwright.stop()

if __name__ == "__main__":
    bot = HelloTalkBot()
    bot.run()
