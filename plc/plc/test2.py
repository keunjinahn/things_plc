# pip install pymodbus==2.5.3
from pymodbus.client.sync import ModbusTcpClient
from typing import List

PLC_IP = "192.168.1.2"   # XBL-EMTA IP
PLC_PORT = 2004           # Modbus/TCP 포트

def read_d_words(start_d: int, count: int = 1):
    """
    D영역을 Holding Register로 매핑했다고 가정.
    start_d=0 -> 40001, start_d=1 -> 40002 ...
    """
    # Modbus 주소는 0-base. 40001 -> address=0
    address = start_d
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    try:
        if not client.connect():
            raise RuntimeError("Modbus 연결 실패")
        rr = client.read_holding_registers(address=address, count=count, unit=1)
        if rr.isError():
            raise RuntimeError(f"Read Error: {rr}")
        return rr.registers  # [int, int, ...]
    finally:
        client.close()

def write_d_words(start_d: int, values: List[int]):
    address = start_d
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    try:
        if not client.connect():
            raise RuntimeError("Modbus 연결 실패")
        # 여러 워드 쓰기
        rq = client.write_registers(address=address, values=values, unit=1)
        if rq.isError():
            raise RuntimeError(f"Write Error: {rq}")
        return True
    finally:
        client.close()

def read_m_bits(start_m: int, count: int = 1):
    """
    M영역을 Coil로 매핑했다고 가정.
    start_m=0 -> 00001(주소 0)
    """
    address = start_m
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    try:
        if not client.connect():
            raise RuntimeError("Modbus 연결 실패")
        rr = client.read_coils(address=address, count=count, unit=1)
        if rr.isError():
            raise RuntimeError(f"Read Error: {rr}")
        return list(rr.bits)[:count]
    finally:
        client.close()

def write_m_bits(start_m: int, values: List[bool]):
    address = start_m
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    try:
        if not client.connect():
            raise RuntimeError("Modbus 연결 실패")
        rq = client.write_coils(address=address, values=values, unit=1)
        if rq.isError():
            raise RuntimeError(f"Write Error: {rq}")
        return True
    finally:
        client.close()

if __name__ == "__main__":
    # 예1) D100 ~ D101 읽기
    d_vals = read_d_words(4010, 1)
    print("D100..D101 =", d_vals)

    # # 예2) D120, D121에 값 쓰기
    # ok = write_d_words(120, [1234, 5678])
    # print("Write D120.. =", ok)

    # # 예3) M10..M15 읽기
    # m_vals = read_m_bits(10, 6)
    # print("M10..M15 =", m_vals)

    # # 예4) M20..M23 ON/OFF 쓰기
    # ok2 = write_m_bits(20, [True, False, True, True])
    # print("Write M20..M23 =", ok2)
