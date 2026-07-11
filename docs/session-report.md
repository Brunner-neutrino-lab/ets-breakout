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
> `Samtec_MCX-J-P-X-ST-SM1.pdf`; the previously-bundled `…ST-MT1.pdf` is the through-hole
> variant — and the live DigiKey listing **SAM10608-ND**, 4,577 in stock, $3.99 @ 100).
> QSE-040 socket confirmed as DigiKey **SAM8124-ND** ($7.27, 2,021 stk; plain suffix only —
> `-RT1` needs retention holes the board lacks). `make_bom.py` PARTS now carries both DK PNs;
> all four board BOM CSVs + fab zips regenerated. Board A re-verified: **0 DRC errors /
> 0 unconnected** (25 warning-level 0.7 mm silk text-height notes only, cosmetic).
> Controlled-impedance fab quotes pulled live: JLCPCB ~$65 HASL / ~$83 ENIG qty 5
> (JLC04161H-7628 stackup, ±5 Ω at 50 Ω, their 50 Ω width ≈0.35 mm vs our 0.34 mm nominal);
> PCBWay ~$122/$148. Full order table + DigiKey quick-add in `docs/BOM.md` §Purchase order.
> **System order ≈ $560–590** (110× MCX + 5× QSE + 5 PCBs, ENIG).
