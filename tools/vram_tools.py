#!/usr/bin/env python3
"""VRAM 덤프에서 타일맵 파싱 + 폰트 타일 렌더링."""
import sys

SH = " .:oO@#"


def read_tilemap(vram, base):
    """32x32 타일맵 엔트리 파싱 -> 2D 리스트[row][col] = (tile, pal, prio, hf, vf)."""
    grid = []
    for row in range(32):
        r = []
        for col in range(32):
            off = base + (row * 32 + col) * 2
            w = vram[off] | (vram[off + 1] << 8)
            tile = w & 0x3FF
            pal = (w >> 10) & 7
            prio = (w >> 13) & 1
            hf = (w >> 14) & 1
            vf = (w >> 15) & 1
            r.append((tile, pal, prio, hf, vf))
        grid.append(r)
    return grid


def show_tilemap_indices(grid):
    """타일 인덱스를 16진 2자리로 격자 출력 (0=공백은 '..')."""
    for row in grid:
        line = []
        for (tile, *_rest) in row:
            if tile == 0:
                line.append("..")
            else:
                line.append(f"{tile & 0xFF:02X}")
        print("".join(line))


def decode_tile_2bpp(data, off):
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
    return rows


def decode_tile_4bpp(data, off):
    rows = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0 = data[off + y * 2]; p1 = data[off + y * 2 + 1]
        p2 = data[off + 16 + y * 2]; p3 = data[off + 16 + y * 2 + 1]
        for x in range(8):
            bit = 7 - x
            rows[y][x] = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1) | \
                         (((p2 >> bit) & 1) << 2) | (((p3 >> bit) & 1) << 3)
    return rows


def render_tiles(vram, chrbase, indices, bpp, per_row=16):
    """주어진 타일 인덱스들을 렌더 (각 인덱스는 chrbase 기준)."""
    dec = decode_tile_2bpp if bpp == 2 else decode_tile_4bpp
    tsize = 16 if bpp == 2 else 32
    maxv = 3 if bpp == 2 else 15
    for base in range(0, len(indices), per_row):
        group = indices[base:base + per_row]
        tiles = [dec(vram, chrbase + idx * tsize) for idx in group]
        for y in range(8):
            line = ""
            for tile in tiles:
                for x in range(8):
                    line += SH[int(tile[y][x] / maxv * (len(SH) - 1))]
                line += "|"
            print(line)
        labels = " ".join(f"{i:3X}" for i in group)
        print(f"-- idx: {labels}")


def main():
    vram = open(sys.argv[1], "rb").read()
    cmd = sys.argv[2]
    if cmd == "map":
        base = int(sys.argv[3], 0)
        show_tilemap_indices(read_tilemap(vram, base))
    elif cmd == "font":
        chrbase = int(sys.argv[3], 0)
        bpp = int(sys.argv[4])
        start = int(sys.argv[5], 0)
        count = int(sys.argv[6])
        render_tiles(vram, chrbase, list(range(start, start + count)), bpp)


if __name__ == "__main__":
    main()
