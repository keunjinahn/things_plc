import socket, struct
from typing import Tuple, List

XGT_IP, XGT_PORT = "192.168.1.2", 2004
SOCK_TIMEOUT = 3.0

COMPANY_ID = b"LGIS-GLOFA"      # 10B
PLC_INFO   = struct.pack("<H", 0x0101) # 2B (응답과 맞춤)
CPU_INFO   = b"\xB0"                   # 1B (응답과 맞춤)
SRC_REQ    = b"\x33"                   # 1B
SRC_RSP    = b"\x11"                   # 1B

# ✅ 올바른 값들 (리틀엔디언 시 바이트가 54 00 / 55 00)
CMD_READ_VARIABLE_REQ = struct.pack("<H", 0x0054)
CMD_READ_VARIABLE_RSP = struct.pack("<H", 0x0055)

# ✅ 올바른 데이터타입 값들 (리틀엔디언 시 02 00 등)
DT_BIT   = 0x0000
DT_BYTE  = 0x0001
DT_WORD  = 0x0002
DT_DWORD = 0x0003
DT_LWORD = 0x0004

UNIT_SIZE = {DT_BIT:1, DT_BYTE:1, DT_WORD:2, DT_DWORD:4, DT_LWORD:8}

def le16(v:int)->bytes: return struct.pack("<H", v)
def hexdump(b:bytes)->str: return " ".join(f"{x:02X}" for x in b)

def build_read_variable_frame(addr_ascii: str, data_type: int, count: int = 1, invoked_id: int = 1) -> bytes:
    if not addr_ascii.endswith("\x00"):
        addr_field = addr_ascii.encode("ascii") + b"\x00"
    else:
        addr_field = addr_ascii.encode("ascii")

    # payload: CMD | DTYPE | RSV | BLOCKS | VARLEN | ADDR | COUNT
    payload = b"".join([
        CMD_READ_VARIABLE_REQ,     # 2 -> 54 00
        le16(data_type),           # 2 -> ex) WORD 02 00
        le16(0x0000),              # 2 reserved
        le16(0x0001),              # 2 block count
        le16(len(addr_field)),     # 2 var length
        addr_field,                # N
        le16(count),               # 2 data count
    ])

    header = b"".join([
        COMPANY_ID,                # 10
        PLC_INFO,                  # 2
        CPU_INFO,                  # 1
        SRC_REQ,                   # 1
        le16(invoked_id),          # 2
        le16(len(payload)),        # 2 (명령어부터 끝)
        b"\x00",                   # 1 position
        b"\x00",                   # 1 checksum (0 허용)
    ])
    return header + payload

def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed while receiving")
        buf += chunk
    return buf

def recv_xgt_response(sock: socket.socket) -> bytes:
    header = recv_exact(sock, 20)
    length = struct.unpack_from("<H", header, 16)[0]
    if length == 0:
        pos = header[18]; csum = header[19]
        raise RuntimeError(f"Header-only response (length=0). position=0x{pos:02X}, checksum=0x{csum:02X}")
    payload = recv_exact(sock, length)
    return header + payload

def parse_read_variable_response(frame: bytes):
    payload = frame[20:]
    p = 0

    cmd = payload[p:p+2]; p += 2
    if cmd != b'\x55\x00':
        raise RuntimeError(f"Unexpected Command in response: {cmd.hex()}")

    dtype = struct.unpack_from("<H", payload, p)[0]; p += 2
    _rsv  = payload[p:p+2]; p += 2

    # --- 축약형: 에러만 존재 ---
    if len(payload) == 8:
        err = struct.unpack_from("<H", payload, p)[0]
        return err, []

    # --- 확장형: 표대로 파싱 ---
    err   = struct.unpack_from("<H", payload, p)[0]; p += 2
    vlen  = struct.unpack_from("<H", payload, p)[0]; p += 2
    p += vlen
    cnt   = struct.unpack_from("<H", payload, p)[0]; p += 2
    if err != 0:
        return err, []

    unit = {0x0000:1, 0x0001:1, 0x0002:2, 0x0003:4, 0x0004:8}.get(dtype, 1)
    vals = []
    for _ in range(cnt):
        raw = payload[p:p+unit]; p += unit
        vals.append(int.from_bytes(raw, "little"))
    return 0, vals




def read_variable(address_ascii: str, data_type: int, count: int = 1, invoked_id: int = 1):
    req = build_read_variable_frame(address_ascii, data_type, count, invoked_id)
    print("[SEND]", hexdump(req))
    with socket.create_connection((XGT_IP, XGT_PORT), timeout=SOCK_TIMEOUT) as s:
        s.sendall(req)
        rsp = recv_xgt_response(s)
    print("[RECV]", hexdump(rsp))
    err, vals = parse_read_variable_response(rsp)
    if err:
        print(f"[XGT ERROR] 0x{err:04X}")
    else:
        print(f"[OK] {address_ascii} -> {vals}")
    return err, vals

if __name__ == "__main__":
    # 우선 문서/예시에 맞춘 형태: 주소는 ASCII "D4010"
    read_variable("%DW8020", DT_BYTE, count=1, invoked_id=0x0001)
