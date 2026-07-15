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
| **A** | 25 × MCX (straight, vertical through-hole) |
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

All `tools/*.py` run under KiCad's bundled interpreter
(`"C:/Program Files/KiCad/10.0/bin/python.exe"`).

```
# Board A (MCX, through-hole) — FreeRouting autoroute, ZERO signal vias:
tools/gen_board.py mcx                 # placement + nets + outline + holes (8/16 planar split)
tools/finalize_board.py <pcb> setup    # 4-layer stackup + GND zones (no routes yet)
tools/export_dsn.py <pcb> B.Cu         # write Specctra .dsn for the router
#   -> FreeRouting v2.2.4 (java) autoroute -> .ses
tools/import_ses.py <pcb>              # pull the routed B.Cu tracks back in
tools/finalize_board.py <pcb> stitch   # GND stitching vias
tools/fill_zones.py <pcb>              # fill GND pours (separate pass)
tools/tie_islands.py <pcb>             # island-tie vias
kicad-cli pcb drc <pcb>                # verify (0 violations, 0 unconnected)

# Boards B/C/D (SMA/U.FL/SMP) — deterministic router, single finalize pass:
tools/gen_board.py [sma|ufl|smp]
tools/finalize_board.py <pcb>          # stackup + 50 ohm routes + GND zones + stitching (one pass)
tools/fill_zones.py <pcb>
kicad-cli pcb drc <pcb>

kicad-cli pcb export gerbers|drill|pos ... ; tools/make_bom.py <pcb> <csv>   # fab outputs
```

**Board A** routes as an **8/16 planar fan on B.Cu**: the QSE's two pin rows split the 24
channels 8 (west) / 16 (east) + IV, so each jack sits on the edge of its own QSE pin column
— a monotonic single-layer fan with **zero connector crossings and zero signal vias** (the
through-hole MCX signal pin is plated through every layer, so the B.Cu escape lands on it
with no face-change via). FreeRouting does the autoroute; only GND stitching + island-tie
vias remain. **Boards B/C/D** still use the deterministic router — escape past the QSE pads →
one straight diagonal to the jack → straight into the signal pad between grounds — with a
12/12 split (retained as the `SPLIT="balanced"` flag) that crosses 4 channels on the bottom
layer. Vertical jacks (U.FL, MCX, SMP) are auto-rotated so their signal pad faces the QSE.

## Status

**All four boards route DRC-clean (0 violations, 0 unconnected)** at the 50 Ω trace
width on the JLCPCB **JLC04161H-7628** 4-layer 1.6 mm stackup. Board A carries **0 signal
vias** (GND stitching + island-tie vias only; all 25 nets on B.Cu).

| Board | Connector | Size | Fab package |
|-------|-----------|------|-------------|
| A | MCX straight, through-hole (MCX-J-P-H-ST-TH1) | 75 × 157 mm | `boards/board-A-mcx/board-A-mcx-fab.zip` |
| B | SMA (901-143-6RFX) | 75 × 149 mm | `boards/board-B-sma/board-B-sma-fab.zip` |
| C | U.FL (U.FL-R-SMT-1) | 70 × 99 mm | `boards/board-C-ufl/board-C-ufl-fab.zip` |
| D | SMP (SMP-MSLD-PCS-20) | 75 × 120 mm | `boards/board-D-smp/board-D-smp-fab.zip` |

Each fab zip = gerbers (4 copper + mask/silk/edge) + Excellon drill + position CSV + BOM CSV.

**Impedance:** channel traces are **0.325 mm** wide ≈ 50 Ω single-ended microstrip on the
JLCPCB **JLC04161H-7628** 4-layer 1.6 mm stack (0.2104 mm 7628 prepreg to the adjacent inner
GND plane, Dk ≈ 4.4), GND pour held back 0.30 mm to limit coplanar coupling. **Order as
controlled impedance** (JLC's impedance-control option on that stackup) so JLC re-tunes the
etched width to their exact stackup.

**Footprints — all datasheet-verified:** MCX `Samtec_MCX-J-P-H-ST-TH1` (straight, vertical
**through-hole** jack) matches the Samtec drawing (`docs/datasheets/`, mcx-j-p-x-st-th1-mkt):
pad 1 signal drill Ø1.10 mm centered + 4× ground drill Ø1.40 mm on a 5.08 mm square. SMA and
U.FL from the KiCad library; QSE-040 from the ETS repo; SMP `SMP_Amphenol_SMP-MSLD-PCS-20`
(Amphenol RF, vertical SMT) is the SnapMagic land pattern (pad `G` renamed to `2`), signal on
an external tab.

**3D models:** QSE-040 and SMP have local STEP models in [`models/`](models/); U.FL uses
KiCad's bundled model. SMA and the through-hole MCX have no 3D model yet (gap). Models are
visual only — fab is unaffected.

**Before committing to fab:**
- Boards are built directly from `pinout.py` (no netlist-driven flow). A **reference
  schematic for human review** is in [`docs/schematic/`](docs/schematic/) (PDF + `.kicad_sch`),
  generated from the same `pinout.py` by `tools/gen_schematic.py` — its exported netlist is
  verified identical to the pin map.
- ~~Confirm the straight-MCX orderable MPN~~ **Confirmed 2026-07-15:** Board A is now
  **through-hole** — `MCX-J-P-H-ST-TH1` (DigiKey SAM8944-ND). Purchase package in [`order/`](order/).
