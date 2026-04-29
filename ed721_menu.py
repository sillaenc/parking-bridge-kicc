"""Interactive menu for ED-721 commands. Refactored to use ed721_proto."""

from __future__ import annotations

import sys

try:
    import serial
except ModuleNotFoundError as e:
    raise SystemExit("pyserial is required: pip install pyserial") from e

from ed721_proto import (
    ACK_TRIPLE,
    CMD,
    DEFAULT_FRAMING,
    Framing,
    NAK_TRIPLE,
    decode_terminal_info,
    next_cnt,
    policy_for,
    send_and_wait,
)


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def choose(prompt: str, default: str) -> str:
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def main() -> None:
    port = choose("Serial port", "COM3" if sys.platform.startswith("win") else "/dev/ttyUSB0")
    baud = int(choose("Baudrate", "115200"))
    wait = float(choose("Max wait seconds", "2.0"))
    cnt = int(choose("Starting CNT (1-255)", "1"))
    framing = Framing(int(choose("len_mode (0-3)", "2")), "big", "big")

    cmd_map = {
        "1": ("init", (CMD, 0x14, 0x01)),
        "2": ("info", (CMD, 0x14, 0x02)),
        "3": ("display", (CMD, 0x14, 0x03)),
        "4": ("approval", (CMD, 0x14, 0x04)),
        "5": ("sound", (CMD, 0x14, 0x13)),
        "6": ("image", (CMD, 0x14, 0x14)),
        "7": ("rfid", (CMD, 0x01, 0x06)),
    }

    menu = ("\nSelect command:\n 1) init\n 2) info\n 3) display\n 4) approval\n"
            " 5) sound\n 6) image\n 7) rfid\n 0) exit\n> ")

    try:
        with serial.Serial(
            port=port, baudrate=baud, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
            timeout=0.05, write_timeout=0.5,
        ) as ser:
            ser.reset_input_buffer(); ser.reset_output_buffer()

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
                    data = b"R" if input('Send "R"? [y/N]: ').lower().startswith("y") else b""

                policy = policy_for(jcd, gcd)
                buf, parsed, attempts = send_and_wait(
                    ser, cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, data=data,
                    framing=framing, max_wait_sec=wait, retry_policy=policy,
                )
                cnt = next_cnt(cnt)

                if buf:
                    print(f"[RECV] {len(buf)}B (attempts={attempts}): {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[INFO] ACK")
                    if NAK_TRIPLE in buf:
                        print(f"[INFO] NAK (재시도 {attempts}회)")
                else:
                    print("[RECV] (no data)")

                if parsed:
                    print(f"[PKT] CNT={parsed.cnt} GCD={parsed.gcd:02X} JCD={parsed.jcd:02X} "
                          f"RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}")
                    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x02:
                        print("[INFO] terminal-info:", decode_terminal_info(parsed.data))
                    if parsed.cmd == CMD and parsed.gcd == 0x01 and parsed.jcd == 0x06:
                        print(f"[INFO] RFID SNO (hex): {parsed.data.hex().upper()}")
                else:
                    print("[WARN] No valid packet parsed.")
    except serial.SerialException as e:
        print(f"[ERROR] Cannot open port {port!r}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
