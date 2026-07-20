#!/usr/bin/env bash
# 한글 롬 빌드: 영문 8x8/그래픽 자산 + build_korean.py(16x16폰트+스크립트) → xkas ×9 → text12ins
set -e
cd "$(dirname "$0")/../toolkit/derlangrisser"
BIN=toolchain/bin
mkdir -p build
cp resources/dl.rom build/dl.sfc

echo "[0] 메뉴 아틀라스 한글 주입(4-bit BMP 직접 편집)"
python ../../tools/edit_menu_atlas.py

echo "[1] 8x8 폰트/스크립트/그래픽 자산"
$BIN/makevwf8
$BIN/text8i
$BIN/bmptoimg
$BIN/bdconv
$BIN/dcconv

echo "[2] 한글 16x16 폰트 + 스크립트 인코딩"
python ../../tools/build_korean.py

echo "[3] xkas 어셈블 ×9"
for a in intro decomp name text_a text_b text_c window font12 font8; do
  $BIN/xkas resources/asm/$a.asm build/dl.sfc
done

echo "[4] 스크립트 삽입"
$BIN/text12ins build/dl.sfc

echo "[5] IPS 생성 + 배포본 복사"
python ../../tools/mkips.py resources/dl.rom build/dl.sfc ../../DerLangrisser_Korean_v1.0.ips
cp build/dl.sfc ../../mesen/out/dl_korean_v01.sfc
echo "완료: build/dl.sfc ($(stat -c%s build/dl.sfc) bytes)"
