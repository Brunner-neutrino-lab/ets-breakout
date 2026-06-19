# Motherboard

**KiCad Project:** `iv-pulse-motherboard.kicad_pro`  
**Schematic:** `iv-pulse-motherboard.kicad_sch`  
**PCB Layout:** `iv-pulse-motherboard.kicad_pcb`

---

## Purpose

The motherboard is the central hub of the ETS 96-channel IV-Pulse Multiplexer system. It:

1. Hosts the **Arduino Nano Every** microcontroller.
2. Distributes the **SPI-like shift register control bus** (SRCLK, RCLK, SER0–SER3) to all four mux boards.
3. Routes the **sense relay enable signals** (IV_ON0–IV_ON3) to the mux boards.
4. Provides **power distribution** (5 V logic, bias voltage, and ground) to all mux boards via board-to-board connectors.
5. Accepts the **shared bias supply input** and the **shared sense/measurement line** from the measurement instrument.
6. Hosts all **QSE-040 board-to-board socket connectors** for the four mux boards.

---

## Schematic Hierarchy

The root schematic `iv-pulse-motherboard.kicad_sch` references the following sub-sheet:

| Sheet File | Description |
|---|---|
| `muxboard-interface.kicad_sch` | Interface circuitry for one mux board slot (instantiated 4 times) |

The motherboard uses the same `muxboard-interface.kicad_sch` hierarchical sheet as the mux board, which defines the 40-pin board-to-board connector pinout and any signal conditioning (level shifting, filtering, etc.) at the interface.

---

## Key Components

### Arduino Nano Every
- **MCU:** ATmega4809 (compiled under Mega2560 board profile)
- **Supply:** 5 V USB or external
- **Serial:** Connected to control PC via USB-to-UART or TTL UART on Serial1
- **GPIO usage:**

| Pin | Signal | Direction | Description |
|---|---|---|---|
| 2 | SER0 | Output | Serial data to Mux Board 0 |
| 3 | SER1 | Output | Serial data to Mux Board 1 |
| 4 | SER2 | Output | Serial data to Mux Board 2 |
| 5 | SER3 | Output | Serial data to Mux Board 3 |
| 8 | SYNC_PULSE | Input | External sync/trigger input (pull-up) |
| 9 | SRCLK | Output | Shift register serial clock |
| 10 | RCLK | Output | Shift register latch/strobe |
| 11 | OE_N / SRCLR | Output | Output enable (active low) |
| 12 | BYPASS | Output | Bypass line control (temporary assignment) |
| 13 | IV_ON (legacy) | — | Not used in IV-pulse-mux variant |
| A0 | IV_ON0 | Output | Sense relay enable, Board 0 |
| A1 | IV_ON1 | Output | Sense relay enable, Board 1 |
| A2 | IV_ON2 | Output | Sense relay enable, Board 2 |
| A3 | IV_ON3 | Output | Sense relay enable, Board 3 |

### QSE-040 Socket Connectors (×4)
- **Part:** Samtec QSE-040-01-X-D-A (socket side)
- **Mates with:** QSH-040 or equivalent header on each mux board
- **Purpose:** Carries all signals, power, and bias lines between motherboard and each mux board
- **Footprints:** `SAMTEC_QSE-040-01-X-D-A` in `samtec-footprints.pretty`

### Bias Supply Interface
- Provides the shared `BIAS_IN` rail to all mux boards via the QSE connector.
- The bias supply connection on the motherboard should include appropriate protection (TVS diode, fuse) — verify in the PCB schematic.

### Sense Line Interface
- Provides the shared `SENSE` line routed to all mux boards.
- Only the selected board's PhotoMOS relay connects this line to the active channel at any given time.

---

## Power Architecture

| Rail | Source | Distribution |
|---|---|---|
| +5 V | Arduino USB or external regulator | Provided to all QSE connectors; powers relay coils and logic on mux boards |
| GND | Common ground | All boards share a common ground reference |
| +BIAS | External bias supply input | Routed through motherboard to all QSE connectors; each mux board switches it per channel |
| BIAS_GND | Bias return (may be isolated) | Should be carefully considered for ground loop avoidance in high-impedance measurements |

> **Note:** The exact power topology (isolated vs. common ground, bulk capacitance, filtering) should be verified in the `iv-pulse-motherboard.kicad_sch` schematic. This document reflects design intent; the schematic is authoritative.

---

## Board-to-Board Mechanical Assembly

1. The four mux boards mount perpendicular or parallel to the motherboard via the Samtec QSE-040 connectors (stacking orientation depends on board outline design).
2. The QSE connector provides both the electrical interface and mechanical support.
3. Additional mechanical support (standoffs, gripping holes) may be present on both boards — see `passthrough.pretty/Gripping_hole_unplated.kicad_mod`.
4. Mounting holes use `MountingHole_2.1mm` from the `passthrough.pretty` library.

---

## External Connectors on Motherboard

| Connector | Type | Signal |
|---|---|---|
| Bias input | BNC or terminal block | External bias voltage supply (`BIAS_IN`, `BIAS_GND`) |
| Sense line | BNC or MCX | Shared measurement line to/from instrument |
| Arduino USB | Micro-USB (onboard Arduino) | Firmware programming and serial control |
| SYNC input | MCX or BNC | External trigger input for timed channel switching |
| BYPASS | MCX or test point | Bypass signal output |

> Exact connector types are defined in the PCB layout. Refer to `iv-pulse-motherboard.kicad_pcb` for authoritative placement.

---

## Known Issues (Rev 1.0)

| Issue | Details |
|---|---|
| BYPASS pin assignment | Pin 12 used as a temporary workaround; correct pin should be chosen in next revision |
| Thermistor inputs unused | A0–A3 occupied by IV_ON signals; thermistor monitoring deferred |
| Absolute symbol library path | `iv-mux-rescue` in `sym-lib-table` points to designer's local path; must be remapped |
