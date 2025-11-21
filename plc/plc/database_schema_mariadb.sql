-- PLC 데이터 수집 시스템 데이터베이스 스키마 (MariaDB/MySQL)
-- MariaDB 10.0 이상, MySQL 5.7 이상에서 사용 가능

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS plc_data_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE plc_data_system;

-- 1. PLC 장치 정보 테이블
CREATE TABLE IF NOT EXISTS plc_devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15) NOT NULL,
    port INT DEFAULT 502,
    protocol VARCHAR(20) DEFAULT 'ModbusTCP' COMMENT 'ModbusTCP, XGT, EtherNet/IP 등',
    description TEXT,
    status VARCHAR(20) DEFAULT 'offline' COMMENT 'online, offline, error',
    last_connection TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. PRG 파싱된 데이터 항목 테이블
CREATE TABLE IF NOT EXISTS plc_data_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plc_device_id INT,
    item_name VARCHAR(100) NOT NULL COMMENT '예: M100, D100, Y000 등',
    item_type VARCHAR(20) NOT NULL COMMENT 'M(Coil), D(Register), Y(Output), X(Input) 등',
    address VARCHAR(50) NOT NULL COMMENT 'PLC 주소 (예: %MW100, %DW100)',
    modbus_address INT COMMENT 'Modbus 주소 (예: 100)',
    modbus_function VARCHAR(10) COMMENT '01(Read Coils), 03(Read Holding Registers) 등',
    description TEXT,
    unit VARCHAR(20) COMMENT '단위 (예: ℃, %, RPM 등)',
    min_value DECIMAL(10,2) COMMENT '최소값',
    max_value DECIMAL(10,2) COMMENT '최대값',
    is_active BOOLEAN DEFAULT TRUE,
    line_number INT COMMENT 'PRG 파일의 라인 번호',
    source_line TEXT COMMENT '원본 PRG 라인',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 실시간 데이터 저장 테이블
CREATE TABLE IF NOT EXISTS plc_real_time_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_item_id INT,
    value DECIMAL(15,4) COMMENT '수집된 값',
    quality VARCHAR(20) DEFAULT 'good' COMMENT 'good, bad, uncertain',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 데이터 수집 이력 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS plc_data_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_item_id INT,
    value DECIMAL(15,4) COMMENT '수집된 값',
    quality VARCHAR(20) COMMENT '데이터 품질',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 데이터 수집 설정 테이블
CREATE TABLE IF NOT EXISTS data_collection_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plc_device_id INT,
    collection_interval INT DEFAULT 1000 COMMENT '수집 주기 (밀리초)',
    retry_count INT DEFAULT 3 COMMENT '재시도 횟수',
    timeout INT DEFAULT 5000 COMMENT '타임아웃 (밀리초)',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
('XGB-PLC-02', '192.168.1.101', 502, 'ModbusTCP', '보조 제어 PLC')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- PRG 파싱 결과 예시
INSERT INTO plc_data_items (plc_device_id, item_name, item_type, address, modbus_address, modbus_function, description, unit) VALUES
(1, 'M100', 'M', '%MW100', 100, '01', '시스템 시작 신호', ''),
(1, 'M101', 'M', '%MW101', 101, '01', '시스템 정지 신호', ''),
(1, 'D100', 'D', '%DW100', 100, '03', '온도 센서 1', '℃'),
(1, 'D101', 'D', '%DW101', 101, '03', '압력 센서 1', 'bar'),
(1, 'Y000', 'Y', '%QW0', 0, '01', '펌프 1 제어', ''),
(1, 'X000', 'X', '%IW0', 0, '02', '수위 센서 1', 'cm')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 사용자 권한 설정 (필요시)
-- GRANT ALL PRIVILEGES ON plc_data_system.* TO 'plc_user'@'localhost' IDENTIFIED BY 'your_password';
-- FLUSH PRIVILEGES;
