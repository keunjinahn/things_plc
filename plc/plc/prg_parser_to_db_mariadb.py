#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRG 파일을 파싱하여 PLC 데이터 항목을 MariaDB에 저장하는 프로그램
"""

import csv
import os
import sys
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from database_config import DatabaseConfig
import pymysql

class PRGParser:
    """PRG 파일 파서 클래스"""
    
    def __init__(self):
        # PLC 데이터 타입별 정규식 패턴
        self.patterns = {
            'M': r'\bM(\d+)\b',  # M100, M101 등
            'D': r'\bD(\d+)\b',  # D100, D101 등
            'Y': r'\bY(\d+)\b',  # Y000, Y001 등
            'X': r'\bX(\d+)\b',  # X000, X001 등
            'T': r'\bT(\d+)\b',  # T0, T1 등 (타이머)
            'C': r'\bC(\d+)\b',  # C0, C1 등 (카운터)
        }
        
        # PLC 데이터 타입별 Modbus 함수 코드
        self.modbus_functions = {
            'M': '01',  # Read Coils
            'D': '03',  # Read Holding Registers
            'Y': '01',  # Read Coils
            'X': '02',  # Read Discrete Inputs
            'T': '03',  # Read Holding Registers
            'C': '03',  # Read Holding Registers
        }
    
    def parse_prg_file(self, file_path: str, encoding: str = None) -> List[Dict]:
        """
        PRG 파일을 파싱하여 PLC 데이터 항목 추출
        
        Args:
            file_path (str): PRG 파일 경로
            encoding (str): 파일 인코딩
            
        Returns:
            List[Dict]: 파싱된 데이터 항목 리스트
        """
        try:
            # 파일 읽기
            if encoding:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            else:
                # 인코딩 자동 감지
                encodings = ['utf-8', 'cp949', 'euc-kr', 'iso-8859-1']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("파일 인코딩을 감지할 수 없습니다.")
            
            # 라인별로 파싱
            lines = content.split('\n')
            data_items = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('//') or line.startswith(';'):
                    continue
                
                # 각 데이터 타입별로 검색
                for item_type, pattern in self.patterns.items():
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        item_name = match.group(0)  # M100, D100 등
                        address_num = int(match.group(1))  # 100, 100 등
                        
                        # 주소 변환 (PLC 주소 형식)
                        plc_address = self._convert_to_plc_address(item_type, address_num)
                        
                        # 설명 생성
                        description = self._generate_description(item_type, address_num, line)
                        
                        data_item = {
                            'item_name': item_name,
                            'item_type': item_type,
                            'address': plc_address,
                            'modbus_address': address_num,
                            'modbus_function': self.modbus_functions[item_type],
                            'description': description,
                            'line_number': line_num,
                            'source_line': line
                        }
                        
                        # 중복 제거
                        if not any(item['item_name'] == item_name for item in data_items):
                            data_items.append(data_item)
            
            return data_items
            
        except Exception as e:
            print(f"PRG 파일 파싱 오류: {e}")
            return []
    
    def _convert_to_plc_address(self, item_type: str, address_num: int) -> str:
        """PLC 주소 형식으로 변환"""
        if item_type == 'M':
            return f'%MW{address_num}'
        elif item_type == 'D':
            return f'%DW{address_num}'
        elif item_type == 'Y':
            return f'%QW{address_num}'
        elif item_type == 'X':
            return f'%IW{address_num}'
        elif item_type == 'T':
            return f'%TW{address_num}'
        elif item_type == 'C':
            return f'%CW{address_num}'
        else:
            return f'%{item_type}W{address_num}'
    
    def _generate_description(self, item_type: str, address_num: int, line: str) -> str:
        """데이터 항목에 대한 설명 생성"""
        type_names = {
            'M': '내부 릴레이',
            'D': '데이터 레지스터',
            'Y': '출력',
            'X': '입력',
            'T': '타이머',
            'C': '카운터'
        }
        
        type_name = type_names.get(item_type, '데이터')
        return f"{type_name} {item_type}{address_num} - {line[:50]}"

class MariaDBManager:
    """MariaDB 관리 클래스"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = DatabaseConfig.create_connection()
            return self.connection is not None
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def save_parsed_items(self, data_items: List[Dict], plc_device_id: int = 1) -> bool:
        """파싱된 데이터 항목을 데이터베이스에 저장"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                # 기존 항목 비활성화
                cursor.execute('''
                    UPDATE plc_data_items 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE plc_device_id = %s
                ''', (plc_device_id,))
                
                # 새 항목 추가
                for item in data_items:
                    cursor.execute('''
                        INSERT INTO plc_data_items (
                            plc_device_id, item_name, item_type, address, modbus_address,
                            modbus_function, description, line_number, source_line
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        plc_device_id, item['item_name'], item['item_type'], 
                        item['address'], item['modbus_address'], item['modbus_function'],
                        item['description'], item['line_number'], item['source_line']
                    ))
                
                self.connection.commit()
                print(f"{len(data_items)}개 데이터 항목 저장 완료")
                return True
                
        except Exception as e:
            print(f"데이터베이스 저장 오류: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_data_items(self, plc_device_id: int = 1, active_only: bool = True) -> List[Dict]:
        """데이터 항목 조회"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return []
        
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = '''
                    SELECT id, item_name, item_type, address, modbus_address, 
                           modbus_function, description, line_number, source_line
                    FROM plc_data_items 
                    WHERE plc_device_id = %s
                '''
                
                if active_only:
                    query += ' AND is_active = TRUE'
                
                query += ' ORDER BY item_type, modbus_address'
                
                cursor.execute(query, (plc_device_id,))
                return cursor.fetchall()
                
        except Exception as e:
            print(f"데이터 조회 오류: {e}")
            return []

