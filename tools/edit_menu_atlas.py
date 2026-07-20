#!/usr/bin/env python3
"""메뉴 아틀라스(font12.bmp)를 4-bit BMP 포맷 그대로 편집한다.
PIL 재저장은 8-bit로 바꿔 makevwf8(loadbmp16, 4-bit 전제)이 오독하므로 금지.
원본 font12_backup.bmp의 헤더/팔레트를 보존하고 픽셀 니블만 수정한다."""
from PIL import ImageFont, ImageDraw, Image

W, H = 128, 512
HDR = 0x76           # 픽셀 데이터 시작(14+40+64)
ROWBYTES = W // 2    # 64 (2픽셀/바이트, 4-bit)
SRC = "D:/Works/lag2/kor_patch/toolkit/derlangrisser/resources/data/font12_backup.bmp"
DST = "D:/Works/lag2/kor_patch/toolkit/derlangrisser/resources/data/font12.bmp"

raw = bytearray(open(SRC, "rb").read())
header = raw[:HDR]
pixdata = raw[HDR:]

# 4-bit 픽셀 배열로 언팩 (하위행부터 저장: file y1=H-1-y). 좌픽셀=상위니블.
px = [[0] * W for _ in range(H)]
for y in range(H):
    y1 = H - 1 - y
    base = y1 * ROWBYTES
    for xb in range(ROWBYTES):
        b = pixdata[base + xb]
        px[y][2 * xb] = (b >> 4) & 0xF
        px[y][2 * xb + 1] = b & 0xF


def clear_region(x0, y0, x1, y1):
    """글리프색(1,2,3)만 배경0으로. 빨강격자(4) 보존."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[y][x] in (1, 2, 3):
                px[y][x] = 0


def put_syllable(ch, cx, cy, font, thr=90, dy=-3):
    # dy=-3: 15px→14px + 위로 3px 이동으로 받침이 16px 셀 하단을 벗어나지 않게(하단 잘림 방지)
    m = Image.new("L", (16, 16), 0)
    ImageDraw.Draw(m).text((1, dy), ch, font=font, fill=255)
    mp = m.load()
    for y in range(16):
        for x in range(16):
            if mp[x, y] > thr:
                px[cy + y][cx + x] = 1  # 흰색


def put_word(word, cx, cy, font, **kw):
    for i, ch in enumerate(word):
        put_syllable(ch, cx + i * 16, cy, font, **kw)


# ── 메뉴 한글 배치 ──────────────────────────────────────────
F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 14)  # 14px: 받침 포함 16px 셀에 맞음

# 커맨드 메뉴(아틀라스 반각타일 $0040~ = 픽셀 y64~): 이동 공격 마법 소환 회복 명령
for row in (64, 80, 96):
    clear_region(0, row, 128, row + 16)
put_word("이동", 0, 64, F)
put_word("공격", 32, 64, F)
put_word("마법", 64, 64, F)
put_word("소환", 96, 64, F)
put_word("회복", 0, 80, F)
put_word("명령", 32, 80, F)

# 항목1 배포 페이즈(tile_list_prepare, y112): Commander→지휘관 $0070-, Sortie→출격 $0078-
clear_region(0, 112, 128, 128)  # y112 전체(Hire T 포함, 아래 용병메뉴로 대체)
put_word("지휘관", 0, 112, F)   # 지 휘 관 = $0070-$0075
put_word("출격", 64, 112, F)    # 출 격 = $0078-$007b

# 용병 고용 메뉴(r_cmd_ops, tile_list_prepare): Hire Troops/Item Equip/Placement → 고용/장비/배치
clear_region(0, 128, 128, 144)  # y128 전체(roops Equipment Placeme 대체)
clear_region(0, 144, 16, 160)   # y144 x0-15($0090-$0091 "nt"만, x16+ Confirm 등 보존)
put_word("고용", 0, 128, F)     # $0080-$0083 → slots $11-$14 (Hire Troops)
put_word("장비", 32, 128, F)    # $0084-$0087 → slots $15-$18 (Item Equip)
put_word("배치", 64, 128, F)    # $0088-$008b → slots $19-$1c (Placement)

# 항목6 시스템 메뉴(tile_list_options, slot=atlas-$00a0). 한글30타일≤영문33타일, 이웃 무손상
clear_region(8, 160, 128, 176)   # $00a1-$00af (x0-7=$00a0 보존)
clear_region(0, 176, 128, 192)   # $00b0-$00bf
clear_region(0, 192, 16, 208)    # $00c0-$00c1 (x16+=No data 등 보존)
put_word("저장하기", 8, 160, F)   # $00a1-$00a8 → slots $01-$08 (Save Game)
put_word("목표", 72, 160, F)      # $00a9-$00ac → slots $09-$0c (Objectives)
put_word("불러오기", 0, 176, F)   # $00b0-$00b7 → slots $10-$17 (Load Game)
put_word("설정", 64, 176, F)      # $00b8-$00bb → slots $18-$1b (Options)
put_word("턴종", 96, 176, F)      # $00bc-$00bf → slots $1c-$1f (End Phase 앞2음절)
put_syllable("료", 0, 192, F)     # $00c0-$00c1 → slots $20-$21 (턴종료 3음절)

# ── 4-bit로 리팩 후 저장(헤더 보존) ─────────────────────────
out = bytearray(header)
newpix = bytearray(len(pixdata))
for y in range(H):
    y1 = H - 1 - y
    base = y1 * ROWBYTES
    for xb in range(ROWBYTES):
        newpix[base + xb] = ((px[y][2 * xb] & 0xF) << 4) | (px[y][2 * xb + 1] & 0xF)
out += newpix
open(DST, "wb").write(out)
print(f"4-bit 아틀라스 저장 완료: {len(out)} bytes (원본 {len(raw)})")
