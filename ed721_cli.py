"""ED-721 POS interface multi-command CLI (serial, no KiccPos.dll).

Refactored to import all protocol primitives from ed721_proto. NAK retry policy
is enforced by ed721_proto.send_and_wait — financial commands (FB/14/04) never
auto-retry on NAK.
"""

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
    ParsedPacket,
    RetryPolicy,
    decode_terminal_info,
    is_approval_success,
    is_cancel_success,
    is_failure_short_message,
    parse_kv_response,
    policy_for,
    send_and_wait,
)


def _format_hex(buf: bytes) -> str:
    return buf.hex(" ").upper()


def _default_port() -> str:
    return "COM3" if sys.platform.startswith("win") else "/dev/ttyUSB0"


def _resolve_framings(args: argparse.Namespace) -> Sequence[Framing]:
    if args.len_mode is not None or args.len_endian is not None or args.crc_endian is not None:
        if args.len_mode is None or args.len_endian is None or args.crc_endian is None:
            raise SystemExit("When overriding framing, set --len-mode, --len-endian and --crc-endian together.")
        return [Framing(args.len_mode, args.len_endian, args.crc_endian)]
    if args.no_auto:
        return [DEFAULT_FRAMING]
    primary = DEFAULT_FRAMING
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


def _print_business_judgement(parsed: ParsedPacket) -> None:
    if parsed.cmd != CMD or parsed.gcd != 0x14 or parsed.jcd != 0x04:
        return
    if parsed.rcd == 0xFF:
        msg = is_failure_short_message(parsed.data)
        print(f"[판정] 거래 실패 ({msg or '본문 별도'})")
        return
    if parsed.rcd == 0x00:
        kv = parse_kv_response(parsed.data)
        s01 = kv.get("S01", "")
        if s01 == "I1":
            ok = is_approval_success(kv)
            print(f"[판정] 승인 {'성공' if ok else '의심(R09=0 → 테스트모드 가능성)'}: "
                  f"S07={kv.get('S07')} R09={kv.get('R09')} R19={kv.get('R19', '')[:20]}")
            if ok:
                print(f"[취소용] S12={kv.get('R09')} S13={kv.get('R07', '')[:6]} S10={kv.get('S10')}")
        elif s01 == "I4":
            ok = is_cancel_success(kv)
            r17 = kv.get("R17", "")
            print(f"[판정] 취소 {'성공' if ok else '실패 (R17 존재)'}: "
                  f"R09={kv.get('R09', '(없음)')} R19={kv.get('R19', '')[:20]}")
            if r17:
                print(f"[안내] R17 메시지: {r17}")


def _print_parsed(parsed: ParsedPacket) -> None:
    print(
        f"[패킷] CNT={parsed.cnt} CMD={parsed.cmd:02X} GCD={parsed.gcd:02X} "
        f"JCD={parsed.jcd:02X} RCD={(parsed.rcd if parsed.rcd is not None else -1):02X}"
    )
    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x02 and parsed.rcd in (0x00, 0xFF):
        info = decode_terminal_info(parsed.data)
        print("[안내] 단말정보:" if info else f"[안내] 단말정보 데이터 길이={len(parsed.data)} (디코딩 실패)", info or "")
    if parsed.cmd == CMD and parsed.gcd == 0x01 and parsed.jcd == 0x06 and parsed.rcd in (0x00, 0xFF):
        print(f"[안내] RFID SNO (hex): {parsed.data.hex().upper()}")
    if parsed.cmd == CMD and parsed.gcd == 0x14 and parsed.jcd == 0x04 and parsed.data:
        try:
            print(f"[안내] 승인응답 Data(ASCII): {parsed.data.decode('ascii', errors='replace')}")
        except Exception:
            print(f"[안내] 승인응답 Data(hex): {parsed.data.hex().upper()}")


def _acquire_port_lock(port: str) -> None:
    """Linux-only fcntl lock to prevent two instances from sharing the serial port."""
    if sys.platform.startswith("win"):
        return
    try:
        import fcntl, os as _os
        path = f"/tmp/ed721{port.replace('/', '_')}.lock"
        fd = _os.open(path, _os.O_CREAT | _os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"[오류] 다른 프로세스가 {port}를 사용 중입니다. (lock={path})")
            sys.exit(3)
    except ImportError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="ED-721 POS serial CLI (no DLL)")
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
    parser.add_argument("--data")
    parser.add_argument("--data-hex")
    parser.add_argument("--retry", type=int, default=3,
                        help="NAK retry count for safe commands (financial cmds always 1)")
    parser.add_argument("--force-retry-financial", action="store_true",
                        help="Override safety: allow NAK retry for FB/14/04. Use only with full understanding.")

    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "info", "display", "approval", "sound", "image"):
        subs.add_parser(name)
    rfid = subs.add_parser("rfid")
    rfid.add_argument("--reverse", action="store_true")

    args = parser.parse_args()

    if args.list_ports:
        if list_ports is None:
            print("[WARN] serial.tools.list_ports unavailable")
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
    cmd_t = cmd_map[args.command]

    data_bytes = _build_data_bytes(args)
    if args.command == "rfid" and args.reverse:
        data_bytes = b"R"

    framings = _resolve_framings(args)

    # Decide retry policy
    policy = policy_for(cmd_t[2], cmd_t[1])
    if args.force_retry_financial and policy == RetryPolicy.NEVER:
        print("[경고] --force-retry-financial: 승인/취소에 NAK 재전송 활성화 (중복청구 위험)")
        policy = RetryPolicy.SAFE
    max_retries = args.retry if policy == RetryPolicy.SAFE else 1

    _acquire_port_lock(args.port)

    try:
        with serial.Serial(
            port=args.port, baudrate=args.baud, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
            timeout=args.timeout, write_timeout=args.timeout,
        ) as ser:
            ser.reset_input_buffer(); ser.reset_output_buffer()
            last_buf = b""
            for idx, framing in enumerate(framings):
                cnt = ((args.cnt - 1 + idx) % 255) + 1
                buf, parsed, attempts = send_and_wait(
                    ser, cnt=cnt, cmd=cmd_t[0], gcd=cmd_t[1], jcd=cmd_t[2],
                    data=data_bytes, framing=framing, max_wait_sec=args.wait,
                    retry_policy=policy, max_retries=max_retries,
                )
                last_buf = buf
                print(f"[전송][len_mode={framing.len_mode} len={framing.len_endian} "
                      f"crc={framing.crc_endian}] (attempts={attempts})")

                if buf:
                    print(f"[수신] {len(buf)} 바이트: {_format_hex(buf)}")
                    if ACK_TRIPLE in buf:
                        print("[안내] ACK(06 06 06) 감지")
                    if NAK_TRIPLE in buf:
                        print(f"[안내] NAK(15 15 15) 감지 — 재시도 {attempts}회")
                else:
                    print("[수신] (데이터 없음)")

                if parsed is None:
                    continue
                _print_parsed(parsed)
                _print_business_judgement(parsed)
                return

            ack_only_cmds = {"init", "display", "sound", "image"}
            if args.command in ack_only_cmds and ACK_TRIPLE in last_buf:
                print(f"[판정] {args.command} 성공 (ACK 수신, 응답 본문 없음 = SPEC 정상)")
                return
            print("[오류] 현재 프레이밍으로 유효한 응답을 파싱하지 못했습니다.")
            sys.exit(2)
    except serial.SerialException as e:
        print(f"[오류] 시리얼 포트 {args.port!r} 열기 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
