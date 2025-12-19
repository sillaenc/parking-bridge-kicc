"""
ED-721 POS interface multi-command CLI (serial, no KiccPos.dll).

Supported commands (from SPEC):
- FB/14/01 : init
- FB/14/02 : terminal info (decodes fields)
- FB/14/03 : display message (DATA=ASCII, '|' for line breaks)
- FB/14/04 : approval request (DATA=key=value; ... ; raw ASCII)
- FB/14/13 : sound play (DATA=wav filename, e.g., beep.wav)
- FB/14/14 : image download (DATA=URL)
- FB/01/06 : RFID card serial number (DATA empty or "R")

Features:
- Builds STX|LEN|CNT|CMD|GCD|JCD|DATA|ETX|CRC with CRC16(0x8005, init 0xFFFF, LSB-first,
  final NOT + byte-swap), CRC range = LEN..ETX.
- Framing search: len_mode 0..3, len/crc endian big/little (spec default works on tested device).
- Sends, collects response, validates CRC, auto-ACK (06 06 06) when a valid packet is parsed.
- Prints hex dump and, when applicable, decoded info (terminal info / RFID SNO).

Prereq: pip install pyserial

Examples (Windows):
  python ed721_cli.py --port COM3 init
  python ed721_cli.py --port COM3 info
  python ed721_cli.py --port COM3 display --data "HELLO|LINE2||LINE4"
  python ed721_cli.py --port COM3 sound --data beep.wav
  python ed721_cli.py --port COM3 image --data http://example.com/img.png
  python ed721_cli.py --port COM3 rfid
  python ed721_cli.py --port COM3 approval --data "S00=002;S01=D1;S02=40;S09=00;S10=1004;S23=POS001;"

If your device already worked with kicc_info_request.py, pin framing:
  --len-mode 2 --len-endian big --crc-endian big
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
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
ACK_TRIPLE = bytes([0x06, 0x06, 0x06])
NAK_TRIPLE = bytes([0x15, 0x15, 0x15])

CMD = 0xFB

Endian = Literal["big", "little"]


@dataclass(frozen=True)
class Framing:
    """LEN/CRC framing definition."""

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
    """CRC16 per SPEC appendix get_crc (poly 0x8005, init 0xFFFF, LSB-first)."""

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


def build_packet(*, cnt: int, cmd: int, gcd: int, jcd: int, data: bytes, framing: Framing) -> bytes:
    len_value = _compute_len_value(framing=framing, data_len=len(data))
    len_bytes = len_value.to_bytes(2, byteorder=framing.len_endian)
    payload = len_bytes + bytes([cnt, cmd, gcd, jcd]) + data + bytes([ETX])
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
    """Return first CRC-valid packet in buf per framing definition."""

    for start in range(len(buf)):
        if buf[start] != STX:
            continue
        if start + 3 > len(buf):
            break
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
    """Decode FB 14 02 response data (excluding RCD)."""

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


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def _default_port() -> str:
    if sys.platform.startswith("win"):
        return "COM3"
    return "/dev/ttyUSB0"


def _request_once(
    *,
    ser: serial.Serial,
    framing: Framing,
    cnt: int,
    cmd: int,
    gcd: int,
    jcd: int,
    data: bytes,
    max_wait_sec: float,
) -> Tuple[bytes, Optional[ParsedPacket]]:
    ser.reset_input_buffer()
    pkt = build_packet(cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, data=data, framing=framing)
    print(
        f"[전송][len_mode={framing.len_mode} len={framing.len_endian} crc={framing.crc_endian}] "
        f"{_format_hex(pkt)}"
    )
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


def _resolve_framings(args: argparse.Namespace) -> Sequence[Framing]:
    if args.len_mode is not None or args.len_endian is not None or args.crc_endian is not None:
        if args.len_mode is None or args.len_endian is None or args.crc_endian is None:
            raise SystemExit("When overriding framing, set --len-mode, --len-endian and --crc-endian together.")
        return [Framing(args.len_mode, args.len_endian, args.crc_endian)]

    primary = Framing(2, "big", "big")
    if args.no_auto:
        return [primary]

    rest = [
        Framing(lm, le, ce)
        for lm in range(4)
        for le in ("big", "little")
        for ce in ("big", "little")
        if (lm, le, ce) != (primary.len_mode, primary.len_endian, primary.crc_endian)
    ]
    return [primary, *rest]


def _build_data_bytes(args: argparse.Namespace) -> bytes:
    if args.data and args.data_hex:
        raise SystemExit("Use either --data (ASCII) or --data-hex (hex string), not both.")
    if args.data_hex:
        try:
            return bytes.fromhex(args.data_hex.replace(" ", ""))
        except ValueError as e:
            raise SystemExit(f"Invalid hex in --data-hex: {e}") from e
    if args.data:
        return args.data.encode("ascii")
    return b""


def _print_parsed(parsed: ParsedPacket) -> None:
    print(
        f"[패킷] CNT={parsed.cnt} CMD={parsed.cmd:02X} GCD={parsed.gcd:02X} "
        f"JCD={parsed.jcd:02X} RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}"
    )
    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x02 and parsed.rcd in (0x00, 0xFF):
        info = decode_terminal_info_fields(parsed.data)
        if info:
            print("[안내] 단말정보:", info)
        else:
            print(f"[안내] 단말정보 데이터 길이={len(parsed.data)} (디코딩 실패)")
    if parsed.cmd == CMD and parsed.gcd == 0x01 and parsed.jcd == 0x06 and parsed.rcd in (0x00, 0xFF):
        # RFID SNO read: data = 4 bytes (binary). Show hex.
        print(f"[안내] RFID SNO (hex): {parsed.data.hex().upper()}")
    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x04 and parsed.rcd in (0x00, 0xFF):
        # 승인/취소/재전송 응답: Data가 ASCII라면 표시
        if parsed.data:
            try:
                txt = parsed.data.decode("ascii", errors="replace")
                print(f"[안내] 승인응답 Data(ASCII): {txt}")
            except Exception:
                print(f"[안내] 승인응답 Data(hex): {parsed.data.hex().upper()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ED-721 POS serial CLI (no DLL)")
    parser.add_argument("--port", default=_default_port(), help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.05, help="serial read timeout (sec)")
    parser.add_argument("--wait", type=float, default=2.0, help="max wait for response (sec)")
    parser.add_argument("--cnt", type=int, default=1, help="packet counter start (1..255)")
    parser.add_argument("--list-ports", action="store_true", help="list serial ports and exit")
    parser.add_argument("--no-auto", action="store_true", help="do not try framing fallbacks")
    parser.add_argument("--len-mode", type=int, choices=[0, 1, 2, 3])
    parser.add_argument("--len-endian", choices=["big", "little"])
    parser.add_argument("--crc-endian", choices=["big", "little"])
    parser.add_argument("--data", help="ASCII data payload (e.g., approval fields Sxx=...;)")
    parser.add_argument("--data-hex", help="Hex data payload (no 0x prefix, spaces allowed)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="FB/14/01 terminal init (no data)")
    subparsers.add_parser("info", help="FB/14/02 terminal info (no data)")
    subparsers.add_parser("display", help="FB/14/03 display message (data=ASCII, '|' for lines)")
    subparsers.add_parser("approval", help="FB/14/04 approval request (data=Sxx=...;)")
    subparsers.add_parser("sound", help="FB/14/13 play sound (data=wav name, e.g., beep.wav)")
    subparsers.add_parser("image", help="FB/14/14 image download (data=URL)")
    rfid = subparsers.add_parser("rfid", help="FB/01/06 RFID card serial (data empty or 'R')")
    rfid.add_argument("--reverse", action="store_true", help='send data "R" (reverse option in spec)')

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

    cmd_map = {
        "init": (CMD, 0x14, 0x01),
        "info": (CMD, 0x14, 0x02),
        "display": (CMD, 0x14, 0x03),
        "approval": (CMD, 0x14, 0x04),
        "sound": (CMD, 0x14, 0x13),
        "image": (CMD, 0x14, 0x14),
        "rfid": (CMD, 0x01, 0x06),
    }
    cmd_tuple = cmd_map[args.command]

    data_bytes = _build_data_bytes(args)
    if args.command == "rfid" and args.reverse:
        data_bytes = b"R"

    framings = _resolve_framings(args)

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
                buf, parsed = _request_once(
                    ser=ser,
                    framing=framing,
                    cnt=cnt,
                    cmd=cmd_tuple[0],
                    gcd=cmd_tuple[1],
                    jcd=cmd_tuple[2],
                    data=data_bytes,
                    max_wait_sec=args.wait,
                )
                last_buf = buf

                if buf:
                    print(f"[수신] {len(buf)} 바이트: {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[안내] ACK(06 06 06) 감지")
                    if NAK_TRIPLE in buf:
                        print("[안내] NAK(15 15 15) 감지")
                else:
                    print("[수신] (데이터 없음)")

                if parsed is None:
                    continue

                _print_parsed(parsed)
                return

            print("[오류] 현재 프레이밍으로 유효한 응답을 파싱하지 못했습니다.")
            if last_buf:
                print("[힌트] 위에 출력된 hex 덤프를 참고하거나 공유해 주세요.")
            sys.exit(2)
    except serial.SerialException as e:
        print(f"[오류] 시리얼 포트 {args.port!r} 열기 실패: {e}")
        if sys.platform.startswith("win"):
            print("[힌트] COM 포트는 동시에 한 프로그램만 열 수 없습니다. 다른 프로그램을 모두 종료하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
