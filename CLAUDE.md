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
position).

**J5 mounts on the BACK face (B.Cu); all coax jacks are on the FRONT (F.Cu)** — the
detector plugs into the back, cables come off the front. J5 is flipped in
`gen_board.py`; the router (`finalize_board.py`) reads which face J5 is on and routes
escapes on that layer (HOME), hopping to the other signal layer (OTHER) only for the
crossing fans.

| Board | Jacks | Part | Status |
|-------|-------|------|--------|
| A | 25× MCX | Samtec MCX-J-P-X-ST-SM1 (straight SMT) | DRC 0/0, fab-ready |
| B | 25× SMA | Amphenol RF 901-143-6RFX | DRC 0/0, fab-ready |
| C | 25× U.FL | Hirose U.FL-R-SMT-1(10) | DRC 0/0, fab-ready |
| D | 25× SMP | Amphenol RF SMP-MSLD-PCS-20 (vertical SMT) | DRC 0/0, fab-ready |

## Iron rules

1. **Single source of truth: [`pinout.py`](pinout.py).** The QSE-040 (J5) pin→net
   map was extracted from the upstream schematic **netlist**
   (`kicad-cli sch export netlist`), *not* hand-transcribed. The generator imports
   it; **never hand-place a channel.** If the upstream board changes, re-export and
   regenerate — do not edit boards directly.
2. **Boards are generated, never hand-placed** (see pipeline below).
3. **Footprints are local and datasheet-verified** ([`lib/ets-breakout.pretty/`](lib/ets-breakout.pretty/)).
   MCX is the straight SMT jack `MCX-J-P-X-ST-SM1`, checked against the Samtec drawing
   rev C in [`docs/datasheets/`](docs/datasheets/), carried over from the sibling
   SMP-feedthrough project; QSE-040 from the upstream repo; SMA + U.FL from the KiCad
   library; SMP (`SMP-MSLD-PCS-20`, Amphenol RF) is the SnapMagic land pattern, pad `G`
   renamed to `2` to match the `1`=sig/`2`=gnd convention.
4. **Upstream is reference-only.** [`reference/ETS-96-channel-IV-pulse-mux/`](reference/)
   is a read-only snapshot (de-gitted); see [`reference/UPSTREAM.md`](reference/UPSTREAM.md).
   Do not build from it.

## Toolchain

- **KiCad 10**, CLI/python at `C:\Program Files\KiCad\10.0\bin\` (not on PATH —
  call by full path). KiCad's bundled `python.exe` has `pcbnew`.
- Python 3.12.

## Build pipeline (KiCad bundled python)

```
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_board.py      [mcx|sma|ufl|smp]  # placement + nets + outline + holes
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/finalize_board.py <pcb>              # 4-layer stackup + 50 ohm routes + GND zones + stitching
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/fill_zones.py     <pcb>              # fill GND pours (SEPARATE pass)
kicad-cli pcb drc <pcb>                                                                 # verify (target 0 violations)
kicad-cli pcb export gerbers|drill|pos ... ; tools/make_bom.py <pcb> <csv>              # fab outputs
```

pcbnew gotchas (shared with the SMP-feedthrough project):
- Headless `ZONE_FILLER.Fill()` **segfaults** on the in-memory board → `fill_zones.py`
  runs as a separate pass on the saved file.
- Routing primitive = escape past the QSE pads → one straight diagonal → straight into
  the signal pad between grounds (monotonic fan ⇒ planar). The 12/12 channel→flange
  split is computed from pad geometry to hit the 4-net crossing floor (routed bottom).
- **Flat (vertical) jacks** (U.FL, straight MCX, SMP) are rotated by `_edge` so the
  signal pad faces the QSE (the side the trace approaches from). The signal pad's native
  direction varies per part (U.FL: -X edge; SMP-MSLD: +Y tab; MCX: centred), so the
  rotation is derived from the actual pad geometry, not hard-coded.

## Repo layout

```
pinout.py                      SINGLE SOURCE OF TRUTH (QSE-040 J5 pin->net + breakout list)
tests/test_pinout.py           sanity + self-consistency checks (run: python tests/test_pinout.py)
tools/  gen_board.py  finalize_board.py  fill_zones.py  make_bom.py
lib/ets-breakout.pretty/       5 datasheet-verified footprints (QSE-040, MCX, SMA, U.FL, SMP)
lib/ets-breakout.kicad_sym     5 schematic symbols (reference-only; project builds from pinout.py)
models/                        3D STEP models + README (QSE/MCX/U.FL/SMP present; SMA = vendor-gated gap)
docs/datasheets/               5 part datasheets (Samtec QSE + MCX, Amphenol SMA + SMP, Hirose U.FL)
docs/BOM.md  docs/BOM.csv       consolidated master BOM + CAD-asset matrix (per-board BOMs in boards/*/fab/)
docs/session-report.md         development history / decisions / rationale
boards/board-{A-mcx,B-sma,C-ufl,D-smp}/   .kicad_pcb/.kicad_pro + routed-top.pdf + fab/ + *-fab.zip
order/                         purchase handover package: JLCPCB upload zip + DigiKey BOM CSV + wizard walkthrough
reference/                     read-only upstream snapshot (de-gitted) + UPSTREAM.md
```

## Status / before fab

- All four boards: **0 DRC violations, 0 unconnected.** Fab packages are the
  `boards/board-*/*-fab.zip` (gerbers + Excellon drill + placement CSV + BOM CSV).
- Trace width **0.34 mm ≈ 50 Ω** microstrip on the PCBWay default 4-layer stackup —
  **order as controlled impedance** so the fab tunes to their exact stackup.
- **U.FL is low-voltage** (~60 V) vs bias up to ~70 V — use U.FL only on un-biased / low-V channels.
- Open (housekeeping, non-blocking): no schematic/netlist (boards built directly
  from `pinout.py`); impedance is nominal until confirmed against the fab stackup.
- **MCX MPN confirmed + purchase-ready (2026-07-11):** `MCX-J-P-H-ST-SM1` verified orderable
  (DigiKey SAM10608-ND; SM1 rev C drawing in `docs/datasheets/`); QSE socket = SAM8124-ND
  (plain suffix — never sub `-RT1`, it needs retention holes the board lacks). Board A is the
  chosen final variant; full purchase order (parts + PCB fab) in
  [`docs/BOM.md`](docs/BOM.md) §Purchase order.
- CAD assets (datasheet/footprint/symbol/3D) are collected per part — see
  [`docs/BOM.md`](docs/BOM.md). 3D STEP models for QSE-040, MCX, U.FL, SMP are local in
  `models/`; **SMA 3D is the only gap** (vendor-gated). Symbols are reference-only.
