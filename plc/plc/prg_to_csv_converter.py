#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XG5000 PRG 파일을 CSV로 변환하는 프로그램
PRG 파일의 각 라인을 파싱하여 CSV 형식으로 저장합니다.
"""

import csv
import os
import sys
from typing import List, Optional

def detect_encoding(file_path: str) -> str:
    """
    파일의 인코딩을 자동으로 감지하거나 일반적인 인코딩을 시도
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        str: 감지된 인코딩 또는 기본 인코딩
    """
    # 일반적인 인코딩 목록 (한국어 환경에서 자주 사용)
    encodings = ['utf-8', 'cp949', 'euc-kr', 'iso-8859-1', 'latin1', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    
    # 모든 인코딩이 실패하면 기본값 반환
    return 'utf-8'

def read_file_with_encoding(file_path: str, encoding: str = None) -> List[str]:
    """
    지정된 인코딩으로 파일을 읽기
    
    Args:
        file_path (str): 파일 경로
        encoding (str): 인코딩 (None이면 자동 감지)
        
    Returns:
        List[str]: 파일의 라인들
        
    Raises:
        UnicodeDecodeError: 인코딩 문제
        FileNotFoundError: 파일 없음
    """
    if encoding is None:
        encoding = detect_encoding(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.readlines()
    except UnicodeDecodeError:
        # 지정된 인코딩으로 실패하면 다른 인코딩 시도
        alt_encoding = detect_encoding(file_path)
        if alt_encoding != encoding:
            with open(file_path, 'r', encoding=alt_encoding) as f:
                return f.readlines()
        raise

def parse_prg_line(line: str) -> List[str]:
    """
    PRG 파일의 한 라인을 파싱하여 토큰 리스트로 반환
    
    Args:
        line (str): PRG 파일의 한 라인
        
    Returns:
        List[str]: 파싱된 토큰 리스트
    """
    # 빈 라인이나 주석 라인 처리
    line = line.strip()
    if not line or line.startswith('//') or line.startswith(';'):
        return []
    
    # 공백 기준으로 토큰 분리
    tokens = line.split()
    
    # 빈 토큰 제거
    tokens = [token for token in tokens if token]
    
    return tokens

def convert_prg_to_csv(input_file: str, output_file: str, delimiter: str = ',', encoding: str = None) -> bool:
    """
    PRG 파일을 CSV 파일로 변환
    
    Args:
        input_file (str): 입력 PRG 파일 경로
        output_file (str): 출력 CSV 파일 경로
        delimiter (str): CSV 구분자 (기본값: 쉼표)
        encoding (str): 파일 인코딩 (None이면 자동 감지)
        
    Returns:
        bool: 변환 성공 여부
    """
    try:
        # 입력 파일 읽기 (인코딩 자동 감지)
        lines = read_file_with_encoding(input_file, encoding)
        detected_encoding = detect_encoding(input_file)
        print(f"파일 인코딩 감지: {detected_encoding}")
        
        # CSV 파일로 쓰기
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            # 헤더 추가 (선택사항)
            header = ["Line", "Token1", "Token2", "Token3", "Token4", "Token5", "Token6", "Token7", "Token8"]
            writer.writerow(header)
            
            line_number = 1
            for line in lines:
                tokens = parse_prg_line(line)
                if tokens:  # 빈 라인이 아닌 경우만 처리
                    # 라인 번호와 토큰들을 CSV 행으로 작성
                    row = [line_number] + tokens
                    writer.writerow(row)
                line_number += 1
        
        print(f"변환 완료: {input_file} -> {output_file}")
        return True
        
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다 - {input_file}")
        return False
    except UnicodeDecodeError as e:
        print(f"오류: 파일 인코딩 문제 - {input_file}")
        print(f"  상세 오류: {e}")
        print("  해결 방법:")
        print("    1. --encoding 옵션으로 인코딩 지정")
        print("    2. 파일을 UTF-8로 저장 후 재시도")
        return False
    except Exception as e:
        print(f"오류: {e}")
        return False

def convert_prg_to_csv_simple(input_file: str, output_file: str, encoding: str = None) -> bool:
    """
    간단한 버전: 원본 토큰 그대로 CSV로 변환
    
    Args:
        input_file (str): 입력 PRG 파일 경로
        output_file (str): 출력 CSV 파일 경로
        encoding (str): 파일 인코딩 (None이면 자동 감지)
        
    Returns:
        bool: 변환 성공 여부
    """
    try:
        # 입력 파일 읽기 (인코딩 자동 감지)
        lines = read_file_with_encoding(input_file, encoding)
        detected_encoding = detect_encoding(input_file)
        print(f"파일 인코딩 감지: {detected_encoding}")
        
        # CSV 파일로 쓰기
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for line in lines:
                # 공백 기준 토큰 분리
                tokens = line.strip().split()
                if tokens:  # 빈 라인이 아닌 경우만 처리
                    writer.writerow(tokens)
        
        print(f"변환 완료: {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"오류: {e}")
        return False

def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python prg_to_csv_converter.py <input.prg> [output.csv]")
        print("  python prg_to_csv_converter.py --simple <input.prg> [output.csv]")
        print("\n옵션:")
        print("  --simple: 간단한 변환 모드 (원본 토큰 그대로)")
        print("  --delimiter=<구분자>: CSV 구분자 지정 (기본값: 쉼표)")
        print("  --encoding=<인코딩>: 파일 인코딩 지정 (예: cp949, euc-kr)")
        return
    
    # 명령행 인수 파싱
    simple_mode = False
    delimiter = ','
    encoding = None
    input_file = None
    output_file = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--simple':
            simple_mode = True
        elif arg.startswith('--delimiter='):
            delimiter = arg.split('=', 1)[1]
        elif arg.startswith('--encoding='):
            encoding = arg.split('=', 1)[1]
        elif arg.startswith('-'):
            print(f"알 수 없는 옵션: {arg}")
            return
        else:
            if input_file is None:
                input_file = arg
            elif output_file is None:
                output_file = arg
            else:
                print(f"너무 많은 인수: {arg}")
                return
        i += 1
    
    # 입력 파일 확인
    if input_file is None:
        print("오류: 입력 파일을 지정해야 합니다.")
        return
    
    # 출력 파일명이 지정되지 않은 경우 자동 생성
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.csv"
    
    # 파일 확장자 확인
    if not input_file.lower().endswith('.prg'):
        print("경고: 입력 파일이 .prg 확장자가 아닙니다.")
    
    # 변환 실행
    if simple_mode:
        success = convert_prg_to_csv_simple(input_file, output_file, encoding)
    else:
        success = convert_prg_to_csv(input_file, output_file, delimiter, encoding)
    
    if success:
        print(f"변환된 파일: {output_file}")
        # 파일 크기 정보 출력
        try:
            input_size = os.path.getsize(input_file)
            output_size = os.path.getsize(output_file)
            print(f"입력 파일 크기: {input_size:,} bytes")
            print(f"출력 파일 크기: {output_size:,} bytes")
        except:
            pass

if __name__ == "__main__":
    main()
