# LS XG5000 PLC 통신 및 배치 처리 시스템

LS XG5000 PLC와의 TCP 통신을 위한 Python 클라이언트 및 배치 처리 시스템입니다.

## 주요 기능

### 1. XG5000Client 클래스
- LS XG5000 PLC와의 TCP 통신
- 데이터 읽기/쓰기 기능
- 배치 읽기/쓰기 지원
- 컨텍스트 매니저 지원
- 자동 재연결 및 오류 처리

### 2. 배치 처리 시스템
- 다중 작업 배치 실행
- 데이터 검증 및 임계값 확인
- 결과 저장 (JSON, CSV)
- 상세한 로깅

### 3. 스케줄러
- 주기적 배치 작업 실행
- 작업 추가/제거 기능
- 안전한 종료 처리

## 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. PLC 연결 설정
`batch_config.py` 파일에서 PLC IP 주소와 포트를 설정하세요:

```python
PLC_CONFIG = PLCConfig(
    ip="192.168.1.2",  # PLC IP 주소
    port=2004,         # PLC 포트
    timeout=2,         # 연결 타임아웃
    retry_count=3,     # 재시도 횟수
    retry_delay=1.0    # 재시도 간격
)
```

### 3. 배치 작업 설정
`batch_config.py`에서 실행할 배치 작업을 정의하세요:

```python
BATCH_JOBS = [
    BatchJob(
        name="온도_압력_모니터링",
        description="온도 및 압력 센서 데이터 읽기",
        read_requests=[
            BatchRequest(
                address=PLCAddress("D", 4001),
                data_type=DataType.WORD,
                command=Command.READ
            ),
            # ... 더 많은 요청
        ],
        write_requests=[]
    )
]
```

## 사용법

### 1. 기본 PLC 통신
```python
from xg5000_client import XG5000Client, PLCAddress, DataType

# PLC 연결
with XG5000Client("192.168.1.2", 2004) as plc:
    # 데이터 읽기
    value = plc.read(PLCAddress("D", 4001), DataType.WORD)
    print(f"D4001 값: {value}")
    
    # 데이터 쓰기
    success = plc.write(PLCAddress("D", 5001), 12345, DataType.WORD)
    print(f"쓰기 성공: {success}")
```

### 2. 배치 처리 실행
```python
from batch_processor import BatchProcessor
from batch_config import PLC_CONFIG, BATCH_JOBS

# 배치 처리기 생성
processor = BatchProcessor(PLC_CONFIG)

# PLC 연결
if processor.connect():
    # 모든 배치 작업 실행
    results = processor.execute_all_jobs(BATCH_JOBS)
    
    # 결과 저장
    processor.save_results_to_json()
    processor.save_results_to_csv()
    
    # 결과 요약 출력
    processor.print_summary()
    
    # 연결 해제
    processor.disconnect()
```

### 3. 스케줄러 실행
```python
from scheduler import create_scheduler_with_default_jobs

# 스케줄러 생성 (5분마다 실행)
scheduler = create_scheduler_with_default_jobs()

# 스케줄러 시작
scheduler.start()
```

### 4. 커맨드 라인 실행

#### 단일 배치 실행
```bash
python batch_processor.py
```

#### 스케줄러 실행
```bash
python scheduler.py
```

## 파일 구조

```
plc/
├── xg5000_client.py      # PLC 통신 클라이언트
├── batch_config.py       # 배치 작업 설정
├── batch_processor.py    # 배치 처리기
├── scheduler.py          # 스케줄러
├── requirements.txt      # 의존성 목록
├── README.md            # 프로젝트 문서
└── batch_results/       # 결과 저장 디렉토리
    ├── *.json           # JSON 결과 파일
    └── *.csv            # CSV 결과 파일
```

## 데이터 타입

- `BIT`: 비트 데이터 (0/1)
- `WORD`: 16비트 워드 데이터
- `DWORD`: 32비트 더블워드 데이터
- `LWORD`: 64비트 롱워드 데이터
- `BYTE`: 8비트 바이트 데이터
- `STRING`: 문자열 데이터

## PLC 주소 형식

- `D`: 데이터 레지스터 (예: D4001)
- `M`: 내부 릴레이 (예: M100)
- `P`: 특수 릴레이 (예: P100)
- `X`: 입력 (예: X000)
- `Y`: 출력 (예: Y000)

## 로깅

시스템은 다음 로그를 생성합니다:
- `plc_communication.log`: PLC 통신 로그
- 콘솔 출력: 실시간 상태 정보

## 오류 처리

- 연결 실패 시 자동 재시도
- 데이터 검증 및 임계값 확인
- 상세한 오류 메시지 및 로깅
- 안전한 연결 해제

## 확장 가능성

- 새로운 데이터 타입 추가
- 추가 PLC 프로토콜 지원
- 웹 인터페이스 연동
- 데이터베이스 저장
- 알림 시스템 연동

## 주의사항

1. PLC IP 주소와 포트가 올바른지 확인하세요
2. 네트워크 연결 상태를 확인하세요
3. PLC가 통신 모드로 설정되어 있는지 확인하세요
4. 방화벽 설정을 확인하세요

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 