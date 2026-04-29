"""ED-721 protocol primitives shared by CLI/menu/fuzzer.

Frame: STX | LEN(2) | CNT | CMD | GCD | JCD | DATA | ETX | CRC(2)
CRC: poly 0x8005, init 0xFFFF, LSB-first, final ~ + byte-swap. Range = LEN..ETX.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Literal, Optional, Tuple

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


DEFAULT_FRAMING = Framing(len_mode=2, len_endian="big", crc_endian="big")


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
    crc = ((crc << 8) | ((crc >> 8) & 0xFF)) & 0xFFFF
    return crc


def compute_len_value(*, framing: Framing, data_len: int) -> int:
    base = 4 + data_len  # CNT+CMD+GCD+JCD+DATA
    if framing.len_mode == 0:
        return base
    if framing.len_mode == 1:
        return base + 1
    if framing.len_mode == 2:
        return base + 2
    if framing.len_mode == 3:
        return base + 3
    raise ValueError("len_mode must be 0..3")


def data_len_from_len_value(*, framing: Framing, len_value: int) -> Optional[int]:
    table = {0: 4, 1: 5, 2: 6, 3: 7}
    if framing.len_mode not in table:
        return None
    n = len_value - table[framing.len_mode]
    return n if n >= 0 else None


def build_packet(
    *,
    cnt: int,
    cmd: int,
    gcd: int,
    jcd: int,
    data: bytes,
    framing: Framing = DEFAULT_FRAMING,
) -> bytes:
    if not (1 <= cnt <= 255):
        raise ValueError("cnt must be 1..255")
    len_value = compute_len_value(framing=framing, data_len=len(data))
    len_bytes = len_value.to_bytes(2, byteorder=framing.len_endian)
    payload = len_bytes + bytes([cnt, cmd, gcd, jcd]) + data + bytes([ETX])
    crc_val = calc_crc(payload)
    crc_bytes = crc_val.to_bytes(2, byteorder=framing.crc_endian)
    return bytes([STX]) + payload + crc_bytes


def try_parse_first_packet(buf: bytes, framing: Framing = DEFAULT_FRAMING) -> Optional[ParsedPacket]:
    """Find first CRC-valid packet in buf; tolerate leading garbage (e.g. ACK)."""
    for start in range(len(buf)):
        if buf[start] != STX:
            continue
        if start + 3 > len(buf):
            break
        len_value = int.from_bytes(buf[start + 1 : start + 3], byteorder=framing.len_endian)
        data_len = data_len_from_len_value(framing=framing, len_value=len_value)
        if data_len is None:
            continue
        total = 10 + data_len  # STX + LEN(2) + 4 + DATA + ETX + CRC(2)
        end = start + total
        if end > len(buf):
            continue
        pkt = buf[start:end]
        etx_idx = 7 + data_len
        if pkt[etx_idx] != ETX:
            continue
        crc_expected = calc_crc(pkt[1 : etx_idx + 1])
        crc_got = int.from_bytes(pkt[etx_idx + 1 : etx_idx + 3], byteorder=framing.crc_endian)
        if crc_got != crc_expected:
            continue
        cnt = pkt[3]
        cmd = pkt[4]
        gcd = pkt[5]
        jcd = pkt[6]
        body = pkt[7:etx_idx]
        rcd = body[0] if body else None
        rest = body[1:] if body else b""
        return ParsedPacket(raw=pkt, cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, rcd=rcd, data=rest)
    return None


def next_cnt(cnt: int) -> int:
    """1..255 wrap; 255 -> 1."""
    if not (1 <= cnt <= 255):
        raise ValueError("cnt must be 1..255")
    return 1 if cnt == 255 else cnt + 1


def _decode_ascii(b: bytes) -> str:
    return b.decode("ascii", errors="replace").rstrip("\x00").strip()


FAILURE_DATA_VALUES = {b"CANCELED", b"TIMEOUT", b"FAIL"}


def is_failure_short_message(data: bytes) -> Optional[str]:
    """If response DATA is one of {CANCELED, TIMEOUT, FAIL}, return that string. Else None."""
    if data in FAILURE_DATA_VALUES:
        return data.decode("ascii")
    return None


def parse_kv_response(data: bytes) -> dict[str, str]:
    """Parse approval response body 'KEY=VAL;KEY=VAL;...'. EUC-KR aware.

    Returns mapping of keys (S00, S07, R09, ...) to decoded string values.
    Tolerates trailing/empty segments. Treats first '=' as separator.
    """
    try:
        text = data.decode("euc-kr", errors="replace")
    except Exception:
        text = data.decode("ascii", errors="replace")
    out: dict[str, str] = {}
    for seg in text.split(";"):
        if not seg:
            continue
        eq = seg.find("=")
        if eq <= 0:
            continue
        out[seg[:eq].strip()] = seg[eq + 1 :]
    return out


def is_cancel_success(fields: dict[str, str]) -> bool:
    """Decide whether a D4 cancel response represents real PG-level success.

    Rules learned from real-device testing (see docs/03_phase3_realtxn.md):
      - R17 must be ABSENT (presence indicates a failure message like "승인 거래 없음")
      - R09 must be present and non-zero (PG transaction id)
      - S01 should be "I4"
      - R19 should NOT be "전표:효력없음"-style; success looks like "KICC로제출"
    Caller must already have validated RCD == 0x00 at the frame level.
    """
    if fields.get("S01") != "I4":
        return False
    if "R17" in fields:
        return False
    r09 = fields.get("R09", "")
    if not r09 or set(r09) == {"0"}:
        return False
    r19 = fields.get("R19", "")
    if "효력없음" in r19:
        return False
    return True


def is_approval_success(fields: dict[str, str]) -> bool:
    """Decide whether a D1 approval response is a real, billable approval.

    Rules:
      - S01 == "I1"
      - R02 == "A"
      - R09 present and non-zero (real PG tx id; if all zeros => test/demo mode)
    Caller must already have validated RCD == 0x00.
    """
    if fields.get("S01") != "I1":
        return False
    if fields.get("R02") != "A":
        return False
    r09 = fields.get("R09", "")
    if not r09 or set(r09) == {"0"}:
        return False
    return True


def extract_cancel_info(approval_fields: dict[str, str]) -> Optional[dict[str, str]]:
    """Given a successful approval's parsed fields, build the cancel parameters.

    Returns dict suitable for D4 DATA construction:
      - S12 = R09 (NOT S07 — S07 is a placeholder on this device)
      - S13 = first 6 chars of R07 (YYMMDD)
      - S10 = original amount
    Returns None if required fields are missing.
    """
    r09 = approval_fields.get("R09")
    r07 = approval_fields.get("R07", "")
    s10 = approval_fields.get("S10")
    if not r09 or not r07 or len(r07) < 6 or s10 is None:
        return None
    return {
        "S12": r09,
        "S13": r07[:6],
        "S10": s10.zfill(10),
    }


def build_cancel_data(*, approval_fields: dict[str, str], pos_id: str = "POSCANC") -> Optional[bytes]:
    """Build the ASCII DATA payload for a D4 cancel given prior approval fields."""
    info = extract_cancel_info(approval_fields)
    if info is None:
        return None
    payload = (
        f"S00=002;S01=D4;S02=40;S09=00;"
        f"S10={info['S10']};S12={info['S12']};S13={info['S13']};S23={pos_id};"
    )
    return payload.encode("ascii")


class RetryPolicy(str, Enum):
    """NAK retry policy. Transaction commands (D1/D4/LA) MUST use NEVER to avoid
    double-charge: device may have actually processed the first packet and the NAK
    came from line noise on a separate read.
    """
    NEVER = "never"      # send once, no retry on NAK
    SAFE = "safe"        # retry up to N times — only for idempotent/non-financial commands
    PROMPT = "prompt"    # caller decides; helper returns NAK as-is


def policy_for(jcd: int, gcd: int = 0x14) -> RetryPolicy:
    """Default retry policy for a given GCD/JCD pair."""
    # Transaction-related commands: D1/D4/LA all use FB/14/04
    if gcd == 0x14 and jcd == 0x04:
        return RetryPolicy.NEVER
    return RetryPolicy.SAFE


def send_and_wait(
    ser,
    *,
    cnt: int,
    cmd: int,
    gcd: int,
    jcd: int,
    data: bytes = b"",
    framing: "Framing" = None,
    max_wait_sec: float = 3.0,
    retry_policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    retry_backoff_sec: float = 0.1,
    auto_ack: bool = True,
) -> Tuple[bytes, Optional["ParsedPacket"], int]:
    """Send a request and wait for a CRC-valid response, with NAK retry.

    Returns: (last_buf, parsed_or_None, attempts_made)

    NAK handling:
      - retry_policy NEVER: NAK -> return immediately (no retry)
      - retry_policy SAFE: same packet (same CNT) re-sent up to max_retries-1 times
      - retry_policy PROMPT: returns to caller, who can decide whether to resend
    """
    if framing is None:
        framing = DEFAULT_FRAMING
    if retry_policy is None:
        retry_policy = policy_for(jcd, gcd)

    pkt = build_packet(cnt=cnt, cmd=cmd, gcd=gcd, jcd=jcd, data=data, framing=framing)

    attempt = 0
    last_buf = b""
    parsed: Optional[ParsedPacket] = None
    while attempt < max_retries:
        attempt += 1
        try:
            ser.reset_input_buffer()
        except Exception:
            pass
        ser.write(pkt)
        ser.flush()

        deadline = time.time() + max_wait_sec
        buf = b""
        while time.time() < deadline:
            chunk = ser.read(ser.in_waiting or 1)
            if chunk:
                buf += chunk
                parsed = try_parse_first_packet(buf, framing)
                if parsed is not None:
                    if auto_ack:
                        try:
                            ser.write(ACK_TRIPLE)
                            ser.flush()
                        except Exception:
                            pass
                    return buf, parsed, attempt
                # If we already have a clear NAK and no parsed packet, decide based on policy.
                if NAK_TRIPLE in buf and ACK_TRIPLE not in buf:
                    break
            else:
                time.sleep(0.01)

        last_buf = buf

        # Decide retry
        if NAK_TRIPLE in buf or buf == b"\x15":
            if retry_policy != RetryPolicy.SAFE:
                return last_buf, None, attempt
            if attempt >= max_retries:
                return last_buf, None, attempt
            time.sleep(retry_backoff_sec)
            continue
        # No NAK and no parsed packet: just timeout. Don't retry (deterministic behavior).
        return last_buf, None, attempt

    return last_buf, parsed, attempt


def decode_terminal_info(data: bytes) -> Optional[dict]:
    """Decode FB/14/02 response (RCD already stripped). 79 bytes expected."""
    expected = 4 + 4 + 12 + 16 + 10 + 3 + 30
    if len(data) < expected:
        return None
    return {
        "model": _decode_ascii(data[0:4]),
        "version": _decode_ascii(data[4:8]),
        "serial_no": _decode_ascii(data[8:20]),
        "secure_id": _decode_ascii(data[20:36]),
        "tid": _decode_ascii(data[36:46]),
        "terminal_no": _decode_ascii(data[46:49]),
        "ip_port": _decode_ascii(data[49:79]),
    }
