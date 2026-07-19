#!/usr/bin/env python3
"""기록된 read run 중에서 알려진 텍스트의 반복구조와 일치하는 것을 탐색.

인코딩을 몰라도, '같은 글자는 같은 코드'라는 반복 패턴만으로 매칭한다.
1바이트 코드 / 2바이트 코드 두 가지 폭을 시도.
"""
import re
import sys

# 화면에서 읽은 프롤로그 텍스트 (개행 제외 순수 문자열)
KNOWN = "イェレスの空、赤き凶星昇りし年はるか呪われしヴェルゼリアの地より、大いなる野望を抱きし者現わる。"


def repeat_sig(seq):
    """시퀀스의 반복 구조 서명: 각 원소를 '처음 등장 위치'로 치환."""
    first = {}
    sig = []
    for i, x in enumerate(seq):
        if x not in first:
            first[x] = i
        sig.append(first[x])
    return sig


def parse_runs(path):
    runs = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"RUN addr=0x([0-9A-Fa-f]+) len=(\d+): (.*)", line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        vals = [int(t, 16) for t in m.group(3).split()]
        runs.append((addr, vals))
    return runs


def find(runs, known_sig, klen, width):
    """width=1 또는 2 코드폭으로 각 run에서 known_sig 매칭."""
    hits = []
    need = klen * width
    for addr, vals in runs:
        if len(vals) < need:
            continue
        # run 안을 슬라이딩
        for start in range(0, len(vals) - need + 1):
            if width == 1:
                codes = vals[start:start + klen]
            else:
                seg = vals[start:start + need]
                codes = [seg[i] | (seg[i + 1] << 8) for i in range(0, need, 2)]
            if repeat_sig(codes) == known_sig:
                hits.append((addr + start, width, codes))
    return hits


def main():
    runs = parse_runs(sys.argv[1])
    print(f"runs={len(runs)}, known len={len(KNOWN)} chars")
    known_sig = repeat_sig(list(KNOWN))
    for width in (1, 2):
        hits = find(runs, known_sig, len(KNOWN), width)
        print(f"\n=== width={width}바이트 코드 매칭: {len(hits)}건 ===")
        for addr, w, codes in hits[:5]:
            print(f" addr=0x{addr:06X} codes({len(codes)}):")
            mapping = {}
            for ch, cd in zip(KNOWN, codes):
                mapping.setdefault(ch, cd)
            print("   " + "  ".join(f"{ch}={cd:0{2*w}X}" for ch, cd in mapping.items()))


if __name__ == "__main__":
    main()
