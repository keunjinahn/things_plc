"""
PLC 배치 처리 설정 파일
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from xg5000_client import PLCAddress, DataType, Command, BatchRequest

@dataclass
class PLCConfig:
    """PLC 연결 설정"""
    ip: str
    port: int = 2004
    timeout: int = 2
    retry_count: int = 3
    retry_delay: float = 1.0

@dataclass
class BatchJob:
    """배치 작업 정의"""
    name: str
    description: str
    read_requests: List[BatchRequest]
    write_requests: List[BatchRequest]
    enabled: bool = True

# PLC 연결 설정
PLC_CONFIG = PLCConfig(
    ip="192.168.1.2",
    port=2004,
    timeout=2,
    retry_count=3,
    retry_delay=1.0
)

# 배치 작업 정의
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
            BatchRequest(
                address=PLCAddress("D", 4002),
                data_type=DataType.WORD,
                command=Command.READ
            ),
            BatchRequest(
                address=PLCAddress("D", 4003),
                data_type=DataType.WORD,
                command=Command.READ
            )
        ],
        write_requests=[]
    ),
    
    BatchJob(
        name="알람_상태_확인",
        description="알람 상태 비트 읽기",
        read_requests=[
            BatchRequest(
                address=PLCAddress("M", 100),
                data_type=DataType.BIT,
                command=Command.READ
            ),
            BatchRequest(
                address=PLCAddress("M", 101),
                data_type=DataType.BIT,
                command=Command.READ
            ),
            BatchRequest(
                address=PLCAddress("M", 102),
                data_type=DataType.BIT,
                command=Command.READ
            )
        ],
        write_requests=[]
    ),
    
    BatchJob(
        name="제어_명령_전송",
        description="제어 명령 쓰기",
        read_requests=[],
        write_requests=[
            BatchRequest(
                address=PLCAddress("D", 5001),
                data_type=DataType.WORD,
                command=Command.WRITE,
                value=100
            ),
            BatchRequest(
                address=PLCAddress("M", 200),
                data_type=DataType.BIT,
                command=Command.WRITE,
                value=1
            )
        ]
    )
]

# 데이터 매핑 설정 (주소별 의미 정의)
DATA_MAPPING = {
    "D4001": "온도_센서1",
    "D4002": "압력_센서1", 
    "D4003": "유량_센서1",
    "M100": "알람_온도_높음",
    "M101": "알람_압력_높음",
    "M102": "알람_유량_낮음",
    "D5001": "목표_온도",
    "M200": "가열_명령"
}

# 임계값 설정
THRESHOLDS = {
    "D4001": {"min": 0, "max": 100, "unit": "°C"},  # 온도
    "D4002": {"min": 0, "max": 1000, "unit": "kPa"},  # 압력
    "D4003": {"min": 0, "max": 500, "unit": "L/min"}  # 유량
} 