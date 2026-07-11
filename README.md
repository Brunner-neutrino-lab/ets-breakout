# ETS per-channel SiPM breakout boards

Passive break-out boards that replace the (broken) **`iv-pulse-mux`** board in the
Brunner-lab **ETS-96-channel-IV-pulse-mux** system. Instead of relay-multiplexing 24
channels onto one shared sense line, each breakout board brings **every channel out to
its own coaxial jack** so channels can be biased/measured individually with external
instruments.

> Note: the public GitHub repo `IV-MUX-public` is a *different, older* board (15
> ch/board relay mux). The authoritative source is the read-only upstream snapshot
> under [`reference/ETS-96-channel-IV-pulse-mux/`](reference/) (`iv-pulse-mux`,
> connector **J5**) — see [`reference/UPSTREAM.md`](reference/UPSTREAM.md).

## What each board does

- Mates the detector-side connector **`QSE-040-01-L-D-A`** (J5) — same socket the
  `iv-pulse-mux` board used, mating the existing QTE-040 header upstream. **J5 sits on
  the back face (B.Cu)**, opposite the jacks: the detector plugs into the back, cables
  come off the front.
- Fans **25 signals → 25 coax jacks**: `SIPM_K0…K23` (24) + `IV` (1).
  `IV` is bussed on QSE pins 40 & 42 → one jack. `THERM4/THERM5` are **not** broken out.
- `GNDA` (52 signal-row pins + 8 G-pads) forms the ground/shield; a **guard ring** per
  channel tied to `GNDA`. No bias-tee / ESD diode / DC block.

### Variants
| Board | Jacks |
|-------|-------|
| **A** | 25 × MCX (straight, vertical SMT) |
| **B** | 25 × SMA |
| **C** | 25 × U.FL |
| **D** | 25 × SMP (vertical SMT, SMP-MSLD-PCS-20) |

One board services one QSE-040 (25 ch). The full 96-channel system uses **4 boards**;
all four connectors share the identical J5 pinout, so a single layout works in every
position.

## Design decisions (2026-06-16)

| Aspect | Decision |
|--------|----------|
| Mechanical | **Free-form standalone** — only the QSE-040 must mate; fresh outline + mounting, no size constraint |
| J5 mounting face | **Back (B.Cu)** — detector mates on the back, all coax jacks on the front |
| Jack mounting | **Edge / right-angle** — jacks at board edges, cables exit sideways |
| Signal integrity | **Controlled 50 Ω, 4-layer** (L1 sig / L2 GND / L3 GND / L4 sig) |
| Guard | Guard ring per channel → `GNDA` |

## Pinout = single source of truth

[`pinout.py`](pinout.py) holds the authoritative QSE-040 (J5) pin→net map, derived from
the upstream schematic netlist (`kicad-cli sch export netlist`), **not** hand-transcribed
from a screenshot. The generator imports it; never hand-place a channel. Re-export and
regenerate if the upstream board changes.

```
python pinout.py             # dump signal -> QSE pin map
python tests/test_pinout.py  # sanity + self-consistency checks
```

## Build pipeline

```
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_board.py   [mcx|sma|ufl|smp]  # placement + nets + outline + holes
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/finalize_board.py <pcb>           # stackup + 50 ohm routes + GND zones + stitching
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/fill_zones.py     <pcb>           # fill pours (separate pass)
kicad-cli pcb drc <pcb>                                                              # verify (all four: 0 violations)
kicad-cli pcb export gerbers|drill|pos ... ; tools/make_bom.py <pcb> <csv>           # fab outputs
```

Routing = escape past the QSE pads → one straight diagonal to the jack → straight into
the signal pad between grounds (monotonic fan ⇒ planar). The 12/12 split is computed from
pad geometry to minimise crossings (4, on the bottom layer). Vertical SMD jacks (U.FL,
straight MCX, SMP) are auto-rotated so their signal pad faces the QSE, where the trace
approaches.

## Status

**All four boards route DRC-clean (0 violations, 0 unconnected)** at the 50 Ω trace
width on PCBWay's default 4-layer 1.6 mm stackup.

| Board | Connector | Size | Fab package |
|-------|-----------|------|-------------|
| A | MCX straight (MCX-J-P-X-ST-SM1) | 76 × 139 mm | `boards/board-A-mcx/board-A-mcx-fab.zip` |
| B | SMA (901-143-6RFX) | 75 × 149 mm | `boards/board-B-sma/board-B-sma-fab.zip` |
| C | U.FL (U.FL-R-SMT-1) | 70 × 99 mm | `boards/board-C-ufl/board-C-ufl-fab.zip` |
| D | SMP (SMP-MSLD-PCS-20) | 75 × 120 mm | `boards/board-D-smp/board-D-smp-fab.zip` |

Each fab zip = gerbers (4 copper + mask/silk/edge) + Excellon drill + position CSV + BOM CSV.

**Impedance:** channel traces are **0.34 mm** wide ≈ 50 Ω microstrip on the PCBWay default
4-layer stack (~0.21 mm L1→L2 prepreg, FR4 Dk ≈ 4.3), GND pour held back 0.30 mm to limit
coplanar coupling. `EDGE_GAP` is set so the fan diagonals stay shallow enough that the
0.34 mm traces clear at the dense escape. **Order as controlled impedance** so PCBWay
fine-tunes the width to their exact measured stackup.

**Footprints — all datasheet-verified:** MCX `Samtec_MCX-J-P-X-ST-SM1` (straight, vertical
SMT jack) matches the Samtec drawing rev C (`docs/datasheets/`): center signal Ø1.65 + 4×
square ground 2.10 mm on a 6.54 mm square. SMA and U.FL from the KiCad library; QSE-040
from the ETS repo; MCX carried over from the sibling SMP-feedthrough project; SMP
`SMP_Amphenol_SMP-MSLD-PCS-20` (Amphenol RF, vertical SMT) is the SnapMagic land pattern
(pad `G` renamed to `2`), signal on an external tab.

**3D models:** QSE-040, MCX, and SMP have local STEP models in [`models/`](models/); U.FL
uses KiCad's bundled model. SMA has no 3D model (skipped). Models are visual only — fab is
unaffected.

**Before committing to fab:**
- Boards are built directly from `pinout.py` (no netlist-driven flow). A **reference
  schematic for human review** is in [`docs/schematic/`](docs/schematic/) (PDF + `.kicad_sch`),
  generated from the same `pinout.py` by `tools/gen_schematic.py` — its exported netlist is
  verified identical to the pin map.
- ~~Confirm the straight-MCX orderable MPN~~ **Confirmed 2026-07-11:** `MCX-J-P-H-ST-SM1`
  (DigiKey SAM10608-ND). Purchase package in [`order/`](order/).
