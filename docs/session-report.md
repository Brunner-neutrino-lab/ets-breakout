# Session handoff — ETS per-channel breakout boards

Report from the development session that built `ets-breakout/`. Intended for a
"manager" session reorganizing the whole working directory.

> **Historical record.** The reorganization this report recommended (§5–§6) has
> since been carried out: `ets-breakout/` is now its own standalone git repo, the
> upstream clone is a de-gitted read-only snapshot under `reference/`, and the SMP
> project is a separate sibling repo. Paths below describe the *old* layout.

> **Update 2026-06-22 — Board D (SMP) added.** A fourth variant was generated with
> the same pipeline: 25× **Amphenol SMP-MSSB-PCS** (SMP *male*, vertical SMT,
> 50 Ω DC–18 GHz), footprint carried over from the sibling SMP-feedthrough project.
> Unlike A/B/C, the SMP's center signal pad is enclosed by its ground frame on all
> four sides, so `finalize_board.py` routes the channel on B.Cu under the frame and
> enters through a **center via-in-pad** (gated on jacks whose footprint name
> contains "SMP"). Board is 74 × 112 mm, **DRC 0/0**, all 25 signal pads via-verified;
> fab package at `boards/board-D-smp/board-D-smp-fab.zip`. Fab note: order with
> plugged/capped vias (or hand-solder) so the SMT joint doesn't wick into the via.

> **Update 2026-06-22 — J5 moved to the back face (all boards).** The QSE-040 (J5)
> is now mounted on the **opposite PCB face from the coax jacks** (J5 on B.Cu, jacks
> on F.Cu): the detector plugs into the back, cables come off the front. `gen_board.py`
> flips J5 after assigning nets; the pad→net binding is preserved, so connectivity is
> unchanged. `finalize_board.py` was made face-agnostic — it detects which copper face
> J5's SMD pads are on (via `IsOnLayer`, since `GetLayer()` lies for a flipped SMD pad)
> and routes escapes on that HOME layer, hopping to the OTHER signal layer only for the
> crossing fans. All four boards re-routed and re-exported: **DRC 0/0**, J5 = bottom and
> all 25 jacks = top in the placement CSVs.

> **Update 2026-06-22 — 3D models + Board A changed to straight MCX.** 3D STEP models
> were attached: QSE-040 (from `reference/`), SMP-MSSB-PCS and the straight MCX (from the
> sibling SMP-feedthrough project) live in `models/` and are referenced via
> `${KIPRJMOD}/../../models/…`; U.FL uses KiCad's bundled model. SMA's 3D model was
> skipped. **Board A now uses a straight (vertical) surface-mount MCX jack**
> (`Samtec MCX-J-P-X-ST-SM1`, datasheet rev C) instead of the right-angle through-hole
> part — cable exits straight up, flat placement, and the signal pad routes like U.FL
> (SMD, signal reachable between the four corner grounds, no center via). The right-angle
> MCX footprint and its datasheet were removed. Boards A & B re-routed and re-exported,
> **DRC 0/0**. Straight-MCX orderable MPN (`MCX-J-P-H-ST-SM1`) is inferred — confirm.

## 1. What this session built

Three PCBs that **replace the broken `iv-pulse-mux` board** in the Brunner-lab
**ETS-96-channel-IV-pulse-mux** system with a *passive per-channel breakout*. Each
board mates the detector-side **QSE-040-01-L-D-A** socket and fans every channel out
to its own coax jack:

| Board | Jacks (25 each) | Part | Status |
|-------|-----------------|------|--------|
| A | MCX × 25 | Samtec MCX-J-P-H-RA-TH1 (DK SAM10607-ND) | DRC 0/0, fab-ready |
| B | SMA × 25 | Amphenol RF 901-143-6RFX (DK ARFX1232-ND) | DRC 0/0, fab-ready |
| C | U.FL × 25 | Hirose U.FL-R-SMT-1(10) | DRC 0/0, fab-ready |

25 break-outs = 24 `SIPM_K0..K23` + `IV`. 12 K-channels bundle to flange 1 (one edge),
12 to flange 2 (other edge), IV to flange 3. 4-layer, 50 Ω microstrip on PCBWay default
4-layer stackup, GND pours all layers + stitching, 4× M3 holes. All footprints are
datasheet-verified.

**Everything is generated from one source of truth, `pinout.py`** — no hand placement.
Pipeline (KiCad 10 bundled Python):
```
gen_board.py [mcx|sma|ufl]   placement + nets + outline + holes  (imports pinout.py)
finalize_board.py <pcb>      4-layer stackup + 50Ω routes + GND zones + stitching
fill_zones.py <pcb>          fill pours (separate pass; in-memory fill segfaults)
kicad-cli pcb drc / export   verify + gerbers/drill/pos ; make_bom.py for BOM
```

