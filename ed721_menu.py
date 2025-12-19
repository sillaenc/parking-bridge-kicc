"""
Interactive menu for ED-721 commands (serial, no KiccPos.dll).
Uses the same framing/CRC as ed721_cli.py but provides a simple 1,2,3... menu.

Supported items:
 1) init      (FB/14/01)
 2) info      (FB/14/02)
 3) display   (FB/14/03, ASCII, '|' for new lines)
 4) approval  (FB/14/04, ASCII key/val e.g. S00=002;S01=D1;...)
 5) sound     (FB/14/13, wav name e.g. beep.wav)
 6) image     (FB/14/14, URL)
 7) rfid      (FB/01/06, optionally send 'R')
 0) exit

Prereq: pip install pyserial
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Tuple

try:
    import serial
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit("pyserial is required: pip install pyserial") from e

STX = 0x02
ETX = 0x03
ACK_TRIPLE = bytes([0x06, 0x06, 0x06])
NAK_TRIPLE = bytes([0x15, 0x15, 0x15])

CMD = 0xFB

Endian = Literal["big", "little"]


@dataclass(frozen=True)
class Framing:
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


def _compute_len_value(framing: Framing, data_len: int) -> int:
    base_len = 4 + data_len
    if framing.len_mode == 0:
        return base_len
    if framing.len_mode == 1:
        return base_len + 1
    if framing.len_mode == 2:
        return base_len + 2
    if framing.len_mode == 3:
        return base_len + 3
    raise ValueError("len_mode must be 0..3")


def build_packet(*, cnt: int, cmd: int, gcd: int, jcd: int, data: bytes, framing: Framing) -> bytes:
    length = _compute_len_value(framing, len(data))
    len_bytes = length.to_bytes(2, byteorder=framing.len_endian)
    payload = len_bytes + bytes([cnt, cmd, gcd, jcd]) + data + bytes([ETX])
    crc_val = calc_crc(payload)
    crc_bytes = crc_val.to_bytes(2, byteorder=framing.crc_endian)
    return bytes([STX]) + payload + crc_bytes


def _data_len_from_len_value(framing: Framing, len_value: int) -> Optional[int]:
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
    for start in range(len(buf)):
        if buf[start] != STX:
            continue
        if start + 3 > len(buf):
            break
        len_bytes = buf[start + 1 : start + 3]
        len_value = int.from_bytes(len_bytes, byteorder=framing.len_endian)
        data_len = _data_len_from_len_value(framing, len_value)
        if data_len is None:
            continue

        total_len = 10 + data_len
        end = start + total_len
        if end > len(buf):
            continue

        pkt = buf[start:end]
        etx_index = 7 + data_len
        if pkt[etx_index] != ETX:
            continue

        crc_expected = calc_crc(pkt[1 : etx_index + 1])
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


def decode_terminal_info_fields(data: bytes) -> Optional[dict]:
    expected = 4 + 4 + 12 + 16 + 10 + 3 + 30
    if len(data) < expected:
        return None
    return {
        "model": data[0:4].decode("ascii", errors="replace").strip(),
        "version": data[4:8].decode("ascii", errors="replace").strip(),
        "serial_no": data[8:20].decode("ascii", errors="replace").strip(),
        "secure_id": data[20:36].decode("ascii", errors="replace").strip(),
        "tid": data[36:46].decode("ascii", errors="replace").strip(),
        "terminal_no": data[46:49].decode("ascii", errors="replace").strip(),
        "ip_port": data[49:79].decode("ascii", errors="replace").strip(),
    }


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def send_command(
    *,
    ser: serial.Serial,
    framing: Framing,
    cnt: int,
    cmd: int,
    gcd: int,
    jcd: int,
    data: bytes,
    wait: float,
) -> Tuple[bytes, Optional[ParsedPacket]]:
    ser.reset_input_buffer()
    pkt = build_packet(cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, data=data, framing=framing)
    print(f"[SEND] {_format_hex(pkt)}")
    ser.write(pkt)
    ser.flush()

    buf = b""
    parsed = None
    deadline = time.time() + wait
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            parsed = try_parse_first_packet(buf, framing)
            if parsed:
                ser.write(ACK_TRIPLE)
                ser.flush()
                break
            continue
        time.sleep(0.01)
    return buf, parsed


def choose(prompt: str, default: str) -> str:
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def main() -> None:
    port = choose("Serial port (e.g., COM3)", "COM3" if sys.platform.startswith("win") else "/dev/ttyUSB0")
    baud = int(choose("Baudrate", "115200"))
    wait = float(choose("Max wait seconds", "2.0"))
    cnt_base = int(choose("Starting CNT (1-255)", "1"))

    # framing defaults to known-good: len_mode=2, big, big
    framing = Framing(len_mode=int(choose("len_mode (0-3)", "2")), len_endian="big", crc_endian="big")

    cmd_map = {
        "1": ("init", (CMD, 0x14, 0x01)),
        "2": ("info", (CMD, 0x14, 0x02)),
        "3": ("display", (CMD, 0x14, 0x03)),
        "4": ("approval", (CMD, 0x14, 0x04)),
        "5": ("sound", (CMD, 0x14, 0x13)),
        "6": ("image", (CMD, 0x14, 0x14)),
        "7": ("rfid", (CMD, 0x01, 0x06)),
    }

    menu = """
