#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XG5000 PLC 클라이언트 - 배치 통신 및 MariaDB 연동 (상세 로깅)
"""

import socket
import struct
import time
import threading
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from database_config import DatabaseConfig
import pymysql

# PLC 연결 설정
PLC_IP = "192.168.1.2"
PLC_PORT = 2004  # XGT Dedicated

class XG5000Logger:
    """XG5000 PLC 클라이언트 전용 로거 클래스"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._setup_logging()
    
    def _setup_logging(self):
        """로깅 시스템 설정"""
        # 로그 디렉토리 생성
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 로그 파일명 (날짜별)
        current_date = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"xg5000_client_{current_date}.log")
        
        # 로거 설정
        self.logger = logging.getLogger('XG5000Client')
        self.logger.setLevel(logging.DEBUG)
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 파일 핸들러 (상세 로그)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # 콘솔 핸들러 (중요 로그만)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 로그 시작 메시지
        self.logger.info("=" * 60)
        self.logger.info("XG5000 PLC 클라이언트 로깅 시작")
        self.logger.info(f"PLC IP: {PLC_IP}, Port: {PLC_PORT}")
        self.logger.info(f"로그 파일: {log_file}")
        self.logger.info("=" * 60)
    
    def log_plc_connection(self, ip: str, port: int, success: bool, details: str = ""):
        """PLC 연결 로그"""
        if success:
            self.logger.info(f"PLC 연결 성공: {ip}:{port}")
            if details:
                self.logger.debug(f"연결 상세: {details}")
        else:
            self.logger.error(f"PLC 연결 실패: {ip}:{port}")
            if details:
                self.logger.error(f"실패 상세: {details}")
    
    def log_xgt_communication(self, direction: str, address: str, count: int, data: bytes, success: bool, response_time: float = None):
        """XGT 통신 로그"""
        if direction == "SEND":
            self.logger.info(f"XGT 전송: {address} x{count} ({len(data)} bytes)")
            self.logger.debug(f"전송 데이터: {' '.join(f'{b:02X}' for b in data)}")
        elif direction == "RECV":
            if success:
                self.logger.info(f"XGT 수신: {address} x{count} ({len(data)} bytes)")
                if response_time:
                    self.logger.info(f"응답 시간: {response_time:.3f}초")
                self.logger.debug(f"수신 데이터: {' '.join(f'{b:02X}' for b in data)}")
            else:
                self.logger.error(f"XGT 수신 실패: {address} x{count}")
                self.logger.debug(f"실패 데이터: {' '.join(f'{b:02X}' for b in data)}")
    
    def log_batch_processing(self, batch_info: Dict):
        """배치 처리 로그"""
        self.logger.info(f"배치 처리: {batch_info['type']} 타입, {batch_info['batch_count']}개 배치")
        for i, batch in enumerate(batch_info['batches']):
            addresses = [item['modbus_address'] for item in batch]
            self.logger.debug(f"  배치 {i+1}: {addresses} ({len(batch)}개 항목)")
    
    def log_data_collection(self, item_count: int, success_count: int, error_count: int, collection_time: float):
        """데이터 수집 로그"""
        self.logger.info(f"데이터 수집 완료: 총 {item_count}개, 성공 {success_count}개, 실패 {error_count}개")
        self.logger.info(f"수집 시간: {collection_time:.3f}초")
        if error_count > 0:
            self.logger.warning(f"수집 실패 항목: {error_count}개")
    
    def log_database_operation(self, operation: str, table: str, record_count: int, success: bool, details: str = ""):
        """데이터베이스 작업 로그"""
        if success:
            self.logger.info(f"DB {operation}: {table} 테이블, {record_count}개 레코드")
            if details:
                self.logger.debug(f"작업 상세: {details}")
        else:
            self.logger.error(f"DB {operation} 실패: {table} 테이블")
            if details:
                self.logger.error(f"실패 상세: {details}")
    
    def log_error(self, error_type: str, error_msg: str, stack_trace: str = ""):
        """오류 로그"""
        self.logger.error(f"{error_type}: {error_msg}")
        if stack_trace:
            self.logger.debug(f"스택 트레이스: {stack_trace}")
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """성능 로그"""
        self.logger.info(f"성능 측정: {operation} - {duration:.3f}초")
        if details:
            self.logger.debug(f"성능 상세: {details}")

