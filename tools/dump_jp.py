#!/usr/bin/env python3
"""dump.php(Sobodash) 파이썬 포팅 — V1.1 롬에서 일본어 스크립트 덤프.

포인터 테이블: ROM 0x120000, LE24 × 95. 각 스크립트를 테이블로 디코드해
resources/scripts/jp/scNN.txt 로 저장(마크업 형식은 원 도구와 동일).
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "toolkit", "derlangrisser")
ROOT = os.path.abspath(ROOT)


def load_tbl(path):
    # UTF-8, git autocrlf로 CRLF일 수 있음 → \n 분리 후 \r 제거 (원본 LF 의도)
    data = open(path, "r", encoding="utf-8").read()
    lines = data.split("\n")
    return [ln.rstrip("\r") for ln in lines]


def main():
    T = lambda n: os.path.join(ROOT, "resources", "tables", n)
    tbl00 = load_tbl(T("00.tbl"))
    tblf7 = load_tbl(T("f7.tbl"))
    tblf8 = load_tbl(T("f8.tbl"))
    tblf9 = load_tbl(T("f9.tbl"))
    tblfa = load_tbl(T("fa.tbl"))
    tblfb = load_tbl(T("fb.tbl"))
    names = load_tbl(T("name.dat"))
    words = load_tbl(T("word.dat"))

    # 256개로 패딩(누락 인덱스는 빈 문자열)
    def pad(lst):
        return {i: (lst[i] if i < len(lst) else "") for i in range(256)}
    tbl00 = pad(tbl00)

    # 특수 케이스 (dump.php와 동일)
    tbl00[0] = "{end}\n\n"; tbl00[1] = "{01}"
    tbl00[2] = "{02}";      tbl00[3] = "{03}"
    tbl00[4] = "{04}";      tbl00[6] = "{06}"
    tbl00[7] = "{07}\n";    tbl00[8] = "\n"
    tbl00[9] = "{09}";      tbl00[252] = "{FC}"
    tbl00[253] = "{FD}";    tbl00[254] = "{FE}"
    tbl00[255] = "{FF}"

    rom = open(os.path.join(ROOT, "resources", "dl.rom"), "rb").read()
    assert __import__("hashlib").md5(rom).hexdigest() == "91d62c4cb790fc2fb38b10b68616e228", "롬 md5 불일치"

    # 포인터 테이블 (0x120000 ~ 0x12011D, LE24, +0x120000)
    ptr = []
    for i in range(0x120000, 0x12011D, 3):
        off = rom[i] | (rom[i + 1] << 8) | (rom[i + 2] << 16)
        ptr.append(0x120000 + off)

    outdir = os.path.join(ROOT, "resources", "scripts", "jp")
    os.makedirs(outdir, exist_ok=True)

    def ext(tbl, idx):
        return tbl[idx] if idx < len(tbl) else ""

    total_scripts = 0
    for i in range(len(ptr) - 1):
        out = []
        p = ptr[i]
        end = ptr[i + 1]
        while p < end:
            c = rom[p]
            if c == 0x01:
                p += 1; out.append("{01}{%02x}" % rom[p])
            elif c == 0x09:
                p += 1; out.append(ext(names, rom[p]))
            elif c == 0xf7:
                p += 1; out.append(ext(tblf7, rom[p]))
            elif c == 0xf8:
                p += 1; out.append(ext(tblf8, rom[p]))
            elif c == 0xf9:
                p += 1; out.append(ext(tblf9, rom[p]))
            elif c == 0xfa:
                p += 1; out.append(ext(tblfa, rom[p]))
            elif c == 0xfb:
                p += 1; out.append(ext(tblfb, rom[p]))
            else:
                cell = tbl00[c]
                if cell == "{04}":
                    p += 1; out.append(ext(words, rom[p]))
                elif cell == "{02}":
                    out.append("{02}")
                else:
                    out.append(cell)
            p += 1
        text = "".join(out)
        with open(os.path.join(outdir, "sc%02d.txt" % i), "w", encoding="utf-8") as f:
            f.write(text)
        total_scripts += 1
    print(f"덤프 완료: {total_scripts}개 스크립트 → {outdir}")
    print(f"포인터 수: {len(ptr)}, 범위 0x{ptr[0]:06X} ~ 0x{ptr[-1]:06X}")


if __name__ == "__main__":
    main()
