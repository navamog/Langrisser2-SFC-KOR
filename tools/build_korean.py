#!/usr/bin/env python3
"""한글 통합 v0.2: 빈도 상위 글리프 폰트(실제 폭) + KO 스크립트를 byuu 바이트포맷으로
인코딩(워드랩: 창 폭에 맞춰 줄/페이지 자동 재배치).

기존 6뱅크(80글리프/뱅크=480). top 479 + placeholder(□). ~97% 커버.
"""
import glob
import os
import re
import collections
from PIL import Image, ImageFont, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TK = os.path.join(ROOT, "toolkit", "derlangrisser")
KO = os.path.join(ROOT, "corpus", "ko")
BUILD = os.path.join(TK, "build")

BANKS = 15                   # 6→15 확장(bank $5A/$5B/$5C에 배치, 1166음절 전량 커버)
PER_BANK = 80
CAP = BANKS * PER_BANK - 1   # 마지막 슬롯은 □ placeholder
FONT_PX = 13
SS = 3                        # 슈퍼샘플 배율(서브픽셀 세로획 보존)
THR = 110                     # 한글 커버리지 임계값: 높을수록 얇음(획 유지 하한 ~140)
GY_PUNC = -3                  # 비한글(문장부호/영문/숫자) 세로보정: 상단 잘림 방지+베이스라인 정렬
THR_PUNC = 72                 # 비한글 임계값(낮게): !? 등 얇은 획 보존
TTF = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", FONT_PX)
TTF_SS = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", FONT_PX * SS)
GY = -4                       # 상단여백 보정
SPACE_W = 6                   # 공백 폭(px)
LINE_PX = 180                 # 한 줄 최대 폭(px) — 엔진 렌더 한계 ~192 미만
LINES_PER_WIN = 3             # 창당 줄 수

TOKEN_BYTE = {"02": 0x02, "03": 0x82, "06": 0x06, "07": 0x07,
              "fc": 0xFC, "fd": 0xFD, "fe": 0xFE, "ff": 0xFF}
PLACEHOLDER = (BANKS - 1, PER_BANK - 1)  # (5,79)


SCRIPTS_DIR = os.path.join(TK, "resources", "scripts")


def _load_msgs(path):
    """스크립트를 {end} 기준 메시지 리스트로(개수=원본 메시지 수, 빈 메시지 포함)."""
    if not os.path.exists(path):
        return []
    t = open(path, encoding="utf-8").read()
    n = t.count("{end}")
    parts = t.split("{end}")
    return [parts[k] for k in range(n)]


def _oneline(s):
    """make_corpus.one_line과 동일: TSV 저장형식(개행→리터럴 \\n)."""
    return s.replace("\t", " ").replace("\n", "\\n").replace("\r", "")


# 영문전용 메시지(JP빈+EN)인데 EN 폴백이 부적절한 경우(나레이션에 영어 끼어듦) → 강제 빈칸.
# sc84 오프닝/엔딩 나레이션의 영문 확장 슬롯(영문판이 일본어보다 길게 분할). 크레딧(k>=39)은 영문 유지.
FORCE_EMPTY = {84: {18, 37}}