def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python prg_parser_to_db_mariadb.py <input.prg> [plc_device_id]")
        print("  python prg_parser_to_db_mariadb.py --list [plc_device_id]")
        print("  python prg_parser_to_db_mariadb.py --init")
        return
    
    if sys.argv[1] == '--init':
        # 데이터베이스 초기화
        print("MariaDB 데이터베이스 초기화 중...")
        if DatabaseConfig.init_database():
            print("✅ 데이터베이스 초기화 완료!")
        else:
            print("❌ 데이터베이스 초기화 실패!")
        return
    
    if sys.argv[1] == '--list':
        # 저장된 데이터 항목 조회
        plc_device_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        db_manager = MariaDBManager()
        
        if db_manager.connect():
            items = db_manager.get_data_items(plc_device_id)
            
            print(f"\n=== PLC 데이터 항목 목록 (장치 ID: {plc_device_id}) ===")
            print(f"{'항목명':<10} {'타입':<5} {'주소':<15} {'Modbus':<10} {'설명'}")
            print("-" * 80)
            
            for item in items:
                print(f"{item['item_name']:<10} {item['item_type']:<5} {item['address']:<15} "
                      f"{item['modbus_function']:<10} {item['description'][:50]}")
            
            print(f"\n총 {len(items)}개 항목")
            db_manager.disconnect()
        return
    
    # PRG 파일 파싱 및 저장
    prg_file = sys.argv[1]
    plc_device_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    if not os.path.exists(prg_file):
        print(f"오류: 파일을 찾을 수 없습니다 - {prg_file}")
        return
    
    print(f"PRG 파일 파싱 시작: {prg_file}")
    
    # PRG 파싱
    parser = PRGParser()
    data_items = parser.parse_prg_file(prg_file)
    
    if not data_items:
        print("파싱된 데이터 항목이 없습니다.")
        return
    
    print(f"파싱 완료: {len(data_items)}개 데이터 항목 발견")
    
    # 데이터베이스에 저장
    db_manager = MariaDBManager()
    if db_manager.connect():
        if db_manager.save_parsed_items(data_items, plc_device_id):
            print("데이터베이스 저장 완료!")
            
            # 저장된 항목 요약 출력
            print("\n=== 파싱된 데이터 항목 요약 ===")
            type_counts = {}
            for item in data_items:
                item_type = item['item_type']
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            for item_type, count in type_counts.items():
                print(f"{item_type} 타입: {count}개")
        
        db_manager.disconnect()
    
    print(f"\n저장된 항목 조회:")
    print(f"  python prg_parser_to_db_mariadb.py --list {plc_device_id}")

if __name__ == "__main__":
    main()
