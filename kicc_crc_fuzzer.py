"""
KICC ED-721 CRC/LEN 퍼저

목적:
- RS-232 통신은 되지만(NAK 수신), 단말기가 패킷 포맷/CRC를 거부하는 상황에서
  ACK(0x06) 응답이 나오는 조합(LEN 계산/엔디안, CRC 바이트 순서)을 찾는다.

주의:
- 이 스크립트는 많은 패킷을 전송한다. 테스트 중에는 단말기/컨버터가 과열되지 않도록 주의한다.
- ACK가 나오면 즉시 중단하고 결과를 파일로 저장한다.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Literal, Optional, Tuple

import serial


# Protocol bytes
STX = 0x02
ETX = 0x03

# 흔히 관측되는 응답 패턴
ACK_TRIPLE = bytes([0x06, 0x06, 0x06])
NAK_TRIPLE = bytes([0x15, 0x15, 0x15])

# 기본 명령(기존 payment_kicc.py 기반): CMD=0xFB, GCD=0x14, JCD=0x01(초기화)
DEFAULT_CMD_BYTES = bytes([0xFB, 0x14, 0x01])

# 파일/동작 상수
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT_SEC = 0.15
DEFAULT_INTER_PACKET_DELAY_SEC = 0.005
DEFAULT_CHECKPOINT_EVERY = 1024


LenEndian = Literal["little", "big"]
CrcEndian = Literal["little", "big"]


@dataclass(frozen=True)
class FuzzMode:
    """퍼징 조합(단말이 요구하는 LEN/CRC 인코딩을 찾기 위한 파라미터 집합)"""

    len_mode: int
    len_endian: LenEndian
    crc_endian: CrcEndian


@dataclass
class Checkpoint:
    """장시간 퍼징 중 재시작을 위한 진행 상황 저장 구조"""

    mode_index: int
    crc_value: int


def _now_ts() -> str:
    """로그 파일명/기록용 타임스탬프 문자열을 생성한다."""

    return time.strftime("%Y%m%d-%H%M%S")


def _safe_write_json(file_path: str, payload: dict) -> None:
    """중간에 프로세스가 죽어도 파일이 깨지지 않도록 원자적으로 JSON을 저장한다."""

    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, file_path)


def _pack_u16(value: int, endian: LenEndian) -> bytes:
    """uint16 값을 지정된 엔디안으로 패킹한다."""

    if endian == "little":
        return bytes([value & 0xFF, (value >> 8) & 0xFF])
    return bytes([(value >> 8) & 0xFF, value & 0xFF])


def _build_packet(
    *,
    cnt: int,
    cmd_bytes: bytes,
    data_bytes: bytes,
    fuzz_mode: FuzzMode,
    crc_value: int,
) -> bytes:
    """
    단말에 전송할 패킷을 조립한다.

    구조(가정):
    [STX][LEN(2)][CNT(1)][CMD(1)][GCD(1)][JCD(1)][DATA][ETX][CRC(2)]

    LEN 모드(전수 탐색):
    - 0: LEN = (CNT+CMD+GCD+JCD+DATA) = 4 + len(DATA)
    - 1: LEN = (CNT+CMD+GCD+JCD+DATA+ETX) = 5 + len(DATA)
    - 2: LEN = (LEN(2)+CNT+CMD+GCD+JCD+DATA) = 6 + len(DATA)
    - 3: LEN = (LEN(2)+CNT+CMD+GCD+JCD+DATA+ETX) = 7 + len(DATA)
    """

    if not (1 <= cnt <= 255):
        raise ValueError("cnt must be 1..255")
    if len(cmd_bytes) != 3:
        raise ValueError("cmd_bytes must be 3 bytes (CMD,GCD,JCD)")
    if not (0 <= crc_value <= 0xFFFF):
        raise ValueError("crc_value must be 0..65535")

    base_len = 4 + len(data_bytes)
    if fuzz_mode.len_mode == 0:
        length = base_len
    elif fuzz_mode.len_mode == 1:
        length = base_len + 1
    elif fuzz_mode.len_mode == 2:
        length = base_len + 2
    elif fuzz_mode.len_mode == 3:
        length = base_len + 3
    else:
        raise ValueError("len_mode must be 0..3")

    len_bytes = _pack_u16(length, fuzz_mode.len_endian)
    cnt_byte = bytes([cnt])
    etx_byte = bytes([ETX])

    crc_bytes = _pack_u16(crc_value, fuzz_mode.crc_endian)
    payload = len_bytes + cnt_byte + cmd_bytes + data_bytes + etx_byte
    return bytes([STX]) + payload + crc_bytes


def _read_reply(ser: serial.Serial, timeout_sec: float) -> bytes:
    """짧은 타임아웃으로 단말 응답(ACK/NAK 포함)을 읽어온다."""

    start = time.time()
    buffer = b""
    while time.time() - start < timeout_sec:
        waiting = ser.in_waiting
        if waiting:
            buffer += ser.read(waiting)
            # ACK/NAK는 즉시 판단할 수 있도록 빠르게 탈출한다.
            if (ACK_TRIPLE in buffer) or (NAK_TRIPLE in buffer) or (b"\x06" in buffer) or (b"\x15" in buffer):
                break
        time.sleep(0.002)
    return buffer


def _open_serial(
    *,
    port: str,
    baudrate: int,
    parity: str,
    stopbits: int,
    bytesize: int,
    read_timeout_sec: float,
) -> serial.Serial:
    """시리얼 포트를 열고 기본 옵션을 적용한다."""

    parity_map = {
        "N": serial.PARITY_NONE,
        "E": serial.PARITY_EVEN,
        "O": serial.PARITY_ODD,
    }
    if parity not in parity_map:
        raise ValueError("parity must be one of: N, E, O")

    return serial.Serial(
        port=port,
        baudrate=baudrate,
        parity=parity_map[parity],
        stopbits=serial.STOPBITS_ONE if stopbits == 1 else serial.STOPBITS_TWO,
        bytesize=serial.EIGHTBITS if bytesize == 8 else serial.SEVENBITS,
        timeout=read_timeout_sec,
        write_timeout=read_timeout_sec,
    )


def fuzz_kicc_crc(
    *,
    port: str,
    baudrate: int,
    parity: str,
    stopbits: int,
    bytesize: int,
    cnt: int,
    cmd_bytes: bytes,
    data_bytes: bytes,
    inter_packet_delay_sec: float,
    response_timeout_sec: float,
    checkpoint_path: str,
    found_path: str,
    checkpoint_every: int,
    start_mode_index: int,
    start_crc_value: int,
    max_packets: Optional[int],
) -> Optional[Tuple[FuzzMode, int]]:
    """
    CRC 값을 전수 시도하며 ACK가 나오는 조합을 찾는다.

    반환:
    - (FuzzMode, crc_value) if found
    - None if not found (또는 max_packets로 종료)
    """

    # 퍼징 모드(= LEN 정의/엔디안 + CRC 바이트 순서) 전수 목록을 만든다.
    fuzz_modes = [
        FuzzMode(len_mode=lm, len_endian=le, crc_endian=ce)
        for lm in range(4)
        for le in ("little", "big")
        for ce in ("little", "big")
    ]

    isFound = False
    sent_packets = 0

    mode_index = max(0, min(start_mode_index, len(fuzz_modes) - 1))
    crc_value = max(0, min(start_crc_value, 0xFFFF))

    # 성능 최적화:
    # - 이전 버전은 CRC 1회 시도마다 포트를 열고 닫아(오버헤드 큼) 시간이 과도하게 소요됐다.
    # - 이제는 포트를 한 번 열고, 모드/CRC 루프를 돌며 재사용한다.
    # - 단말/컨버터 재부팅 등으로 끊기면 그때만 재연결한다.
    ser: Optional[serial.Serial] = None

    def _ensure_connected() -> serial.Serial:
        """시리얼 포트 연결을 보장하고(필요 시 재연결) 핸들을 반환한다."""

        nonlocal ser
        if ser is not None and getattr(ser, "is_open", False):
            return ser

        while True:
            try:
                ser = _open_serial(
                    port=port,
                    baudrate=baudrate,
                    parity=parity,
                    stopbits=stopbits,
                    bytesize=bytesize,
                    read_timeout_sec=response_timeout_sec,
                )
                try:
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except Exception:
                    # 일부 드라이버에서 지원되지 않는 경우가 있어 무시한다.
                    pass
                print("[CONNECTED] serial port opened.", flush=True)
                return ser
            except (serial.SerialException, OSError) as e:
                print(f"[WARN] serial open failed: {e} (retrying in 1s)", flush=True)
                time.sleep(1.0)

    def _disconnect() -> None:
        """시리얼 포트를 안전하게 닫고 핸들을 초기화한다."""

        nonlocal ser
        try:
            if ser is not None and getattr(ser, "is_open", False):
                ser.close()
        finally:
            ser = None

    while mode_index < len(fuzz_modes):
        fuzz_mode = fuzz_modes[mode_index]
        print(f"[MODE] index={mode_index}/{len(fuzz_modes)-1} {fuzz_mode}", flush=True)

        while crc_value <= 0xFFFF:
            if max_packets is not None and sent_packets >= max_packets:
                print(f"[STOP] max_packets reached: {max_packets}", flush=True)
                _disconnect()
                return None

            try:
                ser_handle = _ensure_connected()

                # 누적된 쓰레기 바이트(이전 시도의 NAK 등)가 다음 판정에 섞이지 않도록 가볍게 비운다.
                try:
                    if ser_handle.in_waiting:
                        ser_handle.read(ser_handle.in_waiting)
                except Exception:
                    # 읽기 도중 끊길 수 있으니, 아래 예외 처리에서 재연결한다.
                    pass

                packet = _build_packet(
                    cnt=cnt,
                    cmd_bytes=cmd_bytes,
                    data_bytes=data_bytes,
                    fuzz_mode=fuzz_mode,
                    crc_value=crc_value,
                )

                ser_handle.write(packet)
                ser_handle.flush()

                reply = _read_reply(ser_handle, timeout_sec=response_timeout_sec)
                sent_packets += 1

                hasAck = (ACK_TRIPLE in reply) or (b"\x06" in reply)
                hasNak = (NAK_TRIPLE in reply) or (b"\x15" in reply)

                if hasAck and not hasNak:
                    isFound = True
                    result = {
                        "ts": _now_ts(),
                        "port": port,
                        "baudrate": baudrate,
                        "parity": parity,
                        "stopbits": stopbits,
                        "bytesize": bytesize,
                        "mode": asdict(fuzz_mode),
                        "crc_value": crc_value,
                        "packet_hex": packet.hex().upper(),
                        "reply_hex": reply.hex().upper(),
                    }
                    _safe_write_json(found_path, result)
                    print(f"[FOUND] ACK detected. Saved: {found_path}", flush=True)
                    _disconnect()
                    return fuzz_mode, crc_value

                if (sent_packets % checkpoint_every) == 0:
                    _safe_write_json(
                        checkpoint_path,
                        asdict(Checkpoint(mode_index=mode_index, crc_value=crc_value)),
                    )
                    print(f"[CKPT] packets={sent_packets} mode={mode_index} crc=0x{crc_value:04X}", flush=True)

                crc_value += 1
                if inter_packet_delay_sec > 0:
                    time.sleep(inter_packet_delay_sec)

            except (serial.SerialException, OSError) as e:
                # 연결이 잠깐 끊기거나 장치가 재부팅되는 상황을 견딜 수 있도록 재시도한다.
                print(f"[WARN] serial error: {e} (retrying in 1s)", flush=True)
                _disconnect()
                time.sleep(1.0)
                continue
            except Exception as e:
                # 예상치 못한 오류는 원인 파악이 필요하므로 즉시 중단한다.
                print(f"[ERROR] unexpected error: {e}", flush=True)
                _disconnect()
                raise

        mode_index += 1
        crc_value = 0

    _disconnect()
    if not isFound:
        print("[DONE] no ACK detected in all modes.", flush=True)
    return None


def _load_checkpoint(checkpoint_path: str) -> Checkpoint:
    """체크포인트 파일이 있으면 로드하고, 없으면 0부터 시작한다."""

    if not os.path.exists(checkpoint_path):
        return Checkpoint(mode_index=0, crc_value=0)

    with open(checkpoint_path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return Checkpoint(mode_index=int(obj.get("mode_index", 0)), crc_value=int(obj.get("crc_value", 0)))


def main() -> None:
    """CLI 파라미터를 파싱해 퍼징을 실행한다."""

    parser = argparse.ArgumentParser(description="KICC ED-721 CRC/LEN fuzzer (find ACK).")
    parser.add_argument("--port", required=True, help="예: /dev/tty.usbserial-B000EYUJ")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--parity", choices=["N", "E", "O"], default="N")
    parser.add_argument("--stopbits", type=int, choices=[1, 2], default=1)
    parser.add_argument("--bytesize", type=int, choices=[7, 8], default=8)
    parser.add_argument("--cnt", type=int, default=1, help="CNT(1~255), 기본 1")

    parser.add_argument("--cmd-hex", default=DEFAULT_CMD_BYTES.hex(), help="CMD+GCD+JCD 3바이트(hex), 기본 FB1401")
    parser.add_argument("--data", default="", help="DATA(문자열). 빈 문자열이면 DATA 없음")
    parser.add_argument("--data-encoding", default="euc-kr", help="기본 euc-kr")

    parser.add_argument("--delay-sec", type=float, default=DEFAULT_INTER_PACKET_DELAY_SEC)
    parser.add_argument("--resp-timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--checkpoint-every", type=int, default=DEFAULT_CHECKPOINT_EVERY)
    parser.add_argument("--checkpoint-path", default="kicc_fuzz_checkpoint.json")
    parser.add_argument("--found-path", default="kicc_fuzz_found.json")
    parser.add_argument("--resume", action="store_true", help="체크포인트가 있으면 이어서 진행")
    parser.add_argument("--max-packets", type=int, default=None, help="디버깅용: 최대 전송 패킷 수 제한")

    args = parser.parse_args()

    cmd_bytes = bytes.fromhex(args.cmd_hex)
    if len(cmd_bytes) != 3:
        raise SystemExit("--cmd-hex must be 3 bytes (6 hex chars), e.g., FB1401")

    data_bytes = args.data.encode(args.data_encoding) if args.data else b""

    start_mode_index = 0
    start_crc_value = 0
    if args.resume:
        ckpt = _load_checkpoint(args.checkpoint_path)
        start_mode_index = ckpt.mode_index
        start_crc_value = ckpt.crc_value
        print(f"[RESUME] mode_index={start_mode_index}, crc=0x{start_crc_value:04X}", flush=True)

    fuzz_kicc_crc(
        port=args.port,
        baudrate=args.baudrate,
        parity=args.parity,
        stopbits=args.stopbits,
        bytesize=args.bytesize,
        cnt=args.cnt,
        cmd_bytes=cmd_bytes,
        data_bytes=data_bytes,
        inter_packet_delay_sec=args.delay_sec,
        response_timeout_sec=args.resp_timeout_sec,
        checkpoint_path=args.checkpoint_path,
        found_path=args.found_path,
        checkpoint_every=args.checkpoint_every,
        start_mode_index=start_mode_index,
        start_crc_value=start_crc_value,
        max_packets=args.max_packets,
    )


if __name__ == "__main__":
    main()


