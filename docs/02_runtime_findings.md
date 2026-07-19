# 런타임 추적 결과 (Mesen2 자동화)

## Mesen2 헤드리스 자동화 툴체인 (확립)
- 실행: `Mesen.exe --testrunner /DoNotSaveSettings <rom> <script.lua>`
  - 헤드리스로 lua를 로드·자동실행, `emu.stop(code)`로 종료(exit code 반환).
- **필수 설정**: `settings.json`의 `Debug.ScriptWindow.AllowIoOsAccess=true`
  (기본 false면 Lua `io` 파일접근 차단). Mesen이 종료 시 settings를 덮어쓰므로
  `/DoNotSaveSettings`로 잠글 것.
- 핵심 Lua API:
  - `emu.addEventCallback(fn, emu.eventType.startFrame)`
  - `emu.addMemoryCallback(fn, emu.callbackType.read/write/exec, start, end)` → fn(addr,val)
  - `emu.read(addr, emu.memType.snesVideoRam/ snesCgRam/ snesWorkRam/ snesSpriteRam, false)`
  - `emu.takeScreenshot()` → PNG 바이너리 문자열 (파일로 저장해 눈으로 확인 가능)
  - `emu.setInput({start=true}, 0)` (프레임마다 호출해 버튼 유지)
  - `emu.getState()` → 중첩 테이블 (ppu.layers[n].chrAddress 등)
- 주의: Mesen `getState`의 `ppu.layers[n].chrAddress`는 **워드 단위**.
  실제 VRAM 바이트 오프셋 = 값 × 2. (tilemapAddress는 바이트로 관측됨)

## 텍스트/폰트 아키텍처 (확정)
- **오프닝 프롤로그 텍스트**: 부팅 후 타이틀(≈frame 3300)→Start→프롤로그(≈4200).
  「イェレスの空、赤き凶星昇りし年 / はるか呪われしヴェルゼリアの / 地より、大いなる野望を抱きし者 / 現わる。」
- **표시 레이어**: BG3 (bgMode=1, 2bpp). tilemap = VRAM 0x0400, chr = VRAM **0xC000**.
- **글리프 규격**: **8×16** (세로로 8×8 타일 2장: 상단/하단). 한자도 8×16 반각.
  - tilemap 배열: 한 줄 = 상단타일 행 + 하단타일 행. 상단 01·하단 10 = 첫 글자 등.
- **동적 폰트 업로드(핵심)**: 게임은 전체 한자폰트를 VRAM에 두지 않고,
  **현재 메시지에 필요한 글리프만 표시 순서대로** VRAM 0xC000에 올림.
  → 타일 인덱스는 등장 순서(01,02,03…)이며 원문 문자코드와 별개.
- 합성 검증: tilemap(0x400)+chr(0xC000) 합성 렌더가 화면 텍스트와 정확히 일치.
  (도구: 세션 중 작성한 BG 합성 스크립트 / `tools/vram_png.py`)

## 압축 확인 (정적 분석이 실패한 이유)
- VRAM의 글리프 비트맵(8×16, 2bpp/1bpp)을 ROM에서 직접 검색 → **불일치**.
- ROM 뱅크 0x08 등을 1bpp로 렌더 → 노이즈. **마스터 폰트 압축** 확정.
- 텍스트 코드도 ROM/WRAM에서 고정폭(1·2바이트)+줄구분자 매칭 전부 실패
  → **가변폭 또는 압축**. 표시 시점(3900~4210) 읽기는 전부 WRAM(0x7E)에서 발생
  = 프롤로그 텍스트는 그 이전에 WRAM으로 전개됨(압축 해제).
- WRAM 연속-주소 스윕 후보 버퍼: 0x7E8000(2048=BG3 타일맵 섀도우), 0x7EA880 등.

## 다음 단계 (인코딩/폰트 확보의 정확한 경로)
정적 검색이 아니라 **루틴 단위 실행 추적**이 필요:
1. **메시지 디코더 루틴 찾기**: 프롤로그 진입 직후(≈frame 3300~3900) exec 브레이크로
   압축 텍스트를 읽어 WRAM에 문자코드/타일을 쓰는 루프를 특정.
   그 루프가 만들어내는 코드열 ↔ 화면 글자 대응 → 인코딩 규칙/테이블.
2. **폰트 디컴프 루틴 찾기**: 글리프가 VRAM 0xC000에 써지기 직전의 디컴프레션 관찰
   → 압축 포맷 식별, 마스터 폰트 ROM 위치·포맷 확정.
3. 두 루틴의 소스 포인터 → 포인터 테이블/뱅킹 구조 파악.

## 한글 전략에 대한 시사점
- 동적 업로드 구조라 **거대한 정적 한자폰트 교체가 불필요**. 필요한 글리프만 공급.
- 단, 셀 폭이 **8px(반각)** — 한글 음절은 8×16이 매우 비좁음.
  16×16(2셀) 사용 시 줄당 글자수 절반. 나레이션엔 수용 가능 → 후반 설계 결정.
- 압축된 폰트/텍스트를 다루려면 디컴프/리컴프(또는 비압축 재배치) 도구 필요.

## 산출물 (mesen/)
- `scripts/`: recon, drive, dump_text, dump_state, trace_runs, trace_wram, trace_rom, probe*
- `out/`: 스크린샷(boot_*, drv_*, t4200_shot), VRAM/CGRAM/WRAM 덤프(t4200_*),
  합성/폰트 PNG, 트레이스(runs.txt, wramreads.bin, romruns.txt), state.txt
