# CLAUDE.md — ETS per-channel SiPM breakout boards

Working notes for Claude Code in this repo. Read [`README.md`](README.md) for the
user-facing overview and [`docs/session-report.md`](docs/session-report.md) for the
full development history/rationale.

## What this is

Passive per-channel breakout boards that **replace the broken `iv-pulse-mux`**
relay multiplexer in the Brunner-lab **ETS-96-channel-IV-pulse-mux** system. Each
board mates the detector-side **QSE-040-01-L-D-A** socket (connector **J5**) and
fans every channel out to its own coax jack — 24× `SIPM_K0..K23` + `IV` = 25 jacks
per board. The 96-channel system uses 4 identical boards (same J5 pinout in every
position). **Designators:** the socket keeps **J5** (upstream mapping); the jacks are
**J6..J30** (K0→J6 … K23→J29, IV→J30), each with its channel identity (`K0..K23`, `IV`) as a
**silkscreen label**. Mounting-hole designators (MH…) are hidden on silk.

**J5 mounts on the BACK face (B.Cu); all coax jacks are on the FRONT (F.Cu)** — the
detector plugs into the back, cables come off the front. J5 is flipped in `gen_board.py`.
**Board A (MCX)** is FreeRouting-autorouted as an all-B.Cu **balanced ~12/13** planar fan with
**zero signal vias** (its through-hole jacks plate the signal through every layer; 4 spilled
channels wrap the connector ends on B.Cu). **Boards B/C/D** use the deterministic router
(`finalize_board.py`), which reads which face J5 is on and routes escapes on that layer (HOME),
hopping to the other signal layer (OTHER) only for the crossing fans.

| Board | Jacks | Part | Status |
|-------|-------|------|--------|
| A | 25× MCX | Samtec MCX-J-P-H-ST-TH1 (straight through-hole) | DRC 0/0, fab-ready |
| B | 25× SMA | Amphenol RF 901-143-6RFX | DRC 0/0, fab-ready |
| C | 25× U.FL | Hirose U.FL-R-SMT-1(10) | DRC 0/0, fab-ready |
| D | 25× SMP | Amphenol RF SMP-MSLD-PCS-20 (vertical SMT) | DRC 0/0, fab-ready |

## Iron rules

1. **Single source of truth: [`pinout.py`](pinout.py).** The QSE-040 (J5) pin→net
   map was extracted from the upstream schematic **netlist**
   (`kicad-cli sch export netlist`), *not* hand-transcribed. The generator imports
   it; **never hand-place a channel.** If the upstream board changes, re-export and
   regenerate — do not edit boards directly.
2. **Boards are generated, never hand-placed** (see pipeline below). Placement is always
   generated; so is routing — **Board A (MCX) is FreeRouting-autorouted**, boards B/C/D use
   the bespoke deterministic router.
3. **Footprints are local and datasheet-verified** ([`lib/ets-breakout.pretty/`](lib/ets-breakout.pretty/)).
   MCX is the straight **through-hole** jack `Samtec_MCX-J-P-H-ST-TH1`, checked against the
   Samtec drawing (mcx-j-p-x-st-th1-mkt) in [`docs/datasheets/`](docs/datasheets/) — pad 1
   signal drill Ø1.10 mm centered + 4× ground drill Ø1.40 mm on a 5.08 mm square; QSE-040
   from the upstream repo; SMA + U.FL from the KiCad library; SMP (`SMP-MSLD-PCS-20`,
   Amphenol RF) is the SnapMagic land pattern, pad `G` renamed to `2` to match the
   `1`=sig/`2`=gnd convention.
4. **Upstream is reference-only.** [`reference/ETS-96-channel-IV-pulse-mux/`](reference/)
   is a read-only snapshot (de-gitted); see [`reference/UPSTREAM.md`](reference/UPSTREAM.md).
   Do not build from it.

## Toolchain

