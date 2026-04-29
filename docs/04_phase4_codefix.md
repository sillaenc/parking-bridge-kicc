# Phase 4 — 코드 보강 (Phase 1~3 학습 결과 반영)

## 목적
Phase 3에서 발견한 가장 위험한 버그(취소 RCD=00이지만 PG 실패)를 코드 레벨에서 영구히 차단.

## 변경 파일
- `ed721_proto.py` — 헬퍼 함수 신규 추가
- `ed721_cli.py` — 비즈니스 판정 출력, ACK-only 정상 처리, 시리얼 단일 점유 락
- `tests/fixtures/captures.py` — 실측 응답 10개 회귀 fixture
- `tests/test_phase4_response.py` — 신규 25 테스트

## ed721_proto.py 신규 API
| 함수 | 역할 |
|------|------|
| `is_failure_short_message(data)` | DATA가 `CANCELED`/`TIMEOUT`/`FAIL` 중 하나면 그 문자열, 아니면 None |
| `parse_kv_response(data)` | EUC-KR 인식 후 `S00=...;S01=...;` → `dict` |
| `is_approval_success(fields)` | S01=I1 + R02=A + R09 비제로 (R09=000...은 실 매입 X 상태로 간주) |
| `is_cancel_success(fields)` | S01=I4 + **R17 부재** + R09 존재 + R19에 "효력없음" 없음 |
| `extract_cancel_info(fields)` | 승인 fields → `{S12: R09, S13: R07[:6], S10: zfilled}` |
| `build_cancel_data(fields, pos_id)` | 위 정보로 D4 ASCII payload 생성 |

## 핵심 비즈니스 규칙 (테스트로 잠금)
```python
# tests/test_phase4_response.py 주요 단언:
assert build_cancel_data(...) contains b"S12=30044993"   # R09
assert build_cancel_data(...) does NOT contain b"S12=949094"  # S07 절대 X

assert is_cancel_success(failed_cancel_kv) is False  # RCD=00이어도 실패
assert is_cancel_success(real_cancel_kv) is True

assert is_approval_success(test_mode_kv) is False    # R09=00000000 → 실 매입 X
assert is_approval_success(real_pg_kv) is True
```

## CLI 개선
1. **ACK-only 명령**(init/display/sound/image): ACK 받으면 "성공" 출력, exit 0 (이전: exit 2)
2. **승인/취소 응답 자동 판정 출력**:
   - 승인 시: 성공/의심 표시 + 취소용 S12/S13/S10 자동 안내
   - 취소 시: R17 존재 여부로 진짜 성공 판정
3. **시리얼 포트 락** (`fcntl.flock` on `/tmp/ed721_*.lock`):
   - Phase 3-F에서 발견한 다중 오픈 → byte-split 사고 방지
   - 이미 사용 중이면 exit 3

## 회귀 fixture (tests/fixtures/captures.py)
실측 응답 10종 hex 그대로 보관:
- INFO_RX, RFID_OK_RX, RFID_CANCEL_RX
- APPROVAL_USER_CANCEL_RX, APPROVAL_TIMEOUT_RX, APPROVAL_FAIL_RX
- APPROVAL_TEST_MODE_OK_RX (R09=00000000)
- APPROVAL_REAL_OK_RX (R09=30044993)
- CANCEL_FAILED_RX (S07 사용, R17 메시지 있음)
- CANCEL_OK_RX (R09 사용, R17 없음)

이 fixture로 향후 코드 변경 시 핵심 시나리오 자동 회귀.

## 결과
- pytest: **75/75 PASS** (Phase 1: 50 + Phase 4: 25)
- `init` 실 단말 호출: 더 이상 exit 2 아님 → "성공" 출력 ✅
- 회귀 검증: 어떤 코드가 S12에 S07을 다시 넣으면 즉시 테스트 실패

## 미진행 (선택적)
- `kicc_info_request.py`, `ed721_menu.py`를 `ed721_proto.py` 사용하도록 리팩토링 (3중 코드 중복 제거)
- NAK 시 자동 재전송 정책 — 데이터 손실 위험 분석 후 결정
- 부분 수신 버퍼 누적(현재는 단일 read 가정) — 운영 환경에서 거의 영향 없음
