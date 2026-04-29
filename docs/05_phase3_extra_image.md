# Phase 3 추가 — 이미지 다운로드 (FB/14/14) 검증

## 목적
이 단말이 외부 이미지로 홈 화면/배경을 교체할 수 있는지 확인.

## 결과 — **기능은 되지만 매우 신중해야 함**

### 외부 인터넷 차단 확인
| URL | 응답 | 의미 |
|-----|-----|------|
| `https://raw.githubusercontent.com/.../octocat.png` | RCD=FF, DATA 빈 | HTTPS 또는 외부망 막힘 |
| `http://via.placeholder.com/...` | RCD=FF, DATA 빈 | 외부 HTTP도 막힘 |
| `http://192.168.0.20:8765/test.png` (LAN, plain HTTP) | **RCD=00** | LAN 서버는 OK |

→ 단말 네트워크는 PG/카드사망만 열려있고 외부 일반 인터넷은 차단. **POS 측에서 자체 HTTP 서버를 띄워 이미지 호스팅** 필요.

### 동작 확인
1. 100x100 빨간색 PNG (334B) 송신 → RCD=00 + 단말 HTTP GET 200
2. 결과: **단말 홈 화면 전체가 빨간색으로 교체됨** (영구 변경)

### 응답 패턴
- 성공: `RCD=00, DATA 빈` (이미지 명령은 본문 없음)
- 실패: `RCD=FF, DATA 빈` (CANCELED/TIMEOUT/FAIL 등 텍스트 없음)
- 새로운 패턴 — 기존 명령들과 다름. `is_failure_short_message()`에 매칭되지 않으니 RCD만으로 판정해야 함

### ⚠️ 운영 주의사항
1. **이미지 변경은 영구적**. `init` 보내도 복원 안 됨.
2. **원본 이미지는 단말 펌웨어 내장**이라 사용자가 직접 백업/복원 불가.
3. 복구 경로:
   - 단말 관리자 메뉴 → 공장 초기화 (KICC ED-721 매뉴얼)
   - KICC 지원에 기본 이미지 파일 요청
4. **운영 단말에 image 명령 절대 함부로 보내지 말 것** — 잘못 보내면 결제 안내 화면이 사라짐

### Phase 4 코드 보강 항목 (추가 필요)
- `image` 명령에 `--confirm` 플래그 강제 (실수 방지)
- POS 시스템 통합 시 image 명령은 별도 관리자 인증 후에만 실행
- 응답 RCD=0x00/0xFF 외 값에 대한 처리 (이번엔 둘만 봤음)

## 실험 환경
- Pi: 192.168.0.20 / 192.168.0.228 (eth0/wlan0)
- 단말: 192.168.0.224, 같은 LAN
- HTTP 서버: `python3 -m http.server <port> --bind 0.0.0.0`
- 이미지: 480x320 PNG

## 이미지 사양 (확정)

| 항목 | 값 | 비고 |
|-----|-----|------|
| 해상도 | 480x320 | ED-721 표준 (다른 해상도도 자동 stretch) |
| 포맷 | PNG (RGB 8bit, no alpha) | JPG도 가능 추정 (미검증) |
| 전송 방식 | LAN HTTP (HTTPS 불가) | 외부 인터넷 차단 |
| 단색 PNG 크기 | 약 500~1300B | 압축 후 |

## 화면 변경 이력 (테스트 단말)

| 시각 | 색상 | 파일크기 | 결과 |
|------|------|---------|------|
| 15:45 | 빨강 (255,0,0) 100x100 | 334B | 홈 전체 빨강 (자동 stretch) |
| 15:51 | 흰색 (255,255,255) 480x320 | 1204B | 홈 전체 흰색 |
| 15:55 | 검정 (0,0,0) 480x320 | 527B | 홈 전체 검정 |
| 15:56 | 어두운회색 (50,50,50) 480x320 | 1205B | 홈 전체 회색, 흰 글씨 잘 보임 ✅ |

→ 현재 단말은 어두운 회색 배경. KICC 기본 홈 이미지는 영구 손실 (공장 초기화 불가 환경).

## 단색 PNG 생성 스니펫 (운영용 보관)

```python
import struct, zlib
def png_solid(w, h, rgb):
    """rgb = bytes(R,G,B). e.g., b'\\x32\\x32\\x32' for dark gray."""
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t+d) & 0xffffffff)
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b''.join(b'\\x00' + rgb * w for _ in range(h))
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

# 480x320 dark gray
open('home.png', 'wb').write(png_solid(480, 320, b'\\x32\\x32\\x32'))
```

## 워크플로우 (이미지 교체 절차)

1. POS 시스템에서 HTTP 서버 띄우기 (LAN 노출):
   ```bash
   cd /path/to/images && python3 -m http.server 8765 --bind 0.0.0.0
   ```
2. 명령 송신:
   ```bash
   python3 ed721_cli.py --port /dev/ttyUSB0 --len-mode 2 --len-endian big --crc-endian big \
     --wait 30 --data "http://<POS_IP>:8765/<파일명>.png" image
   ```
3. 단말 응답 RCD=00 + 서버 액세스 로그 200 확인 → 적용 완료
4. HTTP 서버 종료

## ⚠️ 운영 주의사항 (재강조)
1. **이미지 변경은 영구**. `init` 보내도 복원 안 됨.
2. **원본 이미지는 단말 펌웨어 내장**이라 사용자가 직접 백업/복원 불가.
3. 복구 경로:
   - 단말 관리자 메뉴 → 공장 초기화 (KICC ED-721 매뉴얼) — **이 단말은 불가**
   - KICC 지원에 기본 이미지 파일 요청
4. **운영 단말에 image 명령 절대 함부로 보내지 말 것**
