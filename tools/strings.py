#!/usr/bin/env python3
"""롬에서 출력 가능한 ASCII 문자열 추출 (오프셋 표시)."""
import sys


def main():
    path = sys.argv[1]
    minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    start = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0
    end = int(sys.argv[4], 0) if len(sys.argv) > 4 else None
    with open(path, "rb") as f:
        data = f.read()
    if end is None:
        end = len(data)
    cur = bytearray()
    cur_start = 0
    for i in range(start, end):
        b = data[i]
        if 0x20 <= b < 0x7F:
            if not cur:
                cur_start = i
            cur.append(b)
        else:
            if len(cur) >= minlen:
                print(f"0x{cur_start:06X}: {cur.decode('ascii')}")
            cur = bytearray()
    if len(cur) >= minlen:
        print(f"0x{cur_start:06X}: {cur.decode('ascii')}")


if __name__ == "__main__":
    main()