## 2. Key decisions (with rationale)

- **Source repo identification.** The repo Lucas named (`ETS-96-channel-IV-pulse-mux`)
  is the right one; the public GitHub `IV-MUX-public` is a *different, older* board —
  don't conflate. The authoritative QSE-040 (J5) pin→net map was extracted from the
  upstream schematic **netlist** (`kicad-cli sch export netlist`), not eyeballed.
- **QSE-040 is carried on the new board** (same socket the mux used), mating the existing
  QTE-040 upstream. Confirmed with Lucas.
- **Flexible 12/12 channel→flange split** (Lucas's call). The connector's two pin rows
  are asymmetric (16 channels one row, 8 the other), so a 12/12 split has a hard floor of
  **4 nets crossing** the connector (routed on the bottom layer). The generator computes
  the optimal split from pad geometry to hit that floor.
- **Routing primitive = escape + single straight diagonal + straight into pad.** Monotonic
  fans are planar this way. (Vertical-bus and nested-bus fan-outs were tried and both
  introduced crossings — diagonal is correct here.)
- **IV jack** ended up inline on one edge (a center-top position had no clean routing
  lane). Still a separate connector cabled to flange 3.
- **Trace width 0.34 mm ≈ 50 Ω** microstrip on the PCBWay default 4-layer; `EDGE_GAP`
  widened to 26 mm so the end-channel fan diagonals stay shallow enough to clear at width.
  Recommend ordering as **controlled impedance** so PCBWay tunes to their exact stackup.
- **U.FL** = low-voltage use only (rated ~60 V vs bias up to ~70 V); noted, Lucas accepted.

## 3. Status / what's verified vs assumed

- All three boards: **0 DRC violations, 0 unconnected.** Fab packages
  (`boards/board-*/...-fab.zip`) = gerbers (4 copper + mask/silk/edge) + Excellon drill +
  placement CSV + BOM CSV.
- All four footprints datasheet-verified (MCX vs Samtec drawing rev H, archived in
  `docs/datasheets/`; SMA + U.FL from KiCad lib; QSE-040 from the ETS repo).
- **Open items (housekeeping, not blocking):** (a) no schematic/netlist — boards are built
  directly from `pinout.py`, which is unconventional; (b) MCX signal pin assumed centered
  in the ground square (drawing shows no offset); (c) impedance is nominal — confirm with
  PCBWay's stackup; (d) the `MCX-J-P-H-RA-TH1` 3D model isn't attached (cosmetic).

## 4. `ets-breakout/` layout (clean, self-contained)

```
ets-breakout/
  pinout.py                      SINGLE SOURCE OF TRUTH (QSE-040 J5 pin->net, breakout list)
  tests/test_pinout.py           sanity + self-consistency checks
  tools/  gen_board.py finalize_board.py fill_zones.py make_bom.py
  lib/ets-breakout.pretty/       4 verified footprints (QSE-040, MCX, SMA, U.FL)
  docs/datasheets/               Samtec MCX drawing rev H
  boards/board-{A-mcx,B-sma,C-ufl}/   .kicad_pcb/.kicad_pro + renders + *-fab.zip
  README.md                      full pipeline + status
```

## 5. The directory problem the manager should fix

The working dir currently mixes **three unrelated things** at the top level:

1. **The original SMP-feedthrough project** (different deliverable): `CLAUDE.md`,
   `smp-adapter-boards-brief.md`, `README.md`, `boards/`, `geometry/`, `lib/`, `tools/`,
   `tests/`, `docs/`, `models/`, `out/`, `MCX/`, and stray top-level reports
   (`board-A-mcx-drc.rpt`, `board-B-ufl-*.rpt/json`, `board-A-mcx-erc.rpt`).
2. **A clone of the upstream reference repo** `ETS-96-channel-IV-pulse-mux/` — **has its
   own nested `.git`** (messy inside the parent repo). It was the source of the pinout.
3. **This session's project** `ets-breakout/` (self-contained).

⚠️ **Name collision:** the SMP project's boards are *also* named `board-A-mcx` and
`board-B-ufl`; this project has `board-A-mcx`, `board-B-sma`, `board-C-ufl`. Two different
"board-A-mcx" exist. Keep them namespaced by project directory.

Other cruft to clean: `ets-breakout/__pycache__/`, `ets-breakout/board-*-drc.rpt` (kicad-cli
dumps to CWD), redundant renders in `board-A-mcx/` (`placement-A.svg`, `routed-A-*.pdf`,
keep `routed-top.pdf`). No `.gitignore` in `ets-breakout/`.

## 6. Recommended organization

- **Separate the two board projects into top-level directories** (or two repos):
  `smp-feedthrough/` (the original) and `ets-breakout/` (this one). They share *nothing*
  functionally and the name collision alone justifies the split. `ets-breakout/` is
  already self-contained and can move as-is.
- **The upstream `ETS-96-channel-IV-pulse-mux/` clone:** the data we needed is already
  captured (`ets-breakout/pinout.py` + archived datasheet). Recommend **removing its
  nested `.git`** and keeping it under `reference/` (read-only) *or* dropping it entirely
  and recording the upstream URL + commit in a README. Do **not** leave a nested git repo.
- **Add `.gitignore`** for `__pycache__/`, `*.kicad_prl`, stray `*-drc.rpt/json`,
  `out/`, and (decide) the generated `fab/` + renders since they regenerate from the tools.
- **Keep `ets-breakout/` as-is internally** — it follows the SMP project's own conventions
  (single-source-of-truth generator, local datasheet-verified footprints, test + DRC gate).
- Consider a **top-level README** that names the projects and points into each.

If the manager wants the boards rebuilt from scratch to confirm reproducibility:
`for v in mcx sma ufl: gen_board.py $v -> finalize_board.py -> fill_zones.py -> drc`.

> **Update 2026-06-24 — Board D SMP changed to SMP-MSLD-PCS-20.** Swapped the
> SMP-MSSB-PCS (enclosed centre pad) for **Amphenol RF SMP-MSLD-PCS-20** (vertical SMT,
> 4.08 mm max height), imported from the user-supplied SnapMagic footprint/symbol/STEP
> (pad `G` renamed `2`). Its signal is an **external tab** on one side of the body, so the
> centre via-in-pad scheme is gone — it routes like the other flat SMD jacks. `_edge` now
> rotates every flat jack so its signal pad faces the QSE, derived from the actual pad
> geometry (U.FL -X edge, SMP-MSLD +Y tab, MCX centred), replacing the hard-coded U.FL
> rotation; `finalize_board.py` dropped the SMP centre-via branch. Board D is 75 x 120 mm,
> **DRC 0/0**, all 25 tabs verified facing inward; all four boards re-checked 0/0.

> **Update 2026-07-11 — Board A finalized for purchase (MCX MPN confirmed, full order BOM).**
> The one open sourcing item is closed: **`MCX-J-P-H-ST-SM1` is the exact orderable straight-SMT
> MCX** (verified against the Samtec SM1 rev C drawing — now in `docs/datasheets/` as
> `Samtec_MCX-J-P-X-ST-SM1.pdf`; the previously-bundled `…ST-MT1.pdf` was the through-hole
> variant — and the live DigiKey listing **SAM10608-ND**, 4,577 in stock, $3.99 @ 100).
> QSE-040 socket confirmed as DigiKey **SAM8124-ND** ($7.27, 2,021 stk; plain suffix only —
> `-RT1` needs retention holes the board lacks). `make_bom.py` PARTS now carries both DK PNs;
> all four board BOM CSVs + fab zips regenerated. Board A re-verified: **0 DRC errors /
> 0 unconnected** (25 warning-level 0.7 mm silk text-height notes only, cosmetic).
> Controlled-impedance fab quotes pulled live: JLCPCB ~$65 HASL / ~$83 ENIG qty 5
> (JLC04161H-7628 stackup, ±5 Ω at 50 Ω, their 50 Ω width ≈0.35 mm vs our 0.34 mm nominal);
> PCBWay ~$122/$148. Full order table + DigiKey quick-add in `docs/BOM.md` §Purchase order.
> **System order ≈ $560–590** (110× MCX + 5× QSE + 5 PCBs, ENIG).

> **Update 2026-07-11 — MCX datasheet cleanup (MT1 drawing removed).** Re-verified
> `docs/datasheets/Samtec_MCX-J-P-X-ST-SM1.pdf` byte-identical (SHA-256) to the live
> Samtec print (`suddendocs.samtec.com/prints/mcx-j-p-x-st-sm1-mkt.pdf`); its text confirms
> *MCX STRAIGHT, SMT JACK – 50 OHM*, revision **C**, `-H` = heavy gold, tray packaging.
> Removed `Samtec_MCX-J-P-X-ST-MT1.pdf` (rev B, the mixed-technology/through-hole-leg MCX
> family — a different part not used on any board; keeping it invited exactly the
> SM1-vs-MT1 confusion it caused). The reference-only schematic symbol carried over from
> the SnapMagic MT1 import was renamed `MCX-J-P-X-ST-MT1` → `MCX-J-P-X-ST-SM1` (its
> Footprint field already pointed at the SM1 footprint), its Datasheet field repointed to
> the SM1 PDF, PARTREV B → C, and description filled in; `docs/BOM.csv` symbol column
> updated to match. `docs/datasheets/` is back to exactly the 5 per-part drawings
> CLAUDE.md advertises.

> **Update 2026-07-11 (later) — reference schematic for human review.** Added
> `tools/gen_schematic.py` → `docs/schematic/ets-breakout.kicad_sch` + `.pdf`: single A3
> sheet, J5 drawn as an 88-pin symbol whose **pin names are the nets themselves**, 25 jack
> symbols with the board's own refs (K0–K23, IV), all connectivity by net labels, THERM4/5
> no-connected. Generated from the same `pinout.py` the boards build from, so it cannot
> drift. Gates: **ERC 0 errors** (26 warning-level "lib nickname 'ets' not configured"
> notices are inherent to a standalone sheet with embedded symbols) and the sheet's exported
> netlist **machine-verified identical** to `pinout.py` (25 signal nets incl. IV on J5
> pins 40+42, GNDA 85/85 members, THERM4/5 unconnected). This is a review artifact only —
> the board pipeline is unchanged (still generated straight from `pinout.py`).

> **Update 2026-07-15 — Board A re-laid-out: through-hole MCX, 8/16 planar, FreeRouting autoroute, JLC stackup.**
> Board A was redone to eliminate the four connector-crossing traces the engineer flagged, and to
> retarget the design at JLCPCB. **Why the old tracks crossed:** the earlier layout forced a
> *balanced* **12/12** jacks-per-edge split (equal flange bundles), but the QSE-040's two pin rows
> are asymmetric (16 channels one row, 8 the other), so 12/12 has a hard floor of **4 nets crossing**
> the connector — routed on the other signal layer via 4 layer-hops. **The fix:** split the 24
> channels the way the connector already splits them — **8** on the west edge (K8–K15, the odd-pin
> row) and **16** on the east edge (K0–K7, K16–K23) **+ IV**, each jack placed on the edge matching
> its own QSE pin column. That gives a **monotonic single-layer fan on B.Cu with zero connector
> crossings**. (The old even split is retained only as a documented `SPLIT="balanced"` flag in
> `gen_board.py`.)
>
> **Jack changed SMD → through-hole:** Board A now uses **Samtec `MCX-J-P-H-ST-TH1`** (straight/
> vertical, through-hole, 50 Ω, 6 GHz female jack; DigiKey **SAM8944-ND**, $4.21 @ 100, ~11.6 k in
> stock; footprint `Samtec_MCX-J-P-H-ST-TH1`, pad 1 signal drill 1.10 mm centred, 4× ground drill
> 1.40 mm on a 5.08 mm square). A plated through-hole signal pin is copper on *all* layers, so the
> QSE's B.Cu channel escape lands directly on it with **no face-change via** — the whole board now
> has **zero signal vias** (only GND stitching + island-tie vias). This **reverses** the prior
> "confirmed MPN is the straight-SMD `MCX-J-P-H-ST-SM1` / SAM10608-ND" conclusion; that SMD part and
> its SM1 rev C drawing are no longer Board A's part. Right-angle THT `MCX-J-P-H-RA-TH1`
> (SAM10607-ND) is a valid mechanical alternative (side cable exit, needs a re-layout); do **not**
> cross to the 75 Ω `MCX7-J-P-H-ST-TH1` (SAM8945-ND) or the smaller `MMCX-J-P-H-ST-TH1`
> (SAM10617-ND). Assembly is now **mixed**: THT jacks are hand/selective-soldered, the QSE-040 stays SMD.
>
> **Impedance / fab:** trace width **0.325 mm** = 50 Ω single-ended microstrip on the **JLCPCB
> `JLC04161H-7628`** 4-layer 1.6 mm stack (0.2104 mm 7628 prepreg to the adjacent inner GND plane,
> Dk 4.4), GND-pour clearance 0.30 mm. Fab is **JLCPCB only** now (all PCBWay quotes/comparisons
> dropped); order as controlled impedance so JLC re-tunes the etched width. Board grew to
> **75.0 × 157.2 mm** (was 76 × 139; the east edge carries 17 jacks) — still 118 cm², under JLC's
> 650 cm² large-board surcharge. **DRC 0 violations / 0 unconnected**, all 25 nets on B.Cu.
>
> **Router + pipeline:** Board A now autoroutes with **FreeRouting** (KiCad → Specctra `.dsn` →
> FreeRouting v2.2.4 → `.ses` → KiCad), replacing the bespoke deterministic diagonal router (B/C/D
> still use the deterministic router). New Board A pipeline:
> `gen_board.py mcx` → `finalize_board.py <pcb> setup` → `export_dsn.py <pcb> B.Cu` → FreeRouting →
> `import_ses.py <pcb>` → `finalize_board.py <pcb> stitch` → `fill_zones.py <pcb>` →
> `tie_islands.py <pcb>` → `kicad-cli pcb drc`. New tool scripts: `tools/export_dsn.py`,
> `tools/import_ses.py`, `tools/tie_islands.py`; `finalize_board.py` gained `setup`/`stitch` modes.
> Unchanged: QSE socket `QSE-040-01-L-D-A` (SAM8124-ND), IV-out Cinch 3-0347-9 (1097-1372-ND), and
> `pinout.py` as the single source of truth.

> **Update 2026-07-17 — engineer review: balanced pin-ordered re-layout, J-designators, impedance doc, LCSC check.**
> An engineer review pass reworked Board A's layout, designators, and documentation without changing
> the electrical design, part, or fab vendor.
>
> **Why the old routes bundled/wrapped:** the previous **8/16 planar** split (from the 2026-07-15
> redo) was lopsided — the east edge carried 16 jacks + IV against 8 on the west, making the board
> long (75 × 157 mm) and leaving the FreeRouting autoroute to bundle escapes along the crowded edge.
> **The balanced fix:** the 24 channels are now split **~12/13** and, crucially, **each jack is
> ordered by its QSE pin** so every *native* escape is a **straight line**. West edge = **12 jacks**:
> K8–K15 (native, straight) + K16, K17 (wrap the top corner) + K6, K7 (wrap the bottom corner). East
> edge = **13 jacks**: K18–K23, IV, K0–K5. The 4 spilled channels **wrap around the connector ends on
> B.Cu (2 per corner)** rather than crossing the connector, so the design is still **zero signal vias,
> all 25 nets on B.Cu, DRC 0/0**. Balancing shrank the board 32 mm to **75.0 × 125.2 mm**. The old
> lopsided 8/16 is retained only as the `gen_board.py` `SPLIT="planar"` option; `SPLIT="balanced"` is
> now the default.
>
> **Designators K → J:** jack references were the channel names (K0..K23 / IV); those are relay
> designators (K = relay). Jacks are now proper connector references (**J**) — **J6..J30**
> (K0→J6 … K23→J29, IV→J30), while the detector socket keeps its upstream **J5**. The channel identity
> (K0..K23, IV) is now a **silkscreen label** printed next to each jack, and the mounting-hole
> designators (MH1..) are **hidden on silk**.
>
> **Impedance derivation documented:** trace width is **unchanged at 0.325 mm**, but a full derivation
> now lives in **`docs/impedance.md`** — JLCPCB calculator RS_50 = 0.3244 mm plus the KiCad TransLine /
> IPC-2141 microstrip formula, every input stated. 0.325 mm is JLC's own published 50 Ω single-ended
> width for the `JLC04161H-7628` stackup; order as controlled impedance.
>
> **LCSC / assembly — SMT not viable:** **JLCPCB SMT assembly is NOT viable** for this board; it stays
> **fab-only + hand-solder**. The exact 50 Ω THT MCX (`MCX-J-P-H-ST-TH1`) is absent from LCSC — LCSC
> stocks only the wrong-impedance 75 Ω `MCX7-J-P-H-ST-TH1` or the wrong-series `MMCX-J-P-H-ST-TH1`,
> neither acceptable. A new **LCSC** column is populated honestly in the fab BOM (`make_bom.py` now
> emits it): MCX = "n/a — not LCSC-stocked; hand-solder"; QSE = "C3652705 (-TR variant; info only)";
> the Cinch cable adapter = n/a (not board-mounted). **Unchanged:** the THT part (Samtec
> `MCX-J-P-H-ST-TH1` / DigiKey SAM8944-ND), footprint `Samtec_MCX-J-P-H-ST-TH1`, JLCPCB-only fab,
> quantities (MCX 120, QSE 5, IV adapter 4), DigiKey subtotal $831.19, system ≈ $950, QSE = SAM8124-ND,
> IV adapter Cinch 3-0347-9 / 1097-1372-ND, and `pinout.py` as the single source of truth.
