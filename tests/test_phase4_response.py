"""Phase 4 — response parsing & success/failure judgement (regression).

Locks in the most important business rule discovered in Phase 3:
  * Cancel S12 must be R09, NOT S07 (S07 is a fixed placeholder on this device).
  * Cancel success requires R17 absence + R19!="전표:효력없음" + R09 set.
  * RCD=00 alone is NOT proof of business success.
"""

from __future__ import annotations

import pytest

from ed721_proto import (
    DEFAULT_FRAMING,
    build_cancel_data,
    extract_cancel_info,
    is_approval_success,
    is_cancel_success,
    is_failure_short_message,
    parse_kv_response,
    try_parse_first_packet,
)
from tests.fixtures.captures import (
    APPROVAL_FAIL_RX,
    APPROVAL_REAL_OK_RX,
    APPROVAL_TEST_MODE_OK_RX,
    APPROVAL_TIMEOUT_RX,
    APPROVAL_USER_CANCEL_RX,
    CANCEL_FAILED_RX,
    CANCEL_OK_RX,
    INFO_RX,
    RFID_CANCEL_RX,
    RFID_OK_RX,
)


def _parse(rx: bytes):
    return try_parse_first_packet(rx, DEFAULT_FRAMING)


# ---------------- Short failure messages ----------------

class TestFailureShortMessages:
    @pytest.mark.parametrize("rx,expected", [
        (APPROVAL_USER_CANCEL_RX, "CANCELED"),
        (APPROVAL_TIMEOUT_RX, "TIMEOUT"),
        (APPROVAL_FAIL_RX, "FAIL"),
        (RFID_CANCEL_RX, "CANCELED"),
    ])
    def test_recognized(self, rx, expected):
        p = _parse(rx)
        assert p is not None
        assert p.rcd == 0xFF
        assert is_failure_short_message(p.data) == expected

    def test_normal_data_returns_none(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        assert is_failure_short_message(p.data) is None


# ---------------- key=value parsing ----------------

class TestKVParse:
    def test_real_approval_fields(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        kv = parse_kv_response(p.data)
        assert kv["S00"] == "002"
        assert kv["S01"] == "I1"
        assert kv["S07"] == "949094"          # placeholder
        assert kv["S10"] == "10"
        assert kv["R02"] == "A"
        assert kv["R09"] == "30044993"        # real PG approval id
        assert kv["R23"] == "949094"

    def test_eucr_kr_korean_field(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        kv = parse_kv_response(p.data)
        assert "KICC" in kv["R19"]            # "KICC로제출"

    def test_test_mode_signals(self):
        """Test-mode approval has R09=zeros and R19='매입불가...' """
        p = _parse(APPROVAL_TEST_MODE_OK_RX)
        kv = parse_kv_response(p.data)
        assert kv["R09"] == "00000000"
        assert "매입불가" in kv["R19"] or "포인트" in kv["R19"]


# ---------------- approval success ----------------

class TestApprovalSuccess:
    def test_real_pg_approval_is_success(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        kv = parse_kv_response(p.data)
        assert is_approval_success(kv) is True

    def test_test_mode_approval_is_NOT_success(self):
        """R09=zeros means PG didn't actually take it — must NOT report success."""
        p = _parse(APPROVAL_TEST_MODE_OK_RX)
        kv = parse_kv_response(p.data)
        assert is_approval_success(kv) is False


# ---------------- cancel success/failure ----------------

class TestCancelSuccess:
    def test_real_cancel_is_success(self):
        p = _parse(CANCEL_OK_RX)
        kv = parse_kv_response(p.data)
        # Sanity: this came from S12=R09=30044993
        assert kv["S12"] == "30044993"
        assert is_cancel_success(kv) is True

    def test_failed_cancel_is_NOT_success(self):
        """The catastrophic case — RCD=00 but PG rejected.

        RCD-only check would return success here. We must report failure.
        """
        p = _parse(CANCEL_FAILED_RX)
        kv = parse_kv_response(p.data)
        assert p.rcd == 0x00            # frame says OK
        assert kv["S01"] == "I4"        # cancel response code
        assert kv["S12"] == "949094"    # we used S07 — wrong
        assert "R17" in kv              # presence of R17 = failure
        assert is_cancel_success(kv) is False


# ---------------- cancel info extraction ----------------

class TestExtractCancelInfo:
    def test_extracts_R09_not_S07(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        kv = parse_kv_response(p.data)
        info = extract_cancel_info(kv)
        assert info is not None
        assert info["S12"] == "30044993"      # R09
        assert info["S12"] != "949094"        # NOT S07
        assert info["S13"] == "260429"        # R07[:6]
        assert info["S10"] == "0000000010"    # zero-padded

    def test_returns_none_for_test_mode(self):
        """When R09 is all zeros (PG capture didn't happen), we still produce the params
        — caller can decide whether to actually use them based on is_approval_success."""
        p = _parse(APPROVAL_TEST_MODE_OK_RX)
        kv = parse_kv_response(p.data)
        info = extract_cancel_info(kv)
        # extract_cancel_info itself doesn't filter zeros — that's is_approval_success's job.
        # But it should still produce a dict.
        assert info is not None
        assert info["S12"] == "00000000"


class TestBuildCancelData:
    def test_round_trip(self):
        p = _parse(APPROVAL_REAL_OK_RX)
        kv = parse_kv_response(p.data)
        data = build_cancel_data(approval_fields=kv, pos_id="POSCN4")
        assert data is not None
        assert b"S01=D4" in data
        assert b"S12=30044993" in data
        assert b"S12=949094" not in data       # critical: never use S07
        assert b"S13=260429" in data
        assert b"S10=0000000010" in data
        assert b"S23=POSCN4" in data


# ---------------- existing fixtures still parse ----------------

class TestFixtureSanity:
    @pytest.mark.parametrize("rx", [
        INFO_RX, RFID_OK_RX, RFID_CANCEL_RX,
        APPROVAL_USER_CANCEL_RX, APPROVAL_TIMEOUT_RX, APPROVAL_FAIL_RX,
        APPROVAL_TEST_MODE_OK_RX, APPROVAL_REAL_OK_RX,
        CANCEL_FAILED_RX, CANCEL_OK_RX,
    ])
    def test_parses(self, rx):
        assert _parse(rx) is not None
