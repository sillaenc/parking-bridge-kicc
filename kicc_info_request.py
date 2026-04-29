"""Send ED-721 terminal-info request (FB/14/02) over serial. Refactored to use ed721_proto."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

try:
    import serial
except ModuleNotFoundError as e:
    raise SystemExit("pyserial is required: pip install pyserial") from e

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None

from ed721_proto import (
    ACK_TRIPLE,
    CMD,
    DEFAULT_FRAMING,
    Framing,
    NAK_TRIPLE,
    decode_terminal_info,
    send_and_wait,
)

GCD = 0x14
JCD_INFO = 0x02


def _default_port() -> str:
    return "COM3" if sys.platform.startswith("win") else "/dev/ttyUSB0"


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="KICC ED-721 terminal info request")
    parser.add_argument("--port", default=_default_port())
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.05)
    parser.add_argument("--wait", type=float, default=2.0)
    parser.add_argument("--cnt", type=int, default=1)
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--no-auto", action="store_true")
    parser.add_argument("--len-mode", type=int, choices=[0, 1, 2, 3])
    parser.add_argument("--len-endian", choices=["big", "little"])
    parser.add_argument("--crc-endian", choices=["big", "little"])
    args = parser.parse_args()

    if args.list_ports:
        if list_ports is None:
            print("[WARN] list_ports unavailable")
        else:
            for p in list_ports.comports():
                print(f"{p.device}\t{p.description}")
        return

    if not (1 <= args.cnt <= 255):
        raise SystemExit("--cnt must be 1..255")

    if args.len_mode is not None or args.len_endian is not None or args.crc_endian is not None:
        if args.len_mode is None or args.len_endian is None or args.crc_endian is None:
            raise SystemExit("Set --len-mode, --len-endian, --crc-endian together.")
        framings: Sequence[Framing] = [Framing(args.len_mode, args.len_endian, args.crc_endian)]
    else:
        primary = DEFAULT_FRAMING
        if args.no_auto:
            framings = [primary]
        else:
            rest = [Framing(lm, le, ce) for lm in range(4)
                    for le in ("big", "little") for ce in ("big", "little")
                    if (lm, le, ce) != (primary.len_mode, primary.len_endian, primary.crc_endian)]
            framings = [primary, *rest]

    try:
        with serial.Serial(
            port=args.port, baudrate=args.baud, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
            timeout=args.timeout, write_timeout=args.timeout,
        ) as ser:
            ser.reset_input_buffer(); ser.reset_output_buffer()
            for idx, framing in enumerate(framings):
                cnt = ((args.cnt - 1 + idx) % 255) + 1
                buf, parsed, attempts = send_and_wait(
                    ser, cnt=cnt, cmd=CMD, gcd=GCD, jcd=JCD_INFO,
                    data=b"", framing=framing, max_wait_sec=args.wait,
                )
                print(f"[SEND][len_mode={framing.len_mode} len={framing.len_endian} "
                      f"crc={framing.crc_endian}] (attempts={attempts})")

                if buf:
                    print(f"[RECV] {len(buf)} bytes: {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[INFO] ACK detected")
                    if NAK_TRIPLE in buf:
                        print(f"[INFO] NAK detected (재시도 {attempts}회)")
                else:
                    print("[RECV] (no data)")

                if parsed is None:
                    continue

                print(f"[PKT] CNT={parsed.cnt} GCD={parsed.gcd:02X} JCD={parsed.jcd:02X} "
                      f"RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}")
                if parsed.cmd == CMD and parsed.gcd == GCD and parsed.jcd == JCD_INFO:
                    info = decode_terminal_info(parsed.data)
                    if info is None:
                        print(f"[INFO] terminal-info data too short: {len(parsed.data)} bytes")
                    else:
                        print("[INFO] terminal-info:", info)
                    return
            print("[ERROR] Failed to parse a valid response with tested framings.")
            sys.exit(2)
    except serial.SerialException as e:
        print(f"[ERROR] Failed to open serial port {args.port!r}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
