# XG5000 PLC 클라이언트 - 배치 통신 및 MariaDB 연동

XG5000 PLC와 XGT Dedicated 프로토콜을 사용하여 배치 통신으로 데이터를 읽고, MariaDB에 실시간 데이터를 저장하는 클라이언트입니다.

## 🎯 주요 기능

1. **배치 통신**: 연속된 주소의 데이터를 한 번에 읽어 통신 효율성 향상
2. **MariaDB 연동**: PLC 데이터 항목을 DB에서 조회하고 실시간 데이터를 저장
3. **자동 데이터 수집**: 설정된 주기로 PLC 데이터를 자동 수집
4. **XGT 프로토콜 지원**: LSIS XGT Dedicated 프로토콜 사용

## 🏗️ 시스템 아키텍처

```
MariaDB → PLC 데이터 항목 조회 → 배치 그룹 생성 → XGT 통신 → 실시간 데이터 저장
    ↓              ↓                    ↓              ↓           ↓
plc_data_items  연속 주소 그룹화    %DW100-105    PLC 응답   plc_real_time_data
테이블에서 조회   배치로 읽기        한 번에 6개    데이터     테이블에 저장
```

## 📁 파일 구조

- `xg5000_client.py` - XG5000 PLC 클라이언트 (메인 파일)
- `database_config.py` - MariaDB 연결 설정
- `log_viewer.py` - 로그 파일 뷰어 및 분석 도구
- `XG5000_CLIENT_README.md` - 이 파일

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install pymysql
```

### 2. PLC 연결 설정
```python
# xg5000_client.py에서 PLC IP와 포트 설정
PLC_IP = "192.168.1.2"      # PLC IP 주소
PLC_PORT = 2004             # XGT Dedicated 포트
```

### 3. MariaDB 설정
```bash
# 환경변수 설정
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=dbadmin
export DB_PASSWORD=p#ssw0rd
export DB_NAME=plc_data_system
```

### 4. PLC 연결 테스트
```bash
python xg5000_client.py --test
```

## 📋 상세 사용법

### PLC 연결 테스트
```bash
# PLC 연결 및 간단한 읽기 테스트
python xg5000_client.py --test
```

### 데이터 수집 시작
```bash
# 기본 설정으로 시작 (1초 주기)
python xg5000_client.py --start --plc-id 1

# 사용자 정의 설정
python xg5000_client.py --start --plc-id 1 --interval 500
```

### 데이터 수집 중지
```bash
python xg5000_client.py --stop
```

## 📊 로그 시스템

### 로그 레벨 설정
```bash
# 상세 로그 (모든 정보)
python xg5000_client.py --start --log-level DEBUG

# 일반 로그 (기본값)
python xg5000_client.py --start --log-level INFO

# 경고 이상만
python xg5000_client.py --start --log-level WARNING

# 오류만
python xg5000_client.py --start --log-level ERROR
```

### 로그 파일 위치
- 로그 디렉토리: `logs/`
- 파일명 형식: `xg5000_client_YYYYMMDD.log`
- 인코딩: UTF-8

### 로그 뷰어 사용법
```bash
# 사용 가능한 로그 파일 목록
python log_viewer.py --list

# 최근 로그 파일 보기 (마지막 50줄)
python log_viewer.py --latest

# 최근 로그 파일 보기 (마지막 100줄)
python log_viewer.py --latest --lines 100

# 실시간 로그 모니터링
python log_viewer.py --latest --follow

# 로그에서 특정 텍스트 검색
python log_viewer.py --latest --search "ERROR"

# 로그 파일 분석
python log_viewer.py --analyze logs/xg5000_client_20241201.log
```

### 로그 시스템 특징
- **자동 로그 파일 생성**: 날짜별로 자동 생성
- **상세한 통신 로그**: XGT 전송/수신 패킷 상세 기록
- **성능 측정**: 각 작업별 소요 시간 기록
- **오류 추적**: 상세한 오류 정보 및 스택 트레이스
- **배치 처리 로그**: 배치 그룹 생성 및 처리 과정 기록
- **데이터베이스 작업 로그**: DB 연결, 조회, 저장 작업 기록

## 🔧 배치 통신 최적화

### 배치 그룹 생성 알고리즘

1. **데이터 타입별 그룹화**: M, D, Y, X, T, C 타입별로 분류
2. **주소 정렬**: 각 타입 내에서 주소 순으로 정렬
3. **연속 주소 검출**: 연속된 주소들을 하나의 배치로 묶음
4. **배치 통신**: 각 배치를 XGT 프로토콜로 한 번에 읽기

### 예시
```
원본 데이터:
- D100, D101, D102, D105, D106, D107

배치 그룹:
- 배치 1: D100, D101, D102 (연속)
- 배치 2: D105, D106, D107 (연속)

