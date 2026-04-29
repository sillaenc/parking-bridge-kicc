"""3-E redo: full approval → immediately LA, single serial handle."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import serial
from ed721_proto import build_packet, try_parse_first_packet, ACK_TRIPLE, DEFAULT_FRAMING


def send_and_wait(ser, *, cnt, gcd, jcd, data, label, max_wait=90):
    pkt = build_packet(cnt=cnt, cmd=0xFB, gcd=gcd, jcd=jcd, data=data)
    print(f"\n[{label}] TX: {pkt.hex(' ').upper()}")
    ser.reset_input_buffer()
    ser.write(pkt); ser.flush()
    deadline = time.time() + max_wait
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            parsed = try_parse_first_packet(buf, DEFAULT_FRAMING)
            if parsed:
                ser.write(ACK_TRIPLE); ser.flush()
                print(f"[{label}] RX ({len(buf)}B): {buf.hex(' ').upper()}")
                print(f"[{label}] CNT={parsed.cnt} RCD={parsed.rcd:02X}")
                if parsed.data:
                    print(f"[{label}] DATA(ascii): {parsed.data.decode('ascii', errors='replace')}")
                return parsed
        time.sleep(0.01)
    print(f"[{label}] TIMEOUT (no full packet). buf={buf.hex(' ').upper() or '(empty)'}")
    return None


def main():
    with serial.Serial("/dev/ttyUSB0", 115200, parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                       timeout=0.05, write_timeout=0.5) as ser:
        ser.reset_input_buffer(); ser.reset_output_buffer()

        # Step 1: full approval — user must complete with PIN
        approval_data = b"S00=002;S01=D1;S02=40;S09=00;S10=0000000001;S23=POS3E_R1;"
        print(">>> [STEP 1] 승인 명령 전송 — 카드 꽂고 PIN까지 완료해주세요 (90초 대기)")
        approval_resp = send_and_wait(ser, cnt=1, gcd=0x14, jcd=0x04,
                                       data=approval_data, label="APPROVAL")
        if approval_resp is None or approval_resp.rcd != 0x00:
            print("\n!!! 승인 실패 — LA 단계 스킵")
            return

        # 잠시 단말 안정화
        time.sleep(2)

        # Step 2: LA — should return the same approval
        print("\n>>> [STEP 2] LA(직전거래) 전송 — 카드 안 꽂아도 됩니다")
        la_data = b"S00=002;S01=LA;S02=40;S23=POS3E_R2;"
        send_and_wait(ser, cnt=2, gcd=0x14, jcd=0x04, data=la_data, label="LA", max_wait=15)


if __name__ == "__main__":
    main()
