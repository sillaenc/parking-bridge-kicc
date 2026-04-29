# Phase 1 — 프로토콜 단위테스트 (SW only)

## 목적
하드웨어 없이 프레임 빌더/파서/CRC를 단위 테스트로 잠근다. 회귀 방지 베이스라인.

## 산출물
- `ed721_proto.py` — `ed721_cli.py` / `ed721_menu.py` / `kicc_info_request.py` 에 중복되어 있던 로직을 단일 모듈로 추출.
- `tests/test_proto.py` — pytest 테스트.

## 테스트 범위
1. **CRC 알고리즘**
   - 빈 입력 / 단일 바이트 시드 동작 검증
   - 실측 패킷 검증: `00 06 01 FB 14 02 03` → CRC `DE E5`
   - 실측 응답 패킷 검증(수신된 raw에서 LEN..ETX 잘라 CRC 일치)
2. **build_packet (16조합)**
   - len_mode 0~3 × len_endian 2 × crc_endian 2
   - len_mode=2/big/big에서 실측 송신 바이트와 100% 일치
3. **try_parse_first_packet**
   - 정상 응답
   - 앞에 ACK(`06 06 06`) 붙은 케이스(실측)
   - STX 앞에 garbage 바이트
   - 불완전 수신(부분 LEN, 부분 DATA, CRC 1바이트만)
   - CRC mismatch → None
   - ETX 위치 어긋남 → None
4. **info 응답 디코더**
   - 79바이트 정확 입력 → 모든 필드 추출
   - 짧은 입력 → None
   - 공백 패딩 → strip 동작
5. **CNT wrap**
   - 255 다음 1로 순환

## 비포함 (다음 Phase)
- 시리얼 IO, 재시도, ACK 자동 송신은 Phase 2(HW) 또는 Phase 4에서.

## 결과 (2026-04-29)

```
50 passed in 0.10s
```

### 검증 항목 정리
| 분류 | 테스트 수 | 비고 |
|------|----------|------|
| CRC | 3 | 실측 TX/RX 패킷의 CRC 일치, 빈 입력 안전 |
| LEN 계산/역산 | 8 | mode 0~3 + roundtrip + 음수/잘못된 모드 |
| build_packet | 18 | 실측 TX 바이트 일치 + 16 framing 조합 + cnt 범위 |
| parse | 7 | ACK 선행/garbage/truncate/CRC mismatch/ETX 손상/2개 연속 |
| info 디코드 | 3 | 실측 응답 필드 정확, 짧음 → None, 패딩 strip |
| CNT wrap | 7 | 1→2, 254→255, 255→1, 잘못된 입력 |
| 상수 | 1 | ACK_TRIPLE = 06 06 06 |

### 핵심 검증 패킷
- TX (info request, cnt=1):
  `02 00 06 01 FB 14 02 03 DE E5` — `build_packet()` 출력과 byte-perfect 일치
- RX (info response):
  `06 06 06 02 00 56 01 FB 14 02 00 ...79B... 03 9C C0` — leading ACK 무시 + CRC 일치 + 디코드 결과:
  - model=K03, version=0023, serial_no=3K0342000839, secure_id=ED-721X001, tid=8016366, terminal_no="", ip_port=192.168.0.224/

### 발견된 이슈
- 없음(테스트 자체의 인덱스 계산 실수 1건은 즉시 수정).

### 다음 단계 진입 조건 충족
- 프로토콜 빌더/파서가 실측 데이터로 잠겼으므로, Phase 2(HW, 비파괴) 진입 가능.

