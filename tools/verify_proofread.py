#!/usr/bin/env python3
"""교정 워크플로우 후 구조/마크업 보존 검증: corpus/ko vs corpus/ko_backup.
행 수·탭 수·핵심 마크업 토큰 개수가 KO 컬럼에서 보존됐는지 확인.
불일치 파일은 revert 후보로 표시."""
import glob
import os
import re

KO = "D:/Works/lag2/kor_patch/corpus/ko"
BK = "D:/Works/lag2/kor_patch/corpus/ko_backup"

TOKENS = ["{02}", "{03}", "{06}", "{07}", "{09}", "{01}", "\\n"]
SKIP_RE = re.compile(r"\{skip \d+\}")
HEX_RE = re.compile(r"\{[0-9a-fA-F]{2}\}")


def load_rows(path):
    rows = []
    for line in open(path, encoding="utf-8").read().split("\n")[1:]:
        c = line.split("\t")
        if len(c) >= 3:
            rows.append(c)
    return rows


def ko_tokens(rows):
    """KO 컬럼 전체의 토큰 카운트 딕셔너리."""
    ko = "".join(r[2] for r in rows)
    d = {t: ko.count(t) for t in TOKENS}
    d["skip"] = len(SKIP_RE.findall(ko))
    d["hex"] = len(HEX_RE.findall(ko))
    return d


bad = []
for path in sorted(glob.glob(os.path.join(KO, "sc*.tsv"))):
    name = os.path.basename(path)
    bpath = os.path.join(BK, name)
    if not os.path.exists(bpath):
        continue
    cur, old = load_rows(path), load_rows(bpath)
    issues = []
    if len(cur) != len(old):
        issues.append(f"행수 {len(old)}→{len(cur)}")
    # JP/EN 컬럼 불변 확인
    jp_en_changed = sum(1 for a, b in zip(cur, old) if a[0] != b[0] or a[1] != b[1])
    if jp_en_changed:
        issues.append(f"JP/EN변경 {jp_en_changed}행")
    tc, to = ko_tokens(cur), ko_tokens(old)
    for k in tc:
        if tc[k] != to[k]:
            issues.append(f"토큰 {k} {to[k]}→{tc[k]}")
    if issues:
        bad.append((name, issues))

if bad:
    print("=== 구조/마크업 불일치 파일 (revert 검토) ===")
    for name, issues in bad:
        print(f"  {name}: {'; '.join(issues)}")
else:
    print("전체 94 파일 구조·마크업 보존 OK")
print(f"불일치 파일: {len(bad)}")
