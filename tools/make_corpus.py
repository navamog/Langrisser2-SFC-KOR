#!/usr/bin/env python3
"""JP/EN 스크립트를 세그먼트 단위로 정렬해 번역 워크시트(TSV) 생성.

각 스크립트별로 jp \t en \t ko(빈칸) 를 corpus/scNN.tsv 로.
{end}로 세그먼트 분리. 개수 불일치 시 인덱스 정렬 + 잔여 표시.
"""
import os
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "toolkit", "derlangrisser"))
SC = os.path.join(ROOT, "resources", "scripts")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "corpus"))


def segs(path):
    if not os.path.exists(path):
        return None
    t = open(path, encoding="utf-8").read()
    # {end} 기준 분리, 각 세그먼트는 개행/공백 정리(마크업은 유지)
    parts = t.split("{end}")
    return [p.strip() for p in parts]


def one_line(s):
    return s.replace("\t", " ").replace("\n", "\\n").replace("\r", "")


def main():
    os.makedirs(OUT, exist_ok=True)
    jp_files = sorted(glob.glob(os.path.join(SC, "jp", "sc*.txt")))
    total_pairs = 0
    summary = []
    for jf in jp_files:
        name = os.path.basename(jf)
        ef = os.path.join(SC, "en", name)
        j = segs(jf) or []
        e = segs(ef)
        n = max(len(j), len(e) if e else 0)
        rows = []
        for k in range(n):
            js = j[k] if k < len(j) else ""
            es = e[k] if (e and k < len(e)) else ""
            if not js and not es:
                continue
            rows.append(f"{one_line(js)}\t{one_line(es)}\t")
        with open(os.path.join(OUT, name.replace(".txt", ".tsv")), "w", encoding="utf-8") as f:
            f.write("# JP\tEN\tKO\n")
            f.write("\n".join(rows))
        total_pairs += len(rows)
        summary.append((name, len(j), len(e) if e else 0))
    print(f"워크시트 생성: {len(jp_files)}개 → {OUT}")
    print(f"총 세그먼트 행: {total_pairs}")
    mism = [s for s in summary if s[2] and s[1] != s[2]]
    print(f"JP/EN 개수 불일치 스크립트: {len(mism)} (정렬 검토 필요)")
    for name, nj, ne in summary[:8]:
        print(f"  {name}: JP {nj} / EN {ne}")


if __name__ == "__main__":
    main()
