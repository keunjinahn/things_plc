#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC 데이터 수집 시스템 통합 실행 스크립트
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
    print("           PLC 데이터 수집 시스템")
    print("=" * 60)
    print("1. PRG 파일 파싱 및 DB 저장")
    print("2. PLC 실시간 데이터 수집")
    print("3. 데이터 모니터링")
    print("4. 시스템 상태 확인")
    print("5. 종료")
    print("=" * 60)

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
            print(f"\n{selected_file} 파일을 파싱하고 DB에 저장합니다...")
            result = subprocess.run([
                sys.executable, 'prg_parser_to_db.py', selected_file, str(plc_id)
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
            sys.executable, 'plc_data_collector.py', '--start', 
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
            sys.executable, 'plc_data_collector.py', '--status', 
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
    
    # 데이터베이스 파일 확인
    db_file = 'plc_data.db'
    if os.path.exists(db_file):
        db_size = os.path.getsize(db_file)
        print(f"✅ 데이터베이스: {db_file} ({db_size:,} bytes)")
    else:
        print(f"❌ 데이터베이스: {db_file} (파일 없음)")
    
    # PRG 파일 확인
    prg_files = [f for f in os.listdir('.') if f.endswith('.prg')]
    if prg_files:
        print(f"✅ PRG 파일: {len(prg_files)}개 발견")
        for file in prg_files:
            file_size = os.path.getsize(file)
            print(f"   - {file} ({file_size:,} bytes)")
    else:
        print("❌ PRG 파일: 없음")
    
    # Python 스크립트 확인
    required_scripts = [
        'prg_parser_to_db.py',
        'plc_data_collector.py'
    ]
    
    print("\n필수 스크립트:")
    for script in required_scripts:
        if os.path.exists(script):
            print(f"✅ {script}")
        else:
            print(f"❌ {script}")
    
    # 데이터베이스 내용 확인
    try:
        import sqlite3
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # PLC 장치 수
            cursor.execute("SELECT COUNT(*) FROM plc_devices")
            device_count = cursor.fetchone()[0]
            print(f"\n📊 데이터베이스 통계:")
            print(f"   - PLC 장치: {device_count}개")
            
            # 데이터 항목 수
            cursor.execute("SELECT COUNT(*) FROM plc_data_items WHERE is_active = TRUE")
            item_count = cursor.fetchone()[0]
            print(f"   - 활성 데이터 항목: {item_count}개")
            
            # 실시간 데이터 수
            cursor.execute("SELECT COUNT(*) FROM plc_real_time_data")
            realtime_count = cursor.fetchone()[0]
            print(f"   - 실시간 데이터: {realtime_count}개")
            
    except Exception as e:
        print(f"❌ 데이터베이스 상태 확인 실패: {e}")

def main():
    """메인 함수"""
    while True:
        try:
            print_banner()
            choice = input("\n선택 (1-5): ").strip()
            
            if choice == '1':
                parse_prg_file()
            elif choice == '2':
                start_data_collection()
            elif choice == '3':
                monitor_data()
            elif choice == '4':
                check_system_status()
            elif choice == '5':
                print("\n시스템을 종료합니다.")
                break
            else:
                print("잘못된 선택입니다. 1-5 중에서 선택하세요.")
            
            input("\n계속하려면 Enter를 누르세요...")
            
        except KeyboardInterrupt:
            print("\n\n시스템을 종료합니다.")
            break
        except Exception as e:
            print(f"\n오류 발생: {e}")
            input("계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    main()
