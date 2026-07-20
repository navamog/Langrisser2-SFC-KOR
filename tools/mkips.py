#!/usr/bin/env python3
"""IPS 패치 생성: base → target 차이를 IPS로. 확장(target>base) 지원, RLE로 축소.

사용: mkips.py <base> <target> <out.ips>
"""
import sys


def make_ips(base, target):
    out = bytearray(b"PATCH")
    n = len(target)
    i = 0
    while i < n:
        b = base[i] if i < len(base) else None
        if b == target[i]:
            i += 1
            continue
        # 변경 구간 시작
        start = i
        chunk = bytearray()
        while i < n and (i >= len(base) or base[i] != target[i]):
            chunk.append(target[i])
            i += 1
            if len(chunk) >= 0xFFFF:
                break
        # offset가 'EOF'(0x454F46)면 한 바이트 당겨서 회피
        off = start
        if off == 0x454F46:
            off -= 1
            chunk = bytearray([target[off]]) + chunk
        # RLE 판정: 전부 같은 바이트이고 길이>3이면 RLE
        if len(set(chunk)) == 1 and len(chunk) > 3:
            out += off.to_bytes(3, "big")
            out += (0).to_bytes(2, "big")           # size=0 → RLE
            out += len(chunk).to_bytes(2, "big")
            out += bytes([chunk[0]])
        else:
            out += off.to_bytes(3, "big")
            out += len(chunk).to_bytes(2, "big")
            out += bytes(chunk)
    out += b"EOF"
    # target이 base보다 짧을 경우 truncate 확장(여기선 불필요)
    return bytes(out)


def main():
    base = open(sys.argv[1], "rb").read()
    target = open(sys.argv[2], "rb").read()
    ips = make_ips(base, target)
    open(sys.argv[3], "wb").write(ips)
    print(f"IPS 생성: {sys.argv[3]} ({len(ips)} bytes), base {len(base)} → target {len(target)}")


if __name__ == "__main__":
    main()