def read_segments():
    """script i → [("empty",) | ("ko", ko_text), ...] (원본 메시지 구조 보존).
    ko_rows를 **순차가 아닌 JP 내용으로 매칭**해, make_corpus가 일부 메시지를 빠뜨려도
    (재덤프로 en에만 생긴 영문전용 메시지 등) 정렬이 자동 복구됨. 매칭 안 되는
    영문전용 메시지는 EN으로 폴백(기본 Latin 폰트로 영문 렌더)."""
    scripts = {}
    for i in range(94):
        jp = _load_msgs(os.path.join(SCRIPTS_DIR, "jp", f"sc{i:02d}.txt"))
        en = _load_msgs(os.path.join(SCRIPTS_DIR, "en", f"sc{i:02d}.txt"))
        tsv = []   # (jp_oneline, ko)
        f = os.path.join(KO, f"sc{i:02d}.tsv")
        if os.path.exists(f):
            for line in open(f, encoding="utf-8").read().split("\n")[1:]:
                c = line.split("\t")
                if len(c) >= 3:
                    tsv.append((c[0], c[2]))
        N = max(len(jp), len(en))
        msgs = []
        ti = 0
        for k in range(N):
            j = jp[k] if k < len(jp) else ""
            e = en[k] if k < len(en) else ""
            if j.strip() or e.strip():
                if i in FORCE_EMPTY and k in FORCE_EMPTY[i]:
                    msgs.append(("empty",))   # 나레이션 영문 bleed 방지
                    continue
                jl = _oneline(j.strip())
                if ti < len(tsv) and tsv[ti][0] == jl:
                    msgs.append(("ko", tsv[ti][1])); ti += 1
                else:
                    # 갭: TSV에 이 메시지 없음 → EN 폴백(영문전용 메시지)
                    msgs.append(("ko", _oneline(e.strip())))
            else:
                msgs.append(("empty",))
        scripts[i] = msgs
    return scripts


_NORM = {"、": ",", "。": ".", "「": '"', "」": '"', "・": "·", "　": " "}


def norm_char(c):
    o = ord(c)
    if c == "　":            # 전각 공백 → 반각
        return " "
    if 0xFF01 <= o <= 0xFF5E:    # 전각 ASCII → 반각
        return chr(o - 0xFEE0)
    return _NORM.get(c, c)


def iter_chars(seg):
    i = 0
    out = []
    while i < len(seg):
        c = seg[i]
        if c == "\\" and i + 1 < len(seg) and seg[i + 1] == "n":
            out.append(("nl", None)); i += 2; continue
        if c == "{":
            j = seg.find("}", i)
            if j < 0:
                i += 1; continue
            tok = seg[i + 1:j].lower(); i = j + 1
            if tok == "end":
                continue
            if tok in TOKEN_BYTE:
                out.append(("raw", TOKEN_BYTE[tok]))
            elif tok == "01":
                out.append(("raw", 0x01))
            elif tok.startswith("skip "):
                pass  # 한글 재배치에선 원본 skip 무시
            elif re.fullmatch(r"[0-9a-f]{2}", tok):
                out.append(("raw", int(tok, 16)))
            continue
        out.append(("ch", norm_char(c))); i += 1
    return out


def render_glyph(ch):
    """글자 → (64바이트 2bpp, 실제폭). 3배 슈퍼샘플→커버리지 임계값으로
    서브픽셀 세로획(ㅏ/ㅓ의 ㅣ)이 임계값 아래로 탈락하던 문제 해결.
    한글은 GY=-4/THR=110(얇게), 비한글 문장부호/영문은 GY=-3/THR=72
    (상단 잘림 방지+얇은 획 보존, 베이스라인은 한글과 정렬)."""
    hangul = 0xAC00 <= ord(ch) <= 0xD7A3 if len(ch) == 1 else False
    gy = GY if hangul else GY_PUNC
    thr = THR if hangul else THR_PUNC
    img = Image.new("L", (16 * SS, 16 * SS), 0)
    ImageDraw.Draw(img).text((1 * SS, gy * SS), ch, font=TTF_SS, fill=255)
    px = img.load()
    data = bytearray(64)
    maxx = -1
    for y in range(13):
        left = right = 0
        for x in range(16):
            tot = 0
            for dy in range(SS):
                yy = y * SS + dy
                for dx in range(SS):
                    tot += px[x * SS + dx, yy]
            if tot // (SS * SS) > thr:
                if x < 8:
                    left |= (1 << (7 - x))
                else:
                    right |= (1 << (7 - (x - 8)))
                maxx = max(maxx, x)
        data[y * 2] = left
        data[y * 2 + 32] = right
    width = (maxx + 2) if maxx >= 0 else SPACE_W  # 오른쪽 1px 여백
    return bytes(data), min(width, 16)


