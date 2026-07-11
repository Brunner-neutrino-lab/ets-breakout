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
| MCX jack | Samtec | MCX-J-P-H-ST-SM1 | SAM10608-ND | 25 | A | straight (vertical) SMT, 50 Ω — **confirmed orderable** (Active, verified 2026-07-11) |
| SMA jack | Amphenol RF | 901-143-6RFX | ARFX1232-ND | 25 | B | right-angle through-hole, 50 Ω |
| U.FL jack | Hirose | U.FL-R-SMT-1(10) | — | 25 | C | SMT, 50 Ω — **≤60 V** working voltage (low-bias channels only) |
| SMP jack | Amphenol RF | SMP-MSLD-PCS-20 | — | 25 | D | vertical SMT, 50 Ω, 4.08 mm max height |
| Mounting hole | — | — | — | 4 | A B C D | M3 non-plated (mechanical) |

A full 96-channel system uses 4 boards of one chosen variant → **4× QSE-040 + 100× the
chosen jack** per system.

## Purchase order — final build (Board A / MCX, full 96-channel system)

**Board A is the chosen final variant.** Quantities below build 4 boards + 1 spare PCB, with
10 spare jacks and 1 spare socket. All part numbers, stock and prices verified live
**2026-07-11**.

| # | Item | Order PN | Source | Qty | Unit | Ext | Stock (2026-07-11) |
|---|------|----------|--------|----:|-----:|----:|-------|
| 1 | MCX jack `MCX-J-P-H-ST-SM1` | **SAM10608-ND** | DigiKey | 110 | $3.99 (@100) | $438.90 | 4,577 (breaks: 1/$5.83 · 50/$4.91 · 100/$3.99) |
| 2 | QSE socket `QSE-040-01-L-D-A` | **SAM8124-ND** | DigiKey | 5 | $7.27 | $36.35 | 2,021 (Mouser `200-QSE04001LDA` cheaper at $5.59 → $27.95, 2,589 stk — aggregator-sourced, reconfirm in cart) |
| 3 | PCB `board-A-mcx-fab.zip` (76.42 × 138.69 mm, 4-layer, controlled impedance) | — | JLCPCB (or PCBWay) | 5 | — | ~$65 HASL / ~$83 ENIG | JLCPCB 3–4 day build, +~$28 DHL |
| 4 | M3 screws/standoffs (mounting) | — | generic | 16+ | — | — | lab stock |

**Total ≈ $560–590** (DigiKey ~$475 + JLCPCB ENIG ~$83 + shipping). PCBWay quoted ~$122
HASL / ~$148 ENIG (+$48 impedance fee) as the alternative.

DigiKey Quick-Add (`PN, qty`):

```
SAM10608-ND, 110
SAM8124-ND, 5
```

**PCB ordering notes (both fabs confirmed they tune width at file review):**

- Order **controlled impedance** with the note: *"50 Ω single-ended microstrip, 0.34 mm
  nominal on outer layers referenced to the adjacent inner GND plane — adjust width to your
  stackup."*
- JLCPCB: 4-layer → Specify Stackup **JLC04161H-7628** → Impedance Control **±10 % (±5 Ω at
  ≤50 Ω)** (+$32.84 fee on this order). Their calculator's 50 Ω width on that stackup is
  ~0.35 mm — our 0.34 mm is at nominal.
- **ENIG recommended** over HASL: flatter pads for the 0.8 mm-pitch QSE-040 and the SMT MCX.
- Jack/socket caveats: MCX `-H-ST-SM1` is the tray part (`-TR` = tape&reel of the same jack);
  QSE must be the **plain** suffix — never `-RT1` (retention hardware needs board holes this
  layout doesn't have), `-K`/`-TR` are unnecessary pick-and-place packaging variants.

## CAD asset matrix

Datasheets in [`datasheets/`](datasheets/); footprints in
[`../lib/ets-breakout.pretty/`](../lib/ets-breakout.pretty/); schematic symbols in the
single library [`../lib/ets-breakout.kicad_sym`](../lib/ets-breakout.kicad_sym); 3D STEP
models in [`../models/`](../models/).

| Part | Datasheet | Footprint | Symbol | 3D CAD |
|------|:---------:|:---------:|:------:|:------:|
| QSE-040-01-L-D-A | ✅ `Samtec_QSE.pdf` | ✅ | ✅ | ✅ `QSE-040-01-L-D-A.stp` |
| MCX-J-P-X-ST-SM1 | ✅ `Samtec_MCX-J-P-X-ST-SM1.pdf` (SM1 rev C) | ✅ | ✅ | ✅ `MCX-J-P-X-ST-SM1.step` |
| 901-143-6RFX (SMA) | ✅ `Amphenol_901-143-6RFX.pdf` | ✅ | ✅ | ⛔ vendor-gated (Amphenol/SnapMagic login) |
| U.FL-R-SMT-1(10) | ✅ `Hirose_U.FL-R-SMT-1.pdf` | ✅ | ✅ | ✅ `U.FL_Hirose_U.FL-R-SMT-1_Vertical.step` |
| SMP-MSLD-PCS-20 | ✅ `Amphenol_SMP-MSLD-PCS.pdf` | ✅ | ✅ | ✅ `SMP-MSLD-PCS-20.stp` |

**Only gap:** the SMA 3D STEP (Amphenol 901-143-6RFX) — the model is behind a vendor
login (Amphenol RF / SnapMagic / Ultra Librarian), so it isn't bundled. Everything else
(datasheet + footprint + symbol) is present for the SMA. Drop a STEP into `models/` as
`SMA_Amphenol_901-143-6RFX.stp` and add a `(model …)` line to the SMA footprint to fill it.

## Notes

- **Schematic symbols are reference-only.** This project generates boards directly from
  [`../pinout.py`](../pinout.py) (no schematic/netlist). The QSE symbol's pin *numbers*
  (1…80) do not map 1:1 to the footprint's pad *names* (01…80) — fine for a reference
  symbol, but don't drive a layout from these without checking the pin map.
- **MCX MPN confirmed** (2026-07-11): `MCX-J-P-H-ST-SM1` is the exact orderable straight-SMT
  jack (`-H` = heavy gold, tray). Verified against the Samtec SM1 rev C drawing and live
  DigiKey listing (SAM10608-ND, product 2685235); it is *not* the right-angle `-RA-TH1` or
  edge-mount `-EM1`.
- Datasheets were collected from manufacturer/CDN sources; the SMA and SMP drawings come
  from Amphenol's public CDN, U.FL from a Hirose drawing, QSE from the Samtec QSE-series
  catalog, MCX from the Samtec **SM1 rev C** drawing (`Samtec_MCX-J-P-X-ST-SM1.pdf`, added
  2026-07-11, byte-identical to the live Samtec print). The old `…ST-MT1.pdf` (rev B,
  mixed-technology/through-hole family — a different part, not used on any board) was
  removed 2026-07-11.