class XG5000Client:
    """XG5000 PLC 클라이언트 클래스"""
    
    def __init__(self):
        self.connection = None
        self.running = False
        self.collection_thread = None
        self.collection_interval = 1000  # 밀리초
        self.logger = XG5000Logger()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_collection_time': 0.0,
            'collection_count': 0
        }
        
    def connect_database(self) -> bool:
        """MariaDB 연결"""
        start_time = time.time()
        try:
            self.connection = DatabaseConfig.create_connection()
            success = self.connection is not None
            duration = time.time() - start_time
            
            if success:
                self.logger.log_database_operation("연결", "MariaDB", 0, True, f"연결 시간: {duration:.3f}초")
            else:
                self.logger.log_database_operation("연결", "MariaDB", 0, False, "연결 실패")
            
            return success
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error("데이터베이스 연결", str(e))
            self.logger.log_database_operation("연결", "MariaDB", 0, False, f"연결 시간: {duration:.3f}초, 오류: {e}")
            return False
    
    def disconnect_database(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.log_database_operation("연결 해제", "MariaDB", 0, True)
    
    def get_plc_data_items(self, plc_device_id: int = 1) -> List[Dict]:
        """PLC 데이터 항목 조회 - is_active가 1인 항목만 조회"""
        start_time = time.time()
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # is_active = 1인 항목만 조회하여 데이터 수집 대상으로 사용
                cursor.execute('''
                    SELECT id, item_name, item_type, address, modbus_address, 
                           modbus_function, description
                    FROM plc_data_items 
                    WHERE plc_device_id = %s AND is_active = 1
                    ORDER BY item_type, modbus_address
                ''', (plc_device_id,))
                
                items = cursor.fetchall()
                duration = time.time() - start_time
                
                self.logger.log_database_operation("조회", "plc_data_items", len(items), True, f"조회 시간: {duration:.3f}초")
                self.logger.log_performance("데이터 항목 조회", duration, f"PLC 장치 ID: {plc_device_id}")
                
                return items
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error("데이터 항목 조회", str(e))
            self.logger.log_database_operation("조회", "plc_data_items", 0, False, f"조회 시간: {duration:.3f}초, 오류: {e}")
            return []
    
    def batch_read_plc_data(self, data_items: List[Dict]) -> List[Dict]:
        """PLC 데이터 항목들을 개별적으로 읽기 (전체 항목이 10개 이하)"""
        start_time = time.time()
        collected_data = []
        success_count = 0
        error_count = 0
        
        self.logger.logger.info(f"데이터 읽기 시작: 총 {len(data_items)}개 항목")
        
        # 각 항목을 개별적으로 읽기
        for item in data_items:
            try:
                item_start_time = time.time()
                value = self._read_single_item_from_plc(item)
                item_duration = time.time() - item_start_time
                
                if value is not None:
                    collected_data.append({
                        'data_item_id': item['id'],
                        'value': float(value),
                        'quality': 'good'
                    })
                    success_count += 1
                    self.logger.logger.debug(f"항목 {item['item_name']} 읽기 성공: {value}, {item_duration:.3f}초")
                else:
                    collected_data.append({
                        'data_item_id': item['id'],
                        'value': 0.0,
                        'quality': 'bad'
                    })
                    error_count += 1
                    self.logger.logger.warning(f"항목 {item['item_name']} 읽기 실패")
                    
            except Exception as e:
                self.logger.log_error("항목 읽기", f"항목 {item.get('item_name', 'unknown')} 처리 오류: {e}")
                collected_data.append({
                    'data_item_id': item['id'],
                    'value': 0.0,
                    'quality': 'bad'
                })
                error_count += 1
        
        total_duration = time.time() - start_time
        self.logger.log_data_collection(len(data_items), success_count, error_count, total_duration)
        self.logger.log_performance("전체 데이터 읽기", total_duration, f"성공: {success_count}, 실패: {error_count}")
        
        return collected_data
    
    def _create_batch_groups(self, items: List[Dict]) -> List[List[Dict]]:
        """연속된 주소들을 배치 그룹으로 생성"""
        if not items:
            return []
        
        # 주소별로 정렬
        sorted_items = sorted(items, key=lambda x: x['modbus_address'])
        
        batches = []
        current_batch = []
        last_address = -1
        
        for item in sorted_items:
            current_address = item['modbus_address']
            
            # 연속된 주소이거나 첫 번째 항목이면 현재 배치에 추가
            if not current_batch or current_address == last_address + 1:
                current_batch.append(item)
                last_address = current_address
            else:
                # 연속되지 않으면 새 배치 시작
                if current_batch:
                    batches.append(current_batch)
                current_batch = [item]
                last_address = current_address
        
        # 마지막 배치 추가
        if current_batch:
            batches.append(current_batch)
        
        self.logger.logger.debug(f"배치 그룹 생성: {len(items)}개 항목 → {len(batches)}개 배치")
        return batches
    
    def _read_single_item_from_plc(self, item: Dict) -> Optional[int]:
        """PLC에서 개별 항목 데이터 읽기"""
        if not item:
            return None
        
        # 항목의 주소와 타입으로 개별 읽기
        address = item.get('modbus_address')
        item_type = item.get('item_type')
        
        if address is None or item_type is None:
            self.logger.log_error("항목 읽기", f"항목 {item.get('item_name', 'unknown')}에 주소 또는 타입 정보가 없습니다")
            return None
        
        # XGT 주소 형식으로 변환
        addr_str = self._convert_to_xgt_address(item_type, address)
        
        try:
            # XGT 통신으로 개별 항목 읽기 (count=1)
            values = xgt_read_dw(addr_str, 1)
            if values and len(values) > 0:
                return values[0]
            else:
                return None
        except Exception as e:
            self.logger.log_error("PLC 항목 읽기", f"{addr_str} 읽기 오류: {e}")
            return None
    
    def _convert_to_xgt_address(self, item_type: str, address: int) -> str:
        """PLC 데이터 타입을 XGT 주소 형식으로 변환"""
        if item_type == 'M':
            return f"%MW{address}"
        elif item_type == 'D':
            return f"%DW{address}"
        elif item_type == 'Y':
            return f"%QW{address}"
        elif item_type == 'X':
            return f"%IW{address}"
        elif item_type == 'T':
            return f"%TW{address}"
        elif item_type == 'C':
            return f"%CW{address}"
        else:
            return f"%DW{address}"  # 기본값
    
    def save_real_time_data(self, data_list: List[Dict]):
        """실시간 데이터를 데이터베이스에 저장"""
        if not data_list:
            return
        
        start_time = time.time()
        try:
            with self.connection.cursor() as cursor:
                # 기존 실시간 데이터 삭제 (최신 데이터만 유지)
                delete_count = 0
                for data in data_list:
                    cursor.execute('''
                        DELETE FROM plc_real_time_data 
                        WHERE data_item_id = %s
                    ''', (data['data_item_id'],))
                    delete_count += cursor.rowcount
                
                # 새 데이터 삽입
                insert_count = 0
                for data in data_list:
                    cursor.execute('''
                        INSERT INTO plc_real_time_data (data_item_id, value, quality)
                        VALUES (%s, %s, %s)
                    ''', (data['data_item_id'], data['value'], data['quality']))
                    insert_count += 1
                
                self.connection.commit()
                duration = time.time() - start_time
                
                self.logger.log_database_operation("저장", "plc_real_time_data", insert_count, True, 
                                                 f"삭제: {delete_count}개, 삽입: {insert_count}개, 시간: {duration:.3f}초")
                self.logger.log_performance("실시간 데이터 저장", duration, f"삭제: {delete_count}, 삽입: {insert_count}")
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_error("실시간 데이터 저장", str(e))
            self.logger.log_database_operation("저장", "plc_real_time_data", 0, False, f"저장 시간: {duration:.3f}초, 오류: {e}")
            if self.connection:
                self.connection.rollback()
    
    def start_data_collection(self, plc_device_id: int = 1):
        """데이터 수집 시작"""
        if self.running:
            self.logger.logger.warning("데이터 수집이 이미 실행 중입니다.")
            return
        
        # 데이터베이스 연결
        if not self.connect_database():
            self.logger.logger.error("데이터베이스 연결 실패")
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collection_worker,
            args=(plc_device_id,),
            daemon=True
        )
        self.collection_thread.start()
        
        self.logger.logger.info(f"XG5000 PLC 데이터 수집 시작 (장치 ID: {plc_device_id}, 주기: {self.collection_interval}ms)")
    
    def stop_data_collection(self):
        """데이터 수집 중지"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        self.disconnect_database()
        
        # 통계 출력
        self.logger.logger.info("=" * 50)
        self.logger.logger.info("데이터 수집 통계")
        self.logger.logger.info(f"총 요청 수: {self.stats['total_requests']}")
        self.logger.logger.info(f"성공 요청 수: {self.stats['successful_requests']}")
        self.logger.logger.info(f"실패 요청 수: {self.stats['failed_requests']}")
        if self.stats['collection_count'] > 0:
            avg_time = self.stats['total_collection_time'] / self.stats['collection_count']
            self.logger.logger.info(f"평균 수집 시간: {avg_time:.3f}초")
        self.logger.logger.info("=" * 50)
        
        self.logger.logger.info("XG5000 PLC 데이터 수집 중지")
    
    def _collection_worker(self, plc_device_id: int):
        """데이터 수집 워커 스레드"""
        collection_count = 0
        
        while self.running:
            try:
                collection_start_time = time.time()
                collection_count += 1
                
                self.logger.logger.debug(f"데이터 수집 시작 (회차: {collection_count})")
                
                # PLC 데이터 항목 조회
                data_items = self.get_plc_data_items(plc_device_id)
                if not data_items:
                    self.logger.logger.warning(f"데이터 항목이 없습니다: {plc_device_id}")
                    time.sleep(5)
                    continue
                
                # 배치로 PLC 데이터 읽기
                collected_data = self.batch_read_plc_data(data_items)
                
                # 데이터베이스에 저장
                if collected_data:
                    self.save_real_time_data(collected_data)
                
                # 통계 업데이트
                collection_duration = time.time() - collection_start_time
                self.stats['total_collection_time'] += collection_duration
                self.stats['collection_count'] = collection_count
                
                self.logger.logger.debug(f"데이터 수집 완료 (회차: {collection_count}, 시간: {collection_duration:.3f}초)")
                
                # 대기
                time.sleep(self.collection_interval / 1000.0)
                
            except Exception as e:
                self.logger.log_error("데이터 수집", str(e))
                time.sleep(5)  # 오류 시 5초 대기

def bcc_sum(data: bytes) -> int:
    """Application Header의 바이트 합(모듈러 256). BCC 자기 자신은 제외."""
    return sum(data) & 0xFF

def build_read_word(addr_str="%DW4010", count=1, invoke_id=0x0010, slot_base=0x00):
    """
    XGT Dedicated - Individual Read(WORD) 요청 프레임 구성
    addr_str 예: "%DW4010" (D영역 Word), "%MW0"(M Word), "%DB2468"(Byte) 등
    """
    # --- Company Header (10 bytes)
    company = b"LSIS-XGT" + b"\x00\x00"     # 4C 53 49 53 2D 58 47 54 00 00

    # --- Application Header (고정부; BCC 계산 직전까지)
    plc_info   = b"\x00\x00"               # 요청시 don't care
    cpu_info   = b"\xB0"                   # XGB
    src_frame  = b"\x33"                   # Client->Server
    inv_id     = struct.pack("<H", invoke_id)

    # Payload(명령부)는 나중에 만들고 길이를 채웁니다.
    # Length(2B)는 '명령부' 길이 (Command ~ 끝)
    # Position(1B): Base/Slot. PC에서 접속이면 0x00으로 두어도 무방.
    position   = struct.pack("B", slot_base)

    # 임시로 Length=0, BCC=0으로 두고 BCC 계산을 위해 헤더를 구성
    length     = b"\x00\x00"
    app_hdr_wo_bcc = plc_info + cpu_info + src_frame + inv_id + length + position
    bcc = struct.pack("B", bcc_sum(app_hdr_wo_bcc))

    # --- Command/DataType + Data(명령부)
    # Read Request: 0x5400, DataType WORD: 0x0200 (개별)
    cmd      = b"\x54\x00"
    dtype    = b"\x02\x00"                 # WORD
    reserved = b"\x00\x00"                 # Reserved(2)
    block_no = b"\x01\x00"                 # Block = 1
    addr     = addr_str.encode("ascii")    # 예: b"%DW4010"
    var_len  = struct.pack("<H", len(addr))
    cnt      = struct.pack("<H", count)

    payload  = cmd + dtype + reserved + block_no + var_len + addr + cnt
    length   = struct.pack("<H", len(payload))

    # Length 반영 후 BCC 재계산
    app_hdr_wo_bcc = plc_info + cpu_info + src_frame + inv_id + length + position
    bcc = struct.pack("B", bcc_sum(app_hdr_wo_bcc))

    request = company + app_hdr_wo_bcc + bcc + payload
    return request

def parse_read_word_response(resp: bytes):
    """
    0x5500(READ RESP) 개별 WORD 응답 파서
    구조(문서 표 5-7 요약):
      Company(10) | PLC(2) | CPU(1) | Src(1=0x11) | Invoke(2) | Len(2) | Pos(1) | BCC(1)
      Cmd(2=0x5500) | DataType(2=0x0200) | Reserved(2) | Error(2) | VarLen(2) | DataCnt(2) | Data(2*cnt)
    """
    # 헤더 끝 인덱스 계산
    i = 0
    i += 10  # company
    i += 2   # plc info
    i += 1   # cpu info
    i += 1   # source (0x11)
    i += 2   # invoke id
    length = int.from_bytes(resp[i:i+2], "little"); i += 2
    i += 1   # position
    i += 1   # bcc

    cmd = resp[i:i+2]; i += 2
    dtype = resp[i:i+2]; i += 2
    reserved = resp[i:i+2]; i += 2
    err = int.from_bytes(resp[i:i+2], "little"); i += 2
    if err != 0:
        raise RuntimeError(f"PLC Error: 0x{err:04X}")

    var_len = int.from_bytes(resp[i:i+2], "little"); i += 2
    data_cnt = int.from_bytes(resp[i:i+2], "little"); i += 2

    # WORD 데이터: 각 값은 LE 2바이트
    values = []
    for _ in range(data_cnt):
        v = int.from_bytes(resp[i:i+2], "little"); i += 2
        values.append(v)
    return {
        "length_field": length,
        "cmd": cmd,
        "dtype": dtype,
        "count": data_cnt,
        "values": values,
    }

def xgt_read_dw(addr_str="%DW4010", count=1):
    """XGT 통신으로 WORD 데이터 읽기"""
    req = build_read_word(addr_str, count)
    
    # 전송 로그
    print(f"[SEND] {addr_str} x{count}:", " ".join(f"{b:02X}" for b in req))
    
    start_time = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((PLC_IP, PLC_PORT))
            s.sendall(req)
            resp = s.recv(2048)
        
        response_time = time.time() - start_time
        
        # 수신 로그
        print(f"[RECV] {addr_str} x{count}:", " ".join(f"{b:02X}" for b in resp))
        parsed = parse_read_word_response(resp)
        vals = parsed["values"]
        
        # 보기 좋게 10진/16진 동시 출력
        for idx, v in enumerate(vals):
            print(f"{addr_str}+{idx}: dec={v}  hex=0x{v:04X}")
        
        return vals
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"XGT 통신 오류: {e}")
        raise

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='XG5000 PLC 클라이언트 - 배치 통신 및 MariaDB 연동 (상세 로깅)')
    parser.add_argument('--start', action='store_true', help='데이터 수집 시작')
    parser.add_argument('--stop', action='store_true', help='데이터 수집 중지')
    parser.add_argument('--test', action='store_true', help='PLC 연결 테스트')
    parser.add_argument('--plc-id', type=int, default=1, help='PLC 장치 ID (기본값: 1)')
    parser.add_argument('--interval', type=int, default=1000, help='수집 주기 (밀리초, 기본값: 1000)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='로그 레벨 (기본값: INFO)')
    
    args = parser.parse_args()
    
    # 로그 레벨 설정
    if args.log_level == 'DEBUG':
        logging.getLogger('XG5000Client').setLevel(logging.DEBUG)
        print(f"로그 레벨을 {args.log_level}로 설정했습니다.")
    elif args.log_level == 'INFO':
        logging.getLogger('XG5000Client').setLevel(logging.INFO)
        print(f"로그 레벨을 {args.log_level}로 설정했습니다.")
    elif args.log_level == 'WARNING':
        logging.getLogger('XG5000Client').setLevel(logging.WARNING)
        print(f"로그 레벨을 {args.log_level}로 설정했습니다.")
    elif args.log_level == 'ERROR':
        logging.getLogger('XG5000Client').setLevel(logging.ERROR)
        print(f"로그 레벨을 {args.log_level}로 설정했습니다.")
    
    client = XG5000Client()
    client.collection_interval = args.interval
    
    if args.test:
        print("=== PLC 연결 테스트 ===")
        try:
            # 간단한 읽기 테스트
            values = xgt_read_dw("%DW4010", 1)
            print(f"✅ PLC 연결 성공: {values}")
        except Exception as e:
            print(f"❌ PLC 연결 실패: {e}")
    
    elif args.start:
        print("XG5000 PLC 데이터 수집을 시작합니다...")
        client.start_data_collection(args.plc_id)
        
        try:
            # 메인 스레드에서 대기
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
            client.stop_data_collection()
    
    elif args.stop:
        client.stop_data_collection()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
