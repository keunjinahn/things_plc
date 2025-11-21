import socket
import struct

PLC_IP = "192.168.1.2"
PLC_PORT = 2004  # XGT Dedicated

def bcc_sum(data: bytes) -> int:
    """Application Header의 바이트 합(모듈러 256). BCC 자기 자신은 제외."""
    return sum(data) & 0xFF

def build_read_word(addr_str="%DW4010", count=1, invoke_id=0x0010, slot_base=0x00):
    """
    XGT Dedicated - Individual Read(WORD) 요청 프레임 구성
    addr_str 예: "%DW4010" (D영역 Word), "%MW0"(M Word), "%DB2468"(Byte) 등
    """
    # --- Company Header (10 bytes)
    company = b"LSIS-XGT" + b"\x00\x00"     # 4C 53 49 53 2D 58 47 54 00 00

    # --- Application Header (고정부; BCC 계산 직전까지)
    plc_info   = b"\x00\x00"               # 요청시 don't care
    cpu_info   = b"\xB0"                   # XGB
    src_frame  = b"\x33"                   # Client->Server
    inv_id     = struct.pack("<H", invoke_id)

    # Payload(명령부)는 나중에 만들고 길이를 채웁니다.
    # Length(2B)는 '명령부' 길이 (Command ~ 끝)
    # Position(1B): Base/Slot. PC에서 접속이면 0x00으로 두어도 무방.
    position   = struct.pack("B", slot_base)

    # 임시로 Length=0, BCC=0으로 두고 BCC 계산을 위해 헤더를 구성
    length     = b"\x00\x00"
    app_hdr_wo_bcc = plc_info + cpu_info + src_frame + inv_id + length + position
    bcc = struct.pack("B", bcc_sum(app_hdr_wo_bcc))

    # --- Command/DataType + Data(명령부)
    # Read Request: 0x5400, DataType WORD: 0x0200 (개별)
    cmd      = b"\x54\x00"
    dtype    = b"\x02\x00"                 # WORD
    reserved = b"\x00\x00"                 # Reserved(2)
    block_no = b"\x01\x00"                 # Block = 1
    addr     = addr_str.encode("ascii")    # 예: b"%DW4010"
    var_len  = struct.pack("<H", len(addr))
    cnt      = struct.pack("<H", count)

    payload  = cmd + dtype + reserved + block_no + var_len + addr + cnt
    length   = struct.pack("<H", len(payload))

    # Length 반영 후 BCC 재계산
    app_hdr_wo_bcc = plc_info + cpu_info + src_frame + inv_id + length + position
    bcc = struct.pack("B", bcc_sum(app_hdr_wo_bcc))

    request = company + app_hdr_wo_bcc + bcc + payload
    return request

def parse_read_word_response(resp: bytes):
    """
    0x5500(READ RESP) 개별 WORD 응답 파서
    구조(문서 표 5-7 요약):
      Company(10) | PLC(2) | CPU(1) | Src(1=0x11) | Invoke(2) | Len(2) | Pos(1) | BCC(1)
      Cmd(2=0x5500) | DataType(2=0x0200) | Reserved(2) | Error(2) | VarLen(2) | DataCnt(2) | Data(2*cnt)
    """
    # 헤더 끝 인덱스 계산
    i = 0
    i += 10  # company
    i += 2   # plc info
    i += 1   # cpu info
    i += 1   # source (0x11)
    i += 2   # invoke id
    length = int.from_bytes(resp[i:i+2], "little"); i += 2
    i += 1   # position
    i += 1   # bcc

    cmd = resp[i:i+2]; i += 2
    dtype = resp[i:i+2]; i += 2
    reserved = resp[i:i+2]; i += 2
    err = int.from_bytes(resp[i:i+2], "little"); i += 2
    if err != 0:
        raise RuntimeError(f"PLC Error: 0x{err:04X}")

    var_len = int.from_bytes(resp[i:i+2], "little"); i += 2
    data_cnt = int.from_bytes(resp[i:i+2], "little"); i += 2

    # WORD 데이터: 각 값은 LE 2바이트
    values = []
    for _ in range(data_cnt):
        v = int.from_bytes(resp[i:i+2], "little"); i += 2
        values.append(v)
    return {
        "length_field": length,
        "cmd": cmd,
        "dtype": dtype,
        "count": data_cnt,
        "values": values,
    }

def xgt_read_dw(addr_str="%DW4010", count=1):
    req = build_read_word(addr_str, count)
    print("[SEND]", " ".join(f"{b:02X}" for b in req))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        s.connect((PLC_IP, PLC_PORT))
        s.sendall(req)
        resp = s.recv(2048)
    print("[RECV]", " ".join(f"{b:02X}" for b in resp))
    parsed = parse_read_word_response(resp)
    vals = parsed["values"]
    # 보기 좋게 10진/16진 동시 출력
    for idx, v in enumerate(vals):
        print(f"{addr_str}+{idx}: dec={v}  hex=0x{v:04X}")
    return vals

if __name__ == "__main__":
    xgt_read_dw("%DW4010", 1)   # D4010 1워드
