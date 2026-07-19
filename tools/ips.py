#!/usr/bin/env python3
"""IPS 패치 파서/적용/분석 도구.

IPS 포맷:
  "PATCH" (5바이트) 헤더
  레코드 반복:
    offset  3바이트 (big-endian)
    size    2바이트 (big-endian)
      size != 0  -> 그 뒤 size 바이트가 데이터 (일반 기록)
      size == 0  -> RLE: length 2바이트 + value 1바이트
  "EOF" (3바이트)로 종료
"""
import sys


def parse_ips(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:5] == b"PATCH", "IPS 헤더 아님"
    i = 5
    records = []
    while True:
        if data[i:i + 3] == b"EOF":
            # EOF 뒤에 truncate 확장(3바이트)이 있을 수 있음
            i += 3
            break
        offset = int.from_bytes(data[i:i + 3], "big"); i += 3
        size = int.from_bytes(data[i:i + 2], "big"); i += 2
        if size == 0:
            rle_len = int.from_bytes(data[i:i + 2], "big"); i += 2
            value = data[i]; i += 1
            records.append((offset, bytes([value]) * rle_len, True))
        else:
            chunk = data[i:i + size]; i += size
            records.append((offset, chunk, False))
    return records


def apply_ips(rom, records):
    rom = bytearray(rom)
    max_end = len(rom)
    for offset, chunk, _rle in records:
        end = offset + len(chunk)
        if end > len(rom):
            rom.extend(b"\x00" * (end - len(rom)))
        rom[offset:end] = chunk
        max_end = max(max_end, end)
    return bytes(rom)


def summarize(records):
    total_bytes = sum(len(c) for _, c, _ in records)
    offsets = [o for o, _, _ in records]
    print(f"레코드 수: {len(records)}")
    print(f"기록 총 바이트: {total_bytes}")
    print(f"오프셋 범위: 0x{min(offsets):06X} ~ 0x{max(offsets):06X}")
    rle = sum(1 for *_, r in records if r)
    print(f"RLE 레코드: {rle}")
    # 오프셋 구간 히스토그램 (0x10000 = 64KB 단위)
    from collections import Counter
    buckets = Counter()
    for o, c, _ in records:
        buckets[o >> 16] += len(c)
    print("64KB 뱅크별 변경 바이트:")
    for bank in sorted(buckets):
        print(f"  bank 0x{bank:02X} (0x{bank<<16:06X}): {buckets[bank]:>8} bytes")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "summary":
        recs = parse_ips(sys.argv[2])
        summarize(recs)
    elif cmd == "apply":
        recs = parse_ips(sys.argv[2])
        with open(sys.argv[3], "rb") as f:
            rom = f.read()
        out = apply_ips(rom, recs)
        with open(sys.argv[4], "wb") as f:
            f.write(out)
        print(f"적용 완료: {sys.argv[4]} ({len(out)} bytes)")
