#!/usr/bin/env python3
"""
응답 분석 및 처리 모듈
사용자의 답변을 분석하여 적절한 다음 메시지를 선택합니다.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class ResponseHandler:
    """사용자 응답 분석 및 처리 클래스"""
    
    def __init__(self, patterns_file: str = "response_patterns.json"):
        """
        초기화
        
        Args:
            patterns_file: 응답 패턴 설정 파일 경로
        """
        self.patterns_file = Path(patterns_file)
        self.patterns = {}
        self.unhandled_log_file = Path("unhandled_responses.json")
        self.unhandled_responses = []
        self.feedback_file = Path("user_feedback.json")
        self.feedbacks = []
        
        self.load_patterns()
        self.load_unhandled_log()
        self.load_feedback_log()
    
    def load_patterns(self) -> bool:
        """응답 패턴 파일 로드"""
        try:
            if not self.patterns_file.exists():
                print(f"⚠️  패턴 파일을 찾을 수 없습니다: {self.patterns_file}")
                return False
            
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                self.patterns = json.load(f)
            
            print(f"✓ 응답 패턴 로드 완료: {len(self.patterns.get('message_flow', {}))}개 메시지 단계")
            return True
        except Exception as e:
            print(f"❌ 패턴 파일 로드 실패: {e}")
            return False
    
    def load_unhandled_log(self):
        """처리하지 못한 응답 로그 로드"""
        try:
            if self.unhandled_log_file.exists():
                with open(self.unhandled_log_file, 'r', encoding='utf-8') as f:
                    self.unhandled_responses = json.load(f)
            else:
                self.unhandled_responses = []
        except Exception as e:
            print(f"⚠️  예상 밖 응답 로그 로드 실패: {e}")
            self.unhandled_responses = []
    
    def save_unhandled_log(self):
        """처리하지 못한 응답 로그 저장"""
        try:
            with open(self.unhandled_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.unhandled_responses, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  예상 밖 응답 로그 저장 실패: {e}")
    
    def load_feedback_log(self):
        """피드백 로그 로드"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedbacks = json.load(f)
            else:
                self.feedbacks = []
        except Exception as e:
            print(f"⚠️  피드백 로그 로드 실패: {e}")
            self.feedbacks = []
    
    def save_feedback_log(self):
        """피드백 로그 저장"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedbacks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  피드백 로그 저장 실패: {e}")
    
    def save_feedback(self, username: str, message_step: int, user_message: str, 
                     my_last_message: str, feedback_type: str):
        """
        사용자 피드백 저장
        
        Args:
            username: 사용자 이름
            message_step: 피드백을 받은 메시지 단계
            user_message: 사용자 피드백 메시지
            my_last_message: 내가 보낸 마지막 메시지
            feedback_type: 피드백 타입 (예: detailed_feedback, general_positive 등)
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "message_step": message_step,
            "my_message": my_last_message,
            "user_feedback": user_message,
            "feedback_type": feedback_type,
            "analyzed": False
        }
        
        self.feedbacks.append(feedback_entry)
        self.save_feedback_log()
        print(f"   💾 피드백 저장됨: \"{user_message[:50]}...\" (타입: {feedback_type})")
    
    def log_unhandled_response(self, username: str, current_step: int, 
                               user_message: str, my_last_message: str):
        """
        처리하지 못한 응답 기록
        
        Args:
            username: 사용자 이름
            current_step: 현재 메시지 단계
            user_message: 사용자 응답 메시지
            my_last_message: 내가 보낸 마지막 메시지
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "message_step": current_step,
            "my_message": my_last_message,
            "user_response": user_message,
            "analyzed": False
        }
        
        # 중복 체크 (같은 유저의 같은 응답은 한 번만 기록)
        is_duplicate = any(
            log['username'] == username and 
            log['user_response'].lower().strip() == user_message.lower().strip()
            for log in self.unhandled_responses
        )
        
        if not is_duplicate:
            self.unhandled_responses.append(log_entry)
            self.save_unhandled_log()
            print(f"   📝 예상 밖 응답 기록됨: \"{user_message[:50]}...\"")
    
    def normalize_text(self, text: str) -> str:
        """
        텍스트 정규화 (소문자 변환, 특수문자 제거 등)
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        # 소문자 변환
        text = text.lower()
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        # 앞뒤 공백 제거
        text = text.strip()
        return text
    
    def check_keywords(self, text: str, keywords: list) -> bool:
        """
        텍스트에 키워드가 포함되어 있는지 확인
        
        Args:
            text: 검사할 텍스트
            keywords: 키워드 리스트
            
        Returns:
            키워드 포함 여부
        """
        normalized_text = self.normalize_text(text)
        
        for keyword in keywords:
            keyword_normalized = self.normalize_text(keyword)
            
            # 정확한 단어 매칭 (공백 또는 문장부호로 구분)
            pattern = r'\b' + re.escape(keyword_normalized) + r'\b'
            if re.search(pattern, normalized_text):
                return True
        
        return False
    
    def analyze_response(self, user_message: str, current_step: int, 
                        username: str, my_last_message: str) -> Tuple[Optional[int], Optional[str], bool]:
        """
        사용자 응답 분석 및 다음 액션 결정
        
        Args:
            user_message: 사용자 응답 메시지
            current_step: 현재 메시지 단계 (0-based)
            username: 사용자 이름
            my_last_message: 내가 보낸 마지막 메시지
            
        Returns:
            (다음 메시지 인덱스, 대체 메시지 또는 None, 피드백 저장 여부)
            - 다음 메시지 인덱스: -1이면 대화 종료, None이면 매칭 실패
            - 대체 메시지: 기본 메시지 대신 보낼 메시지 (없으면 None)
            - 피드백 저장 여부: True면 피드백 저장 필요
        """
        if not user_message or not user_message.strip():
            return None, None, False
        
        message_flow = self.patterns.get('message_flow', {})
        current_step_str = str(current_step)
        
        if current_step_str not in message_flow:
            print(f"   ⚠️  단계 {current_step}에 대한 패턴이 없습니다.")
            return None, None, False
        
        step_patterns = message_flow[current_step_str]
        expected_responses = step_patterns.get('expected_responses', {})
        
        for response_type, response_data in expected_responses.items():
            keywords = response_data.get('keywords', [])
            
            if self.check_keywords(user_message, keywords):
                next_idx = response_data.get('next_message_index')
                acknowledgment = response_data.get('acknowledgment')
                alternative_msg = response_data.get('alternative_message')
                skip_to_end = response_data.get('skip_to_end', False)
                should_save_feedback = response_data.get('save_feedback', False)
                
                print(f"   ✓ 응답 패턴 매칭: {response_type} → 다음 단계: {next_idx}")
                
                if should_save_feedback:
                    self.save_feedback(username, current_step, user_message, my_last_message, response_type)
                
                if skip_to_end:
                    final_msg = acknowledgment if acknowledgment else alternative_msg
                    return -1, final_msg, should_save_feedback
                
                # acknowledgment이 있으면 다음 step 메시지와 합치기
                if acknowledgment and next_idx is not None and next_idx >= 0:
                    next_step_msg = self.get_message_by_index(next_idx)
                    if next_step_msg:
                        combined_msg = f"{acknowledgment} {next_step_msg}"
                        return next_idx, combined_msg, should_save_feedback
                
                # alternative_message가 있으면 그대로 사용
                if alternative_msg:
                    return next_idx, alternative_msg, should_save_feedback
                
                return next_idx, None, should_save_feedback
        
        # Fallback 응답 체크
        fallback_responses = self.patterns.get('fallback_responses', {})
        for fallback_type, fallback_data in fallback_responses.items():
            keywords = fallback_data.get('keywords', [])
            
            if self.check_keywords(user_message, keywords):
                response = fallback_data.get('response', '')
                flag_user = fallback_data.get('flag_user', False)
                
                print(f"   ⚠️  Fallback 응답: {fallback_type}")
                
                if flag_user:
                    print(f"   🚩 사용자 플래그: {username}")
                
                return current_step, response + " " + step_patterns.get('message', ''), False
        
        print(f"   ⚠️  예상 밖 응답: \"{user_message[:50]}...\"")
        self.log_unhandled_response(username, current_step, user_message, my_last_message)
        
        return current_step + 1, None, False
    
    def get_message_by_index(self, index: int) -> Optional[str]:
        """
        인덱스로 메시지 가져오기
        
        Args:
            index: 메시지 인덱스
            
        Returns:
            메시지 텍스트 또는 None
        """
        message_flow = self.patterns.get('message_flow', {})
        step_data = message_flow.get(str(index))
        
        if step_data:
            return step_data.get('message')
        
        return None
    
    def analyze_user_initiated_message(self, user_message: str) -> Tuple[Optional[str], int]:
        user_initiated_patterns = self.patterns.get('user_initiated', {})
        
        if not user_message or not user_message.strip():
            return None, 0
        
        for pattern_type, pattern_data in user_initiated_patterns.items():
            if pattern_type == 'general':
                continue
                
            keywords = pattern_data.get('keywords', [])
            if self.check_keywords(user_message, keywords):
                acknowledgment = pattern_data.get('acknowledgment')
                response = pattern_data.get('response')
                next_idx = pattern_data.get('next_message_index', 0)
                print(f"   ✓ 유저 시작 패턴 매칭: {pattern_type}")
                
                if acknowledgment:
                    next_step_msg = self.get_message_by_index(next_idx)
                    if next_step_msg:
                        combined_msg = f"{acknowledgment} {next_step_msg}"
                        return combined_msg, next_idx + 1
                
                return response if response else acknowledgment, next_idx
        
        general = user_initiated_patterns.get('general', {})
        acknowledgment = general.get('acknowledgment')
        response = general.get('response')
        next_idx = general.get('next_message_index', 0)
        
        if acknowledgment:
            next_step_msg = self.get_message_by_index(next_idx)
            if next_step_msg:
                combined_msg = f"{acknowledgment} {next_step_msg}"
                return combined_msg, next_idx + 1
        
        return response if response else "Hi! Nice to meet you!", next_idx
    
    def get_unhandled_stats(self) -> Dict:
        """
        처리하지 못한 응답 통계
        
        Returns:
            통계 딕셔너리
        """
        total = len(self.unhandled_responses)
        by_step = {}
        
        for log in self.unhandled_responses:
            step = log.get('message_step', 'unknown')
            by_step[step] = by_step.get(step, 0) + 1
        
        return {
            'total': total,
            'by_step': by_step,
            'recent_10': self.unhandled_responses[-10:] if self.unhandled_responses else []
        }


