# Purchase handover — ETS breakout Board A (MCX), 96-channel system

Everything needed to place the two orders is in this folder. No project context required.
Part numbers, stock and prices were verified live **2026-07-11** (design state: git `e042717`,
board DRC-clean). Questions → see [`../docs/BOM.md`](../docs/BOM.md) §Purchase order.

**What this buys:** 5 PCBs (4 needed + 1 spare), connectors for 4 boards + 20 % spares, and
4× SMA-to-TRB triax adapters for the IV outputs.
**Expected total ≈ $915** ($805 DigiKey + ~$83 PCB + ~$28 shipping).

| File | Use |
|------|-----|
| `board-A-mcx-jlcpcb.zip` | Upload to JLCPCB quote wizard (gerbers + drill, nothing else needed) |
| `digikey-bom-connectors.csv` | Upload to DigiKey myLists (or use the quick-add lines below) |

---

## Order 1 — PCBs at JLCPCB (~$83 + ~$28 DHL)

Go to [jlcpcb.com](https://jlcpcb.com) → **Instant Quote** → upload `board-A-mcx-jlcpcb.zip`.
The wizard auto-detects 4 layers and 76.42 × 138.69 mm. Set the fields:

| Wizard field | Set to |
|---|---|
| Base Material | FR-4 |
| Layers | 4 (auto-detected) |
| PCB Qty | **5** |
| Delivery Format | Single PCB |
| PCB Thickness | 1.6 mm |
| **Specify Stackup** | **Yes → JLC04161H-7628** |
| **Impedance Control** | **Yes — ±10 % (±5 Ω for ≤50 Ω)** |
| Surface Finish | **ENIG** (flat pads for the 0.8 mm-pitch QSE socket — worth the ~$18 over HASL) |
| Outer Copper Weight | 1 oz |
| PCB Color | any (green is cheapest/fastest) |
| Via Covering | default (tented) |
| Confirm Production File | Yes (recommended, ~$1) |

Paste into the **PCB Remark** field:

> 50 ohm single-ended microstrip, 0.34 mm nominal trace on outer layers (F.Cu/B.Cu)
> referenced to the adjacent inner GND plane. Adjust trace width to your stackup to
> hit 50 ohm (JLC04161H-7628 target is ~0.35 mm).

Reference quote pulled 2026-07-11: **$83.08 ENIG qty 5** ($25 engineering + $6.50 board +
$32.84 impedance + $1.04 file confirm + $17.70 ENIG), 3–4 day build, DHL ~$28.
HASL variant was $65.38 if cost matters more than pad flatness.

## Order 2 — Connectors at DigiKey ($804.79)

Upload `digikey-bom-connectors.csv` at DigiKey → **myLists → Upload a File**, review, add to
cart. Or paste into Quick Add (`PN, qty`):

```
SAM10608-ND, 120
SAM8124-ND, 5
1097-1372-ND, 4
```

| PN | Part | Qty | Unit | Ext | Stock 2026-07-11 |
|----|------|----:|-----:|----:|------|
| SAM10608-ND | Samtec MCX-J-P-H-ST-SM1 — MCX jack, straight SMT, 50 Ω | 120 | $3.99 (@100 break) | $478.80 | 4,577 |
| SAM8124-ND | Samtec QSE-040-01-L-D-A — detector-side socket | 5 | $7.27 | $36.35 | 2,021 |
| 1097-1372-ND | Cinch 3-0347-9 — coax adapter, SMA to TRB (triax) — **for IV out**, 1 per board | 4 | $72.41 | $289.64 | 147 |

**Substitution rules (important):**

- MCX: `MCX-J-P-H-ST-SM1-TR` (tape & reel) is the **same jack**, fine if the tray part sells
  out. Do **not** accept `-RA-TH1` (right-angle) or `-EM1` (edge-mount) — different parts.
- QSE: **plain suffix only.** Never `-RT1` (retention hardware — needs board holes this
  layout doesn't have). `-K` / `-TR` are pick-and-place packaging variants — unnecessary but
  harmless. If DigiKey is out: Mouser `200-QSE04001LDA` (was $5.59, 2,589 stock).

## Checklist before submitting

- [ ] JLCPCB: qty **5**, stackup **JLC04161H-7628**, impedance control ON, ENIG, remark pasted
- [ ] DigiKey: 120 + 5, no substitutions outside the rules above
- [ ] Both orders ship to the lab as usual
