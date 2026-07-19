# 공식 번역 툴킷 확보 — 전략 전환

## 요약
영문 팬번역(D=Sobodash / Near=byuu)의 **공식 오픈소스 툴킷**을 확보했다.
GitHub 원본(sobodash/derlangrisser)은 삭제됐으나 미러
`github.com/cualquiercosa327/derlangrisser`에서 클론 → `toolkit/derlangrisser/`.
이로써 프로젝트는 "원본 일본 VM 역공학"에서 **"검증된 툴킷 위에 한글 얹기"**로 전환.

- 필요 롬: **V1.1** (md5 `91d62c4cb790fc2fb38b10b68616e228`) — 보유 파일과 일치 확인.
- 라이선스: 오픈소스 팬번역 도구(비상업).

## 내 역공학과 완전 일치 (검증됨)
- `resources/tables/00.tbl` = **바이트값→글자** 직접표(0x0A=ア, 0x0D=エ, 0x14=サ…) — 내 디코드와 일치.
- `f7.tbl~fb.tbl` = **0xF7~0xFB 확장코드 인자→한자** 표(F7 00=序 …) — 내가 찾은 2바이트 확장 그대로.
- `name.dat`/`word.dat` = 이름/단어 치환(내가 찾은 WRAM 0x7EB006 이름테이블 계열).
- 스크립트 마크업 `{end}`,`{skip N}`,`{02}` = 제어코드(0x00 종료 등)·변수치환의 사람이 읽는 표현.

## 툴킷 구조 (`toolkit/derlangrisser/`)
- `Makefile` — 빌드/덤프 파이프라인.
- `reference/` — codes.md(치트/디버그), notes.md(번역노트), scenarios.txt, style.md, scenario-chart.png.
- `resources/`
  - `scripts/en/scXX.txt` — 시나리오 스크립트(영문). `scripts/event/evXX.txt` — 이벤트.
    `make dump` 시 `scripts/jp/*.txt`(원본 일본어)도 생성.
  - `tables/` — 글자표(위). `data/`,`define/`,`events/` — 데이터/정의.
  - `asm/` — byuu의 재작성 ASM(intro, decomp, name, text_a/b/c, window, font8, font12 …).
- `toolchain/` — dump.php, decompev.php(이벤트 디컴프), createips.php, proper.php, scscan.php,
  `custom/`(C 도구: makevwf8/12, text8/12 i/d, decomp, bmptoimg …), `xkas/`(어셈블러), `dledit/`.

## 빌드 파이프라인
- `make toolchain` : C 도구 + xkas 컴파일(clang/gcc 필요).
- `make dump` : 원본 JP 스크립트/그래픽/이벤트 덤프 → resources/scripts/jp 등.
- `make` : 폰트→바이너리, 스크립트→바이너리, 그래픽 압축, xkas로 ASM 패치, 스크립트 삽입 → build/dl.sfc.
- `make ips` : IPS 패치 생성.
- **요구**: PHP 7+, clang(or gcc), make. (현재 PHP 미설치. Windows는 "on their own".)

## 한글 엔진 관점 (핵심 결정거리)
- byuu 엔진은 **가변폭 폰트(VWF) 8x8·12x12**(라틴 최적화). 한글 음절은 12x12엔 매우 비좁음.
  - 옵션A: 12x12/16x16 폰트 경로에 **한글 글리프** 제작·삽입(byuu 폰트 시스템 확장).
  - 옵션B: 원본 JP의 16x16 전각 경로를 활용(툴킷 ASM 일부 되돌림/수정).
- 조사·삽입에 필요한 ASM·폰트 도구가 모두 소스로 있으므로 수정 가능.

## 한글패치 계획 (개정 — 훨씬 현실적)
1. **빌드 환경 구성**: PHP7+, clang/gcc, make (git-bash/MSYS 또는 WSL). `make toolchain`→`make dump` 성공.
2. **원문 확보**: `scripts/jp/*.txt`(일본어) + `scripts/en/*.txt`(영문) 대응 → 번역 원문.
3. **한글 폰트**: 12x12(또는 16x16) 한글 글리프셋 제작 + byuu 폰트/표시 ASM 수정.
4. **번역**: 스크립트 텍스트를 한글로(마크업 유지). 이름 치환(name.dat) 한국어화(조사 처리 고려).
5. **빌드·검증**: `make` → emucap 라이브 디버거로 인게임 확인.

## 진행: 일본어 원문 덤프 완료 (PHP 없이 파이썬 포팅)
- `tools/dump_jp.py` = dump.php 포팅. 포인터 테이블 **ROM 0x120000**(LE24×95), 테이블 디코드.
  → `toolkit/.../resources/scripts/jp/sc00~sc93.txt` (94개, JP 997KB).
