# BOM & CAD asset collection — ETS per-channel breakout boards

Consolidated bill of materials across all four board variants, plus the collected CAD
assets (datasheet, footprint, schematic symbol, 3D model) for every part. Machine-readable
master BOM: [`BOM.csv`](BOM.csv). Per-board fab BOMs live in each
`boards/board-*/fab/board-*-bom.csv`.

All four boards share the **same QSE-040 socket and mechanical**; they differ only in the
coax jack (one jack type per board). Each board = **1× QSE-040 + 25× coax jack + 4× M3 hole**.

## Master BOM

| Item | Manufacturer | MPN | Digi-Key | Qty/board | Board(s) | Notes |
|------|--------------|-----|----------|:---------:|:--------:|-------|
| J5 socket | Samtec | QSE-040-01-L-D-A | SAM8124-ND | 1 | A B C D | detector-side socket; mounts on the back face. Plain (tray) suffix — do **not** sub `-RT1` (needs retention holes we don't have) |
| MCX jack | Samtec | MCX-J-P-H-ST-TH1 | SAM8944-ND | 25 | A | straight (vertical) **through-hole**, 50 Ω, 6 GHz — **confirmed orderable** (Active, verified 2026-07-15). THT signal pin plated through all layers ⇒ B.Cu channel escape lands on it with no face-change via (zero signal vias) |
| SMA jack | Amphenol RF | 901-143-6RFX | ARFX1232-ND | 25 | B | right-angle through-hole, 50 Ω |
| U.FL jack | Hirose | U.FL-R-SMT-1(10) | — | 25 | C | SMT, 50 Ω — **≤60 V** working voltage (low-bias channels only) |
| SMP jack | Amphenol RF | SMP-MSLD-PCS-20 | — | 25 | D | vertical SMT, 50 Ω, 4.08 mm max height |
| Mounting hole | — | — | — | 4 | A B C D | M3 non-plated (mechanical) |

A full 96-channel system uses 4 boards of one chosen variant → **4× QSE-040 + 100× the
chosen jack** per system.

## Purchase order — final build (Board A / MCX, full 96-channel system)

**Board A is the chosen final variant.** Quantities below build 4 boards + 1 spare PCB, with
**20 % connector spares** (120 jacks, 5 sockets). All part numbers, stock and prices verified
live **2026-07-15**. The ready-to-send handover package (JLCPCB upload zip + DigiKey upload
CSV + wizard walkthrough) is in [`../order/`](../order/README.md).

| # | Item | Order PN | Source | Qty | Unit | Ext | Stock (2026-07-15) |
|---|------|----------|--------|----:|-----:|----:|-------|
| 1 | MCX jack `MCX-J-P-H-ST-TH1` (through-hole) | **SAM8944-ND** | DigiKey | 120 | $4.21 (@100) | $505.20 | ~11,568 (breaks: 1/$6.14 · 50/$5.17 · 100/$4.21) |
| 2 | QSE socket `QSE-040-01-L-D-A` | **SAM8124-ND** | DigiKey | 5 | $7.27 | $36.35 | 2,021 (Mouser `200-QSE04001LDA` cheaper at $5.59 → $27.95, 2,589 stk — aggregator-sourced, reconfirm in cart) |
| 3 | PCB `board-A-mcx-fab.zip` (75.0 × 157.2 mm, 4-layer, controlled impedance) | — | JLCPCB | 5 | — | ~$85–95 ENIG | 118 cm² (under JLC's 650 cm² large-board surcharge); 3–4 day build, +~$28 DHL |
| 4 | SMA-to-TRB (triax) coax adapter, Cinch `3-0347-9` — **for IV out**, 1 per board | **1097-1372-ND** | DigiKey | 4 | $72.41 | $289.64 | 147 |
| 5 | M3 screws/standoffs (mounting) | — | generic | 16+ | — | — | lab stock |

**Total ≈ $950** (DigiKey subtotal $831.19 + JLCPCB ENIG ~$85–95 + ~$28 shipping).

DigiKey Quick-Add (`PN, qty`):

```
SAM8944-ND, 120
SAM8124-ND, 5
1097-1372-ND, 4
```

**PCB ordering notes (JLCPCB tunes width at file review):**

- Order **controlled impedance** with the note: *"50 Ω single-ended microstrip, 0.325 mm
  nominal on outer layers referenced to the adjacent inner GND plane — adjust width to your
  stackup."*
- JLCPCB: 4-layer → Specify Stackup **JLC04161H-7628** (0.2104 mm 7628 prepreg to the
  adjacent inner GND plane, Dk 4.4) → Impedance Control **±10 % (±5 Ω at ≤50 Ω)**. Their
  calculator's 50 Ω width on that stackup is ~0.325 mm — our trace is at nominal.
- **ENIG recommended** over HASL: flatter pads for the 0.8 mm-pitch QSE-040.
- **Mixed assembly:** the THT MCX jacks are hand/selective-soldered (not reflow); the SMD
  QSE-040 is reflowed.
- Jack/socket caveats: MCX `-H-ST-TH1` is the through-hole part — do **not** cross with the
  75 Ω `MCX7-J-P-H-ST-TH1` (SAM8945-ND) or the smaller `MMCX-J-P-H-ST-TH1` (SAM10617-ND). The
  right-angle THT `MCX-J-P-H-RA-TH1` (SAM10607-ND) is a valid mechanical alternative but needs
  a re-layout (cable exits sideways off the edge). QSE must be the **plain** suffix — never
  `-RT1` (retention hardware needs board holes this layout doesn't have).

## CAD asset matrix

Datasheets in [`datasheets/`](datasheets/); footprints in
[`../lib/ets-breakout.pretty/`](../lib/ets-breakout.pretty/); schematic symbols in the
single library [`../lib/ets-breakout.kicad_sym`](../lib/ets-breakout.kicad_sym); 3D STEP
models in [`../models/`](../models/).

| Part | Datasheet | Footprint | Symbol | 3D CAD |
|------|:---------:|:---------:|:------:|:------:|
| QSE-040-01-L-D-A | ✅ `Samtec_QSE.pdf` | ✅ | ✅ | ✅ `QSE-040-01-L-D-A.stp` |
| MCX-J-P-H-ST-TH1 (Board A, THT) | ✅ `mcx-j-p-x-st-th1-mkt.pdf` | ✅ `Samtec_MCX-J-P-H-ST-TH1` | ✅ | ⛔ gap — no vertical THT model yet (the SMD `MCX-J-P-X-ST-SM1.step` no longer matches the through-hole part) |
| 901-143-6RFX (SMA) | ✅ `Amphenol_901-143-6RFX.pdf` | ✅ | ✅ | ⛔ vendor-gated (Amphenol/SnapMagic login) |
| U.FL-R-SMT-1(10) | ✅ `Hirose_U.FL-R-SMT-1.pdf` | ✅ | ✅ | ✅ `U.FL_Hirose_U.FL-R-SMT-1_Vertical.step` |
| SMP-MSLD-PCS-20 | ✅ `Amphenol_SMP-MSLD-PCS.pdf` | ✅ | ✅ | ✅ `SMP-MSLD-PCS-20.stp` |

**3D gaps (two):**
- **Board A MCX THT** (`MCX-J-P-H-ST-TH1`) — no vertical through-hole STEP yet. The bundled
  `MCX-J-P-X-ST-SM1.step` is the old SMD variant and no longer matches Board A's part. Drop a
  vertical THT STEP into `models/` and add a `(model …)` line to `Samtec_MCX-J-P-H-ST-TH1` to
  fill it. Datasheet + footprint + symbol are present.
- **SMA 3D STEP** (Amphenol 901-143-6RFX) — behind a vendor login (Amphenol RF / SnapMagic /
  Ultra Librarian), so it isn't bundled. Everything else (datasheet + footprint + symbol) is
  present. Drop a STEP into `models/` as `SMA_Amphenol_901-143-6RFX.stp` and add a `(model …)`
  line to the SMA footprint to fill it.

## Notes

- **Schematic symbols are reference-only.** This project generates boards directly from
  [`../pinout.py`](../pinout.py) (no schematic/netlist). The QSE symbol's pin *numbers*
  (1…80) do not map 1:1 to the footprint's pad *names* (01…80) — fine for a reference
  symbol, but don't drive a layout from these without checking the pin map.
- **MCX MPN confirmed** (2026-07-15): Board A is deliberately **through-hole** —
  `MCX-J-P-H-ST-TH1` is the exact orderable straight (vertical) THT jack (`-H` = heavy gold,
  50 Ω, 6 GHz). Verified against the Samtec `mcx-j-p-x-st-th1-mkt.pdf` drawing and live DigiKey
  listing (SAM8944-ND). The THT signal pin is plated through all layers, so the QSE's B.Cu
  channel escape lands on it with **no face-change via** (zero signal vias board-wide). Do
  *not* cross with the 75 Ω `MCX7-J-P-H-ST-TH1` (SAM8945-ND) or the smaller
  `MMCX-J-P-H-ST-TH1` (SAM10617-ND); the right-angle `MCX-J-P-H-RA-TH1` (SAM10607-ND) is a
  valid mechanical alternative but needs a re-layout. (Board A previously used the SMD
  `MCX-J-P-H-ST-SM1` / SAM10608-ND — reversed 2026-07-15 in favour of the through-hole part.)
- Datasheets were collected from manufacturer/CDN sources; the SMA and SMP drawings come
  from Amphenol's public CDN, U.FL from a Hirose drawing, QSE from the Samtec QSE-series
  catalog, MCX from the Samtec through-hole drawing (`mcx-j-p-x-st-th1-mkt.pdf`,
  suddendocs.samtec.com/prints/mcx-j-p-x-st-th1-mkt.pdf).
