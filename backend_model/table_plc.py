from backend_model.database import DBManager
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
db = DBManager.db

class UserTbl(db.Model):
    __tablename__ = 'user_tbl'

    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.String(10))
    user_pwd = db.Column('user_pwd', db.String(10))
    user_name = db.Column('user_name', db.String(45))
    user_status = db.Column('user_status', db.Integer, default='1')
    user_role = db.Column('user_role', db.Integer, default='1')
    token = db.Column('token', db.String(128))  # added
    
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id
            , "user_id": self.user_id
            , "user_name": self.user_name
            , "user_status": self.user_status
            , "user_role": self.user_role
            , "token": self.token
        }
        return resultJSON

class PlcDevice(db.Model):
    """PLC 디바이스 정보 테이블"""
    __tablename__ = 'plc_devices'
    
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column('device_name', db.String(100), nullable=False, comment='PLC 디바이스 이름')
    device_type = db.Column('device_type', db.String(50), comment='PLC 타입 (예: XG5000, XGB 등)')
    ip_address = db.Column('ip_address', db.String(15), comment='PLC IP 주소')
    port = db.Column('port', db.Integer, comment='PLC 통신 포트')
    protocol = db.Column('protocol', db.String(20), comment='통신 프로토콜 (예: Modbus TCP, EtherNet/IP 등)')
    is_active = db.Column('is_active', db.Boolean, default=True, comment='활성화 상태')
    description = db.Column('description', db.Text, comment='디바이스 설명')
    created_at = db.Column('created_at', db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column('updated_at', db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계 설정
    data_items = relationship("PlcDataItem", back_populates="device", cascade="all, delete-orphan")
    
    def serialize(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "ip_address": self.ip_address,
            "port": self.port,
            "protocol": self.protocol,
            "is_active": self.is_active,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PlcDataItem(db.Model):
    """PLC 데이터 항목 테이블"""
    __tablename__ = 'plc_data_items'
    
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    plc_device_id = db.Column('plc_device_id', db.Integer, ForeignKey('plc_devices.id', ondelete='CASCADE'), comment='PLC 디바이스 ID')
    item_name = db.Column('item_name', db.String(100), nullable=False, comment='예: M100, D100, Y000 등')
    item_type = db.Column('item_type', db.String(20), nullable=False, comment='M(Coil), D(Register), Y(Output), X(Input) 등')
    address = db.Column('address', db.String(50), nullable=False, comment='PLC 주소 (예: %MW100, %DW100)')
    modbus_address = db.Column('modbus_address', db.Integer, comment='Modbus 주소 (예: 100)')
    modbus_function = db.Column('modbus_function', db.String(10), comment='01(Read Coils), 03(Read Holding Registers) 등')
    description = db.Column('description', db.Text, comment='항목 설명')
    unit = db.Column('unit', db.String(20), comment='단위 (예: ℃, %, RPM 등)')
    min_value = db.Column('min_value', db.Numeric(10, 2), comment='최소값')
    max_value = db.Column('max_value', db.Numeric(10, 2), comment='최대값')
    is_active = db.Column('is_active', db.Boolean, default=True, comment='활성화 상태')
    line_number = db.Column('line_number', db.Integer, comment='PRG 파일의 라인 번호')
    source_line = db.Column('source_line', db.Text, comment='원본 PRG 라인')
    created_at = db.Column('created_at', db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column('updated_at', db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계 설정
    device = relationship("PlcDevice", back_populates="data_items")
    real_time_data = relationship("PlcRealTimeData", back_populates="data_item", cascade="all, delete-orphan")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_plc_data_items_device', 'plc_device_id'),
        Index('idx_plc_data_items_type', 'item_type'),
    )
    
    def serialize(self):
        return {
            "id": self.id,
            "plc_device_id": self.plc_device_id,
            "item_name": self.item_name,
            "item_type": self.item_type,
            "address": self.address,
            "modbus_address": self.modbus_address,
            "modbus_function": self.modbus_function,
            "description": self.description,
            "unit": self.unit,
            "min_value": float(self.min_value) if self.min_value else None,
            "max_value": float(self.max_value) if self.max_value else None,
            "is_active": self.is_active,
            "line_number": self.line_number,
            "source_line": self.source_line,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "device_name": self.device.device_name if self.device else None
        }

class PlcRealTimeData(db.Model):
    """PLC 실시간 데이터 테이블"""
    __tablename__ = 'plc_real_time_data'
    
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    data_item_id = db.Column('data_item_id', db.Integer, ForeignKey('plc_data_items.id', ondelete='CASCADE'), comment='데이터 항목 ID')
    value = db.Column('value', db.Numeric(15, 4), comment='수집된 값')
    quality = db.Column('quality', db.String(20), default='good', comment='good, bad, uncertain')
    timestamp = db.Column('timestamp', db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # 관계 설정
    data_item = relationship("PlcDataItem", back_populates="real_time_data")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_real_time_data_item', 'data_item_id'),
        Index('idx_real_time_data_timestamp', 'timestamp'),
    )
    
    def serialize(self):
        return {
            "id": self.id,
            "data_item_id": self.data_item_id,
            "value": float(self.value) if self.value else None,
            "quality": self.quality,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "item_name": self.data_item.item_name if self.data_item else None,
            "item_type": self.data_item.item_type if self.data_item else None,
            "address": self.data_item.address if self.data_item else None,
            "unit": self.data_item.unit if self.data_item else None,
            "device_name": self.data_item.device.device_name if self.data_item and self.data_item.device else None
        }

    def serialize_basic(self):
        """기본 정보만 직렬화 (대량 데이터 처리용)"""
        return {
            "id": self.id,
            "data_item_id": self.data_item_id,
            "value": float(self.value) if self.value else None,
            "quality": self.quality,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }    
