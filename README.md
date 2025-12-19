# ED-721 POS 연동 및 도구 모음

이 레포는 KICC ED-721 단말을 시리얼(USB-Serial)로 직접 제어하기 위한 Python 도구와 분석 자료를 담습니다. 네이티브 DLL(KiccPos.dll) 없이 STX/LEN/CNT/CMD/GCD/JCD/DATA/ETX/CRC 프레임을 직접 생성·송신하고 응답을 CRC 검증하여 파싱합니다.

## 주요 파일
- `ed721_cli.py` : 명령형 CLI. 단말 초기화/정보/화면표시/승인/취소/소리/이미지/RFID S/N 등을 전송하고 응답을 출력.
- `ed721_menu.py` : 숫자 선택형 메뉴 인터페이스(위 명령 동일).
- `kicc_info_request.py` : 단말정보(FB/14/02) 단일 요청/응답 테스트용 (framing 탐색 포함).
- `ED721_CLI_Commands.txt` : 자주 쓰는 명령 한 줄 예제 모음.
- `ED721_POS_Interface_Analysis_Report.txt` : SPEC 요약/CRC/프레이밍/실험 로그 분석 리포트.
- `SESSION_SUMMARY.txt` : 세션 요약 및 현재 상태 정리.

## 요구 사항
- Python 3.x
- `pip install pyserial`
- 시리얼 포트: `/dev/ttyUSB0` (Raspberry Pi 예시) 또는 `COMx`(Windows)
- ED-721 단말은 RS232/USB-Serial로 응답을 보내도록 설정되어 있어야 합니다.

## 프레이밍 기본값
- `len_mode=2`, `len_endian=big`, `crc_endian=big` (실기기에서 확인된 조합)

## 빠른 사용법 (예제)
아래 예시는 `/dev/ttyUSB0` 기준. Windows는 `COM3` 등으로 변경.

단말정보:
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big info
```

화면표시(4줄, '|' 줄바꿈):
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big --data "READY|TAP CARD||" display
```

승인(신용 D1, 일시불, 10원 예시):
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big --wait 10 \
  --data "S00=002;S01=D1;S02=40;S09=00;S10=0000000010;S23=POS001;" approval
```

취소(원승인번호/일자 필요):
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big --wait 10 \
  --data "S00=002;S01=D4;S02=40;S09=00;S10=0000000010;S12=<승인번호>;S13=<YYMMDD>;S23=POS002;" approval
```

직전 거래 재전송(승인번호 확인용):
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big --wait 10 \
  --data "S00=002;S01=LA;S02=40;S23=POS003;" approval
```

RFID S/N:
```
python ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big rfid
```

## 설계/구현 포인트
- CRC: poly 0x8005, init 0xFFFF, LSB-first, 최종 NOT 후 byte swap. CRC 범위는 LEN..ETX.
- LEN 정의: len_mode 0~3 탐색 가능. 실기기에서는 LEN = LEN(2)+CNT+CMD+GCD+JCD(+DATA)로 동작(len_mode=2).
- 응답 처리: CRC 검증 후 자동 ACK(06 06 06) 전송. 승인/취소 응답은 ASCII로 표시, RFID는 hex로 표시.
- 응답이 없는 명령(display 등)은 ACK만 받고 “응답 없음”으로 끝날 수 있음(정상).

## 주의 사항 / 한계
- 승인 응답이 시리얼로 안 내려오는 환경이 있음(단말이 TCP 세션으로만 응답 송신하도록 설정된 경우). 이때는 단말 설정(TMS/관리자 메뉴)에서 RS232 응답 여부/포트를 확인하거나, `S01=LA`(최종거래내역 재전송)으로 직전 승인 정보를 받아야 합니다.
- 가맹명/홈 화면 텍스트는 연동 API로는 변경 불가. 단말 설정/TMS 영역이며, 배경 이미지는 `FB/14/14`로 교체 가능.
- 포트 점유: COM/tty는 한 번에 한 프로세스만 사용. 다른 시리얼 모니터/샘플 프로그램은 종료 후 실행.

## 기타
- `ed721_menu.py`는 입력 프롬프트 기반 메뉴 버전(포트/baud/len_mode 기본값 입력 후 숫자 선택).
- GPIO 모니터 스크립트는 별도 참고(`gpio_monitor.py` 경로에 존재). 본 ED-721 연동과 직접 연관은 없음.***
