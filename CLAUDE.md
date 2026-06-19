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

| Board | Jacks | Part | Status |
|-------|-------|------|--------|
| A | 25× MCX | Samtec MCX-J-P-H-RA-TH1 | DRC 0/0, fab-ready |
| B | 25× SMA | Amphenol RF 901-143-6RFX | DRC 0/0, fab-ready |
| C | 25× U.FL | Hirose U.FL-R-SMT-1(10) | DRC 0/0, fab-ready |

## Iron rules

1. **Single source of truth: [`pinout.py`](pinout.py).** The QSE-040 (J5) pin→net
   map was extracted from the upstream schematic **netlist**
   (`kicad-cli sch export netlist`), *not* hand-transcribed. The generator imports
   it; **never hand-place a channel.** If the upstream board changes, re-export and
   regenerate — do not edit boards directly.
2. **Boards are generated, never hand-placed** (see pipeline below).
3. **Footprints are local and datasheet-verified** ([`lib/ets-breakout.pretty/`](lib/ets-breakout.pretty/)).
   MCX checked against the Samtec drawing rev H in [`docs/datasheets/`](docs/datasheets/);
   QSE-040 from the upstream repo; SMA + U.FL from the KiCad library.
4. **Upstream is reference-only.** [`reference/ETS-96-channel-IV-pulse-mux/`](reference/)
   is a read-only snapshot (de-gitted); see [`reference/UPSTREAM.md`](reference/UPSTREAM.md).
   Do not build from it.

## Toolchain

- **KiCad 10**, CLI/python at `C:\Program Files\KiCad\10.0\bin\` (not on PATH —
  call by full path). KiCad's bundled `python.exe` has `pcbnew`.
- Python 3.12.

## Build pipeline (KiCad bundled python)

```
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_board.py      [mcx|sma|ufl]  # placement + nets + outline + holes
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/finalize_board.py <pcb>          # 4-layer stackup + 50 ohm routes + GND zones + stitching
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/fill_zones.py     <pcb>          # fill GND pours (SEPARATE pass)
kicad-cli pcb drc <pcb>                                                             # verify (target 0 violations)
kicad-cli pcb export gerbers|drill|pos ... ; tools/make_bom.py <pcb> <csv>          # fab outputs
```

pcbnew gotchas (shared with the SMP-feedthrough project):
- Headless `ZONE_FILLER.Fill()` **segfaults** on the in-memory board → `fill_zones.py`
  runs as a separate pass on the saved file.
- Routing primitive = escape past the QSE pads → one straight diagonal → straight into
  the signal pad between grounds (monotonic fan ⇒ planar). The 12/12 channel→flange
  split is computed from pad geometry to hit the 4-net crossing floor (routed bottom).

## Repo layout

```
pinout.py                      SINGLE SOURCE OF TRUTH (QSE-040 J5 pin->net + breakout list)
tests/test_pinout.py           sanity + self-consistency checks (run: python tests/test_pinout.py)
tools/  gen_board.py  finalize_board.py  fill_zones.py  make_bom.py
lib/ets-breakout.pretty/       4 datasheet-verified footprints (QSE-040, MCX, SMA, U.FL)
docs/datasheets/               Samtec MCX drawing rev H
docs/session-report.md         development history / decisions / rationale
boards/board-{A-mcx,B-sma,C-ufl}/   .kicad_pcb/.kicad_pro + routed-top.pdf + fab/ + *-fab.zip
reference/                     read-only upstream snapshot (de-gitted) + UPSTREAM.md
```

## Status / before fab

- All three boards: **0 DRC violations, 0 unconnected.** Fab packages are the
  `boards/board-*/*-fab.zip` (gerbers + Excellon drill + placement CSV + BOM CSV).
- Trace width **0.34 mm ≈ 50 Ω** microstrip on the PCBWay default 4-layer stackup —
  **order as controlled impedance** so the fab tunes to their exact stackup.
- **U.FL is low-voltage** (~60 V) vs bias up to ~70 V — use U.FL only on un-biased / low-V channels.
- Open (housekeeping, non-blocking): no schematic/netlist (boards built directly
  from `pinout.py`); MCX signal pin assumed centered in the ground square; impedance
  is nominal until confirmed against the fab stackup.