if __name__ == "__main__":
    # 테스트 코드
    handler = ResponseHandler()
    
    print("\n=== 응답 분석 테스트 ===\n")
    
    test_cases = [
        (0, "I've been learning for 6 months"),
        (0, "Just started last week"),
        (0, "Hi! Nice to meet you"),
        (1, "Pronunciation is really hard for me"),
        (1, "Everything is difficult"),
        (2, "I'm a software engineer"),
        (3, "That sounds cool!"),
        (4, "Sure, I'd love to help"),
        (5, "Thanks, I'll check it out"),
        (0, "The weather is nice today"),  # Off-topic
        (0, "asdfasdfasdf"),  # 예상 밖
    ]
    
    for step, user_msg in test_cases:
        print(f"\n단계 {step}: 사용자 응답 = \"{user_msg}\"")
        next_idx, alt_msg, save_fb = handler.analyze_response(user_msg, step, "TestUser", "test message")
        print(f"  → 다음 단계: {next_idx}")
        if alt_msg:
            print(f"  → 대체 메시지: \"{alt_msg[:60]}...\"")
        if save_fb:
            print(f"  → 피드백 저장됨")
    
    print("\n\n=== 통계 ===")
    stats = handler.get_unhandled_stats()
    print(f"예상 밖 응답 총 {stats['total']}개")
    print(f"단계별 분포: {stats['by_step']}")
