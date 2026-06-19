# IV Pulse Mux Board

**KiCad Project:** `iv-pulse-mux.kicad_pro`  
**Schematic:** `iv-pulse-mux.kicad_sch` (root) with multiple hierarchical sheets  
**PCB Layout:** `iv-pulse-mux.kicad_pcb`  
**Channels per Board:** 24  
**Number of Boards in System:** 4 (96 total channels)

---

## Purpose

The IV Pulse Mux board is the primary signal switching module in the system. Each board routes bias and sense signals to one of 24 detector channels. Four identical boards are stacked on the motherboard to achieve 96-channel coverage.

---

## Schematic Hierarchy

The schematic is organized as a hierarchical design in KiCad. The root sheet (`iv-pulse-mux.kicad_sch`) instantiates the following sub-sheets:

| Sheet File | Description |
|---|---|
| `Channels.kicad_sch` | Top-level grouping of 24 channel cells; instantiates sub-rows of `sense-relay` and `bias-relay` sheets |
| `sense-relay.kicad_sch` | Single-channel sense relay cell (PhotoMOS or reed) |
| `sense-relays.kicad_sch` | Group of sense relay cells forming one board row |
| `bias-relay.kicad_sch` | Single-channel bias relay cell (reed relay) |
| `bias-relays-with-control.kicad_sch` | Group of bias relay cells with shift register control logic |
| `control.kicad_sch` | Shift register (MIC5891) control circuitry |
| `muxboard-interface.kicad_sch` | Board-to-board connector interface (Samtec QSE-040) |

---

## Key Components

### MIC5891 Serial-In, Parallel-Out Shift Register
- **Function:** Receives 24-bit serial control data from the Arduino and drives reed relay coils.
- **Interface:** Serial data (SER), serial clock (SRCLK), register clock / latch (RCLK).
- **Output:** Active-high open-drain outputs with internal current limiting, suitable for direct relay coil drive.
- **Note:** Multiple MIC5891 devices may be daisy-chained to achieve the required 24-bit width.

### Reed Relays — Bias Path (Standex-Meder)
- **Function:** Switch the shared bias voltage rail to an individual detector channel.
- **Footprint:** `Relay_StandexMeder_DIP_HighProfile_SSmod` and `Relay_StandexMeder_HI` (custom, in `iv-mux.pretty`).
- **Type:** DIP, high-profile package for air gap clearance.
- **Drive:** Coil driven directly by MIC5891 output pin.

### PhotoMOS Relay — Sense Path
- **Function:** Connect the shared measurement/sense line to the active detector board.
- **Footprint:** `photomos` and `SOP-4_3.8x4.1mm_P2.54mm` (custom, in `iv-mux.pretty`).
- **Alternative footprint:** `TLP170J` (also available in `iv-mux.pretty`).
- **Drive:** Controlled by Arduino `iv_on_pins[]` (A0–A3), one per board.
- **Note:** One sense relay per board (not per channel), because only one channel per board is active at a time.

### Samtec QSE-040 Board-to-Board Connector
- **Function:** Mechanically and electrically connects each mux board to the motherboard.
- **Footprints:** `SAMTEC_QSE-040-01-X-D-A` (PCB), with alignment variants `_SAI`, `_SAI-L`, `_SAI-M` for stacking height compensation.
- **Pin count:** 40 pins (2×20), carries SPI-like control bus, power, and bias/sense signals.
- **3D model:** `QSE-040-01-L-D-A.stp` included in the footprint library.

### MCX Connectors — Channel Outputs
- **Function:** Individual coaxial connectors for each of the 24 channel outputs.
- **Variants used:**
  - `MCX_Vertical` — vertical mount (in `iv-mux.pretty`).
  - `MCX_Molex_73415-1060_Horizontal_1.6mm-PCB` — horizontal mount, PCB edge (in `passthrough.pretty`).
  - `MCX_Molex_73415-1060_Horizontal_1.6mm-PCB_NOSILK` — same without silkscreen.
- **Purpose:** Connects individual detector device under test (DUT) cables.

---

## Signal Description

| Signal Name | Direction | Description |
|---|---|---|
| `BIAS_IN` | Input | Shared bias voltage from bias supply |
| `SENSE_IN` | Bidirectional | Shared sense/measurement line |
| `CH[1..24]` | Output | Individual detector channel connections (MCX) |
| `SER` | Input | Serial data from Arduino (one per board) |
| `SRCLK` | Input | Shift register clock (shared across boards) |
| `RCLK` | Input | Latch clock (shared across boards) |
| `IV_ON` | Input | Sense relay enable (one per board, from Arduino A0–A3) |
| `OE_N` | Input | Output enable (active low); shared across all boards |
| `+5V`, `GND` | Power | Logic and relay coil supply |
| `+BIAS`, `BIAS_GND` | Power | High-voltage bias supply rails |

---

## PCB Design

### Layer Stack
The `iv-pulse-mux.kicad_pcb` design uses a multi-layer stack (up to 31 copper layers as configured in the design rules, though the actual fabricated layer count should be confirmed from the Gerber outputs). See [PCB Design Rules](pcb-design-rules.md) for the full net class assignments.

### Net Classes (Summary)

| Net Class | Typical Traces | Track Width |
|---|---|---|
| `Default` | Control signals, low-current | 0.2032 mm |
| `power` | `+5V`, `GND`, `+BIAS` | 0.508 mm |
| `guard` | Guard ring traces | 0.4064 mm |
| `zcontrol` | SiPM signal traces, RF signals | 0.33528 mm |

### Hierarchical PCB

The file `iv-pulse-mux.kicad_pcb.hierpcb.json` indicates use of KiCad's hierarchical PCB feature, allowing the repeated 24-channel layout to be managed efficiently.

### Custom Footprints

All project-specific footprints are contained in the `iv-mux.pretty/` library. See [Component Libraries](component-libraries.md) for details.

---

## Board Dimensions and Connector Placement

> **Note:** Exact board dimensions and connector coordinates are defined in `iv-pulse-mux.kicad_pcb`. This document describes the design intent; the PCB file is the authoritative source for mechanical dimensions.

- Board edge cut outline is defined in the PCB file.
- Mounting holes use `MountingHole_2.1mm` footprint (in `passthrough.pretty`).
- `Gripping_hole_unplated` (in `passthrough.pretty`) provides mechanical strain relief.
- The McGill University logo appears on the silkscreen (imported from `mcgill-university-2.dxf`/`.svg`).

---

## Known Issues (Rev 1.0)

| Issue | Location | Impact |
|---|---|---|
| `BYPASS` signal connected to Arduino pin 12 (temporary) | Firmware + PCB | Signal routing workaround; should be assigned a dedicated pin |
| `iv_on_pins[]` uses `A0–A3` instead of intended `THERM1–THERM4` | Firmware | Thermistor monitoring not available on those pins |
| `iv-mux-rescue` symbol library references absolute path | `sym-lib-table` | Must be remapped on any new workstation |