- `tools/make_corpus.py` → `corpus/scNN.tsv` (JP\tEN\tKO). {end} 분리 시 **전 94스크립트 개수 정확 일치**,
  총 **10,808 세그먼트**. 캐릭터명 정렬 확인(エルウィン↔Erwin 등). 한국어 열만 채우면 번역 완성.
- 다음: 한글 폰트(byuu VWF 확장) + 스크립트 삽입 도구(text*ins) → build. (빌드엔 PHP/clang/make 필요,
  또는 삽입기도 파이썬 포팅 가능 — dump 역방향.)

## 런타임 한글 POC 결과 (교훈)
- emucap로 대사 화면 VRAM 폰트에 한글 글리프 직접 주입 시도 → 가시 폰트 타일 특정 실패.
  원인: 대사창 폰트가 프롤로그(8x16@0xC000)와 다른 베이스/레이어일 수 있고, BG3가 64x64
  멀티스크린 타일맵이라 가시 셀↔타일 매핑이 까다로움. + 폰트가 프레임마다 재업로드될 소지.
  또한 emucap screenshot은 현재 VRAM 즉시 재렌더가 아니라 마지막 프레임 버퍼를 반환.
- **결론**: 한글 폰트는 런타임 주입이 아니라 **툴킷 빌드 경로**(폰트 비트맵 편집→makevwf→재빌드)로.
  이게 영문팀 방식이자 결정론적. (write_memory 자체는 동작 — 치트/일시 테스트엔 유효.)

## 빌드 환경 구성 진행 (이번 세션)
- **C 툴체인 빌드 성공(13/14)**: LLVM clang 22 설치. `toolchain/bin/*.exe` 컴파일 완료
  (bdconv, bmptoimg, dbconv, dcconv, decomp, makevwf8/12, ptobmp, text8d/i, text12d/i/ins).
  - 이식 수정: 신형 clang 암시적 선언 에러 → `-Wno-error=implicit-function-declaration -include string.h`.
    ucrt `strlwr`/`strupr` 충돌 → 소스에서 `xkstrlwr`/`xkstrupr`로 리네임(libstr.cpp, text12i.c).
  - **검증: text12ins/makevwf12 등 실제 실행 성공**(exit 0, ROM/폰트 생성).
- **xkas(C++ 어셈블러) 수정 완료 ✅**: Windows 이식 버그 2건 해결.
  - `base.h`의 `typedef unsigned long ulong` → 64비트(LLP64)에서 32비트라 포인터 절단 →
    `unsigned long long`로 수정. `strlwr`/`strupr` ucrt 충돌 → `xkstrlwr`/`xkstrupr` 리네임.
  - **결정타**: `assemble()`의 `fopen(dfn, "rb+wb")` — **잘못된 fopen 모드**. 구형 libc는 무시했으나
    신형 ucrt는 invalid-parameter 핸들러로 fastfail(0xC0000409) → 크래시. `"rb+wb"`→`"rb+"` 전부 교체.
- **★전체 빌드 검증 완료 ✅**: 14개 도구로 Makefile `all` 순서 직접 구동 → `build/dl.sfc`(4MB).
  **공식 `dl.ips`(V1.1 적용)와 md5 완전 일치** (`7d696baa7535458b74e385a668785630`) — 소스빌드가
  릴리스를 비트 단위 재현. **한글은 폰트·스크립트·테이블만 교체 후 재빌드하면 됨.**
- Makefile은 macOS(`md5 -q`, `-stdlib=libc++`) 의존이라 미사용, 빌드 단계를 직접 구동(`tools/build.sh` 화 가능).

## 빌드 방법 (Windows, 확립)
```
# 1회: 툴체인 빌드 (LLVM clang 필요)
CLANG="/c/Program Files/LLVM/bin/clang.exe"; CLANGXX=".../clang++.exe"
# C도구: -O2 -w -Wno-error=implicit-function-declaration -include string.h -include stdlib.h
# xkas:  clang++ -O2 -w (base.h ulong·strlwr·"rb+" 수정본)
# 빌드: makevwf8/12 → text8i/text12i → bmptoimg/bdconv/dcconv → xkas ×9(asm) → text12ins
```

## 번역 진행 (병렬 워크플로우)
- `corpus/glossary.md`(고유명사 한국어 표준표) 작성. 94개 스크립트를 sonnet 에이전트로 병렬 번역 →
  `corpus/ko/scNN.tsv`. 품질 양호(마크업·조사·글로서리 준수). 백그라운드 진행 중.

## 자산
- 툴킷: `kor_patch/toolkit/derlangrisser/` (미러 클론).
- 최종 영문 패치: `toolkit/derlangrisser/dl.ips`, 릴리스 zip: `toolkit/extracted/`.
- 참고 아카이브: archive.org `derlangrisser-t-eng-1.3.1`, Software Heritage(봇차단), voidfox.com 블로그.
