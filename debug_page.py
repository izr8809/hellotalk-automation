#!/usr/bin/env python3

import time
from playwright.sync_api import sync_playwright

def debug_page():
    print("=" * 60)
    print("HelloTalk 페이지 구조 분석")
    print("=" * 60)
    
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
        
        if not browser.contexts:
            print("❌ 열린 브라우저가 없습니다.")
            return
        
        context = browser.contexts[0]
        
        page = None
        for p in context.pages:
            if 'hellotalk.com' in p.url:
                page = p
                break
        
        if not page:
            print("❌ HelloTalk 페이지를 찾을 수 없습니다.")
            return
        
        print(f"✓ 연결 완료: {page.url}\n")
        
        print("=" * 60)
        print("페이지 HTML 구조 분석 중...")
        print("=" * 60)
        
        html = page.content()
        
        output_file = "page_structure.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✓ 전체 HTML을 '{output_file}'에 저장했습니다.\n")
        
        print("=" * 60)
        print("주요 요소 검색 중...")
        print("=" * 60)
        
        patterns = [
            "chat",
            "conversation",
            "message",
            "dialog",
            "contact",
            "user",
            "friend",
            "list",
            "item",
        ]
        
        for pattern in patterns:
            selectors_to_try = [
                f'[class*="{pattern}"]',
                f'[id*="{pattern}"]',
                f'[data-testid*="{pattern}"]',
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"\n✓ '{selector}' → {len(elements)}개 요소 발견")
                        
                        for i, elem in enumerate(elements[:3]):
                            try:
                                tag = elem.evaluate("el => el.tagName")
                                classes = elem.evaluate("el => el.className")
                                text = elem.inner_text()[:50] if elem.inner_text() else ""
                                print(f"  [{i+1}] <{tag.lower()}> class=\"{classes}\"")
                                if text:
                                    print(f"      텍스트: \"{text}...\"")
                            except:
                                pass
                except Exception as e:
                    pass
        
        print("\n" + "=" * 60)
        print("모든 클래스 이름 추출 중...")
        print("=" * 60)
        
        all_classes = page.evaluate("""
            () => {
                const classes = new Set();
                document.querySelectorAll('*').forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(' ').forEach(c => {
                            if (c.trim()) classes.add(c.trim());
                        });
                    }
                });
                return Array.from(classes).sort();
            }
        """)
        
        relevant_classes = [c for c in all_classes if any(
            keyword in c.lower() 
            for keyword in ['chat', 'conversation', 'message', 'contact', 'user', 'dialog', 'list', 'item']
        )]
        
        if relevant_classes:
            print("\n관련 클래스 이름:")
            for cls in relevant_classes[:30]:
                print(f"  - {cls}")
            
            if len(relevant_classes) > 30:
                print(f"  ... 외 {len(relevant_classes) - 30}개")
        
        print("\n" + "=" * 60)
        print("스크린샷 저장 중...")
        print("=" * 60)
        
        page.screenshot(path="hellotalk_screenshot.png")
        print("✓ 스크린샷을 'hellotalk_screenshot.png'에 저장했습니다.")
        
        print("\n" + "=" * 60)
        print("분석 완료!")
        print("=" * 60)
        print("\n다음 파일들을 확인하세요:")
        print("  1. page_structure.html - 전체 HTML 구조")
        print("  2. hellotalk_screenshot.png - 현재 화면")
        print("\n이 정보를 바탕으로 정확한 선택자를 찾을 수 있습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    
    finally:
        if 'playwright' in locals():
            playwright.stop()

if __name__ == "__main__":
    debug_page()
