#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 데이터 수집 시스템 통합 실행 스크립트 (MariaDB)
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime

def print_banner():
    """시스템 배너 출력"""
    print("=" * 60)
    print("        PLC 데이터 수집 시스템 (MariaDB)")
    print("=" * 60)
    print("1. 데이터베이스 연결 테스트 및 초기화")
    print("2. PRG 파일 파싱 및 DB 저장")
    print("3. PLC 실시간 데이터 수집")
    print("4. 데이터 모니터링")
    print("5. 시스템 상태 확인")
    print("6. 종료")
    print("=" * 60)

def test_database():
    """데이터베이스 연결 테스트 및 초기화"""
    print("\n=== MariaDB 연결 테스트 및 초기화 ===")
    
    try:
        result = subprocess.run([
            sys.executable, 'database_config.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 데이터베이스 연결 및 초기화 성공!")
            print(result.stdout)
        else:
            print("❌ 데이터베이스 연결 실패!")
            print(result.stderr)
            
    except Exception as e:
        print(f"데이터베이스 테스트 오류: {e}")

def parse_prg_file():
    """PRG 파일 파싱 및 DB 저장"""
    print("\n=== PRG 파일 파싱 및 DB 저장 ===")
    
    # PRG 파일 목록 확인
    prg_files = [f for f in os.listdir('.') if f.endswith('.prg')]
    
    if not prg_files:
        print("현재 디렉토리에 .prg 파일이 없습니다.")
        return
    
    print("사용 가능한 PRG 파일:")
    for i, file in enumerate(prg_files, 1):
        print(f"  {i}. {file}")
    
    try:
        choice = input(f"\n선택할 파일 번호 (1-{len(prg_files)}): ").strip()
        if not choice:
            return
        
        file_index = int(choice) - 1
        if 0 <= file_index < len(prg_files):
            selected_file = prg_files[file_index]
            print(f"\n선택된 파일: {selected_file}")
            
            # PLC 장치 ID 입력
            plc_id = input("PLC 장치 ID (기본값: 1): ").strip()
            plc_id = int(plc_id) if plc_id else 1
            
            # 파싱 실행
            print(f"\n{selected_file} 파일을 파싱하고 MariaDB에 저장합니다...")
            result = subprocess.run([
                sys.executable, 'prg_parser_to_db_mariadb.py', selected_file, str(plc_id)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PRG 파일 파싱 및 DB 저장 완료!")
                print(result.stdout)
            else:
                print("❌ PRG 파일 파싱 실패!")
                print(result.stderr)
                
        else:
            print("잘못된 선택입니다.")
            
    except (ValueError, KeyboardInterrupt):
        print("작업이 취소되었습니다.")

def start_data_collection():
    """PLC 실시간 데이터 수집 시작"""
    print("\n=== PLC 실시간 데이터 수집 시작 ===")
    
    try:
        # PLC 장치 ID 입력
        plc_id = input("PLC 장치 ID (기본값: 1): ").strip()
        plc_id = int(plc_id) if plc_id else 1
        
        # 수집 주기 입력
        interval = input("수집 주기 (밀리초, 기본값: 1000): ").strip()
        interval = int(interval) if interval else 1000
        
        print(f"\nPLC 장치 ID: {plc_id}, 수집 주기: {interval}ms")
        print("데이터 수집을 시작합니다... (Ctrl+C로 중지)")
        
        # 데이터 수집 시작
        result = subprocess.run([
            sys.executable, 'plc_data_collector_mariadb.py', '--start', 
            '--plc-id', str(plc_id), '--interval', str(interval)
        ])
        
    except (ValueError, KeyboardInterrupt):
        print("작업이 취소되었습니다.")

def monitor_data():
    """데이터 모니터링"""
    print("\n=== PLC 실시간 데이터 모니터링 ===")
    
    try:
        # PLC 장치 ID 입력
        plc_id = input("PLC 장치 ID (기본값: 1): ").strip()
        plc_id = int(plc_id) if plc_id else 1
        
        print(f"\nPLC 장치 ID: {plc_id}의 실시간 데이터를 조회합니다...")
        
        # 데이터 조회
        result = subprocess.run([
            sys.executable, 'plc_data_collector_mariadb.py', '--status', 
            '--plc-id', str(plc_id)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ 데이터 조회 실패!")
            print(result.stderr)
            
    except (ValueError, KeyboardInterrupt):
        print("작업이 취소되었습니다.")

def check_system_status():
    """시스템 상태 확인"""
    print("\n=== 시스템 상태 확인 ===")
    
    # MariaDB 연결 테스트
    print("1. MariaDB 연결 상태:")
    try:
        result = subprocess.run([
            sys.executable, 'database_config.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ MariaDB 연결 성공")
        else:
            print("   ❌ MariaDB 연결 실패")
    except:
        print("   ❌ MariaDB 연결 테스트 실패")
    
    # PRG 파일 확인
    prg_files = [f for f in os.listdir('.') if f.endswith('.prg')]
    print(f"\n2. PRG 파일:")
    if prg_files:
        print(f"   ✅ {len(prg_files)}개 발견")
        for file in prg_files:
            file_size = os.path.getsize(file)
            print(f"      - {file} ({file_size:,} bytes)")
    else:
        print("   ❌ 없음")
    
    # Python 스크립트 확인
    required_scripts = [
        'database_config.py',
        'prg_parser_to_db_mariadb.py',
        'plc_data_collector_mariadb.py'
    ]
    
    print("\n3. 필수 스크립트:")
    for script in required_scripts:
        if os.path.exists(script):
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script}")
    
    # 데이터베이스 내용 확인 (간단한 테스트)
    print("\n4. 데이터베이스 내용:")
    try:
        result = subprocess.run([
            sys.executable, 'prg_parser_to_db_mariadb.py', '--list', '1'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 3:  # 헤더 + 데이터가 있는 경우
                print("   ✅ 데이터 항목 존재")
                # 마지막 줄에서 항목 수 추출
                for line in lines:
                    if line.startswith('총'):
                        print(f"      {line}")
                        break
            else:
                print("   ⚠️ 데이터 항목 없음")
        else:
            print("   ❌ 데이터베이스 조회 실패")
    except:
        print("   ❌ 데이터베이스 상태 확인 실패")

def main():
    """메인 함수"""
    while True:
        try:
            print_banner()
            choice = input("\n선택 (1-6): ").strip()
            
            if choice == '1':
                test_database()
            elif choice == '2':
                parse_prg_file()
            elif choice == '3':
                start_data_collection()
            elif choice == '4':
                monitor_data()
            elif choice == '5':
                check_system_status()
            elif choice == '6':
                print("\n시스템을 종료합니다.")
                break
            else:
                print("잘못된 선택입니다. 1-6 중에서 선택하세요.")
            
            input("\n계속하려면 Enter를 누르세요...")
            
        except KeyboardInterrupt:
            print("\n\n시스템을 종료합니다.")
            break
        except Exception as e:
            print(f"\n오류 발생: {e}")
            input("계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    main()

