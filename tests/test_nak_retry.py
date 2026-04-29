"""Phase 4 (2번) — NAK retry policy & send_and_wait via fake serial."""

from __future__ import annotations

import time

import pytest

from ed721_proto import (
    ACK_TRIPLE,
    NAK_TRIPLE,
    RetryPolicy,
    build_packet,
    policy_for,
    send_and_wait,
)
from tests.fixtures.captures import APPROVAL_REAL_OK_RX, INFO_RX


class FakeSerial:
    """pyserial-like stub. Each programmed reply is delivered ONCE per non-ACK write
    (i.e., per request packet). Subsequent reads inside the same request iteration
    don't auto-refill from the next reply."""

    def __init__(self, replies: list[bytes]):
        self.replies = list(replies)
        self.tx_log: list[bytes] = []
        self._buf = b""
        self._delivered_for_current_request = False

    def write(self, data: bytes):
        self.tx_log.append(bytes(data))
        # Only a *non-ACK* write counts as a new request that opens a new reply slot.
        if data != ACK_TRIPLE:
            self._delivered_for_current_request = False

    def flush(self):
        pass

    def reset_input_buffer(self):
        self._buf = b""

    def reset_output_buffer(self):
        pass

    def _maybe_load_next_reply(self):
        if not self._buf and self.replies and not self._delivered_for_current_request:
            self._buf = self.replies.pop(0)
            self._delivered_for_current_request = True

    @property
    def in_waiting(self) -> int:
        self._maybe_load_next_reply()
        return len(self._buf)

    def read(self, n: int = 1) -> bytes:
        self._maybe_load_next_reply()
        chunk, self._buf = self._buf[:n], self._buf[n:]
        return chunk


# ---------------- policy_for ----------------

class TestPolicyFor:
    def test_financial_is_never(self):
        assert policy_for(0x04, 0x14) == RetryPolicy.NEVER

    def test_info_is_safe(self):
        assert policy_for(0x02, 0x14) == RetryPolicy.SAFE

    def test_init_is_safe(self):
        assert policy_for(0x01, 0x14) == RetryPolicy.SAFE

    def test_rfid_is_safe(self):
        assert policy_for(0x06, 0x01) == RetryPolicy.SAFE


# ---------------- send_and_wait happy path ----------------

class TestSendAndWaitHappy:
    def test_info_first_try_success(self):
        ser = FakeSerial([INFO_RX])
        buf, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02, max_wait_sec=1
        )
        assert parsed is not None
        assert parsed.gcd == 0x14 and parsed.jcd == 0x02
        assert attempts == 1
        # ACK must have been auto-sent
        assert ACK_TRIPLE in b"".join(ser.tx_log)

    def test_approval_first_try_success(self):
        ser = FakeSerial([APPROVAL_REAL_OK_RX])
        _, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x04,
            data=b"S00=002;S01=D1;", max_wait_sec=1,
        )
        assert parsed is not None
        assert attempts == 1


# ---------------- NAK behavior ----------------

class TestNakRetry:
    def test_safe_command_retries_on_nak_then_succeeds(self):
        # First reply: NAK only. Second reply: full INFO_RX.
        ser = FakeSerial([NAK_TRIPLE, INFO_RX])
        buf, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02,
            max_wait_sec=1, retry_backoff_sec=0,
        )
        assert parsed is not None
        assert attempts == 2
        # Same packet sent twice (built once), excluding ACK
        sent_packets = [t for t in ser.tx_log if t != ACK_TRIPLE]
        # at least 2 sends of the same payload
        assert sent_packets.count(sent_packets[0]) >= 2

    def test_safe_command_gives_up_after_max_retries(self):
        # All replies are NAK
        ser = FakeSerial([NAK_TRIPLE] * 10)
        buf, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02,
            max_wait_sec=0.2, retry_backoff_sec=0, max_retries=3,
        )
        assert parsed is None
        assert attempts == 3
        assert NAK_TRIPLE in buf

    def test_financial_NEVER_does_not_retry_on_nak(self):
        # Even with multiple NAKs queued, financial command must send only ONCE.
        ser = FakeSerial([NAK_TRIPLE, INFO_RX])  # would succeed if it retried
        buf, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x04,
            data=b"S00=002;", max_wait_sec=0.2, retry_backoff_sec=0,
        )
        assert attempts == 1
        # Must NOT have re-sent the same financial packet
        sent_packets = [t for t in ser.tx_log if t != ACK_TRIPLE]
        assert len(sent_packets) == 1, f"Financial command MUST never auto-retry. Got {len(sent_packets)} sends."

    def test_explicit_NEVER_overrides_default(self):
        ser = FakeSerial([NAK_TRIPLE, INFO_RX])
        _, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02,  # safe by default
            retry_policy=RetryPolicy.NEVER,
            max_wait_sec=0.2, retry_backoff_sec=0,
        )
        assert attempts == 1


# ---------------- Timeout (no NAK, no response) ----------------

class TestTimeoutNoRetry:
    def test_pure_timeout_does_not_retry(self):
        """No NAK and no response — deterministic single send (don't blindly retry)."""
        ser = FakeSerial([])  # nothing comes back
        buf, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02,
            max_wait_sec=0.2, retry_backoff_sec=0, max_retries=5,
        )
        assert parsed is None
        assert buf == b""
        assert attempts == 1


# ---------------- Single-byte NAK (B3 case from real device) ----------------

class TestSingleByteNak:
    def test_single_byte_15_treated_as_nak(self):
        ser = FakeSerial([b"\x15", INFO_RX])
        _, parsed, attempts = send_and_wait(
            ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02,
            max_wait_sec=0.2, retry_backoff_sec=0, max_retries=3,
        )
        assert parsed is not None
        assert attempts == 2
