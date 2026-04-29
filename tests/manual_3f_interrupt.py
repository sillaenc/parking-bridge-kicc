"""3-F redo: send approval, then ~3s later inject display through SAME serial handle."""
import sys, time, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import serial
from ed721_proto import build_packet, try_parse_first_packet, ACK_TRIPLE, DEFAULT_FRAMING


def main():
    with serial.Serial("/dev/ttyUSB0", 115200, parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                       timeout=0.05, write_timeout=0.5) as ser:
        ser.reset_input_buffer(); ser.reset_output_buffer()

        approval = build_packet(cnt=1, cmd=0xFB, gcd=0x14, jcd=0x04,
                                data=b"S00=002;S01=D1;S02=40;S09=00;S10=0000000001;S23=POS3F_R;")
        display = build_packet(cnt=2, cmd=0xFB, gcd=0x14, jcd=0x03,
                               data=b"INTERRUPT TEST||||")

        print(f"[APPROVAL TX] {approval.hex(' ').upper()}")
        ser.write(approval); ser.flush()

        # In a separate thread, inject display 3s later
        def inject():
            time.sleep(3.0)
            print(f"\n[DISPLAY TX (mid-flow)] {display.hex(' ').upper()}")
            ser.write(display); ser.flush()
        threading.Thread(target=inject, daemon=True).start()

        # Read for up to 30s, capture all packets
        deadline = time.time() + 30
        buf = b""
        seen = []
        while time.time() < deadline:
            chunk = ser.read(ser.in_waiting or 1)
            if chunk:
                buf += chunk
                # Try to extract every packet from buf incrementally
                while True:
                    p = try_parse_first_packet(buf, DEFAULT_FRAMING)
                    if not p:
                        break
                    seen.append(p)
                    print(f"\n[PARSED] CNT={p.cnt} GCD={p.gcd:02X} JCD={p.jcd:02X} "
                          f"RCD={(p.rcd if p.rcd is not None else -1):02X}")
                    if p.data:
                        print(f"[PARSED] DATA(ascii): {p.data.decode('ascii', errors='replace')}")
                    ser.write(ACK_TRIPLE); ser.flush()
                    # Cut buf at end of parsed packet
                    idx = buf.find(p.raw) + len(p.raw)
                    buf = buf[idx:]
            time.sleep(0.01)

        print(f"\n[FINAL BUF] {buf.hex(' ').upper() or '(empty)'}")
        print(f"[SUMMARY] {len(seen)} packet(s) parsed")


if __name__ == "__main__":
    main()
