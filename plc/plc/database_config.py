#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MariaDB 데이터베이스 연결 설정
"""

import pymysql
from typing import Optional
import os

class DatabaseConfig:
    """데이터베이스 연결 설정 클래스"""
    
    # 기본 설정 (환경변수로 오버라이드 가능)
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'dbadmin',
        'password': 'p#ssw0rd',
        'database': 'plc_data_system',
        'charset': 'utf8mb4',
        'autocommit': True,
        'connect_timeout': 10,
        'read_timeout': 30,
        'write_timeout': 30
    }
    
    @classmethod
    def get_config(cls) -> dict:
        """데이터베이스 연결 설정 반환"""
        config = cls.DEFAULT_CONFIG.copy()
        
        # 환경변수에서 설정 읽기
        if os.getenv('DB_HOST'):
            config['host'] = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            config['port'] = int(os.getenv('DB_PORT'))
        if os.getenv('DB_USER'):
            config['user'] = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            config['password'] = os.getenv('DB_PASSWORD')
        if os.getenv('DB_NAME'):
            config['database'] = os.getenv('DB_NAME')
        
        return config
    
    @classmethod
    def create_connection(cls) -> Optional[pymysql.Connection]:
        """데이터베이스 연결 생성"""
        try:
            config = cls.get_config()
            connection = pymysql.connect(**config)
            print(f"MariaDB 연결 성공: {config['host']}:{config['port']}/{config['database']}")
            return connection
        except Exception as e:
            print(f"MariaDB 연결 실패: {e}")
            return None
    
    @classmethod
    def test_connection(cls) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            connection = cls.create_connection()
            if connection:
                connection.close()
                return True
            return False
        except Exception as e:
            print(f"연결 테스트 실패: {e}")
            return False
    
    @classmethod
    def init_database(cls) -> bool:
        """데이터베이스 초기화 (테이블 생성)"""
        try:
            connection = cls.create_connection()
            if not connection:
                return False
            
            with connection.cursor() as cursor:
                # 테이블 생성 스크립트 실행
                create_tables_sql = cls._get_create_tables_sql()
                cursor.execute(create_tables_sql)
                
                # 기본 PLC 장치 추가
                cursor.execute('''
                    INSERT IGNORE INTO plc_devices (id, name, ip_address, port, protocol, description)
                    VALUES (1, 'Default PLC', '192.168.1.100', 502, 'ModbusTCP', '기본 PLC 장치')
                ''')
                
                connection.commit()
                print("MariaDB 데이터베이스 초기화 완료")
                return True
                
        except Exception as e:
            print(f"데이터베이스 초기화 오류: {e}")
            return False
        finally:
            if connection:
                connection.close()
    
    @classmethod
    def _get_create_tables_sql(cls) -> str:
        """테이블 생성 SQL 반환"""
        return '''
            CREATE TABLE IF NOT EXISTS plc_devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                ip_address VARCHAR(15) NOT NULL,
                port INT DEFAULT 502,
                protocol VARCHAR(20) DEFAULT 'ModbusTCP',
                description TEXT,
                status VARCHAR(20) DEFAULT 'offline',
                last_connection TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            
            CREATE TABLE IF NOT EXISTS plc_data_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plc_device_id INT,
                item_name VARCHAR(100) NOT NULL,
                item_type VARCHAR(20) NOT NULL,
                address VARCHAR(50) NOT NULL,
                modbus_address INT,
                modbus_function VARCHAR(10),
                description TEXT,
                unit VARCHAR(20),
                min_value DECIMAL(10,2),
                max_value DECIMAL(10,2),
                is_active BOOLEAN DEFAULT TRUE,
                line_number INT,
                source_line TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            
            CREATE TABLE IF NOT EXISTS plc_real_time_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data_item_id INT,
                value DECIMAL(15,4),
                quality VARCHAR(20) DEFAULT 'good',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            
            CREATE TABLE IF NOT EXISTS plc_data_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data_item_id INT,
                value DECIMAL(15,4),
                quality VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (data_item_id) REFERENCES plc_data_items(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            
            CREATE TABLE IF NOT EXISTS data_collection_config (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plc_device_id INT,
                collection_interval INT DEFAULT 1000,
                retry_count INT DEFAULT 3,
                timeout INT DEFAULT 5000,
                is_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (plc_device_id) REFERENCES plc_devices(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        '''

def main():
    """메인 함수 - 연결 테스트 및 초기화"""
    print("=== MariaDB 연결 테스트 ===")
    
    if DatabaseConfig.test_connection():
        print("✅ 데이터베이스 연결 성공!")
        
        print("\n=== 데이터베이스 초기화 ===")
        if DatabaseConfig.init_database():
            print("✅ 데이터베이스 초기화 완료!")
        else:
            print("❌ 데이터베이스 초기화 실패!")
    else:
        print("❌ 데이터베이스 연결 실패!")
        print("\n설정 확인:")
        config = DatabaseConfig.get_config()
        for key, value in config.items():
            if key != 'password':
                print(f"  {key}: {value}")
        print("  password: [보안상 숨김]")
        
        print("\n환경변수 설정 예시:")
        print("  export DB_HOST=localhost")
        print("  export DB_PORT=3306")
        print("  export DB_USER=plc_user")
        print("  export DB_PASSWORD=your_password")
        print("  export DB_NAME=plc_data_system")

if __name__ == "__main__":
    main()
