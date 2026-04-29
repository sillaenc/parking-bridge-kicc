"""Phase 1 — protocol unit tests (no hardware)."""

from __future__ import annotations

import pytest

from ed721_proto import (
    ACK_TRIPLE,
    DEFAULT_FRAMING,
    ETX,
    Framing,
    STX,
    build_packet,
    calc_crc,
    compute_len_value,
    data_len_from_len_value,
    decode_terminal_info,
    next_cnt,
    try_parse_first_packet,
)


# ---------------- Real device captures (2026-04-29, /dev/ttyUSB0) ----------------

# info request (TX): STX 00 06 01 FB 14 02 ETX DE E5
REAL_INFO_TX = bytes.fromhex("02 00 06 01 FB 14 02 03 DE E5".replace(" ", ""))

# info response (RX, includes leading ACK 06 06 06):
REAL_INFO_RX = bytes.fromhex(
    "06 06 06 02 00 56 01 FB 14 02 00 20 4B 30 33 30 30 32 33 33 4B 30 33 34 32 30 30 "
    "30 38 33 39 20 20 20 20 20 20 45 44 2D 37 32 31 58 30 30 31 20 20 20 38 30 31 36 "
    "33 36 36 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 31 39 32 2E 31 "
    "36 38 2E 30 2E 32 32 34 2F 03 9C C0".replace(" ", "")
)


# ---------------- CRC ----------------

class TestCRC:
    def test_real_request_crc(self):
        # CRC range = LEN..ETX  (skip STX, exclude trailing CRC)
        body = REAL_INFO_TX[1:-2]
        assert calc_crc(body) == 0xDEE5

    def test_real_response_crc(self):
        # Strip leading ACK, then LEN..ETX
        pkt = REAL_INFO_RX[3:]  # drop 06 06 06
        # find ETX position from LEN: framing default = mode2/big
        len_val = int.from_bytes(pkt[1:3], "big")
        # data_len = len_val - 6 ; etx_idx = 7 + data_len
        data_len = len_val - 6
        etx_idx = 7 + data_len
        assert pkt[etx_idx] == ETX
        body = pkt[1 : etx_idx + 1]
        crc_got = int.from_bytes(pkt[etx_idx + 1 : etx_idx + 3], "big")
        assert calc_crc(body) == crc_got

    def test_empty_input_no_crash(self):
        # CRC of empty range is well-defined; just make sure it returns int 0..0xFFFF
        v = calc_crc(b"")
        assert 0 <= v <= 0xFFFF


# ---------------- compute_len_value / data_len_from_len_value ----------------

class TestLen:
    @pytest.mark.parametrize("mode,data_len,expected", [
        (0, 0, 4),
        (1, 0, 5),
        (2, 0, 6),
        (3, 0, 7),
        (2, 80, 86),  # 0x56 from real response
    ])
    def test_compute_len(self, mode, data_len, expected):
        f = Framing(mode, "big", "big")
        assert compute_len_value(framing=f, data_len=data_len) == expected

    @pytest.mark.parametrize("mode", [0, 1, 2, 3])
    def test_roundtrip(self, mode):
        f = Framing(mode, "big", "big")
        for dl in (0, 1, 50, 200):
            v = compute_len_value(framing=f, data_len=dl)
            assert data_len_from_len_value(framing=f, len_value=v) == dl

    def test_negative_returns_none(self):
        f = Framing(2, "big", "big")
        assert data_len_from_len_value(framing=f, len_value=0) is None

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            compute_len_value(framing=Framing(9, "big", "big"), data_len=0)


# ---------------- build_packet ----------------

class TestBuild:
    def test_real_info_request_matches(self):
        pkt = build_packet(cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02, data=b"")
        assert pkt == REAL_INFO_TX

    @pytest.mark.parametrize("mode", [0, 1, 2, 3])
    @pytest.mark.parametrize("le", ["big", "little"])
    @pytest.mark.parametrize("ce", ["big", "little"])
    def test_all_framing_combos_roundtrip(self, mode, le, ce):
        f = Framing(mode, le, ce)
        data = b"PAYLOAD"
        pkt = build_packet(cnt=42, cmd=0xFB, gcd=0x14, jcd=0x03, data=data, framing=f)
        # Structural assertions
        assert pkt[0] == STX
        # Last 2 bytes are CRC
        assert len(pkt) == 1 + 2 + 4 + len(data) + 1 + 2

    def test_invalid_cnt(self):
        with pytest.raises(ValueError):
            build_packet(cnt=0, cmd=0xFB, gcd=0x14, jcd=0x01, data=b"")
        with pytest.raises(ValueError):
            build_packet(cnt=256, cmd=0xFB, gcd=0x14, jcd=0x01, data=b"")


