#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC에서 실시간으로 데이터를 수집하여 MariaDB에 저장하는 프로그램
"""

import time
import threading
from typing import List, Dict, Optional
from datetime import datetime
import socket
import struct
from pymodbus.client.sync import ModbusTcpClient
from database_config import DatabaseConfig
import pymysql

class PLCDataCollector:
    """PLC 데이터 수집기 클래스 (MariaDB)"""
    
    def __init__(self):
        self.running = False
        self.collection_thread = None
        self.collection_interval = 1000  # 밀리초
        self.plc_clients = {}  # PLC별 클라이언트 저장
        self.connection = None
    
    def connect_database(self) -> bool:
        """MariaDB 연결"""
        try:
            self.connection = DatabaseConfig.create_connection()
            return self.connection is not None
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False
    
    def disconnect_database(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def start_collection(self, plc_device_id: int = 1):
        """데이터 수집 시작"""
        if self.running:
            print("데이터 수집이 이미 실행 중입니다.")
            return
        
        # 데이터베이스 연결
        if not self.connect_database():
            print("데이터베이스 연결 실패")
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collection_worker,
            args=(plc_device_id,),
            daemon=True
        )
        self.collection_thread.start()
        print(f"PLC 데이터 수집 시작 (장치 ID: {plc_device_id})")
    
    def stop_collection(self):
        """데이터 수집 중지"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        self.disconnect_database()
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
    
    def _collect_plc_data(self, plc_device_id: int):
        """PLC에서 데이터 수집"""
        try:
            # PLC 장치 정보 조회
            plc_info = self._get_plc_device_info(plc_device_id)
            if not plc_info:
                print(f"PLC 장치 정보를 찾을 수 없습니다: {plc_device_id}")
                return
            
            # 데이터 항목 조회
            data_items = self._get_data_items(plc_device_id)
            if not data_items:
                print(f"데이터 항목이 없습니다: {plc_device_id}")
                return
            
            # PLC 연결
            plc_client = self._get_plc_client(plc_info)
            if not plc_client:
                print(f"PLC 연결 실패: {plc_info['ip_address']}")
                return
            
            # 데이터 수집 및 저장
            collected_data = []
            for item in data_items:
                try:
                    value = self._read_plc_value(plc_client, item)
                    if value is not None:
                        collected_data.append({
                            'data_item_id': item['id'],
                            'value': value,
                            'quality': 'good'
                        })
                except Exception as e:
                    print(f"데이터 읽기 오류 ({item['item_name']}): {e}")
                    # 오류 시 bad 품질로 저장
                    collected_data.append({
                        'data_item_id': item['id'],
                        'value': 0,
                        'quality': 'bad'
                    })
            
            # 데이터베이스에 저장
            if collected_data:
                self._save_real_time_data(collected_data)
                print(f"{len(collected_data)}개 데이터 항목 수집 완료")
            
        except Exception as e:
            print(f"PLC 데이터 수집 오류: {e}")
    
    def _get_plc_device_info(self, plc_device_id: int) -> Optional[Dict]:
        """PLC 장치 정보 조회"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute('''
                    SELECT id, name, ip_address, port, protocol, description
                    FROM plc_devices 
                    WHERE id = %s
                ''', (plc_device_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            print(f"PLC 장치 정보 조회 오류: {e}")
            return None
    
    def _get_data_items(self, plc_device_id: int) -> List[Dict]:
        """데이터 항목 조회"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute('''
                    SELECT id, item_name, item_type, address, modbus_address, 
                           modbus_function, description
                    FROM plc_data_items 
                    WHERE plc_device_id = %s AND is_active = TRUE
                    ORDER BY item_type, modbus_address
                ''', (plc_device_id,))
                
                return cursor.fetchall()
                
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
            with self.connection.cursor() as cursor:
                # 기존 실시간 데이터 삭제 (최신 데이터만 유지)
                for data in data_list:
                    cursor.execute('''
                        DELETE FROM plc_real_time_data 
                        WHERE data_item_id = %s
                    ''', (data['data_item_id'],))
                
                # 새 데이터 삽입
                for data in data_list:
                    cursor.execute('''
                        INSERT INTO plc_real_time_data (data_item_id, value, quality)
                        VALUES (%s, %s, %s)
                    ''', (data['data_item_id'], data['value'], data['quality']))
                
                self.connection.commit()
                
        except Exception as e:
            print(f"실시간 데이터 저장 오류: {e}")
            if self.connection:
                self.connection.rollback()
    
    def get_real_time_data(self, plc_device_id: int = 1) -> List[Dict]:
        """실시간 데이터 조회"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute('''
                    SELECT 
                        di.item_name, di.item_type, di.description,
                        rtd.value, rtd.quality, rtd.timestamp
                    FROM plc_real_time_data rtd
                    JOIN plc_data_items di ON rtd.data_item_id = di.id
                    WHERE di.plc_device_id = %s
                    ORDER BY di.item_type, di.modbus_address
                ''', (plc_device_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"실시간 데이터 조회 오류: {e}")
            return []

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PLC 실시간 데이터 수집기 (MariaDB)')
    parser.add_argument('--start', action='store_true', help='데이터 수집 시작')
    parser.add_argument('--stop', action='store_true', help='데이터 수집 중지')
    parser.add_argument('--status', action='store_true', help='현재 상태 및 데이터 조회')
    parser.add_argument('--plc-id', type=int, default=1, help='PLC 장치 ID (기본값: 1)')
    parser.add_argument('--interval', type=int, default=1000, help='수집 주기 (밀리초, 기본값: 1000)')
    
    args = parser.parse_args()
    
    collector = PLCDataCollector()
    collector.collection_interval = args.interval
    
    if args.start:
        print("PLC 데이터 수집을 시작합니다...")
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
        print(f"=== PLC 실시간 데이터 상태 (장치 ID: {args.plc_id}) ===")
        
        if collector.connect_database():
            data = collector.get_real_time_data(args.plc_id)
            
            if data:
                print(f"{'항목명':<10} {'타입':<5} {'값':<10} {'품질':<8} {'시간'}")
                print("-" * 60)
                
                for item in data:
                    print(f"{item['item_name']:<10} {item['item_type']:<5} "
                          f"{item['value']:<10.2f} {item['quality']:<8} {item['timestamp']}")
                
                print(f"\n총 {len(data)}개 데이터 항목")
            else:
                print("수집된 데이터가 없습니다.")
            
            collector.disconnect_database()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

