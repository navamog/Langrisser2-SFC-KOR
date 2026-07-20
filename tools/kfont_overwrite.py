#!/usr/bin/env python3
"""build/fontvN.bin(byuu VWF 폰트)의 글리프를 한글로 덮어써 렌더링을 검증.

byuu 글리프 포맷: 각 글리프 64바이트. 16폭×13행, 2bpp.
  행 y(0..12): 좌8px → data[y*2](plane0), data[y*2+1](plane1);
               우8px → data[y*2+32], data[y*2+33].
fontvN.bin = [80 widths(128B 영역)] + [80 glyphs × 64B].
"""
import sys
from PIL import Image, ImageFont, ImageDraw

FONT = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 14)
SYLS = "가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허고노도로모보소오조초코토포호구누두루무부수우주추쿠투푸후"


def render_glyph(ch):
    """한 글자 → 64바이트 byuu 글리프(2bpp, value 1)."""
    img = Image.new("L", (16, 16), 0)
    d = ImageDraw.Draw(img)
    d.text((1, 1), ch, font=FONT, fill=255)
    px = img.load()
    data = bytearray(64)
    for y in range(13):
        left = right = 0
        for x in range(8):
            if px[x, y] > 90:
                left |= (1 << (7 - x))
            if px[x + 8, y] > 90:
                right |= (1 << (7 - x))
        data[y * 2] = left           # plane0 좌
        data[y * 2 + 1] = 0          # plane1 좌
        data[y * 2 + 32] = right     # plane0 우
        data[y * 2 + 33] = 0
    return bytes(data)


def overwrite(path):
    with open(path, "rb") as f:
        buf = bytearray(f.read())
    nglyph = (len(buf) - 128) // 64
    for z in range(nglyph):
        ch = SYLS[z % len(SYLS)]
        g = render_glyph(ch)
        off = 128 + z * 64
        buf[off:off + 64] = g
        # 폭 테이블(선두 128B 영역, z<80): 한글은 16폭 고정
        if z < 128:
            buf[z] = 16
    with open(path, "wb") as f:
        f.write(buf)
    print(f"{path}: {nglyph}개 글리프 한글로 덮어씀")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        overwrite(p)
