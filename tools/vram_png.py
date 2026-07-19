#!/usr/bin/env python3
"""VRAM/CGRAM 덤프를 실제 팔레트로 PNG 타일시트 렌더.

사용:
  vram_png.py sheet <vram.bin> <cgram.bin> <bpp> <chrbase> <ntiles> <out.png> [palrow]
  vram_png.py bg <vram.bin> <cgram.bin> <bpp> <chrbase> <mapbase> <out.png>  # BG 화면 합성
"""
import sys
from PIL import Image


def load(p):
    return open(p, "rb").read()


def cgram_palette(cgram):
    """CGRAM 512바이트 -> 256색 RGB 리스트 (SNES BGR555)."""
    pal = []
    for i in range(256):
        w = cgram[i * 2] | (cgram[i * 2 + 1] << 8)
        r = (w & 0x1F) << 3
        g = ((w >> 5) & 0x1F) << 3
        b = ((w >> 10) & 0x1F) << 3
        pal.append((r | r >> 5, g | g >> 5, b | b >> 5))
    return pal


def decode_tile(vram, off, bpp):
    px = [[0] * 8 for _ in range(8)]
    if bpp == 2:
        for y in range(8):
            lo = vram[off + y * 2]; hi = vram[off + y * 2 + 1]
            for x in range(8):
                b = 7 - x
                px[y][x] = ((lo >> b) & 1) | (((hi >> b) & 1) << 1)
    else:  # 4bpp
        for y in range(8):
            p0 = vram[off + y * 2]; p1 = vram[off + y * 2 + 1]
            p2 = vram[off + 16 + y * 2]; p3 = vram[off + 16 + y * 2 + 1]
            for x in range(8):
                b = 7 - x
                px[y][x] = ((p0 >> b) & 1) | (((p1 >> b) & 1) << 1) | \
                           (((p2 >> b) & 1) << 2) | (((p3 >> b) & 1) << 3)
    return px


def sheet(vram, pal, bpp, chrbase, ntiles, out, palrow=0, per_row=32, scale=2):
    tsize = 16 if bpp == 2 else 32
    ncol = per_row
    nrow = (ntiles + ncol - 1) // ncol
    # 팔레트 기준: 2bpp는 palrow*4, 4bpp는 palrow*16
    pbase = palrow * (4 if bpp == 2 else 16)
    img = Image.new("RGB", (ncol * 8, nrow * 8), (40, 40, 40))
    px = img.load()
    for t in range(ntiles):
        tile = decode_tile(vram, chrbase + t * tsize, bpp)
        tx = (t % ncol) * 8
        ty = (t // ncol) * 8
        for y in range(8):
            for x in range(8):
                v = tile[y][x]
                color = (20, 20, 20) if v == 0 else pal[pbase + v]
                px[tx + x, ty + y] = color
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(out)
    print(f"saved {out} ({ntiles} tiles, {ncol}x{nrow})")


def main():
    cmd = sys.argv[1]
    if cmd == "sheet":
        vram = load(sys.argv[2]); cgram = load(sys.argv[3])
        bpp = int(sys.argv[4]); chrbase = int(sys.argv[5], 0)
        ntiles = int(sys.argv[6]); out = sys.argv[7]
        palrow = int(sys.argv[8]) if len(sys.argv) > 8 else 0
        sheet(vram, cgram_palette(cgram), bpp, chrbase, ntiles, out, palrow)


if __name__ == "__main__":
    main()
