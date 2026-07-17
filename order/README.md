# Purchase handover — ETS breakout Board A (MCX), 96-channel system

Everything needed to place the two orders is in this folder. No project context required.
Part numbers, stock and prices were verified live **2026-07-15**; **design state 2026-07-17**
(Board A rebalanced to a ~12/13 jack split, **through-hole** MCX jack, board DRC-clean 0/0,
fab zip regenerated). Questions →
see [`../docs/BOM.md`](../docs/BOM.md) §Purchase order.

**What this buys:** 5 PCBs (4 needed + 1 spare), connectors for 4 boards + 20 % spares, and
4× SMA-to-TRB triax adapters for the IV outputs.
**Expected total ≈ $950** ($831 DigiKey + ~$90 PCB + ~$28 shipping).

| File | Use |
|------|-----|
| `board-A-mcx-jlcpcb.zip` | Upload to JLCPCB quote wizard (gerbers + drill, nothing else needed) |
| `digikey-bom-connectors.csv` | Upload to DigiKey myLists (or use the quick-add lines below) |

---

## Order 1 — PCBs at JLCPCB (~$90 + ~$28 DHL)

> **Fab-only order — hand-solder, no JLC assembly.** JLCPCB fabricates the bare PCBs only;
> do **not** add SMT/PCBA assembly to this order. The 50 Ω through-hole MCX
> (`MCX-J-P-H-ST-TH1`) is **not stocked at LCSC** — LCSC lists only the wrong-impedance 75 Ω
> `MCX7-J-P-H-ST-TH1` or the wrong-series `MMCX-J-P-H-ST-TH1`, neither acceptable — so every
> connector is ordered from DigiKey (Order 2) and hand/selective-soldered in the lab.

Go to [jlcpcb.com](https://jlcpcb.com) → **Instant Quote** → upload `board-A-mcx-jlcpcb.zip`
(**regenerated 2026-07-17** for the rebalanced layout — re-upload this current zip, not
any earlier copy). The wizard auto-detects 4 layers and **75.0 × 125.2 mm** (the balanced
~12/13 jack split shrank the board ~32 mm from the earlier revision). Set the fields:

| Wizard field | Set to |
|---|---|
| Base Material | FR-4 |
| Layers | 4 (auto-detected) |
| PCB Qty | **5** |
| Delivery Format | Single PCB |
| PCB Thickness | 1.6 mm |
| **Specify Stackup** | **Yes → JLC04161H-7628** |
| **Impedance Control** | **Yes — ±10 % (±5 Ω for ≤50 Ω)** |
| Surface Finish | **ENIG** (flat pads for the fine 0.8 mm-pitch QSE-040 SMD socket — worth the ~$18 over HASL) |
| Outer Copper Weight | 1 oz |
| PCB Color | any (green is cheapest/fastest) |
| Via Covering | default (tented) |
| Confirm Production File | Yes (recommended, ~$1) |

Paste into the **PCB Remark** field:

> 50 ohm single-ended microstrip, 0.325 mm nominal trace on outer layers (F.Cu/B.Cu)
> referenced to the adjacent inner GND plane (0.2104 mm 7628 prepreg, Dk 4.4). Adjust
> trace width to your etched stackup to hit 50 ohm (JLC04161H-7628 target is ~0.325 mm).

Indicative quote for the 75.0 × 125.2 mm board: **~$85–95 ENIG qty 5** (engineering + board +
impedance-control + file confirm + ENIG), 3–4 day build, DHL ~$28 — **re-quote in the wizard**,
the board shrank from the earlier revision. Well under JLC's 650 cm² large-board surcharge
at ~94 cm². HASL is cheaper if cost matters more than pad flatness.

## Order 2 — Connectors at DigiKey ($831.19)

Upload `digikey-bom-connectors.csv` at DigiKey → **myLists → Upload a File**, review, add to
cart. Or paste into Quick Add (`PN, qty`):

```
SAM8944-ND, 120
SAM8124-ND, 5
1097-1372-ND, 4
```

| PN | Part | Qty | Unit | Ext | Stock 2026-07-15 |
|----|------|----:|-----:|----:|------|
| SAM8944-ND | Samtec MCX-J-P-H-ST-TH1 — MCX jack, straight, **through-hole**, 50 Ω, 6 GHz | 120 | $4.21 (@100 break) | $505.20 | 11,568 |
| SAM8124-ND | Samtec QSE-040-01-L-D-A — detector-side socket | 5 | $7.27 | $36.35 | 2,021 |
| 1097-1372-ND | Cinch 3-0347-9 — coax adapter, SMA to TRB (triax) — **for IV out**, 1 per board | 4 | $72.41 | $289.64 | 147 |

> **The MCX jacks are THROUGH-HOLE** (SAM8944-ND / `MCX-J-P-H-ST-TH1`). They are
> hand- or selective-soldered, **not** reflowed. The QSE-040 socket is SMD, so Board A is a
> mixed assembly: reflow the QSE, then hand/selective-solder the 25 THT jacks per board.

**Substitution rules (important):**

- **MCX — the through-hole part is the intended one.** `MCX-J-P-H-ST-TH1` (SAM8944-ND) mates
  the plated-through signal pin the layout relies on (zero face-change vias). A valid
  mechanical **alternative** is the right-angle THT `MCX-J-P-H-RA-TH1` (SAM10607-ND) — cable
  exits sideways off the board edge, but it needs a re-layout, so only sub with intent. Never
  cross to the **75 Ω** `MCX7-J-P-H-ST-TH1` (SAM8945-ND) or the smaller `MMCX-J-P-H-ST-TH1`
  (SAM10617-ND) — wrong impedance / wrong footprint. The old SMD jack `MCX-J-P-H-ST-SM1`
  (SAM10608-ND) is **no longer this board's part** — do not order it.
- QSE: **plain suffix only.** Never `-RT1` (retention hardware — needs board holes this
  layout doesn't have). `-K` / `-TR` are pick-and-place packaging variants — unnecessary but
  harmless. If DigiKey is out: Mouser `200-QSE04001LDA` (was $5.59, 2,589 stock).

## Checklist before submitting

- [ ] JLCPCB: **fab-only** (no assembly), current (2026-07-17) zip, qty **5**, stackup **JLC04161H-7628**, impedance control ON, ENIG, remark pasted
- [ ] DigiKey: SAM8944-ND (THT MCX) ×120 + SAM8124-ND ×5 + 1097-1372-ND ×4, no substitutions outside the rules above
- [ ] Both orders ship to the lab as usual
