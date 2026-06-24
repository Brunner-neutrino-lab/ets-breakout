# BOM & CAD asset collection — ETS per-channel breakout boards

Consolidated bill of materials across all four board variants, plus the collected CAD
assets (datasheet, footprint, schematic symbol, 3D model) for every part. Machine-readable
master BOM: [`BOM.csv`](BOM.csv). Per-board fab BOMs live in each
`boards/board-*/fab/board-*-bom.csv`.

All four boards share the **same QSE-040 socket and mechanical**; they differ only in the
coax jack (one jack type per board). Each board = **1× QSE-040 + 25× coax jack + 4× M3 hole**.

## Master BOM

| Item | Manufacturer | MPN | Qty/board | Board(s) | Notes |
|------|--------------|-----|:---------:|:--------:|-------|
| J5 socket | Samtec | QSE-040-01-L-D-A | 1 | A B C D | detector-side socket; mounts on the back face |
| MCX jack | Samtec | MCX-J-P-H-ST-SM1 | 25 | A | straight (vertical) SMT, 50 Ω — *MPN inferred from family, confirm* |
| SMA jack | Amphenol RF | 901-143-6RFX | 25 | B | right-angle through-hole, 50 Ω |
| U.FL jack | Hirose | U.FL-R-SMT-1(10) | 25 | C | SMT, 50 Ω — **≤60 V** working voltage (low-bias channels only) |
| SMP jack | Amphenol RF | SMP-MSLD-PCS-20 | 25 | D | vertical SMT, 50 Ω, 4.08 mm max height |
| Mounting hole | — | — | 4 | A B C D | M3 non-plated (mechanical) |

A full 96-channel system uses 4 boards of one chosen variant → **4× QSE-040 + 100× the
chosen jack** per system.

## CAD asset matrix

Datasheets in [`datasheets/`](datasheets/); footprints in
[`../lib/ets-breakout.pretty/`](../lib/ets-breakout.pretty/); schematic symbols in the
single library [`../lib/ets-breakout.kicad_sym`](../lib/ets-breakout.kicad_sym); 3D STEP
models in [`../models/`](../models/).

| Part | Datasheet | Footprint | Symbol | 3D CAD |
|------|:---------:|:---------:|:------:|:------:|
| QSE-040-01-L-D-A | ✅ `Samtec_QSE.pdf` | ✅ | ✅ | ✅ `QSE-040-01-L-D-A.stp` |
| MCX-J-P-X-ST-SM1 | ✅ `Samtec_MCX-J-P-X-ST-MT1.pdf` | ✅ | ✅ | ✅ `MCX-J-P-X-ST-SM1.step` |
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
- **MCX MPN** `MCX-J-P-H-ST-SM1` is inferred from the Samtec family (the footprint/datasheet
  use the generic `-X-` placeholder). Confirm the exact orderable jack before ordering.
- Datasheets were collected from manufacturer/CDN sources; the SMA and SMP drawings come
  from Amphenol's public CDN, U.FL from a Hirose drawing, QSE from the Samtec QSE-series
  catalog, MCX from the Samtec ST-MT1 drawing.
