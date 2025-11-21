# PLC 데이터 수집 시스템 (MariaDB)

XG5000 PLC의 PRG 파일을 파싱하여 데이터 항목을 MariaDB에 저장하고, 실시간으로 PLC에서 데이터를 수집하여 저장하는 통합 시스템입니다.

## 🎯 목표

1. **PRG 파일 파싱**: PLC 프로그램 파일에서 데이터 항목(M100, D100, Y000 등)을 자동 추출
2. **MariaDB 저장**: 추출된 항목을 MariaDB에 저장하여 PLC 접속 정보 관리
3. **실시간 데이터 수집**: DB에 저장된 항목을 기반으로 PLC에서 실시간 데이터 수집
4. **데이터 모니터링**: 수집된 실시간 데이터를 모니터링 및 분석

## 🏗️ 시스템 아키텍처

```
PRG 파일 → 파싱 → MariaDB → PLC 접속 → 실시간 데이터 수집
    ↓           ↓         ↓           ↓           ↓
  M100, D100   M100    plc_data_items  Modbus    plc_real_time_data
  Y000, X000   D100    테이블에 저장    TCP 연결   테이블에 저장
```

## 📁 파일 구조

- `database_schema_mariadb.sql` - MariaDB용 데이터베이스 스키마
- `database_config.py` - MariaDB 연결 설정 및 관리
- `prg_parser_to_db_mariadb.py` - PRG 파일 파싱 및 MariaDB 저장
- `plc_data_collector_mariadb.py` - PLC 실시간 데이터 수집 (MariaDB)
- `run_plc_system_mariadb.py` - 통합 실행 스크립트 (MariaDB)
- `PLC_SYSTEM_MARIADB_README.md` - 이 파일

## 🚀 빠른 시작

### 1. MariaDB 설치 및 설정

#### MariaDB 서버 설치
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mariadb-server

# CentOS/RHEL
sudo yum install mariadb-server

# Windows
# MariaDB 공식 웹사이트에서 설치 파일 다운로드
```

#### MariaDB 서비스 시작
```bash
# Ubuntu/Debian
sudo systemctl start mariadb
sudo systemctl enable mariadb

# CentOS/RHEL
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

#### 초기 설정
```bash
sudo mysql_secure_installation
```

### 2. Python 의존성 설치
```bash
pip install pymysql pymodbus
```

### 3. 데이터베이스 생성
```sql
CREATE DATABASE plc_data_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'plc_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON plc_data_system.* TO 'plc_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 환경변수 설정
```bash
# Linux/macOS
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=plc_user
export DB_PASSWORD=your_password
export DB_NAME=plc_data_system

# Windows
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=plc_user
set DB_PASSWORD=your_password
set DB_NAME=plc_data_system
```

### 5. 시스템 실행
```bash
python run_plc_system_mariadb.py
```

## 📋 상세 사용법

### 1단계: 데이터베이스 연결 테스트 및 초기화

#### 통합 시스템에서
```bash
python run_plc_system_mariadb.py
# 1번 선택
```

#### 수동 실행
```bash
python database_config.py
```

### 2단계: PRG 파일 파싱 및 DB 저장

#### 자동 실행
```bash
python run_plc_system_mariadb.py
# 2번 선택 → PRG 파일 선택 → PLC 장치 ID 입력
```

#### 수동 실행
```bash
# PRG 파일 파싱 및 MariaDB 저장
python prg_parser_to_db_mariadb.py program.prg 1

# 저장된 항목 조회
python prg_parser_to_db_mariadb.py --list 1

# 데이터베이스 초기화
python prg_parser_to_db_mariadb.py --init
```

### 3단계: PLC 실시간 데이터 수집

#### 데이터 수집 시작
```bash
# 기본 설정으로 시작 (1초 주기)
python plc_data_collector_mariadb.py --start --plc-id 1

# 사용자 정의 설정
python plc_data_collector_mariadb.py --start --plc-id 1 --interval 500
```

#### 데이터 수집 중지
```bash
python plc_data_collector_mariadb.py --stop
```

#### 실시간 데이터 조회
```bash
python plc_data_collector_mariadb.py --status --plc-id 1
```

### 4단계: 데이터 모니터링

#### 통합 시스템에서 모니터링
```bash
python run_plc_system_mariadb.py
# 4번 선택 → PLC 장치 ID 입력
```

#### 직접 모니터링
```bash
python plc_data_collector_mariadb.py --status --plc-id 1
```

## 🗄️ MariaDB 데이터베이스 구조

### 주요 테이블

1. **plc_devices**: PLC 장치 정보
   - IP 주소, 포트, 프로토콜, 상태 등

2. **plc_data_items**: PRG에서 파싱된 데이터 항목
   - 항목명(M100, D100), 타입, 주소, Modbus 함수 등

3. **plc_real_time_data**: 실시간 수집된 데이터
   - 값, 품질, 타임스탬프

4. **plc_data_history**: 데이터 수집 이력 (선택사항)

5. **data_collection_config**: 데이터 수집 설정

### 테이블 생성
```bash
# 스키마 파일 실행
mysql -u plc_user -p plc_data_system < database_schema_mariadb.sql

