# Phase 4 추가 — 리팩토링 (1번) + NAK 자동 재전송 (2번)

## 1번 — 리팩토링 (3중 코드 중복 제거)

### Before / After
| 파일 | 이전 LOC | 이후 LOC | 감소 |
|------|---------|---------|------|
| ed721_cli.py | 427 | 250 | 41%↓ |
| ed721_menu.py | 313 | 109 | 65%↓ |
| kicc_info_request.py | 360 | 125 | 65%↓ |
| ed721_proto.py | ~200 | 362 | +162 (NAK retry 포함) |
| **합계** | **1300** | **846** | **35%↓** |

### 변경 내용
- 세 파일에서 중복돼 있던 `calc_crc`, `Framing`, `ParsedPacket`, `build_packet`, `try_parse_first_packet`, `_compute_len_value`, `decode_terminal_info_fields`, `_request_once` 모두 제거
- 모두 `ed721_proto`에서 import
- 새 고수준 헬퍼 `send_and_wait()`로 송수신 루프 통일

### 검증
- pytest 87/87 PASS (이전 75 → +12 NAK retry 테스트)
- 실 단말 `info` 명령 회귀 정상 (TID 8016366, 192.168.0.224/)

## 2번 — NAK 자동 재전송 정책

### 설계 원칙
**중복 청구 사고 방지 최우선**. 단말이 NAK를 보냈을 때 우리가 같은 패킷을 재전송했는데, 사실 단말은 이미 첫 패킷을 처리했고 NAK는 다른 노이즈였을 가능성을 완전히 배제 못함 → **승인/취소(FB/14/04)는 절대 자동 재전송 X**.

### 정책 (RetryPolicy enum)
| 정책 | 동작 |
|------|------|
| `NEVER` | 한 번 송신, NAK 와도 재시도 안 함 |
| `SAFE` | NAK 시 같은 패킷 최대 N회 재시도 (기본 3회) |
| `PROMPT` | NAK를 caller에게 그대로 반환 (사람 결정) |

### 명령별 기본 정책 (`policy_for(jcd, gcd)`)
| 명령 | 정책 | 이유 |
|------|------|------|
| FB/14/04 (승인/취소/LA) | **NEVER** | 중복 청구 위험 |
| FB/14/01 (init) | SAFE | 무해, 멱등 |
| FB/14/02 (info) | SAFE | 무해, 조회 |
| FB/14/03 (display) | SAFE | 화면 표시는 멱등 |
| FB/14/13 (sound) | SAFE | 소리 재생, 무해 |
| FB/14/14 (image) | SAFE | 같은 URL 재요청 무해 |
| FB/01/06 (rfid) | SAFE | 카드 SNO 재요청 무해 |

### 추가 안전장치
- **타임아웃(NAK 없이 응답 없음)은 재시도 안 함** — 단말이 첫 패킷 받고 처리 중일 수 있음. 무지성 재전송으로 새 거래 트리거 위험 차단.
- **단일 바이트 NAK(`0x15`)도 NAK으로 처리** — Phase 3 B3 케이스에서 관찰된 비표준 응답 대응.
- **CLI `--force-retry-financial` 플래그**: 정말 필요할 때만 명시적으로 활성화. 출력에 경고 메시지.

### `send_and_wait()` API
```python
buf, parsed, attempts = send_and_wait(
    ser, cnt=1, cmd=0xFB, gcd=0x14, jcd=0x02, data=b"",
    framing=DEFAULT_FRAMING, max_wait_sec=2.0,
    retry_policy=None,  # None → policy_for(jcd, gcd)
    max_retries=3, retry_backoff_sec=0.1,
    auto_ack=True,
)
```
- `attempts`: 실제 송신 횟수 (1 = 첫 시도 성공)
- ACK 자동 송신 포함

### 테스트 커버리지 (`tests/test_nak_retry.py`, 12개)
- `policy_for`: 명령별 기본 정책 4개 검증
- 행복 경로: 첫 시도 성공 (info, approval)
- NAK 재시도: SAFE 명령 NAK→재시도→성공
- NAK 최대 재시도 도달: 모두 실패시 None 반환
- **결정적 단언**: financial(FB/14/04) NEVER → NAK 와도 재전송 안 함을 강제
- 명시적 NEVER override 동작
- 순수 타임아웃 시 재시도 안 함
- 단일 바이트 NAK 처리

### 핵심 단언 (운영 보호)
```python
def test_financial_NEVER_does_not_retry_on_nak():
    sent_packets = [t for t in ser.tx_log if t != ACK_TRIPLE]
    assert len(sent_packets) == 1, \
        f"Financial command MUST never auto-retry. Got {len(sent_packets)} sends."
```
이 한 줄이 누군가 실수로 승인 NAK→재전송 코드를 넣어도 즉시 알아챕니다.

## 결과 요약
- pytest **87/87 PASS** (50 Phase1 + 25 Phase4-1 + 12 Phase4-2)
- 실 단말 호환성 유지
- 코드 중복 제거 + NAK 회복력 + 중복청구 방지 동시 달성
