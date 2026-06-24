# 3D models

STEP models referenced by the footprints in [`../lib/ets-breakout.pretty/`](../lib/ets-breakout.pretty/).
Footprints reference these via `${KIPRJMOD}/../../models/<file>` — `KIPRJMOD` resolves
to each board's directory (`boards/board-*/`), so `../../models/` lands here regardless
of which board is open.

| Part | File | Source | Status |
|------|------|--------|--------|
| QSE-040-01-L-D-A (J5) | `QSE-040-01-L-D-A.stp` | upstream `reference/` snapshot | **present** |
| MCX-J-P-X-ST-SM1 (Board A) | `MCX-J-P-X-ST-SM1.step` | sibling SMP-feedthrough project | **present** |
| SMP-MSSB-PCS (Board D) | `SMP-MSSB-PCS-NM.stp` | sibling SMP-feedthrough project | **present** |
| U.FL-R-SMT-1 (Board C) | *(KiCad bundled)* | `${KICAD10_3DMODEL_DIR}/Connector_Coaxial.3dshapes/U.FL_Hirose_U.FL-R-SMT-1_Vertical.step` | **resolves** |
| SMA 901-143-6RFX (Board B) | — | — | **skipped** (no 3D model) |

Every footprint except SMA has a resolving model. SMA's 3D model was intentionally
skipped; the footprint carries no `(model …)` line. If you ever want it, drop the vendor
STEP into this folder and add a `(model "${KIPRJMOD}/../../models/<file>")` line to
`lib/ets-breakout.pretty/SMA_Amphenol_901-143_Horizontal.kicad_mod`, then regenerate Board B.