- **KiCad 10**, CLI/python at `C:\Program Files\KiCad\10.0\bin\` (not on PATH —
  call by full path). KiCad's bundled `python.exe` has `pcbnew`.
- Python 3.12.

## Build pipeline (KiCad bundled python)

All `tools/*.py` run under the KiCad bundled interpreter
(`"C:/Program Files/KiCad/10.0/bin/python.exe"`).

```
# Board A (MCX, through-hole) — FreeRouting autoroute, ZERO signal vias:
tools/gen_board.py mcx                 # placement + nets + outline + holes (balanced ~12/13; SPLIT="planar" = old 8/16)
tools/finalize_board.py <pcb> setup    # 4-layer stackup + GND zones (NO routes yet)
tools/export_dsn.py <pcb> B.Cu         # write Specctra .dsn for the router
#   -> FreeRouting v2.2.4 (java) autoroute -> .ses   (see docs/FREEROUTING or the amplifier recipe)
tools/import_ses.py <pcb>              # pull the routed B.Cu tracks back in
tools/finalize_board.py <pcb> stitch   # GND stitching vias
tools/fill_zones.py <pcb>              # fill GND pours (SEPARATE pass)
tools/tie_islands.py <pcb>             # island-tie vias
kicad-cli pcb drc <pcb>                # verify (0 violations, 0 unconnected)

# Boards B/C/D (SMA/U.FL/SMP) — deterministic router, single finalize pass:
tools/gen_board.py [sma|ufl|smp]
tools/finalize_board.py <pcb>          # 4-layer stackup + 50 ohm routes + GND zones + stitching (one pass)
tools/fill_zones.py <pcb>              # fill GND pours (SEPARATE pass)
kicad-cli pcb drc <pcb>

kicad-cli pcb export gerbers|drill|pos ... ; tools/make_bom.py <pcb> <csv>   # fab outputs (both flows)
```

pcbnew gotchas (shared with the SMP-feedthrough project):
- Headless `ZONE_FILLER.Fill()` **segfaults** on the in-memory board → `fill_zones.py`
  runs as a separate pass on the saved file.
- **Board A routing = balanced ~12/13 planar, autorouted (engineer-reviewed).** The 25 jacks
  split 12 west / 13 east and are **ordered by their QSE pin** so every native channel escapes
  as a **straight line**: west = K8-K15 (native) + K16,K17 (wrap top corner) + K6,K7 (wrap
  bottom corner); east = K18-K23, IV, K0-K5. The 4 spilled channels **wrap around the connector
  ends on B.Cu** (2 per corner) — still a single-layer B.Cu fan with **zero connector crossings
  and zero signal vias** (the through-hole MCX signal pin is plated through every layer, so the
  B.Cu escape lands on it with no face-change via). Balancing shrank the board 75×157 → **75.0 ×
  125.2 mm** (−32 mm). FreeRouting (`export_dsn.py` → FreeRouting v2.2.4 → `import_ses.py`) does
  the autoroute. The old lopsided 8/16 fan is retained as the `gen_board` `SPLIT="planar"`
  option; `SPLIT="balanced"` is the default for Board A.
- **Boards B/C/D routing** = the deterministic router: escape past the QSE pads → one
  straight diagonal → straight into the signal pad between grounds (monotonic fan ⇒ planar),
  with a 12/12 channel→flange split (computed from pad geometry to hit the 4-net crossing
  floor, routed bottom), the documented `SPLIT="balanced"` flag in `gen_board.py`.
- **Flat (vertical) jacks** (U.FL, MCX, SMP) are rotated by `_edge` so the
  signal pad faces the QSE (the side the trace approaches from). The signal pad's native
  direction varies per part (U.FL: -X edge; SMP-MSLD: +Y tab; MCX: centred), so the
  rotation is derived from the actual pad geometry, not hard-coded.

## Repo layout

```
pinout.py                      SINGLE SOURCE OF TRUTH (QSE-040 J5 pin->net + breakout list)
tests/test_pinout.py           sanity + self-consistency checks (run: python tests/test_pinout.py)
tools/  gen_board.py  finalize_board.py(setup/stitch)  export_dsn.py  import_ses.py  fill_zones.py  tie_islands.py  make_bom.py  gen_schematic.py
lib/ets-breakout.pretty/       5 datasheet-verified footprints (QSE-040, MCX, SMA, U.FL, SMP)
lib/ets-breakout.kicad_sym     5 schematic symbols (reference-only; project builds from pinout.py)
models/                        3D STEP models + README (QSE/U.FL/SMP present; SMA + through-hole MCX = gaps)
docs/datasheets/               5 part datasheets (Samtec QSE + MCX, Amphenol SMA + SMP, Hirose U.FL)
docs/BOM.md  docs/BOM.csv       consolidated master BOM + CAD-asset matrix (per-board BOMs in boards/*/fab/)
docs/schematic/                REFERENCE schematic for human review (generated from pinout.py; netlist-verified)
docs/session-report.md         development history / decisions / rationale
boards/board-{A-mcx,B-sma,C-ufl,D-smp}/   .kicad_pcb/.kicad_pro + routed-top.pdf + fab/ + *-fab.zip
order/                         purchase handover package: JLCPCB upload zip + DigiKey BOM CSV + wizard walkthrough
reference/                     read-only upstream snapshot (de-gitted) + UPSTREAM.md
```

## Status / before fab

- All four boards: **0 DRC violations, 0 unconnected.** Fab packages are the
  `boards/board-*/*-fab.zip` (gerbers + Excellon drill + placement CSV + BOM CSV).
  Board A has **0 signal vias** (GND stitching + island-tie vias only; all 25 nets on B.Cu),
  and after the balanced ~12/13 re-layout is **75.0 × 125.2 mm**.
- Trace width **0.325 mm ≈ 50 Ω** (unchanged) single-ended microstrip on the JLCPCB
  **JLC04161H-7628** 4-layer 1.6 mm stackup (0.2104 mm 7628 prepreg to the adjacent inner GND
  plane, Dk 4.4), GND pour clearance 0.30 mm — **order as controlled impedance** (JLC's
  impedance-control option on that stackup) so JLC re-tunes the etched width. **Fab is JLCPCB
  only.** Full derivation (JLCPCB calculator RS_50 = 0.3244 mm + KiCad TransLine / IPC-2141
  microstrip, every input stated; 0.325 mm = JLC's own published 50 Ω single-ended width for
  JLC04161H-7628) is in [`docs/impedance.md`](docs/impedance.md).
- **Assembly:** default is **fab-only + hand-solder** (exact Samtec parts from DigiKey). An
  optional **JLCPCB assembled build is viable** as a mixed SMT(QSE)+THT(MCX) job via LCSC:
  QSE-040 = **C3652741** (exact Samtec, plain -A), MCX = **C5137197** (BAT Wireless `BWMCX-KE`
  generic 50 Ω THT jack; alt `C49118404`). Both JLC-library *Extended*; the 25 THT jacks need
  JLC's through-hole assembly add-on. **Gate:** the `BWMCX-KE` land pattern (centre signal + 4
  grounds, 5.08 mm, drills 1.10/1.40) is not dimensionally verified — confirm against its drawing
  before an assembled order, else fall back to the Samtec hand-solder part. `make_bom.py` emits
  the **LCSC column** (MCX C5137197, QSE C3652741; Cinch IV cable adapter = n/a).
- **U.FL is low-voltage** (~60 V) vs bias up to ~70 V — use U.FL only on un-biased / low-V channels.
- Open (housekeeping, non-blocking): impedance is nominal until confirmed against the fab
  stackup. Boards remain generated directly from `pinout.py` (no netlist-driven flow), but a
  **reference schematic** now exists for human review — `docs/schematic/` (`.kicad_sch` + PDF),
  generated by `tools/gen_schematic.py` from the same `pinout.py`; ERC 0 errors and its
  exported netlist is verified identical to the pin map (26 warning-level "lib nickname"
  notices are inherent to a standalone sheet with embedded symbols — ignore).
- **MCX MPN confirmed + purchase-ready (2026-07-15):** Board A is now **through-hole** —
  `MCX-J-P-H-ST-TH1` verified orderable (DigiKey SAM8944-ND; drawing mcx-j-p-x-st-th1-mkt in
  `docs/datasheets/`). Through-hole is deliberate: the plated signal pin lets the QSE's B.Cu
  channel escape land on it with **no face-change via**. Right-angle THT `MCX-J-P-H-RA-TH1`
  (SAM10607-ND) is a valid mechanical alternative (cables exit sideways; needs a re-layout);
  do **not** cross to the 75-Ω `MCX7-J-P-H-ST-TH1` (SAM8945-ND) or the smaller
  `MMCX-J-P-H-ST-TH1` (SAM10617-ND). QSE socket = SAM8124-ND (plain suffix — never sub
  `-RT1`, it needs retention holes the board lacks). Board A is the chosen final variant;
  full purchase order (parts + PCB fab) in [`docs/BOM.md`](docs/BOM.md) §Purchase order.
- CAD assets (datasheet/footprint/symbol/3D) are collected per part — see
  [`docs/BOM.md`](docs/BOM.md). 3D STEP models for QSE-040, U.FL, SMP are local in
  `models/`; **SMA and the through-hole MCX have no 3D model yet** (SMA vendor-gated; MCX
  TH1 model not sourced). Symbols are reference-only.