Select command:
 1) init (FB/14/01)
 2) info (FB/14/02)
 3) display (FB/14/03)
 4) approval (FB/14/04)
 5) sound (FB/14/13)
 6) image (FB/14/14)
 7) rfid (FB/01/06)
 0) exit
> """

    try:
        with serial.Serial(
            port=port,
            baudrate=baud,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.05,
            write_timeout=0.05,
        ) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            cnt = cnt_base

            while True:
                choice = input(menu).strip()
                if choice == "0":
                    print("bye")
                    return
                if choice not in cmd_map:
                    print("Invalid choice")
                    continue

                name, (cmd, gcd, jcd) = cmd_map[choice]
                data = b""
                if name in ("display", "approval", "sound", "image"):
                    data = input("Enter data (ASCII): ").encode("ascii", errors="ignore")
                if name == "rfid":
                    rev = input('Send "R" (reverse) ? [y/N]: ').lower().startswith("y")
                    data = b"R" if rev else b""

                buf, parsed = send_command(
                    ser=ser,
                    framing=framing,
                    cnt=cnt,
                    cmd=cmd,
                    gcd=gcd,
                    jcd=jcd,
                    data=data,
                    wait=wait,
                )
                cnt = (cnt % 255) + 1

                if buf:
                    print(f"[RECV] {len(buf)} bytes: {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[INFO] ACK detected")
                    if NAK_TRIPLE in buf:
                        print("[INFO] NAK detected")
                else:
                    print("[RECV] (no data)")

                if parsed:
                    print(
                        f"[PKT] CNT={parsed.cnt} CMD={parsed.cmd:02X} GCD={parsed.gcd:02X} "
                        f"JCD={parsed.jcd:02X} RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}"
                    )
                    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x02:
                        info = decode_terminal_info_fields(parsed.data)
                        print("[INFO] terminal-info:", info)
                    if parsed.cmd == CMD and parsed.gcd == 0x01 and parsed.jcd == 0x06:
                        print(f"[INFO] RFID SNO (hex): {parsed.data.hex().upper()}")
                else:
                    print("[WARN] No valid packet parsed.")

    except serial.SerialException as e:
        print(f"[ERROR] Cannot open port {port!r}: {e}")
        if sys.platform.startswith("win"):
            print("[HINT] Close other apps using the COM port (KiccTest.exe, serial monitors, etc).")
        sys.exit(1)


if __name__ == "__main__":
    main()