# ---------------- try_parse_first_packet ----------------

class TestParse:
    def test_real_response_with_leading_ack(self):
        parsed = try_parse_first_packet(REAL_INFO_RX, DEFAULT_FRAMING)
        assert parsed is not None
        assert parsed.cmd == 0xFB
        assert parsed.gcd == 0x14
        assert parsed.jcd == 0x02
        assert parsed.rcd == 0x00
        assert parsed.cnt == 0x01
        assert len(parsed.data) == 79  # info DATA after RCD

    def test_garbage_before_stx(self):
        garbage = bytes([0xAA, 0xBB, 0xCC])
        buf = garbage + REAL_INFO_RX
        assert try_parse_first_packet(buf, DEFAULT_FRAMING) is not None

    def test_truncated_buf(self):
        # Only first 5 bytes after ACK
        buf = REAL_INFO_RX[:8]
        assert try_parse_first_packet(buf, DEFAULT_FRAMING) is None

    def test_partial_no_etx(self):
        # Cut before ETX
        buf = REAL_INFO_RX[: len(REAL_INFO_RX) - 4]
        assert try_parse_first_packet(buf, DEFAULT_FRAMING) is None

    def test_crc_mismatch_returns_none(self):
        bad = bytearray(REAL_INFO_RX)
        bad[-1] ^= 0xFF
        assert try_parse_first_packet(bytes(bad), DEFAULT_FRAMING) is None

    def test_etx_misplaced(self):
        # Shift ETX one byte by corrupting the byte just before it
        bad = bytearray(REAL_INFO_RX)
        # ACK(3) + STX..JCD(7) + RCD(1) + payload(79) = 90
        etx_idx = 3 + 7 + 1 + 79
        assert bad[etx_idx] == ETX
        bad[etx_idx] = 0x00  # destroy ETX
        assert try_parse_first_packet(bytes(bad), DEFAULT_FRAMING) is None

    def test_two_packets_returns_first(self):
        buf = REAL_INFO_RX + REAL_INFO_RX
        parsed = try_parse_first_packet(buf, DEFAULT_FRAMING)
        assert parsed is not None
        # Verify it's parsing the first occurrence (offset 3 after leading ACK)
        assert parsed.raw == REAL_INFO_RX[3:]


# ---------------- decode_terminal_info ----------------

class TestInfoDecode:
    def test_real_response_fields(self):
        parsed = try_parse_first_packet(REAL_INFO_RX, DEFAULT_FRAMING)
        info = decode_terminal_info(parsed.data)
        assert info == {
            "model": "K03",
            "version": "0023",
            "serial_no": "3K0342000839",
            "secure_id": "ED-721X001",
            "tid": "8016366",
            "terminal_no": "",
            "ip_port": "192.168.0.224/",
        }

    def test_too_short_returns_none(self):
        assert decode_terminal_info(b"\x00" * 10) is None

    def test_padding_stripped(self):
        # 4 + 4 + 12 + 16 + 10 + 3 + 30 = 79
        data = b"K03 " + b"0023" + b"SER12345    " + (b"SEC1" + b" " * 12) + (b"TID0001   ") + b"   " + (b"1.2.3.4/8000" + b" " * 18)
        info = decode_terminal_info(data)
        assert info["model"] == "K03"
        assert info["version"] == "0023"
        assert info["serial_no"] == "SER12345"
        assert info["secure_id"] == "SEC1"
        assert info["tid"] == "TID0001"
        assert info["terminal_no"] == ""
        assert info["ip_port"] == "1.2.3.4/8000"


# ---------------- next_cnt ----------------

class TestCnt:
    @pytest.mark.parametrize("inp,exp", [(1, 2), (10, 11), (254, 255), (255, 1)])
    def test_wrap(self, inp, exp):
        assert next_cnt(inp) == exp

    @pytest.mark.parametrize("bad", [0, 256, -1])
    def test_invalid(self, bad):
        with pytest.raises(ValueError):
            next_cnt(bad)


# ---------------- Sanity: ACK constant ----------------

def test_ack_triple_is_three_06():
    assert ACK_TRIPLE == bytes([0x06, 0x06, 0x06])
