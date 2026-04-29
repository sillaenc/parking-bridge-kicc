# ED-721 결제기 테스트 문서

## 목적
KICC ED-721 단말의 결제 모듈을 단계적으로 검증한다. 정상 결제뿐 아니라 **취소/거래 도중 카드 빼기/사용자 취소/호스트 타임아웃** 등 비정상 시나리오까지 다룬다.

## 환경
- 단말 IP: 192.168.0.224 (참고용, 실제 통신은 RS-232/USB-Serial)
- 시리얼 포트: `/dev/ttyUSB0`
- 프레이밍 확정값: `len_mode=2, len_endian=big, crc_endian=big`
- 단말 정보(2026-04-29 실측):
  - model=K03, version=0023, serial=3K0342000839, secure_id=ED-721X001, tid=8016366

## Phase 구분
- **Phase 1 (SW only)**: 프로토콜 단위(CRC/build/parse) 자동화 테스트. HW 불필요.
- **Phase 2 (HW, 비파괴)**: 단말 연결 상태에서 정보/표시/소리/RFID 등 결제 외 명령.
- **Phase 3 (실거래)**: 테스트 카드로 승인/취소/도중 빼기/사용자 취소 등 실제 시나리오.
- **Phase 4 (회복/안정성)**: NAK 재전송, 부분 수신, 장시간 idle 등.

## 산출물 위치
- 코드: `ed721_proto.py` (공통 모듈), `tests/`
- 문서: `docs/0X_phaseN.md`
- 결과 fixture: `tests/fixtures/`

## 진행 원칙
- 각 phase가 끝날 때마다 결과를 docs에 추가.
- 실거래 단계는 작업자와 호흡 맞춰 한 시나리오씩.
