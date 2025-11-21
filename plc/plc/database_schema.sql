-- PLC 데이터 수집 시스템 데이터베이스 스키마
-- SQLite, MySQL, PostgreSQL 등에 적용 가능

-- 1. PLC 장치 정보 테이블
CREATE TABLE plc_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15) NOT NULL,
    port INTEGER DEFAULT 502,
    protocol VARCHAR(20) DEFAULT 'ModbusTCP', -- ModbusTCP, XGT, EtherNet/IP 등
    description TEXT,
    status VARCHAR(20) DEFAULT 'offline', -- online, offline, error
    last_connection TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PRG 파싱된 데이터 항목 테이블
CREATE TABLE plc_data_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plc_device_id INTEGER,
    item_name VARCHAR(100) NOT NULL, -- 예: M100, D100, Y000 등
    item_type VARCHAR(20) NOT NULL, -- M(Coil), D(Register), Y(Output), X(Input) 등
    address VARCHAR(50) NOT NULL, -- PLC 주소 (예: %MW100, %DW100)
    modbus_address INTEGER, -- Modbus 주소 (예: 100)
    modbus_function VARCHAR(10), -- 01(Read Coils), 03(Read Holding Registers) 등
    description TEXT,
    unit VARCHAR(20), -- 단위 (예: ℃, %, RPM 등)
    min_value REAL, -- 최소값
    max_value REAL, -- 최대값
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id)
);

-- 3. 실시간 데이터 저장 테이블
CREATE TABLE plc_real_time_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_item_id INTEGER,
    value REAL,
    quality VARCHAR(20) DEFAULT 'good', -- good, bad, uncertain
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id)
);

-- 4. 데이터 수집 이력 테이블 (선택사항)
CREATE TABLE plc_data_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_item_id INTEGER,
    value REAL,
    quality VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id)
);

-- 5. 데이터 수집 설정 테이블
CREATE TABLE data_collection_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plc_device_id INTEGER,
    collection_interval INTEGER DEFAULT 1000, -- 수집 주기 (밀리초)
    retry_count INTEGER DEFAULT 3, -- 재시도 횟수
    timeout INTEGER DEFAULT 5000, -- 타임아웃 (밀리초)
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id)
);

-- 인덱스 생성
CREATE INDEX idx_plc_data_items_device ON plc_data_items(plc_device_id);
CREATE INDEX idx_plc_data_items_type ON plc_data_items(item_type);
CREATE INDEX idx_real_time_data_item ON plc_real_time_data(data_item_id);
CREATE INDEX idx_real_time_data_timestamp ON plc_real_time_data(timestamp);
CREATE INDEX idx_data_history_item ON plc_data_history(data_item_id);
CREATE INDEX idx_data_history_timestamp ON plc_data_history(timestamp);

-- 샘플 데이터 삽입
INSERT INTO plc_devices (name, ip_address, port, protocol, description) VALUES
('XGB-PLC-01', '192.168.1.100', 502, 'ModbusTCP', '메인 제어 PLC'),
('XGB-PLC-02', '192.168.1.101', 502, 'ModbusTCP', '보조 제어 PLC');

-- PRG 파싱 결과 예시
INSERT INTO plc_data_items (plc_device_id, item_name, item_type, address, modbus_address, modbus_function, description, unit) VALUES
(1, 'M100', 'M', '%MW100', 100, '01', '시스템 시작 신호', ''),
(1, 'M101', 'M', '%MW101', 101, '01', '시스템 정지 신호', ''),
(1, 'D100', 'D', '%DW100', 100, '03', '온도 센서 1', '℃'),
(1, 'D101', 'D', '%DW101', 101, '03', '압력 센서 1', 'bar'),
(1, 'Y000', 'Y', '%QW0', 0, '01', '펌프 1 제어', ''),
(1, 'X000', 'X', '%IW0', 0, '02', '수위 센서 1', 'cm');