def build_glyph_map(scripts):
    freq = collections.Counter()
    for segs in scripts.values():
        for msg in segs:
            if msg[0] != "ko":
                continue
            for kind, val in iter_chars(msg[1]):
                if kind == "ch" and val not in "\t\r":
                    freq[val] += 1
    top = [ch for ch, _ in freq.most_common(CAP)]
    gmap = {}
    for idx, ch in enumerate(top):
        gmap[ch] = (idx // PER_BANK, idx % PER_BANK)
    print(f"글리프맵: {len(top)}/{len(freq)} (미포함 {len(freq)-len(top)} → □)")
    return gmap, top


def write_fonts(top):
    """fontv0-14.bin 생성 + width_map[(bank,idx)] 반환."""
    wmap = {}
    total = BANKS * PER_BANK
    layout = list(top) + [" "] * (total - len(top))
    ph_idx = PLACEHOLDER[0] * PER_BANK + PLACEHOLDER[1]  # □ 전용 마지막 슬롯
    layout[ph_idx] = "□"
    for bank in range(BANKS):
        widths = bytearray(128)
        glyphs = bytearray()
        for idx in range(PER_BANK):
            gi = bank * PER_BANK + idx
            ch = layout[gi] if gi < len(layout) else " "
            g, w = render_glyph(ch)
            if ch == " ":
                w = SPACE_W
            widths[idx] = w
            wmap[(bank, idx)] = w
            glyphs += g
        with open(os.path.join(BUILD, f"fontv{bank}.bin"), "wb") as f:
            f.write(bytes(widths) + bytes(glyphs))
    print(f"한글 폰트 {BANKS}뱅크 생성 완료")
    return wmap


# byuu 영문 인코딩(table12a.tbl): 글리프 index → 문자. 이름/클래스는 태그 없이
# 기본 폰트로 렌더되므로, 기본 폰트를 이 Latin 뱅크로 지정하면 영문으로 표시됨.
def _latin_map():
    m = {}
    for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        m[i] = c                    # idx 0-25
    for i, c in enumerate("abcdefghijklmnopqrs"):
        m[26 + i] = c               # idx 26-44 (a-s)
    for i, c in enumerate("tuvwxyz"):
        m[75 + i] = c               # idx 75-81 (t-z)
    m[82] = " "                     # space(0x5c)
    for i, c in enumerate("0123456789"):
        m[87 + i] = c               # idx 87-96 (숫자: load_number가 0x61+d로 출력)
    return m


LATIN_GLYPHS = 97                   # idx 0-96 (영문+space+숫자)


def write_latin_bank():
    """fontvL.bin: byuu 배치의 영문 글리프 뱅크(이름/클래스 기본 폰트용)."""
    lm = _latin_map()
    widths = bytearray(128)
    glyphs = bytearray()
    for idx in range(LATIN_GLYPHS):
        ch = lm.get(idx, " ")
        g, w = render_glyph(ch)
        if ch == " ":
            w = SPACE_W
        widths[idx] = w
        glyphs += g
    with open(os.path.join(BUILD, "fontvL.bin"), "wb") as f:
        f.write(bytes(widths) + bytes(glyphs))
    print(f"Latin 뱅크 생성 완료({LATIN_GLYPHS}글리프)")


def layout_message(items, gmap, wmap):
    """items(파싱된 세그먼트) → 워드랩된 바이트열.
    space로 단어 분리, 창 폭 초과 시 줄바꿈(0x08), 3줄 초과 시 새창(0x06 0x07)."""
    # 단어/토큰 단위로 정리
    words = []      # 각 원소: ('w', [(bank,idx,w),...]) | ('raw',byte) | ('page',) | ('sp',)
    cur = []
    for kind, val in items:
        if kind == "ch":
            if val == " ":
                if cur:
                    words.append(("w", cur)); cur = []
                words.append(("sp",))
            elif val in "\t\r":
                continue
            else:
                bank, idx = gmap.get(val, PLACEHOLDER)
                cur.append((bank, idx, wmap.get((bank, idx), 14)))
        elif kind == "nl":
            if cur:
                words.append(("w", cur)); cur = []
            words.append(("sp",))  # 번역가 개행은 공백으로(재배치)
        elif kind == "raw":
            if val == 0x06:
                pass  # 0x06,0x07 페어를 page로
            elif val == 0x07:
                if cur:
                    words.append(("w", cur)); cur = []
                words.append(("page",))
            elif val == 0x01:
                words.append(("raw", 0x01))
            else:
                words.append(("raw", val))
    if cur:
        words.append(("w", cur))

    space_slot = gmap.get(" ", PLACEHOLDER)
    out = bytearray()
    cur_bank = -1
    line_px = 0
    line_no = 0

    def emit_glyph(bank, idx):
        nonlocal cur_bank
        if bank != cur_bank:
            out.append(0x90 + bank); cur_bank = bank
        out.append(0x0A + idx)

    def newline():
        nonlocal line_px, line_no, cur_bank
        out.append(0x08); line_px = 0; line_no += 1; cur_bank = -1

    def newwin():
        nonlocal line_px, line_no, cur_bank
        out.append(0x06); out.append(0x07); line_px = 0; line_no = 0; cur_bank = -1

    need_space = False
    for w in words:
        if w[0] == "page":
            newwin(); need_space = False
        elif w[0] == "sp":
            need_space = True
        elif w[0] == "raw":
            if w[1] == 0x02:      # 플레이어명 치환: Latin 폰트(0xa0)로 감싸 영문 렌더
                out.append(0xA0)
                out.append(0x02)
                cur_bank = -1     # 이름 뒤 다음 글리프가 한글 태그 재발행
                line_px += 48
            else:
                out.append(w[1])
            need_space = False
        elif w[0] == "w":
            glyphs = w[1]
            wpx = sum(g[2] for g in glyphs)
            if line_px == 0:
                for (b, x, gw) in glyphs:
                    emit_glyph(b, x); line_px += gw
            elif line_px + SPACE_W + wpx <= LINE_PX:
                if need_space:
                    emit_glyph(*space_slot); line_px += SPACE_W
                for (b, x, gw) in glyphs:
                    emit_glyph(b, x); line_px += gw
            else:
                if line_no >= LINES_PER_WIN - 1:
                    newwin()
                else:
                    newline()
                for (b, x, gw) in glyphs:
                    emit_glyph(b, x); line_px += gw
            need_space = False
    out.append(0x00)
    return out


def encode(scripts, gmap, wmap):
    os.makedirs(BUILD, exist_ok=True)
    pt = 0x100000
    sc = bytearray()
    for i in range(94):
        segs = scripts.get(i, [])
        out = bytearray()
        for msg in segs:
            if msg[0] == "empty":
                out.append(0x00)
            else:
                out += layout_message(iter_chars(msg[1]), gmap, wmap)
        if not out:
            out = bytearray(2048)
        with open(os.path.join(BUILD, f"sc{i:02d}.bin"), "wb") as f:
            f.write(bytes(out))
        sc += bytes([pt & 0xFF, (pt >> 8) & 0xFF, (pt >> 16) & 0xFF])
        pt += len(out)
    with open(os.path.join(BUILD, "sc.bin"), "wb") as f:
        f.write(bytes(sc))
    print(f"스크립트 인코딩 완료: 94개, 총 {pt-0x100000} 바이트")


def main():
    scripts = read_segments()
    gmap, top = build_glyph_map(scripts)
    wmap = write_fonts(top)
    write_latin_bank()
    encode(scripts, gmap, wmap)


if __name__ == "__main__":
    main()
