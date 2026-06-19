# Custom Component Libraries

This document describes the custom schematic symbol and PCB footprint libraries used in the ETS 96-Channel IV-Pulse Mux project. These libraries supplement KiCad's built-in standard libraries and provide project-specific components.

---

## Library Configuration Files

### `fp-lib-table`
Defines the three project footprint libraries:

```
(fp_lib_table
  (lib (name "samtec-footprints") (uri "${KIPRJMOD}/samtec-footprints.pretty") ...)
  (lib (name "passthrough")       (uri "${KIPRJMOD}/passthrough.pretty") ...)
  (lib (name "iv-mux")            (uri "${KIPRJMOD}/iv-mux.pretty") ...)
)
```

All library paths use `${KIPRJMOD}` (KiCad project directory variable), making the project portable across workstations.

### `sym-lib-table`
Defines schematic symbol libraries:

```
(sym_lib_table
  (lib (name "samtec-QSE") (uri "${KIPRJMOD}/bias-switches-symlibs/samtec-QSE.kicad_sym") ...)
  (lib (name "iv-mux-rescue") (uri "C:/Users/eamon/.../iv-mux-rescue.kicad_sym") ...)
)
```

> ⚠️ **Important:** The `iv-mux-rescue` library references an **absolute path on the original designer's Windows machine**. On any other workstation, KiCad will not find this library until the path is updated. To fix:
> 1. In KiCad, go to **Preferences → Manage Symbol Libraries → Project Libraries**.
> 2. Update the path for `iv-mux-rescue` to point to `${KIPRJMOD}/iv-mux-rescue.kicad_sym`.

---

## Footprint Libraries

### `iv-mux.pretty/` — Core Project Footprints

| Footprint File | Component | Description |
|---|---|---|
| `Relay_StandexMeder_DIP_HighProfile_SSmod.kicad_mod` | Standex-Meder reed relay | Modified DIP footprint with high-profile clearance; `SSmod` indicates surface-mount pads variant |
| `Relay_StandexMeder_HI.kicad_mod` | Standex-Meder reed relay | High-insertion DIP footprint for tall relay packages |
| `photomos.kicad_mod` | PhotoMOS relay | Generic 4-pin SOP/DIP footprint for PhotoMOS optocoupler relay |
| `TLP170J.kicad_mod` | Toshiba TLP170J | Specific footprint for TLP170J PhotoMOS relay (SOP-4) |
| `SOP-4_3.8x4.1mm_P2.54mm.kicad_mod` | Generic SOP-4 package | 3.8 × 4.1 mm body, 2.54 mm pitch — used for alternate PhotoMOS parts |
| `MCX_Vertical.kicad_mod` | MCX coaxial connector | Vertical-mount MCX receptacle |
| `NetTie-2_SMD_Pad6mil.kicad_mod` | Net tie (6 mil pad) | Zero-ohm SMD bridge for connecting net segments |
| `NetTie-2_SMD_Pad14mil.kicad_mod` | Net tie (14 mil pad) | Zero-ohm SMD bridge, wider pad variant |
| `NetTie-2_SMD_Pad20mil.kicad_mod` | Net tie (20 mil pad) | Zero-ohm SMD bridge, widest pad variant |

### `samtec-footprints.pretty/` — Samtec QSE Connector Footprints

| Footprint File | Component | Description |
|---|---|---|
| `SAMTEC_QSE-040-01-X-D-A.kicad_mod` | Samtec QSE-040-01-X-D-A | 40-pin (2×20) board-to-board socket, standard version |
| `CONN_QSE-020-01-L-D-A_SAI.kicad_mod` | Samtec QSE-020 (20-pin) | 20-pin variant with SAI alignment pin |
| `CONN_QSE-020-01-L-D-A_SAI-L.kicad_mod` | Samtec QSE-020 (long SAI) | 20-pin variant with long SAI alignment |
| `CONN_QSE-020-01-L-D-A_SAI-M.kicad_mod` | Samtec QSE-020 (mid SAI) | 20-pin variant with medium SAI alignment |
| `QSE-040-01-L-D-A.stp` | 3D model (STEP) | STEP model for the 40-pin QSE connector (3D visualization) |

### `passthrough.pretty/` — Panel and Chassis Connectors

| Footprint File | Component | Description |
|---|---|---|
| `BNC_coax_or_triax.kicad_mod` | BNC connector | Chassis/PCB-mount BNC for coaxial or triaxial connections |
| `MCX_Molex_73415-1060_Horizontal_1.6mm-PCB.kicad_mod` | Molex 73415-1060 MCX | Horizontal MCX with 1.6 mm PCB edge offset |
| `MCX_Molex_73415-1060_Horizontal_1.6mm-PCB_NOSILK.kicad_mod` | Same, no silkscreen | Same connector footprint without silkscreen markings |
| `MountingHole_2.1mm.kicad_mod` | Mounting hole | 2.1 mm diameter plated or unplated mounting hole |
| `Gripping_hole_unplated.kicad_mod` | Gripping/strain-relief hole | Unplated hole for mechanical retention (cable or board) |

---

## Schematic Symbol Libraries

### `bias-switches-symlibs/samtec-QSE.kicad_sym`

Contains custom schematic symbols for the Samtec QSE series board-to-board connectors. These symbols match the physical pinout of the QSE-040 and QSE-020 connectors used in the project.

### `iv-mux-rescue.kicad_sym`

A KiCad "rescue" library that was automatically generated to preserve symbol definitions that could not be matched to standard library components at the time of rescue. This library should be treated as read-only and its symbols should eventually be migrated to properly named custom symbols.

> See the `sym-lib-table` note above regarding the absolute path issue for this library.

---

## McGill University Logo Assets

The following files contain the McGill University logo used on PCB silkscreen layers:

| File | Format | Use |
|---|---|---|
| `mcgill-university-2.svg` | SVG vector | Source artwork |
| `mcgill-university-2.dxf` | DXF | Imported into KiCad PCB silkscreen |
| `mcgill-university-2.png` | PNG raster | Reference image |
| `mcgill-university-2a.svg` | SVG vector | Alternate/trimmed variant |
| `mcgill-university-2a.dxf` | DXF | Alternate DXF for PCB import |

---

## Adding New Components

When adding new custom components to this project:

1. **Footprint:** Create a `.kicad_mod` file in the most appropriate `.pretty` directory (`iv-mux.pretty` for board-specific parts, `passthrough.pretty` for panel/chassis connectors).
2. **Symbol:** Add a new symbol to `bias-switches-symlibs/samtec-QSE.kicad_sym` (for connectors) or create a new `.kicad_sym` file and register it in `sym-lib-table`.
3. **3D Model:** If a STEP model is available, place it in the same `.pretty` directory and reference it in the footprint's 3D model property.
4. **Documentation:** Update this file to record the new component.