# 또는 Python으로 초기화
python database_config.py
```

## 🔧 설정 및 커스터마이징

### 데이터베이스 연결 설정
```python
# database_config.py 수정
DEFAULT_CONFIG = {
    'host': 'your_mariadb_host',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'plc_data_system',
    'charset': 'utf8mb4'
}
```

### 환경변수 설정
```bash
# .env 파일 생성
DB_HOST=192.168.1.100
DB_PORT=3306
DB_USER=plc_user
DB_PASSWORD=secure_password
DB_NAME=plc_data_system
```

### PLC 장치 추가
```sql
INSERT INTO plc_devices (name, ip_address, port, protocol, description)
VALUES ('PLC-02', '192.168.1.101', 502, 'ModbusTCP', '보조 PLC');
```

## 📊 지원하는 PLC 데이터 타입

| 타입 | 설명 | Modbus 함수 | 예시 |
|------|------|-------------|------|
| **M** | 내부 릴레이 | 01 (Read Coils) | M100, M101 |
| **D** | 데이터 레지스터 | 03 (Read Holding Registers) | D100, D101 |
| **Y** | 출력 | 01 (Read Coils) | Y000, Y001 |
| **X** | 입력 | 02 (Read Discrete Inputs) | X000, X001 |
| **T** | 타이머 | 03 (Read Holding Registers) | T0, T1 |
| **C** | 카운터 | 03 (Read Holding Registers) | C0, C1 |

## 🚨 문제 해결

### MariaDB 연결 문제
1. **서비스 상태 확인**
   ```bash
   sudo systemctl status mariadb
   ```

2. **포트 확인**
   ```bash
   sudo netstat -tlnp | grep 3306
   ```

3. **방화벽 설정**
   ```bash
   sudo ufw allow 3306
   ```

4. **사용자 권한 확인**
   ```sql
   SELECT User, Host FROM mysql.user WHERE User = 'plc_user';
   SHOW GRANTS FOR 'plc_user'@'localhost';
   ```

### 인코딩 문제
```bash
# 자동 인코딩 감지
python prg_parser_to_db_mariadb.py program.prg

# 수동 인코딩 지정
python prg_parser_to_db_mariadb.py --encoding=cp949 program.prg
```

### PLC 연결 문제
1. **네트워크 확인**: PLC IP 주소와 포트 확인
2. **방화벽 설정**: Modbus TCP 포트(502) 개방
3. **PLC 상태 확인**: PLC가 네트워크에 연결되어 있는지 확인

## 📈 성능 최적화

### MariaDB 최적화
```sql
-- InnoDB 설정 최적화
SET GLOBAL innodb_buffer_pool_size = 1073741824;  -- 1GB
SET GLOBAL innodb_log_file_size = 268435456;      -- 256MB

-- 쿼리 최적화
EXPLAIN SELECT * FROM plc_real_time_data WHERE timestamp > NOW() - INTERVAL 1 HOUR;
```

### 데이터 수집 주기 조정
- **빠른 응답 필요**: 100-500ms
- **일반적인 모니터링**: 1000ms (1초)
- **저주파 데이터**: 5000-10000ms (5-10초)

## 🔒 보안 고려사항

1. **네트워크 격리**: PLC 네트워크를 사무실 네트워크와 분리
2. **데이터베이스 보안**: 강력한 비밀번호 사용 및 사용자 권한 제한
3. **접근 제어**: PLC 접속 권한이 있는 사용자만 시스템 사용
4. **데이터 백업**: 정기적인 MariaDB 백업 수행
5. **로그 모니터링**: PLC 접속 로그 정기 확인

## 📞 지원 및 문의

### 시스템 요구사항
- Python 3.6 이상
- MariaDB 10.0 이상 또는 MySQL 5.7 이상
- pymysql, pymodbus 라이브러리
- 네트워크 접근 권한

### 권장 사양
- CPU: Intel i3 이상
- 메모리: 4GB 이상
- 저장공간: 10GB 이상 (데이터 이력 저장 시)
- 네트워크: 100Mbps 이상

### MariaDB 권장 사양
- 메모리: 2GB 이상 (InnoDB 버퍼 풀용)
- 저장공간: SSD 권장
- 백업: 자동 백업 설정 권장

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 상업적 사용 시 별도 라이선스가 필요할 수 있습니다.

## 🔄 업데이트 내역

- **v1.0.0**: 초기 버전 - SQLite 기반
- **v1.1.0**: 자동 인코딩 감지 및 에러 처리 개선
- **v1.2.0**: 통합 실행 시스템 및 모니터링 기능 추가
- **v2.0.0**: MariaDB 지원 추가 - 기업용 환경 대응

