#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC에서 실시간으로 데이터를 수집하여 데이터베이스에 저장하는 프로그램
"""

import time
import threading
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import socket
import struct
from pymodbus.client.sync import ModbusTcpClient

class PLCDataCollector:
    """PLC 데이터 수집기 클래스"""
    
    def __init__(self, db_path: str = None):
        # 기본 데이터베이스 경로 설정
        if db_path is None:
            # 현재 디렉토리와 상위 디렉토리에서 데이터베이스 파일 찾기
            import os
            possible_paths = [
                'plc_data.db',
                'data/hoseosucdb.sql',  # 프로젝트에 있는 SQL 파일
                '../data/hoseosucdb.sql',
                '../../data/hoseosucdb.sql'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    if path.endswith('.sql'):
                        # SQL 파일이면 SQLite 데이터베이스로 변환
                        db_path = path.replace('.sql', '.db')
                        self._convert_sql_to_sqlite(path, db_path)
                    else:
                        db_path = path
                    break
            
            if db_path is None:
                db_path = 'plc_data.db'
        
        self.db_path = db_path
        self.running = False
        self.collection_thread = None
        self.collection_interval = 1000  # 밀리초
        self.plc_clients = {}  # PLC별 클라이언트 저장
        
        # 데이터베이스 초기화
        self._init_database()
    
    def _convert_sql_to_sqlite(self, sql_file_path: str, db_path: str):
        """SQL 파일을 SQLite 데이터베이스로 변환"""
        try:
            import os
            if os.path.exists(db_path):
                print(f"데이터베이스 파일이 이미 존재합니다: {db_path}")
                return
            
            print(f"SQL 파일을 SQLite 데이터베이스로 변환 중: {sql_file_path} -> {db_path}")
            
            # SQL 파일 읽기
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # SQLite 데이터베이스 생성
            with sqlite3.connect(db_path) as conn:
                # SQL 문을 개별적으로 실행
                sql_statements = sql_content.split(';')
                for statement in sql_statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            conn.execute(statement)
                        except Exception as e:
                            print(f"SQL 실행 오류 (무시됨): {e}")
                            continue
                
                conn.commit()
                print(f"데이터베이스 변환 완료: {db_path}")
                
        except Exception as e:
            print(f"SQL 변환 오류: {e}")
    
    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 테이블 확인
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                print(f"기존 테이블: {existing_tables}")
                
                # plc_devices 테이블이 없으면 생성
                if 'plc_devices' not in existing_tables:
                    cursor.execute('''
                        CREATE TABLE plc_devices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            ip_address TEXT NOT NULL,
                            port INTEGER DEFAULT 502,
                            protocol TEXT DEFAULT 'modbus',
                            description TEXT,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    print("plc_devices 테이블 생성됨")
                
                # plc_data_items 테이블이 없으면 생성
                if 'plc_data_items' not in existing_tables:
                    cursor.execute('''
                        CREATE TABLE plc_data_items (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            plc_device_id INTEGER NOT NULL,
                            item_name TEXT NOT NULL,
                            item_type TEXT NOT NULL,
                            address TEXT NOT NULL,
                            modbus_address INTEGER,
                            modbus_function TEXT DEFAULT '03',
                            description TEXT,
                            unit TEXT,
                            min_value REAL,
                            max_value REAL,
                            is_active BOOLEAN DEFAULT TRUE,
                            line_number INTEGER,
                            source_line TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (plc_device_id) REFERENCES plc_devices (id)
                        )
                    ''')
                    print("plc_data_items 테이블 생성됨")
                
                # plc_real_time_data 테이블이 없으면 생성
                if 'plc_real_time_data' not in existing_tables:
                    cursor.execute('''
                        CREATE TABLE plc_real_time_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            data_item_id INTEGER NOT NULL,
                            value REAL,
                            quality TEXT DEFAULT 'good',
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (data_item_id) REFERENCES plc_data_items (id)
                        )
                    ''')
                    print("plc_real_time_data 테이블 생성됨")
                
                # 인덱스 생성 (이미 존재하면 무시됨)
                try:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_plc_data_items_device ON plc_data_items(plc_device_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_plc_data_items_active ON plc_data_items(is_active)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_real_time_data_item ON plc_real_time_data(data_item_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_real_time_data_timestamp ON plc_real_time_data(timestamp)')
                except Exception as e:
                    print(f"인덱스 생성 오류 (무시됨): {e}")
                
                conn.commit()
                print("데이터베이스 초기화 완료")
                
        except Exception as e:
            print(f"데이터베이스 초기화 오류: {e}")
            print(f"데이터베이스 경로: {self.db_path}")
            print(f"현재 작업 디렉토리: {os.getcwd()}")
    
    def test_database_connection(self):
        """데이터베이스 연결 및 테이블 구조 테스트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"\n=== 데이터베이스 연결 테스트 ===")
                print(f"데이터베이스 경로: {self.db_path}")
                print(f"테이블 목록: {[table[0] for table in tables]}")
                
                # 각 테이블의 구조 확인
                for table in tables:
                    table_name = table[0]
                    print(f"\n--- {table_name} 테이블 구조 ---")
                    try:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor.fetchall()
                        for col in columns:
                            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PK' if col[5] else ''}")
                        
                        # 레코드 수 확인
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        print(f"  레코드 수: {count}")
                        
                    except Exception as e:
                        print(f"  테이블 구조 확인 오류: {e}")
                
                return True
                
        except Exception as e:
            print(f"데이터베이스 연결 테스트 오류: {e}")
            return False
    
    def create_sample_data(self):
        """테스트용 샘플 데이터 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # PLC 장치 샘플 데이터
                cursor.execute('''
                    INSERT OR IGNORE INTO plc_devices (id, name, ip_address, port, protocol, description)
                    VALUES (1, 'PLC_001', '192.168.1.100', 502, 'modbus', '테스트 PLC 장치 1')
                ''')
                
                cursor.execute('''
                    INSERT OR IGNORE INTO plc_devices (id, name, ip_address, port, protocol, description)
                    VALUES (2, 'PLC_002', '192.168.1.101', 502, 'modbus', '테스트 PLC 장치 2')
                ''')
                
                # PLC 데이터 항목 샘플 데이터
                sample_items = [
                    (1, 'D0000', 'D', 'D0000', 0, '03', '데이터 레지스터 D0'),
                    (1, 'D0001', 'D', 'D0001', 1, '03', '데이터 레지스터 D1'),
                    (1, 'M0000', 'M', 'M0000', 0, '01', '내부 릴레이 M0'),
                    (1, 'M0001', 'M', 'M0001', 1, '01', '내부 릴레이 M1'),
                    (2, 'D0000', 'D', 'D0000', 0, '03', '데이터 레지스터 D0'),
                    (2, 'Y0000', 'Y', 'Y0000', 0, '01', '출력 Y0'),
                ]
                
                for item in sample_items:
                    cursor.execute('''
                        INSERT OR IGNORE INTO plc_data_items 
                        (plc_device_id, item_name, item_type, address, modbus_address, modbus_function, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', item)
                
                # 실시간 데이터 샘플
                cursor.execute('''
                    INSERT OR IGNORE INTO plc_real_time_data (data_item_id, value, quality)
                    SELECT id, RANDOM() % 100, 'good' FROM plc_data_items
                ''')
                
                conn.commit()
                print("샘플 데이터 생성 완료")
                
        except Exception as e:
            print(f"샘플 데이터 생성 오류: {e}")
    
    def start_collection(self, plc_device_id: int = None):
        """데이터 수집 시작 (plc_device_id가 None이면 모든 PLC 장치의 데이터 수집)"""
        if self.running:
            print("데이터 수집이 이미 실행 중입니다.")
            return
        
        self.running = True
        
        if plc_device_id is not None:
            print(f"PLC 데이터 수집 시작 (장치 ID: {plc_device_id})")
        else:
            print("PLC 데이터 수집 시작 (모든 장치)")
        
        self.collection_thread = threading.Thread(
            target=self._collection_worker,
            args=(plc_device_id,),
            daemon=True
        )
        self.collection_thread.start()
    
    def stop_collection(self):
        """데이터 수집 중지"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        print("PLC 데이터 수집 중지")
    
    def _collection_worker(self, plc_device_id: int):
        """데이터 수집 워커 스레드"""
        while self.running:
            try:
                # 데이터 수집 실행
                self._collect_plc_data(plc_device_id)
                
                # 대기
                time.sleep(self.collection_interval / 1000.0)
                
            except Exception as e:
                print(f"데이터 수집 오류: {e}")
                time.sleep(5)  # 오류 시 5초 대기
    
    def _collect_plc_data(self, plc_device_id: int = None):
        """PLC에서 데이터 수집 (plc_id 상관없이 모든 항목 수집)"""
        try:
            # 데이터 항목 조회 (plc_id 상관없이)
            data_items = self._get_data_items(plc_device_id)
            if not data_items:
                print(f"데이터 항목이 없습니다.")
                return
            
            # PLC 장치별로 그룹화
            plc_groups = {}
            for item in data_items:
                plc_id = item['plc_device_id']
                if plc_id not in plc_groups:
                    plc_groups[plc_id] = []
                plc_groups[plc_id].append(item)
            
            # 각 PLC 장치별로 데이터 수집
            all_collected_data = []
            
            for plc_id, items in plc_groups.items():
                try:
                    # PLC 장치 정보 조회
                    plc_info = self._get_plc_device_info(plc_id)
                    if not plc_info:
                        print(f"PLC 장치 정보를 찾을 수 없습니다: {plc_id}")
                        continue
                    
                    # PLC 연결
                    plc_client = self._get_plc_client(plc_info)
                    if not plc_client:
                        print(f"PLC 연결 실패: {plc_info['ip_address']}")
                        continue
                    
                    # 해당 PLC의 데이터 수집
                    for item in items:
                        try:
                            value = self._read_plc_value(plc_client, item)
                            if value is not None:
                                all_collected_data.append({
                                    'data_item_id': item['id'],
                                    'value': value,
                                    'quality': 'good'
                                })
                        except Exception as e:
                            print(f"데이터 읽기 오류 ({item['item_name']}): {e}")
                            # 오류 시 bad 품질로 저장
                            all_collected_data.append({
                                'data_item_id': item['id'],
                                'value': 0,
                                'quality': 'bad'
                            })
                
                except Exception as e:
                    print(f"PLC {plc_id} 데이터 수집 오류: {e}")
                    continue
            
            # 데이터베이스에 저장
            if all_collected_data:
                self._save_real_time_data(all_collected_data)
                print(f"{len(all_collected_data)}개 데이터 항목 수집 완료 (PLC 장치: {len(plc_groups)}개)")
            
        except Exception as e:
            print(f"PLC 데이터 수집 오류: {e}")
    
    def _get_plc_device_info(self, plc_device_id: int) -> Optional[Dict]:
        """PLC 장치 정보 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, ip_address, port, protocol, description
                    FROM plc_devices 
                    WHERE id = ?
                ''', (plc_device_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'ip_address': row[2],
                        'port': row[3],
                        'protocol': row[4],
                        'description': row[5]
                    }
                return None
                
        except Exception as e:
            print(f"PLC 장치 정보 조회 오류: {e}")
            return None
    
    def _get_data_items(self, plc_device_id: int = None) -> List[Dict]:
        """데이터 항목 조회 (plc_id 상관없이 모든 항목 조회)"""
        try:
            print("self.db_path : ",self.db_path)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, plc_device_id, item_name, item_type, address, modbus_address, 
                            modbus_function, description
                    FROM plc_data_items 
                    WHERE is_active = TRUE
                    ORDER BY plc_device_id, item_type, modbus_address
                ''')
            
                rows = cursor.fetchall()
                print(" rows :",rows)
                return [
                    {
                        'id': row[0],
                        'plc_device_id': row[1],
                        'item_name': row[2],
                        'item_type': row[3],
                        'address': row[4],
                        'modbus_address': row[5],
                        'modbus_function': row[6],
                        'description': row[7]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            print(f"데이터 항목 조회 오류: {e}")
            return []
    
    def _get_plc_client(self, plc_info: Dict) -> Optional[ModbusTcpClient]:
        """PLC 클라이언트 생성 및 연결"""
        try:
            # 기존 클라이언트 확인
            client_key = f"{plc_info['ip_address']}:{plc_info['port']}"
            
            if client_key in self.plc_clients:
                client = self.plc_clients[client_key]
                # 연결 상태 확인
                try:
                    if client.is_socket_open():
                        return client
                except:
                    pass
            
            # 새 클라이언트 생성
            client = ModbusTcpClient(plc_info['ip_address'], port=plc_info['port'])
            
            if client.connect():
                self.plc_clients[client_key] = client
                print(f"PLC 연결 성공: {plc_info['ip_address']}:{plc_info['port']}")
                return client
            else:
                print(f"PLC 연결 실패: {plc_info['ip_address']}:{plc_info['port']}")
                return None
                
        except Exception as e:
            print(f"PLC 클라이언트 생성 오류: {e}")
            return None
    
    def _read_plc_value(self, client: ModbusTcpClient, item: Dict) -> Optional[float]:
        """PLC에서 특정 데이터 읽기"""
        try:
            modbus_function = item['modbus_function']
            address = item['modbus_address']
            
            if modbus_function == '01':  # Read Coils
                result = client.read_coils(address=address, count=1, unit=1)
                if result.isError():
                    raise Exception(f"Coil 읽기 오류: {result}")
                return float(result.bits[0])
                
            elif modbus_function == '02':  # Read Discrete Inputs
                result = client.read_discrete_inputs(address=address, count=1, unit=1)
                if result.isError():
                    raise Exception(f"Discrete Input 읽기 오류: {result}")
                return float(result.bits[0])
                
            elif modbus_function == '03':  # Read Holding Registers
                result = client.read_holding_registers(address=address, count=1, unit=1)
                if result.isError():
                    raise Exception(f"Holding Register 읽기 오류: {result}")
                return float(result.registers[0])
                
            elif modbus_function == '04':  # Read Input Registers
                result = client.read_input_registers(address=address, count=1, unit=1)
                if result.isError():
                    raise Exception(f"Input Register 읽기 오류: {result}")
                return float(result.registers[0])
                
            else:
                raise Exception(f"지원하지 않는 Modbus 함수: {modbus_function}")
                
        except Exception as e:
            print(f"PLC 값 읽기 오류 ({item['item_name']}): {e}")
            return None
    
    def _save_real_time_data(self, data_list: List[Dict]):
        """실시간 데이터를 데이터베이스에 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 실시간 데이터 삭제 (최신 데이터만 유지)
                for data in data_list:
                    cursor.execute('''
                        DELETE FROM plc_real_time_data 
                        WHERE data_item_id = ?
                    ''', (data['data_item_id'],))
                
                # 새 데이터 삽입
                for data in data_list:
                    cursor.execute('''
                        INSERT INTO plc_real_time_data (data_item_id, value, quality)
                        VALUES (?, ?, ?)
                    ''', (data['data_item_id'], data['value'], data['quality']))
                
                conn.commit()
                
        except Exception as e:
            print(f"실시간 데이터 저장 오류: {e}")
    
    def get_real_time_data(self, plc_device_id: int = None) -> List[Dict]:
        """실시간 데이터 조회 (plc_device_id가 None이면 모든 PLC 장치의 데이터 조회)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if plc_device_id is not None:
                    # 특정 PLC 장치의 데이터만 조회
                    cursor.execute('''
                        SELECT 
                            di.plc_device_id, di.item_name, di.item_type, di.description,
                            rtd.value, rtd.quality, rtd.timestamp
                        FROM plc_real_time_data rtd
                        JOIN plc_data_items di ON rtd.data_item_id = di.id
                        WHERE di.plc_device_id = ?
                        ORDER BY di.item_type, di.modbus_address
                    ''', (plc_device_id,))
                else:
                    # 모든 PLC 장치의 데이터 조회
                    cursor.execute('''
                        SELECT 
                            di.plc_device_id, di.item_name, di.item_type, di.description,
                            rtd.value, rtd.quality, rtd.timestamp
                        FROM plc_real_time_data rtd
                        JOIN plc_data_items di ON rtd.data_item_id = di.id
                        ORDER BY di.plc_device_id, di.item_type, di.modbus_address
                    ''')
                
                rows = cursor.fetchall()
                return [
                    {
                        'plc_device_id': row[0],
                        'item_name': row[1],
                        'item_type': row[2],
                        'description': row[3],
                        'value': row[4],
                        'quality': row[5],
                        'timestamp': row[6]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            print(f"실시간 데이터 조회 오류: {e}")
            return []

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PLC 실시간 데이터 수집기')
    parser.add_argument('--start', action='store_true', help='데이터 수집 시작')
    parser.add_argument('--stop', action='store_true', help='데이터 수집 중지')
    parser.add_argument('--status', action='store_true', help='현재 상태 및 데이터 조회')
    parser.add_argument('--plc-id', type=int, help='특정 PLC 장치 ID (지정하지 않으면 모든 장치)')
    parser.add_argument('--interval', type=int, default=1000, help='수집 주기 (밀리초, 기본값: 1000)')
    parser.add_argument('--test-db', action='store_true', help='데이터베이스 연결 및 테이블 구조 테스트')
    parser.add_argument('--create-sample', action='store_true', help='테스트용 샘플 데이터 생성')
    
    args = parser.parse_args()
    
    collector = PLCDataCollector()
    collector.collection_interval = args.interval
    
    if args.test_db:
        print("데이터베이스 연결 테스트 중...")
        collector.test_database_connection()
    
    elif args.create_sample:
        print("샘플 데이터 생성 중...")
        collector.create_sample_data()
    
    elif args.start:
        if args.plc_id:
            print(f"PLC {args.plc_id} 데이터 수집을 시작합니다...")
        else:
            print("모든 PLC 장치의 데이터 수집을 시작합니다...")
        
        collector.start_collection(args.plc_id)
        
        try:
            # 메인 스레드에서 대기
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
            collector.stop_collection()
    
    elif args.stop:
        collector.stop_collection()
    
    elif args.status:
        if args.plc_id:
            print(f"=== PLC 실시간 데이터 상태 (장치 ID: {args.plc_id}) ===")
        else:
            print("=== 모든 PLC 장치 실시간 데이터 상태 ===")
        
        data = collector.get_real_time_data(args.plc_id)
        
        if data:
            if args.plc_id:
                print(f"{'항목명':<10} {'타입':<5} {'값':<10} {'품질':<8} {'시간'}")
                print("-" * 60)
            else:
                print(f"{'PLC ID':<8} {'항목명':<10} {'타입':<5} {'값':<10} {'품질':<8} {'시간'}")
                print("-" * 70)
            
            for item in data:
                if args.plc_id:
                    print(f"{item['item_name']:<10} {item['item_type']:<5} "
                          f"{item['value']:<10.2f} {item['quality']:<8} {item['timestamp']}")
                else:
                    print(f"{item['plc_device_id']:<8} {item['item_name']:<10} {item['item_type']:<5} "
                          f"{item['value']:<10.2f} {item['quality']:<8} {item['timestamp']}")
            
            print(f"\n총 {len(data)}개 데이터 항목")
        else:
            print("수집된 데이터가 없습니다.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

