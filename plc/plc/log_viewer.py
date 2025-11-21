#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XG5000 PLC 클라이언트 로그 뷰어
"""

import os
import time
import argparse
from datetime import datetime
from pathlib import Path

class LogViewer:
    """로그 파일 뷰어 클래스"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.current_file = None
        self.file_position = 0
        
    def get_latest_log_file(self) -> str:
        """가장 최근 로그 파일 찾기"""
        if not os.path.exists(self.log_dir):
            print(f"로그 디렉토리가 존재하지 않습니다: {self.log_dir}")
            return None
        
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.startswith("xg5000_client_") and file.endswith(".log"):
                file_path = os.path.join(self.log_dir, file)
                log_files.append((file_path, os.path.getmtime(file_path)))
        
        if not log_files:
            print(f"로그 파일을 찾을 수 없습니다: {self.log_dir}")
            return None
        
        # 가장 최근 파일 반환
        latest_file = max(log_files, key=lambda x: x[1])[0]
        return latest_file
    
    def list_log_files(self):
        """사용 가능한 로그 파일 목록 출력"""
        if not os.path.exists(self.log_dir):
            print(f"로그 디렉토리가 존재하지 않습니다: {self.log_dir}")
            return
        
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.startswith("xg5000_client_") and file.endswith(".log"):
                file_path = os.path.join(self.log_dir, file)
                file_size = os.path.getsize(file_path)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                log_files.append((file, file_path, file_size, mod_time))
        
        if not log_files:
            print(f"로그 파일을 찾을 수 없습니다: {self.log_dir}")
            return
        
        print(f"\n=== 사용 가능한 로그 파일 ===")
        print(f"{'파일명':<25} {'크기':<10} {'수정 시간'}")
        print("-" * 50)
        
        for file_name, file_path, file_size, mod_time in sorted(log_files, key=lambda x: x[3], reverse=True):
            size_str = f"{file_size:,} bytes" if file_size < 1024*1024 else f"{file_size/1024/1024:.1f} MB"
            print(f"{file_name:<25} {size_str:<10} {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def view_log_file(self, file_path: str, follow: bool = False, lines: int = 50):
        """로그 파일 내용 보기"""
        if not os.path.exists(file_path):
            print(f"로그 파일을 찾을 수 없습니다: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if follow:
                    # 실시간 모니터링 모드
                    print(f"실시간 로그 모니터링 시작: {file_path}")
                    print("Ctrl+C로 중지")
                    print("-" * 80)
                    
                    # 파일 끝으로 이동
                    f.seek(0, 2)
                    
                    while True:
                        line = f.readline()
                        if line:
                            print(line.rstrip())
                        else:
                            time.sleep(0.1)  # 100ms 대기
                            
                else:
                    # 일반 보기 모드
                    print(f"로그 파일 보기: {file_path}")
                    print("-" * 80)
                    
                    # 마지막 N줄 읽기
                    all_lines = f.readlines()
                    if lines > 0:
                        start_line = max(0, len(all_lines) - lines)
                        for line in all_lines[start_line:]:
                            print(line.rstrip())
                    else:
                        for line in all_lines:
                            print(line.rstrip())
                            
        except KeyboardInterrupt:
            if follow:
                print("\n로그 모니터링을 중지했습니다.")
        except Exception as e:
            print(f"로그 파일 읽기 오류: {e}")
    
    def search_log(self, file_path: str, search_term: str, case_sensitive: bool = False):
        """로그 파일에서 특정 텍스트 검색"""
        if not os.path.exists(file_path):
            print(f"로그 파일을 찾을 수 없습니다: {file_path}")
            return
        
        if not case_sensitive:
            search_term = search_term.lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f"로그 검색: '{search_term}' (대소문자 구분: {case_sensitive})")
                print("-" * 80)
                
                line_number = 0
                found_count = 0
                
                for line in f:
                    line_number += 1
                    line_lower = line.lower() if not case_sensitive else line
                    
                    if search_term in line_lower:
                        found_count += 1
                        print(f"라인 {line_number:6d}: {line.rstrip()}")
                
                print("-" * 80)
                print(f"검색 완료: {found_count}개 결과 발견")
                
        except Exception as e:
            print(f"로그 검색 오류: {e}")
    
    def analyze_log(self, file_path: str):
        """로그 파일 분석"""
        if not os.path.exists(file_path):
            print(f"로그 파일을 찾을 수 없습니다: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f"로그 파일 분석: {file_path}")
                print("-" * 80)
                
                total_lines = 0
                error_count = 0
                warning_count = 0
                info_count = 0
                debug_count = 0
                
                # PLC 통신 통계
                xgt_send_count = 0
                xgt_recv_count = 0
                plc_connection_count = 0
                db_operation_count = 0
                
                for line in f:
                    total_lines += 1
                    
                    # 로그 레벨별 카운트
                    if '[ERROR]' in line:
                        error_count += 1
                    elif '[WARNING]' in line:
                        warning_count += 1
                    elif '[INFO]' in line:
                        info_count += 1
                    elif '[DEBUG]' in line:
                        debug_count += 1
                    
                    # 특정 작업별 카운트
                    if 'XGT 전송:' in line:
                        xgt_send_count += 1
                    elif 'XGT 수신:' in line:
                        xgt_recv_count += 1
                    elif 'PLC 연결' in line:
                        plc_connection_count += 1
                    elif 'DB ' in line:
                        db_operation_count += 1
                
                # 분석 결과 출력
                print(f"총 로그 라인: {total_lines:,}")
                print(f"\n로그 레벨별 분포:")
                print(f"  ERROR: {error_count:,}")
                print(f"  WARNING: {warning_count:,}")
                print(f"  INFO: {info_count:,}")
                print(f"  DEBUG: {debug_count:,}")
                
                print(f"\n작업별 통계:")
                print(f"  XGT 전송: {xgt_send_count:,}")
                print(f"  XGT 수신: {xgt_recv_count:,}")
                print(f"  PLC 연결: {plc_connection_count:,}")
                print(f"  DB 작업: {db_operation_count:,}")
                
                # 오류가 있는 경우 상세 분석
                if error_count > 0:
                    print(f"\n⚠️  오류가 {error_count}개 발견되었습니다.")
                    print("자세한 내용은 '--search ERROR' 옵션으로 확인하세요.")
                
        except Exception as e:
            print(f"로그 분석 오류: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='XG5000 PLC 클라이언트 로그 뷰어')
    parser.add_argument('--list', action='store_true', help='사용 가능한 로그 파일 목록')
    parser.add_argument('--view', type=str, help='특정 로그 파일 보기')
    parser.add_argument('--follow', '-f', action='store_true', help='실시간 로그 모니터링')
    parser.add_argument('--lines', '-n', type=int, default=50, help='표시할 라인 수 (기본값: 50)')
    parser.add_argument('--search', type=str, help='로그에서 특정 텍스트 검색')
    parser.add_argument('--case-sensitive', action='store_true', help='검색 시 대소문자 구분')
    parser.add_argument('--analyze', type=str, help='로그 파일 분석')
    parser.add_argument('--latest', action='store_true', help='가장 최근 로그 파일 보기')
    
    args = parser.parse_args()
    
    viewer = LogViewer()
    
    if args.list:
        viewer.list_log_files()
    
    elif args.view:
        viewer.view_log_file(args.view, args.follow, args.lines)
    
    elif args.follow:
        if args.latest:
            latest_file = viewer.get_latest_log_file()
            if latest_file:
                viewer.view_log_file(latest_file, follow=True)
        else:
            print("--follow 옵션은 --view 또는 --latest와 함께 사용해야 합니다.")
    
    elif args.search:
        if args.latest:
            latest_file = viewer.get_latest_log_file()
            if latest_file:
                viewer.search_log(latest_file, args.search, args.case_sensitive)
        else:
            print("--search 옵션은 --latest와 함께 사용하거나 --view로 파일을 지정해야 합니다.")
    
    elif args.analyze:
        viewer.analyze_log(args.analyze)
    
    elif args.latest:
        latest_file = viewer.get_latest_log_file()
        if latest_file:
            viewer.view_log_file(latest_file, follow=False, lines=args.lines)
    
    else:
        # 기본 동작: 최근 로그 파일 보기
        latest_file = viewer.get_latest_log_file()
        if latest_file:
            print(f"가장 최근 로그 파일: {latest_file}")
            viewer.view_log_file(latest_file, follow=False, lines=args.lines)
        else:
            parser.print_help()

if __name__ == "__main__":
    main()

