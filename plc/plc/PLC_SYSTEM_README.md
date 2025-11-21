# PLC 데이터 수집 시스템

XG5000 PLC의 PRG 파일을 파싱하여 데이터 항목을 데이터베이스에 저장하고, 실시간으로 PLC에서 데이터를 수집하여 저장하는 통합 시스템입니다.

## 🎯 목표

1. **PRG 파일 파싱**: PLC 프로그램 파일에서 데이터 항목(M100, D100, Y000 등)을 자동 추출
2. **데이터베이스 저장**: 추출된 항목을 DB에 저장하여 PLC 접속 정보 관리
3. **실시간 데이터 수집**: DB에 저장된 항목을 기반으로 PLC에서 실시간 데이터 수집
4. **데이터 모니터링**: 수집된 실시간 데이터를 모니터링 및 분석

## 🏗️ 시스템 아키텍처

```
PRG 파일 → 파싱 → 데이터베이스 → PLC 접속 → 실시간 데이터 수집
    ↓           ↓         ↓           ↓           ↓
  M100, D100   M100    plc_data_items  Modbus    plc_real_time_data
  Y000, X000   D100    테이블에 저장    TCP 연결   테이블에 저장
```

## 📁 파일 구조

- `database_schema.sql` - 데이터베이스 스키마 정의
- `prg_parser_to_db.py` - PRG 파일 파싱 및 DB 저장
- `plc_data_collector.py` - PLC 실시간 데이터 수집
- `run_plc_system.py` - 통합 실행 스크립트
- `PLC_SYSTEM_README.md` - 이 파일

## 🚀 빠른 시작

### 1. 시스템 실행
```bash
python run_plc_system.py
```

### 2. 메뉴 선택
- **1번**: PRG 파일 파싱 및 DB 저장
- **2번**: PLC 실시간 데이터 수집 시작
- **3번**: 데이터 모니터링
- **4번**: 시스템 상태 확인
- **5번**: 종료

## 📋 상세 사용법

### 1단계: PRG 파일 파싱 및 DB 저장

#### 자동 실행
```bash
python run_plc_system.py
# 1번 선택 → PRG 파일 선택 → PLC 장치 ID 입력
```

#### 수동 실행
```bash
# PRG 파일 파싱 및 DB 저장
python prg_parser_to_db.py program.prg 1

# 저장된 항목 조회
python prg_parser_to_db.py --list 1
```

### 2단계: PLC 실시간 데이터 수집

#### 데이터 수집 시작
```bash
# 기본 설정으로 시작 (1초 주기)
python plc_data_collector.py --start --plc-id 1

# 사용자 정의 설정
python plc_data_collector.py --start --plc-id 1 --interval 500
```

#### 데이터 수집 중지
```bash
python plc_data_collector.py --stop
```

#### 실시간 데이터 조회
```bash
python plc_data_collector.py --status --plc-id 1
```

### 3단계: 데이터 모니터링

#### 통합 시스템에서 모니터링
```bash
python run_plc_system.py
# 3번 선택 → PLC 장치 ID 입력
```

#### 직접 모니터링
```bash
python plc_data_collector.py --status --plc-id 1
```

## 🗄️ 데이터베이스 구조

### 주요 테이블

1. **plc_devices**: PLC 장치 정보
   - IP 주소, 포트, 프로토콜, 상태 등

2. **plc_data_items**: PRG에서 파싱된 데이터 항목
   - 항목명(M100, D100), 타입, 주소, Modbus 함수 등

3. **plc_real_time_data**: 실시간 수집된 데이터
   - 값, 품질, 타임스탬프

4. **plc_data_history**: 데이터 수집 이력 (선택사항)

## 🔧 설정 및 커스터마이징

### PLC 장치 추가
```sql
INSERT INTO plc_devices (name, ip_address, port, protocol, description)
VALUES ('PLC-02', '192.168.1.101', 502, 'ModbusTCP', '보조 PLC');
```

### 데이터 수집 주기 변경
```bash
python plc_data_collector.py --start --plc-id 1 --interval 2000  # 2초 주기
```

### 데이터 품질 임계값 설정
```sql
UPDATE plc_data_items 
SET min_value = 0, max_value = 100 
WHERE item_name = 'D100';
```

## 📊 지원하는 PLC 데이터 타입

| 타입 | 설명 | Modbus 함수 | 예시 |
|------|------|-------------|------|
| M | 내부 릴레이 | 01 (Read Coils) | M100, M101 |
| D | 데이터 레지스터 | 03 (Read Holding Registers) | D100, D101 |
| Y | 출력 | 01 (Read Coils) | Y000, Y001 |
| X | 입력 | 02 (Read Discrete Inputs) | X000, X001 |
| T | 타이머 | 03 (Read Holding Registers) | T0, T1 |
| C | 카운터 | 03 (Read Holding Registers) | C0, C1 |

## 🚨 문제 해결

### 인코딩 문제
```bash
# 자동 인코딩 감지
python prg_parser_to_db.py program.prg

# 수동 인코딩 지정
python prg_parser_to_db.py --encoding=cp949 program.prg
```

### PLC 연결 문제
1. **네트워크 확인**: PLC IP 주소와 포트 확인
2. **방화벽 설정**: Modbus TCP 포트(502) 개방
3. **PLC 상태 확인**: PLC가 네트워크에 연결되어 있는지 확인

### 데이터 수집 오류
1. **로그 확인**: 콘솔 출력에서 오류 메시지 확인
2. **PLC 상태 확인**: PLC가 정상 작동 중인지 확인
3. **Modbus 주소 확인**: PRG 파일의 주소와 실제 PLC 주소 일치 여부 확인

## 📈 성능 최적화

### 데이터 수집 주기 조정
- **빠른 응답 필요**: 100-500ms
- **일반적인 모니터링**: 1000ms (1초)
- **저주파 데이터**: 5000-10000ms (5-10초)

### 데이터베이스 최적화
```sql
-- 인덱스 생성 (자동 생성됨)
CREATE INDEX idx_real_time_data_timestamp ON plc_real_time_data(timestamp);

-- 오래된 데이터 정리
DELETE FROM plc_data_history WHERE timestamp < datetime('now', '-30 days');
```

## 🔒 보안 고려사항

1. **네트워크 격리**: PLC 네트워크를 사무실 네트워크와 분리
2. **접근 제어**: PLC 접속 권한이 있는 사용자만 시스템 사용
3. **데이터 백업**: 정기적인 데이터베이스 백업 수행
4. **로그 모니터링**: PLC 접속 로그 정기 확인

## 📞 지원 및 문의

### 시스템 요구사항
- Python 3.6 이상
- pymodbus 라이브러리
- SQLite3 (기본 내장)
- 네트워크 접근 권한

### 권장 사양
- CPU: Intel i3 이상
- 메모리: 4GB 이상
- 저장공간: 10GB 이상 (데이터 이력 저장 시)
- 네트워크: 100Mbps 이상

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 상업적 사용 시 별도 라이선스가 필요할 수 있습니다.

## 🔄 업데이트 내역

- **v1.0.0**: 초기 버전 - 기본 PRG 파싱 및 데이터 수집
- **v1.1.0**: 자동 인코딩 감지 및 에러 처리 개선
- **v1.2.0**: 통합 실행 시스템 및 모니터링 기능 추가

