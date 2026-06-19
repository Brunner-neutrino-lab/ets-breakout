# PCB Design Rules

This document describes the net classes, trace widths, clearances, and design rule constraints used in the ETS 96-Channel IV-Pulse Mux PCB designs.

---

## Net Classes

Four net classes are defined in `iv-pulse-mux.kicad_pro`. These are used to automatically apply appropriate clearance and trace width rules based on signal type.

### Default
| Parameter | Value |
|---|---|
| Track width | 0.2032 mm (~8 mil) |
| Clearance | 0.2032 mm |
| Via diameter | 0.6 mm |
| Via drill | 0.3 mm |
| Microvia diameter | 0.3 mm |
| Microvia drill | 0.1 mm |

Used for: standard digital control signals, low-current signal traces.

---

### `power`
| Parameter | Value |
|---|---|
| Track width | 0.508 mm (~20 mil) |
| Clearance | 0.2032 mm |
| Via diameter | 0.6 mm |
| Via drill | 0.3 mm |

Used for: `+5V`, `GND`, bias voltage supply rails (`+BIAS`, `BIAS_GND`). Wider traces reduce resistive voltage drop and improve current handling.

---

### `guard`
| Parameter | Value |
|---|---|
| Track width | 0.4064 mm (~16 mil) |
| Clearance | 0.1524 mm (6 mil) |

Used for: guard ring traces surrounding sensitive analog nodes. Tighter clearance allows guard rings to closely surround signal pads while the wider track provides a low-impedance driven shield.

> **Guard ring purpose:** In high-impedance or low-current measurements (e.g., SiPM leakage current), guard rings driven at the same potential as the signal conductor prevent leakage currents across PCB surface from reaching the measurement node. This is critical for accurate pA–nA-level current measurements.

---

### `zcontrol`
| Parameter | Value |
|---|---|
| Track width | 0.33528 mm (~13 mil) |
| Clearance | 0.2032 mm |
| Via diameter | 0.6 mm |
| Via drill | 0.3 mm |

Used for: SiPM signal traces and RF signal paths. The `z` prefix and the net class pattern assignment (`*SIPM*`, `*RF*`) indicate that any net whose name matches `*SIPM*` or `*RF*` is automatically assigned to this class.

**Net class pattern rules (from project file):**
```
Pattern: *SIPM*  → netclass: zcontrol
Pattern: *RF*    → netclass: zcontrol
```

---

## PCB Design Rule Check (DRC) Severities

The following DRC rules are configured as **errors** (will block fabrication submission):

- Annular width violations
- Clearance violations
- Copper-to-edge clearance
- Courtyard overlaps
- Creepage distance violations
- Drill out of range
- Footprint errors
- Hole clearance / hole-to-hole / hole-near-hole
- Invalid board outline
- Items on disabled layers
- Microvia drill out of range
- Track length out of range

The following are **warnings** (reported but do not block):
- Connection width
- Copper slivers
- Duplicate footprints
- Extra footprints / missing footprints
- Footprint/symbol mismatch
- Isolated copper

The following are **ignored**:
- Missing courtyard
- Footprint type mismatch
- NPTH inside courtyard

---

## Default PCB Text and Drawing Sizes

| Property | Value |
|---|---|
| Board outline line width | 0.05 mm |
| Copper text size (H/V) | 1.5 mm × 1.5 mm |
| Copper text thickness | 0.3 mm |
| Silkscreen text size (H/V) | 1.0 mm × 1.0 mm |
| Silkscreen text thickness | 0.1 mm |
| Fab layer text size (H/V) | 5.0 mm × 5.0 mm |
| Courtyard line width | 0.05 mm |
| Fab layer line width | 0.1 mm |
| Other line width | 0.3 mm |

---

## Default Pad Dimensions

| Parameter | Value |
|---|---|
| Drill diameter | 0.762 mm |
| Pad height | 1.524 mm |
| Pad width | 1.524 mm |

---

## Fabrication Output Configuration

The `fab-files.kicad_jobset` automates production of:

| Output | Destination |
|---|---|
| Gerber files (all active layers) | `pcbfab/gerber/` |
| Drill files | `pcbfab/drill/` |
| BOM (CSV) | `assembly/iv-pulse-mux-bom.csv` |
| Component placement (CSV) | `assembly/iv-pulse-mux-positions.csv` |

Fabrication toolkit options (`fabrication-toolkit-options.json`):
- All active layers exported.
- Auto-translate enabled (coordinate origin correction).
- Auto-fill enabled.
- DNP (Do Not Populate) components excluded from assembly output.

> **Note:** Gerber output directories are listed in `.gitignore` and are **not committed to the repository**. They must be regenerated locally using the KiCad job set before board submission.

---

## Design Considerations for High-Impedance Measurements

The IV-pulse multiplexer is intended for precision low-current measurements. The following PCB practices are especially important:

1. **Guard rings** — Use the `guard` net class for guard traces around all high-impedance nodes (SiPM bias, sense lines, relay contacts).
2. **Surface leakage** — Use low-absorption PCB substrate (e.g., Rogers, PTFE, or at minimum FR4 with surface treatment) if measuring below ~1 nA.
3. **Relay contact protection** — Ensure no DC paths exist across relay contacts when open (relevant for reverse-biased detectors).
4. **Ground plane continuity** — Maintain continuous ground plane under signal layers to reduce noise coupling.
5. **Trace separation** — Sufficient spacing between bias rail and sense rail to prevent leakage at high bias voltages (creepage distance rule is enforced by DRC).
