#!/usr/bin/env python3
"""
HelloTalk 자동 메시지 전송 프로그램

이 프로그램은 HelloTalk 웹 버전에서 여러 사용자에게 자동으로 메시지를 전송합니다.
QR 코드 스캔을 통한 수동 로그인 후 자동화가 시작됩니다.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Set
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hellotalk_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HelloTalkAutomation:
    """HelloTalk 자동화 클래스"""
    
    def __init__(self, messages_file: str = "messages.txt", 
                 exclude_file: str = "exclude_users.txt",
                 interval_seconds: int = 60):
        """
        초기화
        
        Args:
            messages_file: 전송할 메시지 목록 파일
            exclude_file: 제외할 사용자 목록 파일
            interval_seconds: 메시지 전송 간격 (초)
        """
        self.messages_file = Path(messages_file)
        self.exclude_file = Path(exclude_file)
        self.interval_seconds = interval_seconds
        self.messages: List[str] = []
        self.excluded_users: Set[str] = set()
        self.current_message_index = 0
        
    def load_messages(self) -> bool:
        """메시지 파일 로드"""
        try:
            if not self.messages_file.exists():
                logger.error(f"메시지 파일을 찾을 수 없습니다: {self.messages_file}")
                return False
            
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                self.messages = [line.strip() for line in f if line.strip()]
            
            if not self.messages:
                logger.error("메시지 파일이 비어있습니다.")
                return False
            
            logger.info(f"{len(self.messages)}개의 메시지를 로드했습니다.")
            return True
        except Exception as e:
            logger.error(f"메시지 파일 로드 실패: {e}")
            return False
    
    def load_excluded_users(self) -> bool:
        """제외할 사용자 목록 로드"""
        try:
            if not self.exclude_file.exists():
                logger.warning(f"제외 사용자 파일을 찾을 수 없습니다: {self.exclude_file}")
                logger.info("모든 사용자에게 메시지를 전송합니다.")
                return True
            
            with open(self.exclude_file, 'r', encoding='utf-8') as f:
                self.excluded_users = {line.strip() for line in f if line.strip()}
            
            logger.info(f"{len(self.excluded_users)}명의 사용자를 제외합니다.")
            return True
        except Exception as e:
            logger.error(f"제외 사용자 파일 로드 실패: {e}")
            return False
    
    def get_next_message(self) -> str:
        """다음 메시지 가져오기 (순환)"""
        message = self.messages[self.current_message_index]
        self.current_message_index = (self.current_message_index + 1) % len(self.messages)
        return message
    
    async def wait_for_login(self, page: Page) -> bool:
        """
        사용자가 QR 코드를 스캔하여 로그인할 때까지 대기
        
        Returns:
            로그인 성공 여부
        """
        logger.info("=" * 60)
        logger.info("HelloTalk 웹 페이지가 열렸습니다.")
        logger.info("모바일 앱으로 QR 코드를 스캔하여 로그인해주세요.")
        logger.info("로그인이 완료되면 자동으로 진행됩니다...")
        logger.info("=" * 60)
        
        try:
            # 로그인 완료 대기 (최대 5분)
            # 로그인 후 URL이 변경되거나 특정 요소가 나타나는지 확인
            await page.wait_for_function(
                "() => !document.querySelector('#login_box') || document.querySelector('.chatList, .chat-list, [class*=\"chat\"]')",
                timeout=300000  # 5분
            )
            
            # 추가 대기 (페이지 로드 완료)
            await asyncio.sleep(3)
            
            logger.info("로그인이 완료되었습니다!")
            return True
            
        except Exception as e:
            logger.error(f"로그인 대기 중 오류 발생: {e}")
            logger.error("5분 내에 로그인하지 않았거나 페이지 구조가 변경되었습니다.")
            return False
    
    async def get_user_list(self, page: Page) -> List[dict]:
        """
        대화 가능한 사용자 목록 가져오기
        
        Returns:
            사용자 정보 리스트 [{name: str, element: ElementHandle}, ...]
        """
        try:
            logger.info("사용자 목록을 가져오는 중...")
            
            # 다양한 선택자 시도
            selectors = [
                '.chatList .chat-item',
                '.chat-list .chat-item',
                '[class*="chatList"] [class*="item"]',
                '[class*="chat-list"] [class*="item"]',
                '.conversation-item',
                '[class*="conversation"]'
            ]
            
            users = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"선택자 '{selector}'로 {len(elements)}개의 요소를 찾았습니다.")
                        
                        for element in elements:
                            try:
                                # 사용자 이름 추출
                                name_element = await element.query_selector('.name, .username, [class*="name"]')
                                if name_element:
                                    name = await name_element.inner_text()
                                    name = name.strip()
                                    
                                    if name and name not in self.excluded_users:
                                        users.append({
                                            'name': name,
                                            'element': element
                                        })
                                        logger.debug(f"사용자 추가: {name}")
                            except Exception as e:
                                logger.debug(f"사용자 정보 추출 실패: {e}")
                                continue
                        
                        if users:
                            break
                except Exception as e:
                    logger.debug(f"선택자 '{selector}' 시도 실패: {e}")
                    continue
            
            if not users:
                logger.warning("사용자 목록을 찾을 수 없습니다. 페이지 구조를 확인해주세요.")
                # 페이지 구조 디버깅 정보 출력
                html_structure = await page.evaluate("""
                    () => {
                        const divs = document.querySelectorAll('div[class*="chat"], div[class*="list"], div[class*="conversation"]');
                        return Array.from(divs).slice(0, 5).map(d => ({
                            class: d.className,
                            text: d.innerText?.substring(0, 50)
                        }));
                    }
                """)
                logger.debug(f"페이지 구조 샘플: {html_structure}")
            else:
                logger.info(f"총 {len(users)}명의 사용자를 찾았습니다 (제외된 사용자 제외).")
            
            return users
            
        except Exception as e:
            logger.error(f"사용자 목록 가져오기 실패: {e}")
            return []
    
    async def send_message_to_user(self, page: Page, user: dict, message: str) -> bool:
        """
        특정 사용자에게 메시지 전송
        
        Args:
            page: Playwright 페이지 객체
            user: 사용자 정보 딕셔너리
            message: 전송할 메시지
            
        Returns:
            전송 성공 여부
        """
        try:
            user_name = user['name']
            logger.info(f"'{user_name}'에게 메시지 전송 시도...")
            
            # 사용자 클릭하여 대화창 열기
            await user['element'].click()
            await asyncio.sleep(2)  # 대화창 로드 대기
            
            # 메시지 입력창 찾기
            input_selectors = [
                'textarea[placeholder*="메시지"], textarea[placeholder*="message"]',
                'input[type="text"][placeholder*="메시지"], input[type="text"][placeholder*="message"]',
                '.message-input textarea, .message-input input',
                '[class*="input"] textarea, [class*="input"] input[type="text"]',
                'textarea',
                'input[type="text"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = await page.wait_for_selector(selector, timeout=5000)
                    if input_element:
                        logger.debug(f"입력창 발견: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                logger.error(f"'{user_name}': 메시지 입력창을 찾을 수 없습니다.")
                return False
            
            # 메시지 입력
            await input_element.fill(message)
            await asyncio.sleep(0.5)
            
            # 전송 버튼 찾기 및 클릭
            send_selectors = [
                'button[type="submit"]',
                'button:has-text("전송"), button:has-text("Send")',
                '.send-button, .btn-send',
                '[class*="send"]',
            ]
            
            sent = False
            for selector in send_selectors:
                try:
                    send_button = await page.query_selector(selector)
                    if send_button:
                        await send_button.click()
                        sent = True
                        logger.debug(f"전송 버튼 클릭: {selector}")
                        break
                except:
                    continue
            
            # 전송 버튼을 못 찾으면 Enter 키 시도
            if not sent:
                logger.debug("전송 버튼을 찾지 못해 Enter 키를 시도합니다.")
                await input_element.press('Enter')
            
            await asyncio.sleep(1)
            
            logger.info(f"✓ '{user_name}'에게 메시지 전송 완료: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"'{user.get('name', 'Unknown')}'에게 메시지 전송 실패: {e}")
            return False
    
    async def run(self):
        """메인 실행 함수"""
        # 설정 파일 로드
        if not self.load_messages():
            return
        
        if not self.load_excluded_users():
            return
        
        async with async_playwright() as p:
            # 브라우저 실행 (헤드리스 모드 비활성화 - 사용자가 QR 스캔을 봐야 함)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # HelloTalk 웹 페이지 열기
                logger.info("HelloTalk 웹 페이지를 여는 중...")
                await page.goto('https://web.hellotalk.com/')
                
                # 로그인 대기
                if not await self.wait_for_login(page):
                    logger.error("로그인에 실패했습니다. 프로그램을 종료합니다.")
                    return
                
                # 사용자 목록 가져오기
                users = await self.get_user_list(page)
                
                if not users:
                    logger.error("전송할 사용자가 없습니다. 프로그램을 종료합니다.")
                    return
                
                # 각 사용자에게 메시지 전송
                logger.info("=" * 60)
                logger.info(f"총 {len(users)}명에게 메시지 전송을 시작합니다.")
                logger.info(f"전송 간격: {self.interval_seconds}초")
                logger.info("=" * 60)
                
                success_count = 0
                fail_count = 0
                
                for idx, user in enumerate(users, 1):
                    message = self.get_next_message()
                    
                    logger.info(f"\n[{idx}/{len(users)}] 진행 중...")
                    
                    if await self.send_message_to_user(page, user, message):
                        success_count += 1
                    else:
                        fail_count += 1
                    
                    # 마지막 사용자가 아니면 대기
                    if idx < len(users):
                        logger.info(f"{self.interval_seconds}초 대기 중...")
                        await asyncio.sleep(self.interval_seconds)
                
                # 결과 요약
                logger.info("\n" + "=" * 60)
                logger.info("메시지 전송 완료!")
                logger.info(f"성공: {success_count}명")
                logger.info(f"실패: {fail_count}명")
                logger.info(f"총: {len(users)}명")
                logger.info("=" * 60)
                
                # 브라우저를 5초 후 닫기 (사용자가 결과를 확인할 수 있도록)
                logger.info("5초 후 브라우저를 닫습니다...")
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"실행 중 오류 발생: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                await browser.close()


async def main():
    """메인 함수"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         HelloTalk 자동 메시지 전송 프로그램                ║
    ║                                                            ║
    ║  주의사항:                                                 ║
    ║  1. messages.txt 파일에 전송할 메시지를 작성하세요         ║
    ║  2. exclude_users.txt에 제외할 사용자를 작성하세요         ║
    ║  3. QR 코드 스캔으로 로그인해야 합니다                     ║
    ║  4. 1분 간격으로 메시지가 전송됩니다                       ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    automation = HelloTalkAutomation(
        messages_file="messages.txt",
        exclude_file="exclude_users.txt",
        interval_seconds=60  # 1분 간격
    )
    
    await automation.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())
