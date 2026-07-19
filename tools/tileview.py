#!/usr/bin/env python3
"""SNES 타일 렌더러 — 폰트 포맷(bpp/크기) 식별용 ASCII 아트 출력.

사용: tileview.py <rom> <offset> <bpp> <count> [tiles_per_row]
  bpp: 1, 2, 4
"""
import sys

SHADE = " .:oO@#"  # 밝기 단계


def decode_tile_1bpp(data, off):
    """8x8 1bpp -> 8행 리스트(각 행 8픽셀 0/1)."""
    rows = []
    for y in range(8):
        b = data[off + y]
        rows.append([(b >> (7 - x)) & 1 for x in range(8)])
    return rows  # 8 bytes/tile


def decode_tile_2bpp(data, off):
    """8x8 2bpp planar (SNES) -> 값 0..3."""
    rows = []
    for y in range(8):
        lo = data[off + y * 2]
        hi = data[off + y * 2 + 1]
        row = []
        for x in range(8):
            bit = 7 - x
            v = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1)
            row.append(v)
        rows.append(row)
    return rows  # 16 bytes/tile


def decode_tile_4bpp(data, off):
    rows = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0 = data[off + y * 2]
        p1 = data[off + y * 2 + 1]
        p2 = data[off + 16 + y * 2]
        p3 = data[off + 16 + y * 2 + 1]
        for x in range(8):
            bit = 7 - x
            v = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1) | \
                (((p2 >> bit) & 1) << 2) | (((p3 >> bit) & 1) << 3)
            rows[y][x] = v
    return rows  # 32 bytes/tile


def main():
    rom = open(sys.argv[1], "rb").read()
    off = int(sys.argv[2], 0)
    bpp = int(sys.argv[3])
    count = int(sys.argv[4])
    per_row = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    dec = {1: decode_tile_1bpp, 2: decode_tile_2bpp, 4: decode_tile_4bpp}[bpp]
    tilesize = {1: 8, 2: 16, 4: 32}[bpp]
    maxv = {1: 1, 2: 3, 4: 15}[bpp]
    # per_row 개씩 가로로 이어 붙여 출력
    tiles = []
    for t in range(count):
        tiles.append(dec(rom, off + t * tilesize))
    for base in range(0, count, per_row):
        group = tiles[base:base + per_row]
        for y in range(8):
            line = []
            for tile in group:
                for x in range(8):
                    v = tile[y][x]
                    idx = int(v / maxv * (len(SHADE) - 1)) if maxv else v
                    line.append(SHADE[idx])
                line.append("|")
            print("".join(line))
        print(f"--- tiles {base}..{base+len(group)-1} @ 0x{off+base*tilesize:06X} ---")


if __name__ == "__main__":
    main()
