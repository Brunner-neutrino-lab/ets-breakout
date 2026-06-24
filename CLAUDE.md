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
| D | 25× SMP | Amphenol RF SMP-MSSB-PCS (male, vertical SMT) | DRC 0/0, fab-ready |

## Iron rules

1. **Single source of truth: [`pinout.py`](pinout.py).** The QSE-040 (J5) pin→net
   map was extracted from the upstream schematic **netlist**
   (`kicad-cli sch export netlist`), *not* hand-transcribed. The generator imports
   it; **never hand-place a channel.** If the upstream board changes, re-export and
   regenerate — do not edit boards directly.
2. **Boards are generated, never hand-placed** (see pipeline below).
3. **Footprints are local and datasheet-verified** ([`lib/ets-breakout.pretty/`](lib/ets-breakout.pretty/)).
   MCX is the straight SMT jack `MCX-J-P-X-ST-SM1`, checked against the Samtec drawing
   rev C in [`docs/datasheets/`](docs/datasheets/); QSE-040 from the upstream repo; SMA +
   U.FL from the KiCad library; MCX + SMP (`SMP-MSSB-PCS`, Amphenol outline rev D) carried
   over from the sibling SMP-feedthrough project.
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
- **SMP exception:** its center signal pad is enclosed by the ground frame on all four
  sides, so the channel can't enter on F.Cu. `finalize_board.py` detects SMP jacks and
  runs the approach on B.Cu under the frame, popping up into the pad with a center
  via-in-pad (recommend plugged/capped vias or hand-solder at assembly).

## Repo layout

```
pinout.py                      SINGLE SOURCE OF TRUTH (QSE-040 J5 pin->net + breakout list)
tests/test_pinout.py           sanity + self-consistency checks (run: python tests/test_pinout.py)
tools/  gen_board.py  finalize_board.py  fill_zones.py  make_bom.py
lib/ets-breakout.pretty/       5 datasheet-verified footprints (QSE-040, MCX, SMA, U.FL, SMP)
models/                        3D STEP models + README (QSE/SMP present, U.FL bundled; MCX/SMA = drop-in TODO)
docs/datasheets/               Samtec MCX drawing rev H
docs/session-report.md         development history / decisions / rationale
boards/board-{A-mcx,B-sma,C-ufl,D-smp}/   .kicad_pcb/.kicad_pro + routed-top.pdf + fab/ + *-fab.zip
reference/                     read-only upstream snapshot (de-gitted) + UPSTREAM.md
```

## Status / before fab

- All four boards: **0 DRC violations, 0 unconnected.** Fab packages are the
  `boards/board-*/*-fab.zip` (gerbers + Excellon drill + placement CSV + BOM CSV).
- Trace width **0.34 mm ≈ 50 Ω** microstrip on the PCBWay default 4-layer stackup —
  **order as controlled impedance** so the fab tunes to their exact stackup.
- **U.FL is low-voltage** (~60 V) vs bias up to ~70 V — use U.FL only on un-biased / low-V channels.
- Open (housekeeping, non-blocking): no schematic/netlist (boards built directly
  from `pinout.py`); impedance is nominal until confirmed against the fab stackup;
  **SMP uses center via-in-pad** (spec plugged/capped vias, or hand-solder, so the joint
  doesn't wick); straight-MCX MPN (`MCX-J-P-H-ST-SM1`) is inferred from the family —
  confirm the exact orderable jack PN.
- 3D models: QSE-040, MCX (straight), SMP attached locally; U.FL via KiCad's bundled lib.
  SMA has no 3D model (intentionally skipped). See [`models/README.md`](models/README.md).
