#!/usr/bin/env python3
"""두 롬 바이너리를 비교해 차이 구간을 요약."""
import sys


def load(p):
    with open(p, "rb") as f:
        return f.read()


def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    n = min(len(a), len(b))
    print(f"A={len(a)} B={len(b)} 공통={n}")
    # 차이 구간 병합 (연속 diff를 하나의 run으로)
    runs = []
    start = None
    for i in range(n):
        if a[i] != b[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                runs.append((start, i))
                start = None
    if start is not None:
        runs.append((start, n))
    diff_bytes = sum(e - s for s, e in runs)
    print(f"다른 바이트: {diff_bytes} ({100*diff_bytes/n:.1f}%), run 수: {len(runs)}")
    # 64KB 뱅크별
    from collections import Counter
    buckets = Counter()
    for s, e in runs:
        for bank in range(s >> 16, ((e - 1) >> 16) + 1):
            lo = max(s, bank << 16)
            hi = min(e, (bank + 1) << 16)
            buckets[bank] += hi - lo
    print("뱅크별 차이:")
    for bank in sorted(buckets):
        print(f"  0x{bank<<16:06X}: {buckets[bank]:>8}")


if __name__ == "__main__":
    main()
