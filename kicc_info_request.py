"""
Send ED-721 terminal-info request (CMD=0xFB, GCD=0x14, JCD=0x02) over serial.

This script talks *directly* to the ED-721 serial protocol (no KiccPos.dll).

Protocol (per spec):
  STX(0x02) | LEN(2) | CNT | CMD | GCD | JCD | [RCD] | DATA | ETX(0x03) | CRC(2)

CRC is implemented exactly as appendix get_crc:
  poly 0x8005, init 0xFFFF, LSB-first, final bitwise NOT then byte swap.
CRC covers LEN..ETX (inclusive).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys
import time
from typing import Iterable, Literal, Optional, Sequence, Tuple

try:
    import serial
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit("pyserial is required: pip install pyserial") from e

try:
    from serial.tools import list_ports
except Exception:  # pragma: no cover
    list_ports = None  # optional

STX = 0x02
ETX = 0x03
CMD = 0xFB
GCD = 0x14
JCD_INFO = 0x02  # terminal info request
ACK_TRIPLE = bytes([0x06, 0x06, 0x06])
NAK_TRIPLE = bytes([0x15, 0x15, 0x15])

Endian = Literal["big", "little"]


@dataclass(frozen=True)
class Framing:
    """Packet framing variations.

    Real devices are sometimes picky about LEN definition / endian and CRC byte order.
    We support a small search space (same as kicc_crc_fuzzer.py).

    len_mode meanings (DATA length = len(DATA) excluding ETX/CRC and excluding STX):
      0: LEN = CNT+CMD+GCD+JCD+DATA
      1: LEN = CNT+CMD+GCD+JCD+DATA+ETX
      2: LEN = LEN(2)+CNT+CMD+GCD+JCD+DATA
      3: LEN = LEN(2)+CNT+CMD+GCD+JCD+DATA+ETX
    """

    len_mode: int
    len_endian: Endian
    crc_endian: Endian


@dataclass(frozen=True)
class ParsedPacket:
    raw: bytes
    cnt: int
    cmd: int
    gcd: int
    jcd: int
    rcd: Optional[int]
    data: bytes


def calc_crc(data: Iterable[int]) -> int:
    """CRC16 per spec appendix get_crc (poly 0x8005, init 0xFFFF, LSB-first)."""

    seed = 0x8005
    crc = 0xFFFF
    for b in data:
        temp = b & 0xFF
        for _ in range(8):
            if (crc & 1) ^ (temp & 1):
                crc = (crc >> 1) ^ seed
            else:
                crc >>= 1
            temp >>= 1
    crc = (~crc) & 0xFFFF
    temp = crc
    crc = ((crc << 8) | ((temp >> 8) & 0xFF)) & 0xFFFF
    return crc


def _compute_len_value(*, framing: Framing, data_len: int) -> int:
    base_len = 4 + data_len  # CNT+CMD+GCD+JCD+DATA
    if framing.len_mode == 0:
        return base_len
    if framing.len_mode == 1:
        return base_len + 1  # +ETX
    if framing.len_mode == 2:
        return base_len + 2  # +LEN(2)
    if framing.len_mode == 3:
        return base_len + 3  # +LEN(2)+ETX
    raise ValueError("len_mode must be 0..3")


def build_request_packet(*, cnt: int, framing: Framing) -> bytes:
    """Build `FB 14 02` terminal-info request packet (DATA empty)."""

    data_bytes = b""
    len_value = _compute_len_value(framing=framing, data_len=len(data_bytes))
    len_bytes = len_value.to_bytes(2, byteorder=framing.len_endian)

    payload = len_bytes + bytes([cnt, CMD, GCD, JCD_INFO]) + data_bytes + bytes([ETX])
    crc_val = calc_crc(payload)  # LEN..ETX
    crc_bytes = crc_val.to_bytes(2, byteorder=framing.crc_endian)
    return bytes([STX]) + payload + crc_bytes


def _data_len_from_len_value(*, framing: Framing, len_value: int) -> Optional[int]:
    if framing.len_mode == 0:
        data_len = len_value - 4
    elif framing.len_mode == 1:
        data_len = len_value - 5
    elif framing.len_mode == 2:
        data_len = len_value - 6
    elif framing.len_mode == 3:
        data_len = len_value - 7
    else:
        return None
    if data_len < 0:
        return None
    return data_len


def try_parse_first_packet(buf: bytes, framing: Framing) -> Optional[ParsedPacket]:
    """Scan `buf` and return the first CRC-valid packet matching `framing`."""

    for start in range(len(buf)):
        if buf[start] != STX:
            continue
        if start + 3 > len(buf):
            break  # not enough bytes for LEN
        len_bytes = buf[start + 1 : start + 3]
        len_value = int.from_bytes(len_bytes, byteorder=framing.len_endian)
        data_len = _data_len_from_len_value(framing=framing, len_value=len_value)
        if data_len is None:
            continue

        total_len = 10 + data_len  # STX + LEN(2) + CNT+CMD+GCD+JCD + DATA + ETX + CRC(2)
        end = start + total_len
        if end > len(buf):
            continue

        pkt = buf[start:end]
        etx_index = 7 + data_len
        if pkt[etx_index] != ETX:
            continue

        crc_expected = calc_crc(pkt[1 : etx_index + 1])  # LEN..ETX
        crc_got = int.from_bytes(pkt[etx_index + 1 : etx_index + 3], byteorder=framing.crc_endian)
        if crc_got != crc_expected:
            continue

        cnt = pkt[3]
        cmd = pkt[4]
        gcd = pkt[5]
        jcd = pkt[6]
        data_bytes = pkt[7:etx_index]
        rcd = data_bytes[0] if data_bytes else None
        rest = data_bytes[1:] if data_bytes else b""
        return ParsedPacket(raw=pkt, cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, rcd=rcd, data=rest)

    return None


def _decode_ascii_field(b: bytes) -> str:
    return b.decode("ascii", errors="replace").rstrip("\x00").strip()


def decode_terminal_info_fields(data: bytes) -> Optional[dict]:
    """Decode `FB 14 02` response data fields (excluding RCD)."""

    # Spec: model(4), version(4), serial(12), secure_id(16), tid(10), termno(3), ip/port(30)
    expected = 4 + 4 + 12 + 16 + 10 + 3 + 30
    if len(data) < expected:
        return None

    model = _decode_ascii_field(data[0:4])
    version = _decode_ascii_field(data[4:8])
    serial_no = _decode_ascii_field(data[8:20])
    secure_id = _decode_ascii_field(data[20:36])
    tid = _decode_ascii_field(data[36:46])
    term_no = _decode_ascii_field(data[46:49])
    ip_port = _decode_ascii_field(data[49:79])
    return {
        "model": model,
        "version": version,
        "serial_no": serial_no,
        "secure_id": secure_id,
        "tid": tid,
        "terminal_no": term_no,
        "ip_port": ip_port,
    }


def _read_until_deadline(ser: serial.Serial, deadline: float) -> bytes:
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            continue
        time.sleep(0.01)
    return buf


def _request_once(
    *,
    ser: serial.Serial,
    framing: Framing,
    cnt: int,
    max_wait_sec: float,
) -> Tuple[bytes, Optional[ParsedPacket]]:
    ser.reset_input_buffer()
    pkt = build_request_packet(cnt=cnt, framing=framing)
    print(f"[SEND][len_mode={framing.len_mode} len={framing.len_endian} crc={framing.crc_endian}] {pkt.hex(' ').upper()}")
    ser.write(pkt)
    ser.flush()

    deadline = time.time() + max_wait_sec
    buf = b""
    parsed: Optional[ParsedPacket] = None
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            parsed = try_parse_first_packet(buf, framing)
            if parsed is not None:
                # POS must ACK after receiving response.
                ser.write(ACK_TRIPLE)
                ser.flush()
                break
            continue
        time.sleep(0.01)

    return buf, parsed


def _default_port() -> str:
    if sys.platform.startswith("win"):
        return "COM3"
    # macOS/others: a sensible placeholder (user should override)
    return "/dev/ttyUSB0"


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="KICC ED-721 terminal info request over serial")
    parser.add_argument("--port", default=_default_port(), help="e.g. COM3 (Windows) or /dev/ttyUSB0 (Linux)")
    parser.add_argument("--baud", type=int, default=115200, help="default 115200")
    parser.add_argument("--timeout", type=float, default=0.05, help="serial read timeout (sec)")
    parser.add_argument("--wait", type=float, default=2.0, help="max wait for response (sec)")
    parser.add_argument("--cnt", type=int, default=1, help="packet counter (1..255)")
    parser.add_argument("--list-ports", action="store_true", help="list serial ports and exit")
    parser.add_argument("--no-auto", action="store_true", help="do not try fallback framing combinations")
    parser.add_argument("--len-mode", type=int, choices=[0, 1, 2, 3], help="override LEN mode (0..3)")
    parser.add_argument("--len-endian", choices=["big", "little"], help="override LEN endian")
    parser.add_argument("--crc-endian", choices=["big", "little"], help="override CRC endian")
    args = parser.parse_args()

    if args.list_ports:
        if list_ports is None:
            print("[WARN] serial.tools.list_ports is not available in this environment.")
        else:
            for p in list_ports.comports():
                print(f"{p.device}\t{p.description}")
        return

    if not (1 <= args.cnt <= 255):
        raise SystemExit("--cnt must be 1..255")

    if args.len_mode is not None or args.len_endian is not None or args.crc_endian is not None:
        if args.len_mode is None or args.len_endian is None or args.crc_endian is None:
            raise SystemExit("When overriding framing, set --len-mode, --len-endian and --crc-endian together.")
        framings: Sequence[Framing] = [Framing(args.len_mode, args.len_endian, args.crc_endian)]
    else:
        # Try spec-default first, then try the remaining combinations unless disabled.
        primary = Framing(2, "big", "big")
        if args.no_auto:
            framings = [primary]
        else:
            rest = [
                Framing(lm, le, ce)
                for lm in range(4)
                for le in ("big", "little")
                for ce in ("big", "little")
                if (lm, le, ce) != (primary.len_mode, primary.len_endian, primary.crc_endian)
            ]
            framings = [primary, *rest]

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baud,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=args.timeout,
            write_timeout=args.timeout,
        ) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            last_buf = b""
            for idx, framing in enumerate(framings):
                cnt = ((args.cnt - 1 + idx) % 255) + 1
                buf, parsed = _request_once(ser=ser, framing=framing, cnt=cnt, max_wait_sec=args.wait)
                last_buf = buf

                if buf:
                    print(f"[RECV] {len(buf)} bytes: {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[INFO] ACK(06 06 06) detected")
                    if NAK_TRIPLE in buf:
                        print("[INFO] NAK(15 15 15) detected")
                else:
                    print("[RECV] (no data)")

                if parsed is None:
                    continue

                print(
                    f"[PKT] CNT={parsed.cnt} CMD={parsed.cmd:02X} GCD={parsed.gcd:02X} "
                    f"JCD={parsed.jcd:02X} RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}"
                )
                if parsed.cmd == CMD and parsed.gcd == GCD and parsed.jcd == JCD_INFO and parsed.rcd in (0x00, 0xFF):
                    info = decode_terminal_info_fields(parsed.data)
                    if info is None:
                        print(f"[INFO] terminal-info data too short: {len(parsed.data)} bytes")
                    else:
                        print("[INFO] terminal-info:", info)
                    return
    except serial.SerialException as e:
        print(f"[ERROR] Failed to open serial port {args.port!r}: {e}")
        if sys.platform.startswith("win"):
            print("[HINT] COM 포트는 동시에 한 프로그램만 열 수 있습니다.")
            print("       KiccTest.exe(샘플), 시리얼 모니터, PuTTY/TeraTerm 등을 모두 종료하고 다시 시도하세요.")
            print("       그래도 안 되면 USB 분리/재연결 또는 재부팅이 필요할 수 있습니다.")
        sys.exit(1)

        print("[ERROR] Failed to parse a valid terminal-info response with tested framings.")
        if last_buf:
            print("[HINT] If you see bytes but parsing fails, share the hex dump above.")
        sys.exit(2)


if __name__ == "__main__":
    main()
