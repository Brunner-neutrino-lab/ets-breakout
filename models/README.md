# 3D models

STEP models referenced by the footprints in [`../lib/ets-breakout.pretty/`](../lib/ets-breakout.pretty/).
Footprints reference these via `${KIPRJMOD}/../../models/<file>` — `KIPRJMOD` resolves
to each board's directory (`boards/board-*/`), so `../../models/` lands here regardless
of which board is open.

| Part | File | Source | Status |
|------|------|--------|--------|
| QSE-040-01-L-D-A (J5) | `QSE-040-01-L-D-A.stp` | upstream `reference/` snapshot | **present** |
| MCX-J-P-H-ST-TH1 (Board A, THT) | — | — | **gap** (need vertical through-hole model; the SMD `MCX-J-P-X-ST-SM1.step` no longer matches Board A's through-hole part) |
| SMP-MSLD-PCS-20 (Board D) | `SMP-MSLD-PCS-20.stp` | Amphenol / SnapMagic | **present** |
| U.FL-R-SMT-1 (Board C) | `U.FL_Hirose_U.FL-R-SMT-1_Vertical.step` | KiCad bundled lib (copied local) | **present** |
| SMA 901-143-6RFX (Board B) | — | — | **gap** (vendor-gated) |

Two footprints lack a local resolving model — **Board A MCX THT** and **SMA**.

- **MCX-J-P-H-ST-TH1** (Board A): Board A moved from the SMD MCX to the through-hole
  `MCX-J-P-H-ST-TH1`. The old `MCX-J-P-X-ST-SM1.step` is the SMD variant and no longer matches
  the through-hole part, so no model resolves for the `Samtec_MCX-J-P-H-ST-TH1` footprint. To
  fill it, source a vertical THT MCX STEP, drop it here, and add a
  `(model "${KIPRJMOD}/../../models/<file>")` line to
  `lib/ets-breakout.pretty/Samtec_MCX-J-P-H-ST-TH1.kicad_mod`.
- **SMA** (Board B): the SMA STEP is behind a vendor login (Amphenol RF / SnapMagic / Ultra
  Librarian); its footprint carries no `(model …)` line. To fill it, drop the vendor STEP here
  as `SMA_Amphenol_901-143-6RFX.stp` and add a
  `(model "${KIPRJMOD}/../../models/SMA_Amphenol_901-143-6RFX.stp")` line to
  `lib/ets-breakout.pretty/SMA_Amphenol_901-143_Horizontal.kicad_mod`, then regenerate Board B.
