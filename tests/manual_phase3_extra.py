"""Phase 3 extra — invalid DATA / invalid CRC / rapid-fire single-process tests.

Each test prints what was sent and what came back. Card insertion is NOT required;
short waits used. After each approval-like test we send a small wait + try to settle
the device to home before next test.
"""
from __future__ import annotations
import json, sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import serial
from ed721_proto import (
    STX, ETX, ACK_TRIPLE, NAK_TRIPLE, build_packet, calc_crc,
    try_parse_first_packet, DEFAULT_FRAMING, parse_kv_response,
    is_failure_short_message,
)

PORT = "/dev/ttyUSB0"
results = []


def send_raw_and_read(ser, raw, *, wait=3.0, label=""):
    ser.reset_input_buffer()
    ser.write(raw); ser.flush()
    deadline = time.time() + wait
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
        else:
            time.sleep(0.01)
    parsed = try_parse_first_packet(buf, DEFAULT_FRAMING)
    if parsed:
        try:
            ser.write(ACK_TRIPLE); ser.flush()
        except Exception:
            pass
    summary = {
        "label": label,
        "tx_hex": raw.hex(" ").upper(),
        "rx_len": len(buf),
        "rx_hex": buf.hex(" ").upper() if buf else "",
        "had_ack": ACK_TRIPLE in buf,
        "had_nak": NAK_TRIPLE in buf,
        "rcd": parsed.rcd if parsed else None,
        "data": (parsed.data.decode("ascii", errors="replace") if parsed and parsed.data else None),
    }
    print(f"\n=== {label} ===")
    print(f"TX({len(raw)}B): {summary['tx_hex']}")
    print(f"RX({summary['rx_len']}B): {summary['rx_hex'] or '(empty)'}")
    if parsed:
        print(f"  parsed: RCD={parsed.rcd:02X} CNT={parsed.cnt} DATA={summary['data'][:80] if summary['data'] else ''}")
    results.append(summary)
    return parsed


def settle(ser):
    """Best-effort: send NAK to clear, then short pause."""
    time.sleep(0.5)


def main():
    ser = serial.Serial(PORT, 115200, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                        timeout=0.05, write_timeout=0.5)
    try:
        ser.reset_input_buffer(); ser.reset_output_buffer()

        # ---------- A. Invalid DATA on approval ----------
        approval_cases = [
            ("A1_no_S00",       b"S01=D1;S02=40;S09=00;S10=0000000001;S23=PA1;"),
            ("A2_no_S01",       b"S00=002;S02=40;S09=00;S10=0000000001;S23=PA2;"),
            ("A3_no_S10",       b"S00=002;S01=D1;S02=40;S09=00;S23=PA3;"),
            ("A4_invalid_S01",  b"S00=002;S01=ZZ;S02=40;S09=00;S10=0000000001;S23=PA4;"),
            ("A5_zero_amount",  b"S00=002;S01=D1;S02=40;S09=00;S10=0000000000;S23=PA5;"),
            ("A6_big_amount",  b"S00=002;S01=D1;S02=40;S09=00;S10=9999999999;S23=PA6;"),
            ("A7_empty_data",   b""),
            ("A8_no_semicolons",b"S00=002 S01=D1 S10=0000000001"),
        ]
        for label, data in approval_cases:
            pkt = build_packet(cnt=1, cmd=0xFB, gcd=0x14, jcd=0x04, data=data)
            send_raw_and_read(ser, pkt, wait=5, label=label)
            settle(ser)

        # ---------- B. Invalid CRC / framing ----------
        # Build a valid info packet, then mutate it in different ways.
        good = build_packet(cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02, data=b"")

        # B1: flip last CRC byte
        b1 = bytearray(good); b1[-1] ^= 0xFF
        send_raw_and_read(ser, bytes(b1), wait=2, label="B1_crc_flipped")
        settle(ser)

        # B2: ETX byte zeroed
        b2 = bytearray(good)
        # find ETX position
        etx_idx = len(good) - 3
        assert b2[etx_idx] == ETX
        b2[etx_idx] = 0x00
        send_raw_and_read(ser, bytes(b2), wait=2, label="B2_etx_zeroed")
        settle(ser)

        # B3: missing CRC bytes (truncate last 2)
        send_raw_and_read(ser, good[:-2], wait=2, label="B3_no_crc")
        settle(ser)

        # B4: STX duplicated at front
        send_raw_and_read(ser, b"\x02" + good, wait=2, label="B4_extra_stx")
        settle(ser)

        # B5: completely random 10 bytes starting with STX (unlikely valid CRC)
        rand = bytes([STX, 0x00, 0x06, 0x01, 0xFB, 0x14, 0x02, ETX, 0xAB, 0xCD])
        send_raw_and_read(ser, rand, wait=2, label="B5_random_crc")
        settle(ser)

        # B6: send only STX
        send_raw_and_read(ser, b"\x02", wait=2, label="B6_stx_only")
        settle(ser)

        # ---------- C. Rapid-fire info ----------
        print("\n=== C. Rapid-fire info x10 (no per-call wait) ===")
        # Send 10 info requests quickly; collect responses afterward
        c_results = []
        for i in range(10):
            pkt = build_packet(cnt=((i % 254) + 1), cmd=0xFB, gcd=0x14, jcd=0x02, data=b"")
            ser.write(pkt)
        ser.flush()
        # Read for up to 8s and try to parse all packets
        deadline = time.time() + 8
        buf = b""
        parsed_count = 0
        while time.time() < deadline:
            chunk = ser.read(ser.in_waiting or 1)
            if chunk:
                buf += chunk
                while True:
                    p = try_parse_first_packet(buf, DEFAULT_FRAMING)
                    if not p:
                        break
                    parsed_count += 1
                    ser.write(ACK_TRIPLE); ser.flush()
                    idx = buf.find(p.raw) + len(p.raw)
                    buf = buf[idx:]
            else:
                time.sleep(0.005)
        results.append({
            "label": "C_rapid_fire_info_x10",
            "tx_count": 10,
            "rx_total_bytes_unused": len(buf),
            "parsed_count": parsed_count,
            "remaining_buf_hex": buf.hex(" ").upper(),
        })
        print(f"sent=10  parsed={parsed_count}  remaining={len(buf)}B")

        # Save full results
        out_path = os.path.join(os.path.dirname(__file__), "fixtures", "phase3_extra_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVED] {out_path}")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