통신 횟수: 2회 (개별 읽기 시 6회)
```

## 📊 지원하는 PLC 데이터 타입

| 타입 | XGT 주소 형식 | 설명 | 예시 |
|------|---------------|------|------|
| **M** | %MW | 내부 릴레이 | %MW100, %MW101 |
| **D** | %DW | 데이터 레지스터 | %DW100, %DW101 |
| **Y** | %QW | 출력 | %QW0, %QW1 |
| **X** | %IW | 입력 | %IW0, %IW1 |
| **T** | %TW | 타이머 | %TW0, %TW1 |
| **C** | %CW | 카운터 | %CW0, %CW1 |

## 🗄️ MariaDB 연동

### 데이터베이스 테이블

1. **plc_data_items**: PLC 데이터 항목 정보
   - `id`: 항목 ID
   - `item_name`: 항목명 (M100, D100 등)
   - `item_type`: 데이터 타입 (M, D, Y, X, T, C)
   - `modbus_address`: PLC 주소 번호
   - `description`: 항목 설명

2. **plc_real_time_data**: 실시간 수집된 데이터
   - `data_item_id`: 데이터 항목 ID
   - `value`: 수집된 값
   - `quality`: 데이터 품질 (good, bad)
   - `timestamp`: 수집 시간

### 데이터 흐름

```
1. MariaDB에서 plc_data_items 조회
2. 데이터 타입별로 그룹화
3. 연속 주소를 배치로 묶기
4. XGT 프로토콜로 배치 읽기
5. 결과를 개별 항목에 매핑
6. plc_real_time_data에 저장
```

## ⚙️ 설정 및 커스터마이징

### PLC 연결 설정
```python
# xg5000_client.py 수정
PLC_IP = "192.168.1.100"    # PLC IP 주소
PLC_PORT = 2004             # XGT 포트
```

### 데이터 수집 주기 조정
```bash
# 빠른 응답 필요
python xg5000_client.py --start --interval 100

# 일반적인 모니터링
python xg5000_client.py --start --interval 1000

# 저주파 데이터
python xg5000_client.py --start --interval 5000
```

### 배치 크기 최적화
```python
# _create_batch_groups 메서드에서 배치 생성 로직 수정
# 현재는 연속된 주소만 배치로 묶음
# 필요시 최대 배치 크기 제한 추가 가능
```

## 🚨 문제 해결

### PLC 연결 문제
1. **네트워크 확인**: PLC IP 주소와 포트 확인
2. **방화벽 설정**: XGT 포트(2004) 개방
3. **PLC 상태 확인**: PLC가 네트워크에 연결되어 있는지 확인

### MariaDB 연결 문제
1. **데이터베이스 상태 확인**: MariaDB 서비스 실행 여부
2. **사용자 권한 확인**: DB 사용자 권한 및 비밀번호
3. **테이블 존재 확인**: 필요한 테이블이 생성되어 있는지 확인

### 배치 통신 오류
1. **주소 범위 확인**: PLC에서 지원하는 주소 범위 확인
2. **배치 크기 조정**: 너무 큰 배치 크기로 인한 타임아웃 방지
3. **통신 로그 확인**: XGT 통신 패킷 분석

## 📈 성능 최적화

### 배치 통신 최적화
- **연속 주소 그룹화**: 연속된 주소를 최대한 하나의 배치로 묶기
- **배치 크기 조정**: PLC 성능에 맞는 적절한 배치 크기 설정
- **통신 주기 조정**: 응답 시간과 데이터 신선도 고려

### 데이터베이스 최적화
- **인덱스 활용**: `plc_data_items` 테이블의 인덱스 활용
- **배치 저장**: 실시간 데이터를 배치로 저장하여 DB 부하 감소
- **연결 풀링**: 데이터베이스 연결 재사용

## 🔒 보안 고려사항

1. **네트워크 격리**: PLC 네트워크를 사무실 네트워크와 분리
2. **접근 제어**: PLC 접속 권한이 있는 사용자만 시스템 사용
3. **데이터 암호화**: 민감한 데이터는 암호화하여 저장
4. **로그 모니터링**: PLC 접속 로그 정기 확인

## 📞 지원 및 문의

### 시스템 요구사항
- Python 3.6 이상
- MariaDB 10.0 이상 또는 MySQL 5.7 이상
- pymysql 라이브러리
- 네트워크 접근 권한

### 권장 사양
- CPU: Intel i3 이상
- 메모리: 4GB 이상
- 네트워크: 100Mbps 이상 (PLC 통신용)

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 상업적 사용 시 별도 라이선스가 필요할 수 있습니다.

## 🔄 업데이트 내역

- **v1.0.0**: 초기 버전 - 기본 XGT 통신
- **v2.0.0**: 배치 통신 및 MariaDB 연동 추가
- **v2.1.0**: 자동 데이터 수집 및 실시간 저장 기능
