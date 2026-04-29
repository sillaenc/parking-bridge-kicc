# ED-721 POS 연동 및 도구 모음

KICC ED-721 단말을 시리얼(USB-Serial)로 직접 제어하기 위한 Python 도구와 분석/검증 자료를 담습니다. 네이티브 DLL(KiccPos.dll) 없이 STX/LEN/CNT/CMD/GCD/JCD/DATA/ETX/CRC 프레임을 직접 생성·송신하고 응답을 CRC 검증해 파싱합니다.

## 주요 파일
- `ed721_proto.py` : 공통 프로토콜 모듈(CRC/프레임 빌더·파서/응답 판정 헬퍼/NAK 재전송 정책). 모든 CLI가 이 모듈을 import.
- `ed721_cli.py` : 명령형 CLI. 단말 초기화/정보/화면표시/승인/취소/소리/이미지/RFID 송신·응답 판정·자동 ACK·시리얼 단일 점유 락 포함.
- `ed721_menu.py` : 숫자 선택형 메뉴 인터페이스(위 명령 동일).
- `kicc_info_request.py` : 단말정보(FB/14/02) 단일 요청/응답 테스트용 (framing 탐색 포함).
- `kicc_crc_fuzzer.py` : 잘못된 CRC 패킷을 의도적으로 생성하는 framing 탐색용 퍼저(독립 유지).
- `ED721_CLI_Commands.txt` : 자주 쓰는 명령 한 줄 예제 모음(R09 안내, 신규 플래그 포함).
- `ED721_POS_Interface_Analysis_Report.txt` : SPEC 요약/CRC/프레이밍/실험 로그 분석 리포트.
- `SESSION_SUMMARY.txt` : 세션 요약과 docs/ 가이드 포인터.
- `docs/` : 단계별 검증 문서. **`docs/REPORT.md` = 종합 보고서(여기부터 읽으면 됩니다).**
- `tests/` : pytest 87개 + 수동 시나리오 스크립트 + 실측 응답 fixture.

## 요구 사항
- Python 3.x
- `pip install pyserial pytest`
- 시리얼 포트: `/dev/ttyUSB0` (Raspberry Pi 예시) 또는 `COMx` (Windows)
- ED-721 단말은 RS232/USB-Serial로 응답을 보내도록 설정되어 있어야 합니다.

## 프레이밍 기본값
- `len_mode=2, len_endian=big, crc_endian=big` (실기기에서 확인된 조합, 기본값)

## 빠른 사용법 (예제)
아래 예시는 `/dev/ttyUSB0` 기준. Windows는 `COM3` 등으로 변경.

단말정보:
```
python ed721_cli.py --port /dev/ttyUSB0 info
```

화면표시(4줄, '|' 줄바꿈):
```
python ed721_cli.py --port /dev/ttyUSB0 --data "READY|TAP CARD||" display
```

승인(신용 D1, 일시불, 10원):
```
python ed721_cli.py --port /dev/ttyUSB0 --wait 90 \
  --data "S00=002;S01=D1;S02=40;S09=00;S10=0000000010;S23=POS001;" approval
```

취소 — **반드시 S12 에 R09 값을 사용**(S07 은 단말 placeholder):
```
python ed721_cli.py --port /dev/ttyUSB0 --wait 90 \
  --data "S00=002;S01=D4;S02=40;S09=00;S10=0000000010;S12=<R09값>;S13=<YYMMDD>;S23=POS002;" approval
```

CLI는 승인 응답 수신 시 자동으로 `[취소용] S12=... S13=... S10=...` 라인을 출력해 줍니다. 그 값을 그대로 옮겨 적으면 됩니다.

RFID S/N:
```
python ed721_cli.py --port /dev/ttyUSB0 rfid
```

## 테스트
```
pytest tests/         # 87개 pytest (프로토콜 50 + 응답 판정 25 + NAK 재전송 12)
```

## 설계/구현 포인트
- CRC: poly 0x8005, init 0xFFFF, LSB-first, 최종 NOT 후 byte swap. CRC 범위는 LEN..ETX.
- LEN 정의: len_mode 0~3 탐색 가능. 실기기에서는 LEN = LEN(2)+CNT+CMD+GCD+JCD(+DATA)로 동작(len_mode=2).
- 응답 처리: CRC 검증 후 자동 ACK(06 06 06) 전송. 승인/취소 응답은 ASCII로 표시, RFID는 hex로 표시.
- 응답이 없는 명령(init/display/sound/image)은 ACK만 받고 정상 종료(exit 0).
- 시리얼 포트는 `fcntl.flock` 으로 단일 점유 락 자동 적용(Linux).

## 운영상 핵심 규칙 (반드시 준수)
1. **취소 S12 = R09** (S07 절대 X). 자세한 발견 경위는 `docs/REPORT.md` 참조.
2. **취소 성공 판정**은 RCD=0x00 단독 X — R17 부재 + R19 정상값 + R09 존재 동시 검증.
3. **승인/취소 명령은 NAK 자동 재전송 금지** (RetryPolicy.NEVER 강제). 사람 확인 후 수동 재시도.
4. **거래 진행 중에 다른 명령 송신 금지** — display 조차 거래를 인터럽트한다.

## 주의 사항 / 한계
- 이 단말은 LA(직전거래 재전송)를 지원하지 않음 (등록 상태 무관 항상 FAIL). 다른 ED-721 단말 별도 검증 권장.
- 가맹명/홈 화면 텍스트는 연동 API로는 변경 불가. 단말 설정/TMS 영역이며, 배경 이미지는 `FB/14/14`로 교체 가능하지만 변경은 영구이므로 운영 단말에 함부로 사용 금지.
- 외부 인터넷 차단됨. 이미지 다운로드는 LAN 내부 HTTP 서버에서만 가능.
- 포트 점유: COM/tty는 한 번에 한 프로세스만 사용. 다른 시리얼 모니터/샘플 프로그램은 종료 후 실행.

## 관련 문서
- `docs/REPORT.md` — 종합 보고서(여기부터)
- `docs/00_overview.md` — 단계별 가이드
- `docs/01_phase1_protocol.md` ~ `docs/07_phase4_refactor_nak_retry.md` — 단계별 결과
