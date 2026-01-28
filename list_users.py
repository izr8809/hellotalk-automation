#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright

playwright = sync_playwright().start()
browser = playwright.chromium.connect_over_cdp("http://localhost:9222")

if not browser.contexts:
    print("❌ 열린 브라우저가 없습니다.")
    sys.exit(1)

context = browser.contexts[0]
page = None

for p in context.pages:
    if 'hellotalk.com' in p.url:
        page = p
        break

if not page:
    print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
    sys.exit(1)

users = page.query_selector_all('.memberItem')
print(f"총 {len(users)}명의 유저 발견\n")

import json
with open('bot_state.json', 'r') as f:
    state = json.load(f)

for idx, user in enumerate(users, 1):
    name_elem = user.query_selector('.name')
    if name_elem:
        name = name_elem.inner_text().strip()
        
        # Check if in state
        in_state = name in state['user_states']
        is_gao = 'gao' in name.lower() and 'vang' in name.lower()
        
        marker = ""
        if is_gao:
            marker = " ← GAO VANG"
        elif in_state:
            marker = " (in state)"
        
        print(f"{idx}. {name}{marker}")

print("\nGao Vang으로 검색되는 유저:")
for user in users:
    name_elem = user.query_selector('.name')
    if name_elem:
        name = name_elem.inner_text().strip()
        if 'gao' in name.lower() or 'vang' in name.lower():
            print(f"  - \"{name}\"")
